from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import string
import time
import uuid

from fastapi import HTTPException

logger = logging.getLogger(__name__)

from game_engine import bag as bag_module, board as board_module, scoring  # noqa: E402
from game_engine import dictionary as dict_module # noqa: E402
from game_engine.models import ( # noqa: E402
    Dictionary, GamePhase, GameState, Move, MoveType, PlacedTile, Player, Tile,
) 

from backend_api import game_manager, sse_manager # noqa: E402
from backend_api.repositories.game_repo import GameRepo # noqa: E402
from backend_api.schemas import CreateGameOut, GameStateOut, JoinGameOut # noqa: E402
from backend_api.session import PlayerSession, generate_token # noqa: E402


def _generate_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class GameService:
    def __init__(self, repo: GameRepo) -> None:
        self._repo = repo

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def create_game(
        self, nickname: str, dictionary: Dictionary, time_per_player_secs: float, avatar: str | None = None
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
                    avatar=avatar,
                )
            ],
        )

        await self._repo.save_game(state)
        await self._repo.save_session(token, PlayerSession(
            token=token, player_id=player_id, game_code=code, nickname=nickname
        ))
        await self._repo.register_active(code)
        logger.info(f"Game {code} created by {nickname} (dict={dictionary}, time={int(time_per_player_secs)}s)")

        return CreateGameOut(code=code, token=token, player_id=player_id)

    async def join_game(self, code: str, nickname: str, avatar: str | None = None) -> JoinGameOut:
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
                    avatar=avatar,
                )
            )
            state.phase = GamePhase.PLAYING

            await self._repo.save_game(state)
            await self._repo.save_session(token, PlayerSession(
                token=token, player_id=player_id, game_code=code, nickname=nickname
            ))
            self._start_timer(state)
            p1, p2 = state.players[0].nickname, state.players[1].nickname
            logger.info(f"Game {code} started: {p1} vs {p2}")

            return JoinGameOut(
                token=token,
                player_id=player_id,
                state=self._to_view(state, viewer_id=player_id),
            )

    async def get_game(self, code: str, player_id: str) -> GameStateOut:
        state = await self._load_or_404(code)
        return self._to_view(state, viewer_id=player_id)

    async def place_tiles(
        self, code: str, player_id: str, placed: list[PlacedTile]
    ) -> GameStateOut:
        payloads: dict[str, str] | None = None
        async with game_manager.get_lock(code):
            state = await self._load_or_404(code)
            self._assert_turn(state, player_id)

            try:
                if not board_module.validate_placement(state, placed):
                    raise HTTPException(status_code=422, detail="Invalid placement")

                new_board = board_module.apply_placement(state.board, placed)
                formed = board_module.formed_words(new_board, placed)
                for word in formed:
                    if not dict_module.is_valid_word(word, state.dictionary):
                        raise HTTPException(status_code=422, detail=f"{word} is not a valid word")
            except HTTPException:
                await self._broadcast_notification(code, player_id, "Opponent made an invalid move")
                raise

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

            move = Move(type=MoveType.PLACE, player_id=player_id, tiles=placed, letters=[], score_delta=points, words=formed)
            state.last_move = move
            state.move_history.append(move)
            state.consecutive_passes = 0

            if self._check_end(state):
                await self._repo.save_game(state)
                await self._broadcast(state)
                game_manager.remove_game(code)
                return self._to_view(state, viewer_id=player_id)

            if self._deduct_time(state, code):
                return await self._end_by_timeout(state, code, player_id)

            self._advance_turn(state)
            await self._repo.save_game(state)
            payloads = await self._serialize_game(state)
            self._start_timer(state)

        if payloads:
            await sse_manager.broadcast(payloads)
        return self._to_view(state, viewer_id=player_id)

    async def swap_tiles(
        self, code: str, player_id: str, letters: list[str]
    ) -> GameStateOut:
        payloads: dict[str, str] | None = None
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
            payloads = await self._serialize_game(state)
            self._start_timer(state)

        if payloads:
            await sse_manager.broadcast(payloads)
        return self._to_view(state, viewer_id=player_id)

    async def pass_turn(self, code: str, player_id: str) -> GameStateOut:
        payloads: dict[str, str] | None = None
        async with game_manager.get_lock(code):
            state = await self._load_or_404(code)
            self._assert_turn(state, player_id)

            state.consecutive_passes += 1
            move = Move(type=MoveType.PASS, player_id=player_id, tiles=[], letters=[])
            state.last_move = move
            state.move_history.append(move)

            if state.consecutive_passes >= 6:
                state.phase = GamePhase.FINISHED
                for p in state.players:
                    p.score -= sum(t.points for t in p.rack)
                logger.info(f"Game {code} ended by 6 consecutive passes")
                await self._repo.save_game(state)
                await self._broadcast(state)
                game_manager.remove_game(code)
                return self._to_view(state, viewer_id=player_id)

            if self._deduct_time(state, code):
                return await self._end_by_timeout(state, code, player_id)

            self._advance_turn(state)
            await self._repo.save_game(state)
            payloads = await self._serialize_game(state)
            self._start_timer(state)

        if payloads:
            await sse_manager.broadcast(payloads)
        return self._to_view(state, viewer_id=player_id)

    async def forfeit(self, code: str, player_id: str) -> GameStateOut:
        payloads: dict[str, str] | None = None
        async with game_manager.get_lock(code):
            game_manager.clear_turn_started(code)
            state = await self._load_or_404(code)
            forfeiter = next((p.nickname for p in state.players if p.id == player_id), player_id)
            logger.info(f"Game {code}: {forfeiter} forfeited")
            state.phase = GamePhase.FINISHED
            move = Move(type=MoveType.FORFEIT, player_id=player_id, tiles=[], letters=[])
            state.last_move = move
            state.move_history.append(move)
            await self._repo.save_game(state)
            payloads = await self._serialize_game(state)
            game_manager.remove_game(code)

        if payloads:
            await sse_manager.broadcast(payloads)
        return self._to_view(state, viewer_id=player_id)

    # -----------------------------------------------------------------------
    # Disconnect / Adjournment
    # -----------------------------------------------------------------------

    async def connect_player(self, code: str, player_id: str, token: str = "") -> None:
        """Register an SSE connection for a player. If game was PAUSED and both
        are back, resume. Silently returns if the game doesn't exist."""
        async with game_manager.get_lock(code):
            game_manager.add_connection(code, player_id, token)

            state = await self._repo.load_game(code)
            if state is None:
                return
            if state.phase not in (GamePhase.PLAYING, GamePhase.PAUSED):
                return
            if not any(p.id == player_id for p in state.players):
                return

            if state.phase == GamePhase.PAUSED:
                cmap = game_manager.get_connected(code)
                all_connected = all(
                    cmap.get(p.id, False) for p in state.players
                )
                if all_connected:
                    self._resume_game(state)
                    await self._repo.save_game(state)
                    await self._broadcast(state)
                    return

            await self._repo.save_game(state)

    async def disconnect_player(self, code: str, player_id: str, token: str = "") -> None:
        """Remove one SSE connection for a player. If no connections remain,
        schedule a short grace pause. If the player reconnects (new SSE) before
        the grace timer fires, the pause is cancelled.
        Does nothing if the player was never marked connected.
        Silently returns if the game doesn't exist — safe to call from SSE generator."""
        async with game_manager.get_lock(code):
            state = await self._repo.load_game(code)
            if state is None:
                return
            if state.phase not in (GamePhase.PLAYING, GamePhase.PAUSED):
                return
            if not any(p.id == player_id for p in state.players):
                return

            was_last = game_manager.remove_connection(code, player_id, token)
            if not was_last:
                return  # player still has other active connections

            if state.phase == GamePhase.PLAYING:
                task = asyncio.create_task(
                    self._pause_after_grace(code, player_id)
                )
                game_manager.schedule_disconnect_check(code, player_id, task)
            elif state.phase == GamePhase.PAUSED:
                await self._repo.save_game(state)
                self._spawn_disconnect_grace_task(state)

    def _pause_game(self, state: GameState) -> None:
        """Freeze the active turn clock and transition to PAUSED."""
        elapsed = game_manager.get_elapsed(state.code)
        game_manager.clear_turn_started(state.code)
        player = state.players[state.current_player_index]
        new_time = player.time_remaining_secs - elapsed
        new_time = math.floor(max(0.0, new_time))

        state.paused_time_left = new_time
        state.paused_at = time.time()
        state.phase = GamePhase.PAUSED

    def _resume_game(self, state: GameState) -> None:
        """Restore from paused and transition back to PLAYING."""
        game_manager.cancel_pause_timer(state.code)
        player = state.players[state.current_player_index]
        if state.paused_time_left is not None:
            player.time_remaining_secs = state.paused_time_left
        state.paused_time_left = None
        state.paused_at = None
        state.phase = GamePhase.PLAYING
        self._start_timer(state)

    def _spawn_disconnect_grace_task(self, state: GameState) -> None:
        """Spawn or reset the 5-minute grace timer for a paused game."""
        task = asyncio.create_task(
            self._disconnect_grace_task(state.code, grace_secs=300.0)
        )
        game_manager.set_pause_timer(state.code, task)

    async def _disconnect_grace_task(self, code: str, grace_secs: float = 300.0) -> None:
        """5-minute grace period. After expiry, forfeit against the disconnected player.
        Always cleans up runtime state (lock, timers, connected map) when PAUSED."""
        try:
            await asyncio.sleep(grace_secs)
        except asyncio.CancelledError:
            return

        async with game_manager.get_lock(code):
            state = await self._repo.load_game(code)
            if state is None:
                game_manager.remove_game(code)
                return
            game_manager.cancel_pause_timer(code)
            if state.phase != GamePhase.PAUSED:
                return  # game was resumed or finished since timer started

            cmap = game_manager.get_connected(code)
            connected_ids = [pid for pid, c in cmap.items() if c]
            if len(connected_ids) == 1:
                winner_id = connected_ids[0]
                loser = next(p for p in state.players if p.id != winner_id)
                logger.info(f"Game {code}: {loser.nickname} forfeited by disconnection timeout")
                state.phase = GamePhase.FINISHED
                move = Move(type=MoveType.TIMEOUT, player_id=loser.id, tiles=[], letters=[])
                state.last_move = move
                state.move_history.append(move)
                state.paused_time_left = None
                state.paused_at = None
                await self._repo.save_game(state)
                await self._broadcast(state)

            game_manager.remove_game(code)

    async def _pause_after_grace(self, code: str, player_id: str, grace_secs: float = 10.0) -> None:
        """Wait grace_secs, then pause the game if the player is still gone.
        Cancelled automatically by game_manager.cancel_disconnect_check when
        connect_player re-marks the player."""
        try:
            await asyncio.sleep(grace_secs)
        except asyncio.CancelledError:
            return

        async with game_manager.get_lock(code):
            if game_manager.is_player_connected(code, player_id):
                return  # reconnected during grace window
            state = await self._repo.load_game(code)
            if state is None or state.phase != GamePhase.PLAYING:
                return
            self._pause_game(state)
            await self._repo.save_game(state)
            await self._broadcast(state)
            self._spawn_disconnect_grace_task(state)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _to_view(self, state: GameState, viewer_id: str) -> GameStateOut:
        return GameStateOut.from_domain(
            state,
            viewer_id=viewer_id,
            connected_map=game_manager.get_connected(state.code),
        )

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
        logger.info(f"Game {state.code} ended normally (bag empty)")
        return True

    def _deduct_time(self, state: GameState, code: str) -> bool:
        """
        Deducts elapsed time from the current player's bank.
        - Each of the first 3 overspends: applies −10 penalty, resets bank to 60 s,
          increments overtime_count (max −30 pts total across three overtime minutes).
        - Fourth overspend: sets bank to 0 s and returns True (caller must end the game).
        Returns True only when the forfeit threshold is reached.
        """
        elapsed = game_manager.get_elapsed(code)
        game_manager.clear_turn_started(code)
        player = state.players[state.current_player_index]
        new_time = player.time_remaining_secs - elapsed

        if new_time > 0:
            player.time_remaining_secs = new_time
            return False

        if player.overtime_count < 3:
            player.score -= 10
            player.overtime_count += 1
            player.time_remaining_secs = 60.0
            logger.warning(f"Game {code}: OT·{player.overtime_count} granted to {player.nickname} (-10 pts)")
            return False

        # Three full overtime minutes exhausted — caller must end the game
        logger.warning(f"Game {code}: {player.nickname} exhausted all OT — forfeiting")
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
            if player.overtime_count < 3:
                player.score -= 10
                player.overtime_count += 1
                player.time_remaining_secs = 60.0
                logger.warning(f"Game {code}: OT·{player.overtime_count} granted to {player.nickname} (-10 pts) via timer")
                game_manager.set_turn_started(code)
                await self._repo.save_game(state)
                await self._broadcast(state)
                task = asyncio.create_task(
                    self._time_bank_task(code, player_id, 60.0)
                )
                game_manager.set_timer(code, task)
            else:
                logger.warning(f"Game {code}: {player.nickname} timed out after 3 OT minutes")
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
        return self._to_view(state, viewer_id=viewer_id)

    async def _broadcast(self, state: GameState) -> None:
        tokens = sse_manager.tokens_for_game(state.code)
        payloads: dict[str, str] = {}
        for token in tokens:
            pid = sse_manager.player_id_for_token(token)
            if pid is None:
                continue
            view = self._to_view(state, viewer_id=pid)
            payloads[token] = json.dumps(view.model_dump(mode="json"))
        await sse_manager.broadcast(payloads)

    async def _serialize_game(self, state: GameState) -> dict[str, str]:
        """Serialise game state once per connected player. Returns {token: json_string}.
        Call inside the lock; pass result to sse_manager.broadcast() outside the lock."""
        tokens = sse_manager.tokens_for_game(state.code)
        payloads: dict[str, str] = {}
        for token in tokens:
            pid = sse_manager.player_id_for_token(token)
            if pid is None:
                continue
            view = self._to_view(state, viewer_id=pid)
            payloads[token] = json.dumps(view.model_dump(mode="json"))
        return payloads

    async def _broadcast_notification(
        self, game_code: str, skip_player_id: str, text: str, notif_type: str = "error",
    ) -> None:
        """Send a notification SSE event to all connected players except skip_player_id."""
        tokens = sse_manager.tokens_for_game(game_code)
        payloads: dict[str, str] = {}
        for token in tokens:
            pid = sse_manager.player_id_for_token(token)
            if pid is None or pid == skip_player_id:
                continue
            payloads[token] = json.dumps(
                {"type": "notification", "payload": {"text": text, "type": notif_type}},
            )
        if payloads:
            await sse_manager.broadcast(payloads)
