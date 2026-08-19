from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from game_engine.models import (
    Dictionary, GamePhase, Move, MoveType, GameState, PlacedTile, Player, Tile,
)

from backend_api import turn_clock


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
    nickname: str = Field(min_length=1, max_length=15)
    dictionary: Dictionary
    time_per_player_secs: float
    avatar: str | None = None


class JoinGameRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=15)
    avatar: str | None = None


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
        # For blanks, show the letter they were played as, not the space
        display = tile.plays_as if tile.letter == " " and tile.plays_as else tile.letter
        return cls(row=tile.row, col=tile.col, letter=display)


class MoveOut(BaseModel):
    type: MoveType
    player_id: str
    tiles: list[PlacedTileOut]
    letters: list[str]
    score_delta: int = 0
    words: list[str] = []

    @classmethod
    def from_domain(cls, move: Move) -> MoveOut:
        return cls(
            type=move.type,
            player_id=move.player_id,
            tiles=[PlacedTileOut.from_domain(t) for t in move.tiles],
            letters=move.letters,
            score_delta=move.score_delta,
            words=move.words,
        )


class PlayerOut(BaseModel):
    id: str
    nickname: str
    score: int
    time_remaining_secs: float
    overtime_count: int
    connected: bool
    rack: list[TileOut]
    avatar: str | None = None

    @classmethod
    def from_domain(
        cls,
        player: Player,
        *,
        is_self: bool,
        connected: bool = False,
        time_remaining_secs: float | None = None,
    ) -> PlayerOut:
        """time_remaining_secs overrides the stored bank — GameStateOut passes
        the live value for whoever's turn it is, so a mid-turn fetch doesn't
        rewind the clock to the start of the move."""
        return cls(
            id=player.id,
            nickname=player.nickname,
            score=player.score,
            time_remaining_secs=(
                player.time_remaining_secs if time_remaining_secs is None else time_remaining_secs
            ),
            overtime_count=player.overtime_count,
            connected=connected,
            rack=[TileOut.from_domain(t) for t in player.rack] if is_self else [],
            avatar=player.avatar,
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
    move_history: list[MoveOut] = []

    @classmethod
    def from_domain(cls, state: GameState, *, viewer_id: str, connected_map: dict[str, bool] | None = None) -> GameStateOut:
        # Only the player on the move is burning time, and only while the game
        # is actually running. Serializing the live value here covers all three
        # channels at once (GET, SSE broadcast, SSE initial event). Left as a
        # float — the frontend does its own ceil for display.
        live_index = state.current_player_index if state.phase == GamePhase.PLAYING else -1
        return cls(
            code=state.code,
            phase=state.phase,
            dictionary=state.dictionary,
            board=state.board,
            bag_size=len(state.bag),
            players=[
                PlayerOut.from_domain(
                    p,
                    is_self=(p.id == viewer_id),
                    connected=connected_map.get(p.id, False) if connected_map else False,
                    time_remaining_secs=(
                        turn_clock.clock.live_remaining(p, state.code) if i == live_index else None
                    ),
                )
                for i, p in enumerate(state.players)
            ],
            current_player_index=state.current_player_index,
            consecutive_passes=state.consecutive_passes,
            last_move=MoveOut.from_domain(state.last_move) if state.last_move else None,
            move_history=[MoveOut.from_domain(m) for m in state.move_history],
        )


class CreateGameOut(BaseModel):
    code: str
    token: str
    player_id: str


class JoinGameOut(BaseModel):
    token: str
    player_id: str
    state: GameStateOut
