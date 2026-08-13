from __future__ import annotations

import asyncio
import logging
import random
import string
import uuid

from fastapi import HTTPException

logger = logging.getLogger(__name__)

from game_engine import bag as bag_module
from game_engine import Turn, TurnError, TurnOutcome, TurnResult
from game_engine.models import (
    Dictionary, GamePhase, GameState, Move, MoveType, Player, Tile,
)

from backend_api import game_manager, sse_manager, turn_clock
from backend_api.connection_lifecycle import lifecycle
from backend_api.game_broadcaster import broadcaster
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
        payloads: dict[str, str] | None = None
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
            # Push the started game to whoever's already sitting in the lobby
            # (the creator) — otherwise their screen never learns someone
            # joined until they refresh.
            payloads = broadcaster.serialize(state, lifecycle.connected_map(code))

        if payloads:
            await sse_manager.broadcast(payloads)

        return JoinGameOut(
            token=token,
            player_id=player_id,
            state=self._to_view(state, viewer_id=player_id),
        )

    async def get_game(self, code: str, player_id: str) -> GameStateOut:
        state = await self._load_or_404(code)
        return self._to_view(state, viewer_id=player_id)

    async def apply_move(
        self, code: str, player_id: str, request: Turn.Request,
    ) -> GameStateOut:
        """Execute any player move (place/swap/pass) through the engine's Turn
        module. Maps TurnError values to HTTP and end-of-game outcomes to
        broadcast + cleanup at the seam."""
        payloads: dict[str, str] | None = None
        async with game_manager.get_lock(code):
            state = await self._load_or_404(code)

            try:
                elapsed_secs = turn_clock.clock.elapsed(code)
                state, result = Turn.apply(state, request, elapsed_secs)
            finally:
                # Re-anchor rather than clear: the elapsed time above has just
                # been charged to the player, so the next measurement window
                # starts now — clearing would let elapsed() silently read ~0
                # for however long it takes them to try again.
                turn_clock.clock.mark_turn_started(code)

            if not result.ok:
                # NOT_YOUR_TURN / NOT_PLAYING are rejected before any clock
                # charge happens, so only the other errors mutate the state.
                # Rejected-move feedback (including which word failed) stays
                # private to the mover via the HTTP error below — the
                # opponent doesn't need to know about a move that never
                # actually happened.
                if result.error not in (TurnError.NOT_YOUR_TURN, TurnError.NOT_PLAYING):
                    await self._repo.save_game(state)
                self._raise_move_error(result)
                raise AssertionError("unreachable")

            if result.outcome != TurnOutcome.OK:
                await self._repo.save_game(state)
                await broadcaster.broadcast(state, lifecycle.connected_map(code))
                lifecycle.remove_game(code)
                return self._to_view(state, viewer_id=player_id)

            await self._repo.save_game(state)
            payloads = broadcaster.serialize(state, lifecycle.connected_map(code))
            self._start_timer(state)

        if payloads:
            await sse_manager.broadcast(payloads)
        return self._to_view(state, viewer_id=player_id)

    async def forfeit(self, code: str, player_id: str) -> GameStateOut:
        payloads: dict[str, str] | None = None
        async with game_manager.get_lock(code):
            turn_clock.clock.clear(code)
            state = await self._load_or_404(code)
            forfeiter = next((p.nickname for p in state.players if p.id == player_id), player_id)
            logger.info(f"Game {code}: {forfeiter} forfeited")
            state.phase = GamePhase.FINISHED
            move = Move(type=MoveType.FORFEIT, player_id=player_id, tiles=[], letters=[])
            state.last_move = move
            state.move_history.append(move)
            await self._repo.save_game(state)
            payloads = broadcaster.serialize(state, lifecycle.connected_map(code))
            lifecycle.remove_game(code)

        if payloads:
            await sse_manager.broadcast(payloads)
        return self._to_view(state, viewer_id=player_id)

    # -----------------------------------------------------------------------
    # Disconnect / Adjournment
    # -----------------------------------------------------------------------

    async def connect_player(self, code: str, player_id: str, token: str = "") -> None:
        """Register an SSE connection. Delegates the whole state machine
        (connected-map, pause/resume, grace) to ConnectionLifecycle."""
        await lifecycle.connect(code, player_id, token, self._repo, start_timer=self._start_timer)

    async def disconnect_player(self, code: str, player_id: str, token: str = "") -> None:
        """Remove one SSE connection and schedule a grace pause if it was the last.
        Delegates to ConnectionLifecycle — safe to call from the SSE generator."""
        await lifecycle.disconnect(code, player_id, token, self._repo)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _to_view(self, state: GameState, viewer_id: str) -> GameStateOut:
        return GameStateOut.from_domain(
            state,
            viewer_id=viewer_id,
            connected_map=lifecycle.connected_map(state.code),
        )

    async def _load_or_404(self, code: str) -> GameState:
        state = await self._repo.load_game(code)
        if state is None:
            raise HTTPException(status_code=404, detail="Game not found")
        return state

    def _raise_move_error(self, result: TurnResult) -> None:
        """Maps engine TurnError values to HTTP responses at the seam."""
        error = result.error
        if error == TurnError.NOT_YOUR_TURN:
            raise HTTPException(status_code=403, detail="Not your turn")
        if error == TurnError.NOT_PLAYING:
            raise HTTPException(status_code=400, detail="Game is not in progress")
        if error == TurnError.INVALID_WORD:
            word = result.words[0] if result.words else "That word"
            raise HTTPException(status_code=422, detail=f'"{word}" is not a valid word')
        statuses = {
            TurnError.INVALID_PLACEMENT: (422, "Invalid placement"),
            TurnError.LETTER_NOT_IN_RACK: (422, "Tile not in rack"),
            TurnError.BAG_TOO_SMALL: (422, "Not enough tiles in bag to swap"),
        }
        status, detail = statuses[error]
        raise HTTPException(status_code=status, detail=detail)

    def _start_timer(self, state: GameState) -> None:
        turn_clock.clock.mark_turn_started(state.code)
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
            if turn_clock.clock.apply_elapsed(player, secs):
                logger.warning(f"Game {code}: {player.nickname} timed out after 3 OT minutes")
                state.phase = GamePhase.FINISHED
                move = Move(type=MoveType.TIMEOUT, player_id=player_id, tiles=[], letters=[])
                state.last_move = move
                state.move_history.append(move)
                await self._repo.save_game(state)
                await broadcaster.broadcast(state, lifecycle.connected_map(code))
                lifecycle.remove_game(code)
                return

            logger.warning(f"Game {code}: OT·{player.overtime_count} granted to {player.nickname} (-10 pts) via timer")
            await self._repo.save_game(state)
            await broadcaster.broadcast(state, lifecycle.connected_map(code))
            task = asyncio.create_task(
                self._time_bank_task(code, player_id, 60.0)
            )
            turn_clock.clock.mark_turn_started(code)
            game_manager.set_timer(code, task)
