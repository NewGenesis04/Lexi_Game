from __future__ import annotations

import asyncio
import json
import random
import string
import time
import uuid

from fastapi import HTTPException

from game_engine import bag as bag_module, board as board_module, scoring
from game_engine import dictionary as dict_module
from game_engine.models import (
    Dictionary, GamePhase, GameState, Move, MoveType, PlacedTile, Player, Tile,
)

from backend_api import game_manager, sse_manager
from backend_api.repositories.game_repo import GameRepo
from backend_api.schemas import CreateGameOut, GameStateOut, JoinGameOut
from backend_api.session import PlayerSession, generate_token


def _generate_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class GameService:
    def __init__(self, repo: GameRepo) -> None:
        self._repo = repo

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def create_game(
        self, nickname: str, dictionary: Dictionary, time_per_player_secs: float
    ) -> CreateGameOut:
        code = _generate_code()
        player_id = str(uuid.uuid4())
        token = generate_token()

        bag = bag_module.build_bag()
        rack, bag = bag_module.draw_tiles(bag, 7)

        state = GameState(
            code=code,
            phase=GamePhase.CREATED,
            dictionary=dictionary,
            bag=bag,
            players=[
                Player(
                    id=player_id,
                    nickname=nickname,
                    rack=rack,
                    time_remaining_secs=time_per_player_secs,
                )
            ],
        )

        await self._repo.save_game(state)
        await self._repo.save_session(token, PlayerSession(
            token=token, player_id=player_id, game_code=code, nickname=nickname
        ))
        await self._repo.register_active(code)

        return CreateGameOut(code=code, token=token, player_id=player_id)

    async def join_game(self, code: str, nickname: str) -> JoinGameOut:
        async with game_manager.get_lock(code):
            state = await self._load_or_404(code)
            if state.phase != GamePhase.CREATED:
                raise HTTPException(status_code=400, detail="Game already started")
            if len(state.players) >= 2:
                raise HTTPException(status_code=400, detail="Game is full")

            player_id = str(uuid.uuid4())
            token = generate_token()

            rack, new_bag = bag_module.draw_tiles(state.bag, 7)
            state.bag = new_bag
            state.players.append(
                Player(
                    id=player_id,
                    nickname=nickname,
                    rack=rack,
                    time_remaining_secs=state.players[0].time_remaining_secs,
                )
            )
            state.phase = GamePhase.PLAYING

            await self._repo.save_game(state)
            await self._repo.save_session(token, PlayerSession(
                token=token, player_id=player_id, game_code=code, nickname=nickname
            ))
            self._start_timer(state)

            return JoinGameOut(
                token=token,
                player_id=player_id,
                state=GameStateOut.from_domain(state, viewer_id=player_id),
            )

    async def get_game(self, code: str, player_id: str) -> GameStateOut:
        state = await self._load_or_404(code)
        return GameStateOut.from_domain(state, viewer_id=player_id)

    async def place_tiles(
        self, code: str, player_id: str, placed: list[PlacedTile]
    ) -> GameStateOut:
        async with game_manager.get_lock(code):
            state = await self._load_or_404(code)
            self._assert_turn(state, player_id)

            if not board_module.validate_placement(state, placed):
                raise HTTPException(status_code=422, detail="Invalid placement")

            new_board = board_module.apply_placement(state.board, placed)
            for word in board_module.formed_words(new_board, placed):
                if not dict_module.is_valid_word(word, state.dictionary):
                    raise HTTPException(status_code=422, detail=f"{word} is not a valid word")

            points = scoring.score_placement(state.board, placed)
            state.board = new_board

            player = state.players[state.current_player_index]
            player.score += points

            remaining = list(player.rack)
            for pt in placed:
                found = False
                for i, t in enumerate(remaining):
                    if t.letter == pt.letter:
                        remaining.pop(i)
                        found = True
                        break
                if not found:
                    raise HTTPException(status_code=422, detail="Placed tile not in rack")

            drawn, state.bag = bag_module.draw_tiles(state.bag, len(placed))
            player.rack = remaining + drawn

            move = Move(type=MoveType.PLACE, player_id=player_id, tiles=placed, letters=[])
            state.last_move = move
            state.move_history.append(move)
            state.consecutive_passes = 0

            if self._check_end(state):
                await self._repo.save_game(state)
                await self._broadcast(state)
                game_manager.remove_game(code)
                return GameStateOut.from_domain(state, viewer_id=player_id)

            if self._deduct_time(state, code):
                return await self._end_by_timeout(state, code, player_id)

            self._advance_turn(state)
            await self._repo.save_game(state)
            self._start_timer(state)
            await self._broadcast(state)

        return GameStateOut.from_domain(state, viewer_id=player_id)

    async def swap_tiles(
        self, code: str, player_id: str, letters: list[str]
    ) -> GameStateOut:
        async with game_manager.get_lock(code):
            state = await self._load_or_404(code)
            self._assert_turn(state, player_id)

            if len(state.bag) < len(letters):
                raise HTTPException(status_code=422, detail="Not enough tiles in bag to swap")

            player = state.players[state.current_player_index]
            returned: list[Tile] = []
            temp = list(player.rack)
            for letter in letters:
                for i, t in enumerate(temp):
                    if t.letter == letter:
                        returned.append(temp.pop(i))
                        break
            if len(returned) != len(letters):
                raise HTTPException(status_code=422, detail="Letters not in rack")

            drawn, state.bag = bag_module.exchange_tiles(state.bag, returned, len(letters))
            player.rack = temp + drawn

            move = Move(type=MoveType.SWAP, player_id=player_id, tiles=[], letters=letters)
            state.last_move = move
            state.move_history.append(move)
            state.consecutive_passes = 0

            if self._deduct_time(state, code):
                return await self._end_by_timeout(state, code, player_id)

            self._advance_turn(state)
            await self._repo.save_game(state)
            self._start_timer(state)
            await self._broadcast(state)

        return GameStateOut.from_domain(state, viewer_id=player_id)

    async def pass_turn(self, code: str, player_id: str) -> GameStateOut:
        async with game_manager.get_lock(code):
            state = await self._load_or_404(code)
            self._assert_turn(state, player_id)

            state.consecutive_passes += 1
            move = Move(type=MoveType.PASS, player_id=player_id, tiles=[], letters=[])
            state.last_move = move
            state.move_history.append(move)

            if state.consecutive_passes >= 6:
                state.phase = GamePhase.FINISHED
                await self._repo.save_game(state)
                await self._broadcast(state)
                game_manager.remove_game(code)
                return GameStateOut.from_domain(state, viewer_id=player_id)

            if self._deduct_time(state, code):
                return await self._end_by_timeout(state, code, player_id)

            self._advance_turn(state)
            await self._repo.save_game(state)
            self._start_timer(state)
            await self._broadcast(state)

        return GameStateOut.from_domain(state, viewer_id=player_id)

    async def forfeit(self, code: str, player_id: str) -> GameStateOut:
        async with game_manager.get_lock(code):
            game_manager.clear_turn_started(code)
            state = await self._load_or_404(code)
            state.phase = GamePhase.FINISHED
            move = Move(type=MoveType.FORFEIT, player_id=player_id, tiles=[], letters=[])
            state.last_move = move
            state.move_history.append(move)
            await self._repo.save_game(state)
            await self._broadcast(state)
            game_manager.remove_game(code)

        return GameStateOut.from_domain(state, viewer_id=player_id)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    async def _load_or_404(self, code: str) -> GameState:
        state = await self._repo.load_game(code)
        if state is None:
            raise HTTPException(status_code=404, detail="Game not found")
        return state

    def _assert_turn(self, state: GameState, player_id: str) -> None:
        if state.phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game is not in progress")
        if state.players[state.current_player_index].id != player_id:
            raise HTTPException(status_code=403, detail="Not your turn")

    def _advance_turn(self, state: GameState) -> None:
        state.current_player_index = (state.current_player_index + 1) % len(state.players)

    def _check_end(self, state: GameState) -> bool:
        """True (and mutates state to FINISHED) when bag empty and current player emptied rack."""
        if state.bag:
            return False
        player = state.players[state.current_player_index]
        if player.rack:
            return False

        for p in state.players:
            if p.id == player.id:
                continue
            penalty = sum(t.points for t in p.rack)
            p.score -= penalty
            player.score += penalty

        state.phase = GamePhase.FINISHED
        return True

    def _deduct_time(self, state: GameState, code: str) -> bool:
        """
        Deducts elapsed time from the current player's bank.
        - First overspend: applies −10 penalty, resets bank to 60 s, increments overtime_count.
        - Second overspend: sets bank to 0 s and returns True (caller must end the game).
        Returns True only when the second overtime fires and a forfeit is required.
        """
        elapsed = game_manager.get_elapsed(code)
        game_manager.clear_turn_started(code)
        player = state.players[state.current_player_index]
        new_time = player.time_remaining_secs - elapsed

        if new_time > 0:
            player.time_remaining_secs = new_time
            return False

        if player.overtime_count == 0:
            player.score -= 10
            player.overtime_count = 1
            player.time_remaining_secs = 60.0
            return False

        # Second overspend — caller must end the game
        player.time_remaining_secs = 0.0
        return True

    def _start_timer(self, state: GameState) -> None:
        game_manager.set_turn_started(state.code)
        player = state.players[state.current_player_index]
        task = asyncio.create_task(
            self._time_bank_task(state.code, player.id, player.time_remaining_secs)
        )
        game_manager.set_timer(state.code, task)

    async def _time_bank_task(self, code: str, player_id: str, secs: float) -> None:
        await asyncio.sleep(secs)
        async with game_manager.get_lock(code):
            state = await self._repo.load_game(code)
            if state is None or state.phase != GamePhase.PLAYING:
                return
            if state.players[state.current_player_index].id != player_id:
                return

            player = state.players[state.current_player_index]
            if player.overtime_count == 0:
                player.score -= 10
                player.time_remaining_secs = 60.0
                player.overtime_count = 1
                game_manager.set_turn_started(code)
                await self._repo.save_game(state)
                await self._broadcast(state)
                task = asyncio.create_task(
                    self._time_bank_task(code, player_id, 60.0)
                )
                game_manager.set_timer(code, task)
            else:
                player.time_remaining_secs = 0.0
                state.phase = GamePhase.FINISHED
                move = Move(type=MoveType.TIMEOUT, player_id=player_id, tiles=[], letters=[])
                state.last_move = move
                state.move_history.append(move)
                await self._repo.save_game(state)
                await self._broadcast(state)
                game_manager.remove_game(code)

    async def _end_by_timeout(self, state: GameState, code: str, viewer_id: str) -> GameStateOut:
        """Ends the game when a player exhausts their second overtime bank mid-move."""
        timed_out_id = state.players[state.current_player_index].id
        state.phase = GamePhase.FINISHED
        move = Move(type=MoveType.TIMEOUT, player_id=timed_out_id, tiles=[], letters=[])
        state.last_move = move
        state.move_history.append(move)
        await self._repo.save_game(state)
        await self._broadcast(state)
        game_manager.remove_game(code)
        return GameStateOut.from_domain(state, viewer_id=viewer_id)

    async def _broadcast(self, state: GameState) -> None:
        tokens = sse_manager.tokens_for_game(state.code)
        payloads: dict[str, str] = {}
        for token in tokens:
            session = await self._repo.load_session(token)
            if session is None:
                continue
            view = GameStateOut.from_domain(state, viewer_id=session.player_id)
            payloads[token] = json.dumps(view.model_dump(mode="json"))
        await sse_manager.broadcast(payloads)
