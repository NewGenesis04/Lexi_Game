from __future__ import annotations

import asyncio

_locks: dict[str, asyncio.Lock] = {}
_timers: dict[str, asyncio.Task] = {}


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
