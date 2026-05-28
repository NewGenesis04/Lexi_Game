from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from game_engine.models import (
    Dictionary, GamePhase, Move, MoveType, GameState, PlacedTile, Player, Tile,
)


# ---------------------------------------------------------------------------
# Inbound
# ---------------------------------------------------------------------------

class PlacedTileIn(BaseModel):
    row: int
    col: int
    letter: str
    plays_as: str | None = None

    def to_domain(self) -> PlacedTile:
        return PlacedTile(row=self.row, col=self.col, letter=self.letter, plays_as=self.plays_as)


class CreateGameRequest(BaseModel):
    nickname: str
    dictionary: Dictionary
    time_per_player_secs: float


class JoinGameRequest(BaseModel):
    nickname: str


class PlaceTilesRequest(BaseModel):
    tiles: list[PlacedTileIn]


class SwapTilesRequest(BaseModel):
    letters: list[str]


class PlaceMoveRequest(BaseModel):
    type: Literal["place"]
    tiles: list[PlacedTileIn]


class SwapMoveRequest(BaseModel):
    type: Literal["swap"]
    letters: list[str]


class PassMoveRequest(BaseModel):
    type: Literal["pass"]


MoveRequest = Annotated[
    Union[PlaceMoveRequest, SwapMoveRequest, PassMoveRequest],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Outbound
# ---------------------------------------------------------------------------

class TileOut(BaseModel):
    letter: str
    points: int

    @classmethod
    def from_domain(cls, tile: Tile) -> TileOut:
        return cls(letter=tile.letter, points=tile.points)


class PlacedTileOut(BaseModel):
    row: int
    col: int
    letter: str

    @classmethod
    def from_domain(cls, tile: PlacedTile) -> PlacedTileOut:
        return cls(row=tile.row, col=tile.col, letter=tile.letter)


class MoveOut(BaseModel):
    type: MoveType
    player_id: str
    tiles: list[PlacedTileOut]

    @classmethod
    def from_domain(cls, move: Move) -> MoveOut:
        return cls(
            type=move.type,
            player_id=move.player_id,
            tiles=[PlacedTileOut.from_domain(t) for t in move.tiles],
        )


class PlayerOut(BaseModel):
    id: str
    nickname: str
    score: int
    time_remaining_secs: float
    rack: list[TileOut]

    @classmethod
    def from_domain(cls, player: Player, *, is_self: bool) -> PlayerOut:
        return cls(
            id=player.id,
            nickname=player.nickname,
            score=player.score,
            time_remaining_secs=player.time_remaining_secs,
            rack=[TileOut.from_domain(t) for t in player.rack] if is_self else [],
        )


class GameStateOut(BaseModel):
    code: str
    phase: GamePhase
    dictionary: Dictionary
    board: list[list[str | None]]
    bag_size: int
    players: list[PlayerOut]
    current_player_index: int
    consecutive_passes: int
    last_move: MoveOut | None

    @classmethod
    def from_domain(cls, state: GameState, *, viewer_id: str) -> GameStateOut:
        return cls(
            code=state.code,
            phase=state.phase,
            dictionary=state.dictionary,
            board=state.board,
            bag_size=len(state.bag),
            players=[
                PlayerOut.from_domain(p, is_self=(p.id == viewer_id))
                for p in state.players
            ],
            current_player_index=state.current_player_index,
            consecutive_passes=state.consecutive_passes,
            last_move=MoveOut.from_domain(state.last_move) if state.last_move else None,
        )


class CreateGameOut(BaseModel):
    code: str
    token: str
    player_id: str


class JoinGameOut(BaseModel):
    token: str
    player_id: str
    state: GameStateOut
