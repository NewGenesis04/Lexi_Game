from __future__ import annotations

import asyncio
import time

_locks: dict[str, asyncio.Lock] = {}
_timers: dict[str, asyncio.Task] = {}
_turn_started_at: dict[str, float] = {}
_pause_timers: dict[str, asyncio.Task] = {}
_connections: dict[str, dict[str, set[str]]] = {}  # code → {player_id → {token, ...}}
_pending_disconnects: dict[str, dict[str, asyncio.Task]] = {}  # code → {player_id → cancel_task}


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


def add_connection(code: str, player_id: str, token: str) -> None:
    """Register one SSE connection for a player. Cancels any pending disconnect."""
    cancel_disconnect_check(code, player_id)
    _connections.setdefault(code, {}).setdefault(player_id, set()).add(token)


def remove_connection(code: str, player_id: str, token: str) -> None:
    """Remove one SSE connection for a player. Returns True if player has no more connections."""
    conns = _connections.get(code, {}).get(player_id)
    if conns is not None:
        conns.discard(token)
        if not conns:
            del _connections[code][player_id]
            if not _connections[code]:
                del _connections[code]
            return True
    return False


def is_player_connected(code: str, player_id: str) -> bool:
    return bool(_connections.get(code, {}).get(player_id))


def get_connected(code: str) -> dict[str, bool]:
    return {pid: True for pid in _connections.get(code, {})}


def remove_game(code: str) -> None:
    _locks.pop(code, None)
    cancel_timer(code)
    cancel_pause_timer(code)
    _turn_started_at.pop(code, None)
    _connections.pop(code, None)
    for task in _pending_disconnects.pop(code, {}).values():
        task.cancel()


def set_turn_started(code: str) -> None:
    _turn_started_at[code] = time.monotonic()


def get_elapsed(code: str) -> float:
    return time.monotonic() - _turn_started_at.get(code, time.monotonic())


def clear_turn_started(code: str) -> None:
    _turn_started_at.pop(code, None)


# ---------------------------------------------------------------------------
# Disconnect grace-period helpers
# ---------------------------------------------------------------------------

def schedule_disconnect_check(code: str, player_id: str, task: asyncio.Task) -> None:
    cancel_disconnect_check(code, player_id)
    _pending_disconnects.setdefault(code, {})[player_id] = task


def cancel_disconnect_check(code: str, player_id: str) -> None:
    if pending := _pending_disconnects.get(code, {}).pop(player_id, None):
        pending.cancel()
