from __future__ import annotations

import time
from typing import Callable

from game_engine.models import Player
from game_engine.turn import apply_elapsed as _engine_apply_elapsed

ClockFn = Callable[[], float]


class TurnClock:
    """Measures elapsed time between turns, per game code.

    Process-scoped: one instance serves every game, keyed by game code
    (never per-request). The monotonic clock is injected at construction so
    time logic is deterministic to test. It owns only measurement and the
    thin apply_elapsed delegation; the async sleep-then-fire timer task stays
    in the service."""

    def __init__(self, clock: ClockFn = time.monotonic) -> None:
        self._clock = clock
        self._turn_started_at: dict[str, float] = {}

    def mark_turn_started(self, code: str) -> None:
        self._turn_started_at[code] = self._clock()

    def elapsed(self, code: str) -> float:
        return self._clock() - self._turn_started_at.get(code, self._clock())

    def clear(self, code: str) -> None:
        self._turn_started_at.pop(code, None)

    def apply_elapsed(self, player: Player, elapsed_secs: float) -> bool:
        """Delegates to the engine's pure overtime math (one home for the rules)."""
        return _engine_apply_elapsed(player, elapsed_secs)


# Process-scoped singleton — shared across all games and all requests.
# replace (`clock = TurnClock(my_fake)`) in tests at this seam.
clock = TurnClock()