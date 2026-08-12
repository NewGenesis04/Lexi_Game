from __future__ import annotations

import asyncio
import logging
import math
import time

from game_engine.models import GamePhase, GameState, Move, MoveType

from backend_api import game_manager
from backend_api.game_broadcaster import broadcaster
from backend_api.repositories.game_repo import GameRepo
from backend_api.turn_clock import clock

logger = logging.getLogger(__name__)


class ConnectionLifecycle:
    """Process-scoped singleton owning the player-connection state machine.

    All state is keyed by game_code (prime invariant). The repo is passed in
    per call because the grace tasks outlive any single request. The turn
    timer is a service concern: connect() accepts an optional start_timer
    callback so resume can restart it without coupling here."""

    def __init__(self) -> None:
        self._connections: dict[str, dict[str, set[str]]] = {}
        self._pending_disconnects: dict[str, dict[str, asyncio.Task]] = {}
        self._pause_timers: dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Connected-map primitives
    # ------------------------------------------------------------------

    def add_connection(self, code: str, player_id: str, token: str) -> None:
        """Register one SSE connection for a player. Cancels any pending disconnect."""
        self.cancel_disconnect_check(code, player_id)
        self._connections.setdefault(code, {}).setdefault(player_id, set()).add(token)

    def remove_connection(self, code: str, player_id: str, token: str) -> bool:
        """Remove one SSE connection. True if the player has no more connections."""
        conns = self._connections.get(code, {}).get(player_id)
        if conns is not None:
            conns.discard(token)
            if not conns:
                del self._connections[code][player_id]
                if not self._connections[code]:
                    del self._connections[code]
                return True
        return False

    def is_player_connected(self, code: str, player_id: str) -> bool:
        return bool(self._connections.get(code, {}).get(player_id))

    def connected_map(self, code: str) -> dict[str, bool]:
        return {pid: True for pid in self._connections.get(code, {})}

    # ------------------------------------------------------------------
    # Timer primitives
    # ------------------------------------------------------------------

    def set_pause_timer(self, code: str, task: asyncio.Task) -> None:
        self.cancel_pause_timer(code)
        self._pause_timers[code] = task

    def cancel_pause_timer(self, code: str) -> None:
        if task := self._pause_timers.pop(code, None):
            task.cancel()

    def schedule_disconnect_check(self, code: str, player_id: str, task: asyncio.Task) -> None:
        self.cancel_disconnect_check(code, player_id)
        self._pending_disconnects.setdefault(code, {})[player_id] = task

    def cancel_disconnect_check(self, code: str, player_id: str) -> None:
        if pending := self._pending_disconnects.get(code, {}).pop(player_id, None):
            pending.cancel()

    # ------------------------------------------------------------------
    # Connect / disconnect
    # ------------------------------------------------------------------

    async def connect(
        self,
        code: str,
        player_id: str,
        token: str,
        repo: GameRepo,
        start_timer=None,
    ) -> None:
        """Register an SSE connection. If the game was PAUSED and both players
        are back, resume it. Silently returns if the game doesn't exist."""
        async with game_manager.get_lock(code):
            self.add_connection(code, player_id, token)

            state = await repo.load_game(code)
            if state is None:
                return
            if state.phase not in (GamePhase.PLAYING, GamePhase.PAUSED):
                return
            if not any(p.id == player_id for p in state.players):
                return

            if state.phase == GamePhase.PAUSED:
                cmap = self.connected_map(code)
                all_connected = all(cmap.get(p.id, False) for p in state.players)
                if all_connected:
                    self.resume(state)
                    await repo.save_game(state)
                    if start_timer is not None:
                        start_timer(state)
                    await broadcaster.broadcast(state, self.connected_map(state.code))
                    return

            await repo.save_game(state)

    async def disconnect(self, code: str, player_id: str, token: str, repo: GameRepo) -> None:
        """Remove one SSE connection. If no connections remain, schedule a short
        grace pause. If the player reconnects before the grace timer fires, the
        pause is cancelled. Does nothing if the player was never connected."""
        async with game_manager.get_lock(code):
            state = await repo.load_game(code)
            if state is None:
                return
            if state.phase not in (GamePhase.PLAYING, GamePhase.PAUSED):
                return
            if not any(p.id == player_id for p in state.players):
                return

            was_last = self.remove_connection(code, player_id, token)
            if not was_last:
                return  # player still has other active connections

            if state.phase == GamePhase.PLAYING:
                task = asyncio.create_task(self._pause_after_grace(code, player_id, repo))
                self.schedule_disconnect_check(code, player_id, task)
            elif state.phase == GamePhase.PAUSED:
                await repo.save_game(state)
                self._spawn_disconnect_grace_task(state, repo)

    # ------------------------------------------------------------------
    # Pause / resume
    # ------------------------------------------------------------------

    def pause(self, state: GameState) -> None:
        """Freeze the active turn clock and transition to PAUSED."""
        elapsed = clock.elapsed(state.code)
        clock.clear(state.code)
        player = state.players[state.current_player_index]
        new_time = math.floor(max(0.0, player.time_remaining_secs - elapsed))

        state.paused_time_left = new_time
        state.paused_at = time.time()
        state.phase = GamePhase.PAUSED

    def resume(self, state: GameState) -> None:
        """Restore from paused and transition back to PLAYING."""
        self.cancel_pause_timer(state.code)
        player = state.players[state.current_player_index]
        if state.paused_time_left is not None:
            player.time_remaining_secs = state.paused_time_left
        state.paused_time_left = None
        state.paused_at = None
        state.phase = GamePhase.PLAYING

    # ------------------------------------------------------------------
    # Grace / forfeit-by-disconnect
    # ------------------------------------------------------------------

    async def _pause_after_grace(self, code: str, player_id: str, repo: GameRepo, grace_secs: float = 10.0) -> None:
        """Wait grace_secs, then pause the game if the player is still gone.
        Cancelled automatically by connect() when the player returns."""
        try:
            await asyncio.sleep(grace_secs)
        except asyncio.CancelledError:
            return

        async with game_manager.get_lock(code):
            if self.is_player_connected(code, player_id):
                return  # reconnected during the grace window
            state = await repo.load_game(code)
            if state is None or state.phase != GamePhase.PLAYING:
                return
            self.pause(state)
            await repo.save_game(state)
            await broadcaster.broadcast(state, self.connected_map(state.code))
            self._spawn_disconnect_grace_task(state, repo)

    def _spawn_disconnect_grace_task(self, state: GameState, repo: GameRepo) -> None:
        """Spawn or reset the 5-minute grace timer for a paused game."""
        task = asyncio.create_task(
            self._disconnect_grace_task(state.code, repo, grace_secs=300.0)
        )
        self.set_pause_timer(state.code, task)

    async def _disconnect_grace_task(self, code: str, repo: GameRepo, grace_secs: float = 300.0) -> None:
        """5-minute grace period after a pause. On expiry, forfeit against the
        disconnected player. Always cleans up runtime state."""
        try:
            await asyncio.sleep(grace_secs)
        except asyncio.CancelledError:
            return

        async with game_manager.get_lock(code):
            state = await repo.load_game(code)
            if state is None:
                self.remove_game(code)
                return
            self.cancel_pause_timer(code)
            if state.phase != GamePhase.PAUSED:
                return  # game was resumed or finished since the timer started

            cmap = self.connected_map(code)
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
                await repo.save_game(state)
                await broadcaster.broadcast(state, self.connected_map(state.code))

            self.remove_game(code)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def remove_game(self, code: str) -> None:
        """Full runtime teardown: lifecycle maps + lock/turn-timer/clock."""
        game_manager.remove_game(code)
        self.cancel_pause_timer(code)
        self._connections.pop(code, None)
        for task in self._pending_disconnects.pop(code, {}).values():
            task.cancel()

lifecycle = ConnectionLifecycle()