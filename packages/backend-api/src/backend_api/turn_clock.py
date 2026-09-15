from __future__ import annotations

import time
from typing import Callable

from game_engine.models import Player
from game_engine.turn import apply_elapsed as _engine_apply_elapsed

ClockFn = Callable[[], float]


class TurnClock:
    """Measures elapsed time between turns, per game code.

    Process-scoped: one instance serves every game, keyed by game code
    (never per-request). Two clocks live behind the seam: a monotonic one for
    live measurement (it must never jump), and a wall clock for the persisted
    anchor (it must survive process restarts). Both are injected so time logic
    is deterministic to test. This module owns only measurement and the thin
    apply_elapsed delegation; the async sleep-then-fire timer task stays in
    the service."""

    def __init__(self, clock: ClockFn = time.monotonic, wall: ClockFn = time.time) -> None:
        self._clock = clock
        self._wall = wall
        self._turn_started_at: dict[str, float] = {}

    def wall_now(self) -> float:
        return self._wall()

    def mark_turn_started(self, code: str) -> None:
        self._turn_started_at[code] = self._clock()

    def elapsed(self, code: str) -> float:
        return self._clock() - self._turn_started_at.get(code, self._clock())

    def clear(self, code: str) -> None:
        self._turn_started_at.pop(code, None)

    def live_remaining(self, player: Player, code: str) -> float:
        """The active player's bank as of *now* — stored time minus the
        in-flight turn. Measurement stays in this one home, so views never
        re-derive it from a wall clock of their own."""
        return max(0.0, player.time_remaining_secs - self.elapsed(code))

    def apply_elapsed(self, player: Player, elapsed_secs: float) -> bool:
        """Delegates to the engine's pure overtime math (one home for the rules)."""
        return _engine_apply_elapsed(player, elapsed_secs)


# Process-scoped singleton — shared across all games and all requests.
# replace (`clock = TurnClock(my_fake)`) in tests at this seam.
clock = TurnClock()