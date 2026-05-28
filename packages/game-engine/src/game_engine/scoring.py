from __future__ import annotations

from game_engine.board import apply_placement
from game_engine.models import Board, PlacedTile

_LETTER_POINTS: dict[str, int] = {
    "A": 1,  "B": 3,  "C": 3,  "D": 2,  "E": 1,  "F": 4,  "G": 2,  "H": 4,
    "I": 1,  "J": 8,  "K": 5,  "L": 1,  "M": 3,  "N": 1,  "O": 1,  "P": 3,
    "Q": 10, "R": 1,  "S": 1,  "T": 1,  "U": 1,  "V": 4,  "W": 4,  "X": 8,
    "Y": 4,  "Z": 10,
}

_TW: frozenset[tuple[int, int]] = frozenset([
    (0, 0),  (0, 7),  (0, 14),
    (7, 0),  (7, 14),
    (14, 0), (14, 7), (14, 14),
])

_DW: frozenset[tuple[int, int]] = frozenset([
    (1, 1),   (2, 2),   (3, 3),   (4, 4),
    (7, 7),
    (10, 10), (11, 11), (12, 12), (13, 13),
    (1, 13),  (2, 12),  (3, 11),  (4, 10),
    (10, 4),  (11, 3),  (12, 2),  (13, 1),
])

_TL: frozenset[tuple[int, int]] = frozenset([
    (1, 5),  (1, 9),
    (5, 1),  (5, 5),  (5, 9),  (5, 13),
    (9, 1),  (9, 5),  (9, 9),  (9, 13),
    (13, 5), (13, 9),
])

_DL: frozenset[tuple[int, int]] = frozenset([
    (0, 3),  (0, 11),
    (2, 6),  (2, 8),
    (3, 0),  (3, 7),  (3, 14),
    (6, 2),  (6, 6),  (6, 8),  (6, 12),
    (7, 3),  (7, 11),
    (8, 2),  (8, 6),  (8, 8),  (8, 12),
    (11, 0), (11, 7), (11, 14),
    (12, 6), (12, 8),
    (14, 3), (14, 11),
])


def _score_word_at(
    board: Board,
    new_positions: set[tuple[int, int]],
    new_tiles: dict[tuple[int, int], PlacedTile],
    row: int,
    col: int,
    horizontal: bool,
) -> int:
    r, c = row, col
    if horizontal:
        while c > 0 and board[r][c - 1] is not None:
            c -= 1
    else:
        while r > 0 and board[r - 1][c] is not None:
            r -= 1

    word_score = 0
    word_mult = 1
    length = 0

    while r < 15 and c < 15:
        cell = board[r][c]
        if cell is None:
            break
        pos = (r, c)
        if pos in new_positions:
            tile = new_tiles[pos]
            pts = 0 if tile.letter == " " else _LETTER_POINTS.get(tile.letter, 0)
            if pos in _DL:
                pts *= 2
            elif pos in _TL:
                pts *= 3
            if pos in _DW:
                word_mult *= 2
            elif pos in _TW:
                word_mult *= 3
            word_score += pts
        else:
            # lowercase = blank placed in a previous turn → 0 pts
            word_score += 0 if cell.islower() else _LETTER_POINTS.get(cell, 0)
        length += 1
        if horizontal:
            c += 1
        else:
            r += 1

    return word_score * word_mult if length >= 2 else 0


def score_placement(board: Board, tiles: list[PlacedTile]) -> int:
    """Score a placement. board is the state BEFORE tiles are placed."""
    if not tiles:
        return 0

    new_positions = {(t.row, t.col) for t in tiles}
    new_tiles = {(t.row, t.col): t for t in tiles}
    board_after = apply_placement(board, tiles)

    rows = {t.row for t in tiles}
    cols = {t.col for t in tiles}
    horizontal = len(rows) == 1

    total = 0

    if horizontal:
        row = next(iter(rows))
        total += _score_word_at(board_after, new_positions, new_tiles, row, tiles[0].col, horizontal=True)
        for t in tiles:
            total += _score_word_at(board_after, new_positions, new_tiles, t.row, t.col, horizontal=False)
    else:
        col = next(iter(cols))
        total += _score_word_at(board_after, new_positions, new_tiles, tiles[0].row, col, horizontal=False)
        for t in tiles:
            total += _score_word_at(board_after, new_positions, new_tiles, t.row, t.col, horizontal=True)

    if len(tiles) == 7:
        total += 50

    return total
