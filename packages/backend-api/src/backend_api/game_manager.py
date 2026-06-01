from __future__ import annotations

import asyncio
import time

_locks: dict[str, asyncio.Lock] = {}
_timers: dict[str, asyncio.Task] = {}
_turn_started_at: dict[str, float] = {}
_pause_timers: dict[str, asyncio.Task] = {}
_connected: dict[str, dict[str, bool]] = {}  # code → {player_id → True/False}


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


def set_pause_timer(code: str, task: asyncio.Task) -> None:
    cancel_pause_timer(code)
    _pause_timers[code] = task


def cancel_pause_timer(code: str) -> None:
    if task := _pause_timers.pop(code, None):
        task.cancel()


def mark_connected(code: str, player_id: str) -> None:
    _connected.setdefault(code, {})[player_id] = True


def mark_disconnected(code: str, player_id: str) -> None:
    if code in _connected:
        _connected[code].pop(player_id, None)
        if not _connected[code]:
            del _connected[code]


def get_connected(code: str) -> dict[str, bool]:
    return dict(_connected.get(code, {}))


def is_player_connected(code: str, player_id: str) -> bool:
    return _connected.get(code, {}).get(player_id, False)


def remove_game(code: str) -> None:
    _locks.pop(code, None)
    cancel_timer(code)
    cancel_pause_timer(code)
    _turn_started_at.pop(code, None)
    _connected.pop(code, None)


def set_turn_started(code: str) -> None:
    _turn_started_at[code] = time.monotonic()


def get_elapsed(code: str) -> float:
    return time.monotonic() - _turn_started_at.get(code, time.monotonic())


def clear_turn_started(code: str) -> None:
    _turn_started_at.pop(code, None)
