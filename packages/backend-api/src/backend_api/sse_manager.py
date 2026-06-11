from __future__ import annotations

import asyncio

_queues: dict[str, asyncio.Queue[str]] = {}      # token → queue
_game_tokens: dict[str, set[str]] = {}            # code  → {token, ...}
_player_by_token: dict[str, str] = {}              # token → player_id


def subscribe(code: str, token: str, player_id: str) -> asyncio.Queue[str]:
    q: asyncio.Queue[str] = asyncio.Queue()
    _queues[token] = q
    _game_tokens.setdefault(code, set()).add(token)
    _player_by_token[token] = player_id
    return q


def unsubscribe(code: str, token: str) -> None:
    _queues.pop(token, None)
    _game_tokens.get(code, set()).discard(token)
    _player_by_token.pop(token, None)


def tokens_for_game(code: str) -> set[str]:
    return set(_game_tokens.get(code, set()))


def player_id_for_token(token: str) -> str | None:
    return _player_by_token.get(token)


async def broadcast(payloads: dict[str, str]) -> None:
    """Push per-recipient sanitized JSON. payloads: {token: json_string}"""
    for token, payload in payloads.items():
        if q := _queues.get(token):
            await q.put(payload)
