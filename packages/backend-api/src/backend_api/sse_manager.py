from __future__ import annotations

import asyncio

# A token is a player's identity, not a connection: the same session lives in
# localStorage, so every tab of one browser opens its own /events stream under
# the same token. One queue per *connection*, so a second tab can't silently
# starve the first by replacing its queue.
_queues: dict[str, set[asyncio.Queue[str]]] = {}   # token → {queue per connection}
_game_tokens: dict[str, set[str]] = {}            # code  → {token, ...}
_player_by_token: dict[str, str] = {}              # token → player_id


def subscribe(code: str, token: str, player_id: str) -> asyncio.Queue[str]:
    q: asyncio.Queue[str] = asyncio.Queue()
    _queues.setdefault(token, set()).add(q)
    _game_tokens.setdefault(code, set()).add(token)
    _player_by_token[token] = player_id
    return q


def unsubscribe(code: str, token: str, queue: asyncio.Queue[str] | None = None) -> None:
    """Drop one connection. The token stays registered while any other
    connection under it is still live — otherwise closing a second tab would
    unregister the player from broadcasts entirely. Pass queue=None to drop
    every connection for the token (teardown)."""
    queues = _queues.get(token)
    if queues is not None and queue is not None:
        queues.discard(queue)
        if queues:
            return

    _queues.pop(token, None)
    _game_tokens.get(code, set()).discard(token)
    _player_by_token.pop(token, None)


def tokens_for_game(code: str) -> set[str]:
    return set(_game_tokens.get(code, set()))


def player_id_for_token(token: str) -> str | None:
    return _player_by_token.get(token)


async def broadcast(payloads: dict[str, str]) -> None:
    """Push per-recipient sanitized JSON to every live connection for each
    token. payloads: {token: json_string}"""
    for token, payload in payloads.items():
        for q in set(_queues.get(token, ())):
            await q.put(payload)
