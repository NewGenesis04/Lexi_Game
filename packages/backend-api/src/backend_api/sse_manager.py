from __future__ import annotations

import asyncio

_queues: dict[str, asyncio.Queue[str]] = {}      # token → queue
_game_tokens: dict[str, set[str]] = {}            # code  → {token, ...}


def subscribe(code: str, token: str) -> asyncio.Queue[str]:
    q: asyncio.Queue[str] = asyncio.Queue()
    _queues[token] = q
    _game_tokens.setdefault(code, set()).add(token)
    return q


def unsubscribe(code: str, token: str) -> None:
    _queues.pop(token, None)
    _game_tokens.get(code, set()).discard(token)


def tokens_for_game(code: str) -> set[str]:
    return set(_game_tokens.get(code, set()))


async def broadcast(payloads: dict[str, str]) -> None:
    """Push per-recipient sanitized JSON. payloads: {token: json_string}"""
    for token, payload in payloads.items():
        if q := _queues.get(token):
            await q.put(payload)
