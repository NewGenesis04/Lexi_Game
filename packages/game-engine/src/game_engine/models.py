from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GamePhase(str, Enum):
    CREATED = "created"
    PLAYING = "playing"
    PAUSED = "paused"
    FINISHED = "finished"


class MoveType(str, Enum):
    PLACE = "place"
    SWAP = "swap"
    PASS = "pass"
    FORFEIT = "forfeit"


class Dictionary(str, Enum):
    TWL06 = "TWL06"
    CSW21 = "CSW21"


@dataclass
class Tile:
    letter: str  # " " for blank
    points: int


@dataclass
class PlacedTile:
    row: int
    col: int
    letter: str       # " " for blank
    plays_as: str | None = None  # required when letter == " "


@dataclass
class Move:
    type: MoveType
    player_id: str
    tiles: list[PlacedTile] = field(default_factory=list)  # PLACE
    letters: list[str] = field(default_factory=list)        # SWAP


@dataclass
class Player:
    id: str
    nickname: str
    rack: list[Tile] = field(default_factory=list)
    time_remaining_secs: float = 0.0
    score: int = 0
    overtime_count: int = 0


Board = list[list[str | None]]  # 15×15; None = empty, str = letter placed


@dataclass
class GameState:
    code: str
    phase: GamePhase
    dictionary: Dictionary
    board: Board = field(default_factory=lambda: [[None] * 15 for _ in range(15)])
    bag: list[Tile] = field(default_factory=list)
    players: list[Player] = field(default_factory=list)
    current_player_index: int = 0
    move_history: list[Move] = field(default_factory=list)
    consecutive_passes: int = 0
    last_move: Move | None = None
    paused_time_left: float | None = None
