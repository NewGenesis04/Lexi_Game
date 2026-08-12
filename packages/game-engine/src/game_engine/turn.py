from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from game_engine import bag as bag_module, board as board_module, scoring as scoring_module
from game_engine import dictionary as dict_module
from game_engine.models import (
    GamePhase,
    GameState,
    Move,
    MoveType,
    PlacedTile,
    Player,
    Tile,
)


class TurnOutcome(str, Enum):
    OK = "ok"
    ENDED_BAG_EMPTY = "ended_bag_empty"
    ENDED_SIX_PASSES = "ended_six_passes"
    ENDED_TIMEOUT = "ended_timeout"


class TurnError(str, Enum):
    INVALID_PLACEMENT = "invalid_placement"
    INVALID_WORD = "invalid_word"
    NOT_YOUR_TURN = "not_your_turn"
    LETTER_NOT_IN_RACK = "letter_not_in_rack"
    BAG_TOO_SMALL = "bag_too_small"
    NOT_PLAYING = "not_playing"


@dataclass
class PlaceRequest:
    player_id: str
    tiles: list[PlacedTile] = field(default_factory=list)


@dataclass
class SwapRequest:
    player_id: str
    letters: list[str] = field(default_factory=list)


@dataclass
class PassRequest:
    player_id: str


Request = PlaceRequest | SwapRequest | PassRequest


@dataclass
class TurnResult:
    outcome: TurnOutcome = TurnOutcome.OK
    error: TurnError | None = None
    words: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.error is None


def apply_elapsed(player: Player, elapsed_secs: float) -> bool:
    """Deduct elapsed time from the player's bank, applying overtime grants.

    First three overspends: −10 pts, overtime_count += 1, bank reset to 60 s.
    Fourth overspend: bank set to 0. Returns True only when the forfeit
    threshold is reached (caller must end the game). Mutates the player."""
    new_time = player.time_remaining_secs - elapsed_secs

    if new_time > 0:
        player.time_remaining_secs = new_time
        return False

    if player.overtime_count < 3:
        player.score -= 10
        player.overtime_count += 1
        player.time_remaining_secs = 60.0
        return False

    player.time_remaining_secs = 0.0
    return True


def _current_player(state: GameState) -> Player:
    return state.players[state.current_player_index]


def _remove_from_rack(rack: list[Tile], target_letter: str) -> Tile | None:
    for i, t in enumerate(rack):
        if t.letter == target_letter:
            return rack.pop(i)
    return None


def _advance_turn(state: GameState) -> None:
    state.current_player_index = (state.current_player_index + 1) % len(state.players)


def _apply_place(state: GameState, req: PlaceRequest) -> TurnResult:
    if not board_module.validate_placement(state, req.tiles):
        return TurnResult(error=TurnError.INVALID_PLACEMENT)

    new_board = board_module.apply_placement(state.board, req.tiles)
    formed = board_module.formed_words(new_board, req.tiles)
    for word in formed:
        if not dict_module.is_valid_word(word, state.dictionary):
            return TurnResult(error=TurnError.INVALID_WORD, words=[word])

    player = _current_player(state)
    remaining = list(player.rack)
    for pt in req.tiles:
        if _remove_from_rack(remaining, pt.letter) is None:
            return TurnResult(error=TurnError.LETTER_NOT_IN_RACK)

    points = scoring_module.score_placement(state.board, req.tiles)
    drawn, state.bag = bag_module.draw_tiles(state.bag, len(req.tiles))

    state.board = new_board
    player.score += points
    player.rack = remaining + drawn

    move = Move(
        type=MoveType.PLACE, player_id=req.player_id, tiles=req.tiles,
        letters=[], score_delta=points, words=formed,
    )
    state.last_move = move
    state.move_history.append(move)
    state.consecutive_passes = 0
    return TurnResult()


def _apply_swap(state: GameState, req: SwapRequest) -> TurnResult:
    if len(state.bag) < len(req.letters):
        return TurnResult(error=TurnError.BAG_TOO_SMALL)

    player = _current_player(state)
    returned: list[Tile] = []
    temp = list(player.rack)
    for letter in req.letters:
        tile = _remove_from_rack(temp, letter)
        if tile is None:
            return TurnResult(error=TurnError.LETTER_NOT_IN_RACK)
        returned.append(tile)

    drawn, state.bag = bag_module.exchange_tiles(state.bag, returned, len(req.letters))
    player.rack = temp + drawn

    move = Move(type=MoveType.SWAP, player_id=req.player_id, tiles=[], letters=req.letters)
    state.last_move = move
    state.move_history.append(move)
    state.consecutive_passes = 0
    return TurnResult()


def _apply_pass(state: GameState, req: PassRequest) -> TurnResult:
    state.consecutive_passes += 1
    move = Move(type=MoveType.PASS, player_id=req.player_id, tiles=[], letters=[])
    state.last_move = move
    state.move_history.append(move)
    return TurnResult()


def _end_bag_empty(state: GameState) -> TurnResult:
    """Bag empty + current player emptied their rack: apply end-game penalties."""
    player = _current_player(state)
    for p in state.players:
        if p.id == player.id:
            continue
        penalty = sum(t.points for t in p.rack)
        p.score -= penalty
        player.score += penalty
    state.phase = GamePhase.FINISHED
    return TurnResult(outcome=TurnOutcome.ENDED_BAG_EMPTY)


def _end_timeout(state: GameState, player_id: str) -> TurnResult:
    """Clock expired mid-turn: record a TIMEOUT move and end the game.
    The current player's bank is already 0 (apply_elapsed returned True)."""
    state.phase = GamePhase.FINISHED
    move = Move(type=MoveType.TIMEOUT, player_id=player_id, tiles=[], letters=[])
    state.last_move = move
    state.move_history.append(move)
    return TurnResult(outcome=TurnOutcome.ENDED_TIMEOUT)


def apply(state: GameState, request: Request, elapsed_secs: float = 0.0) -> tuple[GameState, TurnResult]:
    """Apply a player move to the GameState, mutating it in place.

    Guards first (phase, turn), then the move transition, then the end
    conditions the move can trigger: bag emptied, six consecutive passes,
    clock expiry mid-turn. On OK the turn advances to the next player.
    Error results are values — the caller maps them to HTTP."""
    if state.phase != GamePhase.PLAYING:
        return state, TurnResult(error=TurnError.NOT_PLAYING)
    if _current_player(state).id != request.player_id:
        return state, TurnResult(error=TurnError.NOT_YOUR_TURN)

    # Real time elapsed since the previous action is charged to the current
    # player before the action itself is judged — a rejected move still cost
    # them the seconds they spent on it.
    if apply_elapsed(_current_player(state), elapsed_secs):
        return state, _end_timeout(state, request.player_id)

    if isinstance(request, PlaceRequest):
        result = _apply_place(state, request)
    elif isinstance(request, SwapRequest):
        result = _apply_swap(state, request)
    else:
        result = _apply_pass(state, request)

    if result.error is not None:
        return state, result

    if state.phase == GamePhase.FINISHED:
        return state, result

    if not state.bag and not _current_player(state).rack:
        return state, _end_bag_empty(state)

    if state.consecutive_passes >= 6:
        for p in state.players:
            p.score -= sum(t.points for t in p.rack)
        state.phase = GamePhase.FINISHED
        return state, TurnResult(outcome=TurnOutcome.ENDED_SIX_PASSES)

    _advance_turn(state)
    return state, result


class Turn:
    """The deep module seam: one interface for the whole turn transition."""

    apply = staticmethod(apply)
    apply_elapsed = staticmethod(apply_elapsed)