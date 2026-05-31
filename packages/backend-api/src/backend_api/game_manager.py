from __future__ import annotations

import asyncio
import time

_locks: dict[str, asyncio.Lock] = {}
_timers: dict[str, asyncio.Task] = {}
_turn_started_at: dict[str, float] = {}


def get_lock(code: str) -> asyncio.Lock:
    if code not in _locks:
        _locks[code] = asyncio.Lock()
    return _locks[code]


def set_timer(code: str, task: asyncio.Task) -> None:
    cancel_timer(code)
    _timers[code] = task


def cancel_timer(code: str) -> None:
    if task := _timers.pop(code, None):
        task.cancel()


def remove_game(code: str) -> None:
    _locks.pop(code, None)
    cancel_timer(code)
    _turn_started_at.pop(code, None)


def set_turn_started(code: str) -> None:
    _turn_started_at[code] = time.monotonic()


def get_elapsed(code: str) -> float:
    return time.monotonic() - _turn_started_at.get(code, time.monotonic())


def clear_turn_started(code: str) -> None:
    _turn_started_at.pop(code, None)
