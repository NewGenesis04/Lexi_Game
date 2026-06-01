from __future__ import annotations

import dataclasses
import json
from enum import Enum
from typing import Any

import redis.asyncio as aioredis

from game_engine.models import (
    Dictionary, GameState, GamePhase, Move, MoveType, PlacedTile, Player, Tile,
)
from backend_api.session import PlayerSession


class _EnumEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


def _to_json(obj: Any) -> str:
    return json.dumps(dataclasses.asdict(obj), cls=_EnumEncoder)


def _tile_from_dict(d: dict) -> Tile:
    return Tile(letter=d["letter"], points=d["points"])


def _placed_tile_from_dict(d: dict) -> PlacedTile:
    return PlacedTile(row=d["row"], col=d["col"], letter=d["letter"], plays_as=d.get("plays_as"))


def _move_from_dict(d: dict | None) -> Move | None:
    if d is None:
        return None
    return Move(
        type=MoveType(d["type"]),
        player_id=d["player_id"],
        tiles=[_placed_tile_from_dict(t) for t in d["tiles"]],
        letters=d["letters"],
    )


def _player_from_dict(d: dict) -> Player:
    return Player(
        id=d["id"],
        nickname=d["nickname"],
        rack=[_tile_from_dict(t) for t in d["rack"]],
        time_remaining_secs=d["time_remaining_secs"],
        score=d["score"],
        overtime_count=d.get("overtime_count", 0),
    )


def _state_from_dict(d: dict) -> GameState:
    state = GameState(
        code=d["code"],
        phase=GamePhase(d["phase"]),
        dictionary=Dictionary(d["dictionary"]),
        bag=[_tile_from_dict(t) for t in d["bag"]],
        players=[_player_from_dict(p) for p in d["players"]],
        current_player_index=d["current_player_index"],
        consecutive_passes=d["consecutive_passes"],
        paused_time_left=d["paused_time_left"],
    )
    raw_board = d["board"]
    state.board = raw_board
    state.last_move = _move_from_dict(d.get("last_move"))
    state.move_history = [m for raw in d.get("move_history", []) if (m := _move_from_dict(raw)) is not None]
    return state


class GameRepo:
    def __init__(self, client: aioredis.Redis) -> None:
        self._r = client

    async def save_game(self, state: GameState) -> None:
        await self._r.set(f"game:{state.code}", _to_json(state))

    async def load_game(self, code: str) -> GameState | None:
        raw = await self._r.get(f"game:{code}")
        if raw is None:
            return None
        return _state_from_dict(json.loads(raw))

    async def delete_game(self, code: str) -> None:
        await self._r.delete(f"game:{code}")

    async def save_session(self, token: str, session: PlayerSession) -> None:
        await self._r.set(f"session:{token}", _to_json(session))

    async def load_session(self, token: str) -> PlayerSession | None:
        raw = await self._r.get(f"session:{token}")
        if raw is None:
            return None
        d = json.loads(raw)
        return PlayerSession(
            token=d["token"],
            player_id=d["player_id"],
            game_code=d["game_code"],
            nickname=d["nickname"],
        )

    async def delete_session(self, token: str) -> None:
        await self._r.delete(f"session:{token}")

    async def register_active(self, code: str) -> None:
        await self._r.sadd("active_games", code)  # type: ignore[misc]

    async def deregister_active(self, code: str) -> None:
        await self._r.srem("active_games", code)  # type: ignore[misc]

    async def active_codes(self) -> set[str]:
        return await self._r.smembers("active_games")  # type: ignore[misc]
