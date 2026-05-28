from __future__ import annotations

from game_engine.models import Board, GameState, PlacedTile


def apply_placement(board: Board, tiles: list[PlacedTile]) -> Board:
    new_board = [row[:] for row in board]
    for t in tiles:
        new_board[t.row][t.col] = t.plays_as.lower() if t.letter == " " else t.letter
    return new_board


def _any_adjacent(board: Board, tiles: list[PlacedTile]) -> bool:
    for t in tiles:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, c = t.row + dr, t.col + dc
            if 0 <= r < 15 and 0 <= c < 15 and board[r][c] is not None:
                return True
    return False


def validate_placement(state: GameState, tiles: list[PlacedTile]) -> bool:
    if not tiles:
        return False

    if not all(0 <= t.row < 15 and 0 <= t.col < 15 for t in tiles):
        return False

    positions = [(t.row, t.col) for t in tiles]
    if len(positions) != len(set(positions)):
        return False

    if any(state.board[t.row][t.col] is not None for t in tiles):
        return False

    if any(t.letter == " " and not t.plays_as for t in tiles):
        return False

    rows = {t.row for t in tiles}
    cols = {t.col for t in tiles}
    horizontal = len(rows) == 1
    vertical = len(cols) == 1
    if not (horizontal or vertical):
        return False

    board_after = apply_placement(state.board, tiles)
    if horizontal:
        row = next(iter(rows))
        min_col, max_col = min(cols), max(cols)
        if not all(board_after[row][c] is not None for c in range(min_col, max_col + 1)):
            return False
    else:
        col = next(iter(cols))
        min_row, max_row = min(rows), max(rows)
        if not all(board_after[r][col] is not None for r in range(min_row, max_row + 1)):
            return False

    board_empty = all(cell is None for row in state.board for cell in row)
    if board_empty:
        if (7, 7) not in set(positions):
            return False
    else:
        if not _any_adjacent(state.board, tiles):
            return False

    return True


def _scan_word(board: Board, row: int, col: int, horizontal: bool) -> str | None:
    letters: list[str] = []
    if horizontal:
        c = col
        while c > 0 and board[row][c - 1] is not None:
            c -= 1
        while c < 15:
            cell = board[row][c]
            if cell is None:
                break
            letters.append(cell.upper())
            c += 1
    else:
        r = row
        while r > 0 and board[r - 1][col] is not None:
            r -= 1
        while r < 15:
            cell = board[r][col]
            if cell is None:
                break
            letters.append(cell.upper())
            r += 1
    return "".join(letters) if len(letters) >= 2 else None


def formed_words(board: Board, tiles: list[PlacedTile]) -> list[str]:
    if not tiles:
        return []

    rows = {t.row for t in tiles}
    cols = {t.col for t in tiles}
    horizontal = len(rows) == 1

    words: list[str] = []

    if horizontal:
        row = next(iter(rows))
        main = _scan_word(board, row, tiles[0].col, horizontal=True)
        if main:
            words.append(main)
        for t in tiles:
            cross = _scan_word(board, t.row, t.col, horizontal=False)
            if cross:
                words.append(cross)
    else:
        col = next(iter(cols))
        main = _scan_word(board, tiles[0].row, col, horizontal=False)
        if main:
            words.append(main)
        for t in tiles:
            cross = _scan_word(board, t.row, t.col, horizontal=True)
            if cross:
                words.append(cross)

    return words
