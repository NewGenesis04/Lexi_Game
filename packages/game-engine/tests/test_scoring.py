from game_engine.board import apply_placement  # type: ignore
from game_engine.models import Board, PlacedTile  # type: ignore
from game_engine.scoring import score_placement  # type: ignore


def _blank_board() -> Board:
    return [[None] * 15 for _ in range(15)]


def _pt(row: int, col: int, letter: str, plays_as: str | None = None) -> PlacedTile:
    return PlacedTile(row=row, col=col, letter=letter, plays_as=plays_as)


def _board_with(placements: dict[tuple[int, int], str]) -> Board:
    board = _blank_board()
    for (r, c), letter in placements.items():
        board[r][c] = letter
    return board


# --- face value only ---

def test_score_no_premiums():
    # existing A(1) at (2,3); new T(1) at (2,4), E(1) at (2,5) — no premiums
    # word "ATE" = 1+1+1 = 3
    board = _board_with({(2, 3): "A"})
    tiles = [_pt(2, 4, "T"), _pt(2, 5, "E")]
    assert score_placement(board, tiles) == 3


# --- letter multipliers ---

def test_score_double_letter():
    # existing A(1) at (7,2); new T(1) at (7,3)[DL]
    # word "AT" = 1 + 1×2 = 3
    board = _board_with({(7, 2): "A"})
    tiles = [_pt(7, 3, "T")]
    assert score_placement(board, tiles) == 3


def test_score_triple_letter():
    # existing A(1) at (5,0); new T(1) at (5,1)[TL]
    # word "AT" = 1 + 1×3 = 4
    board = _board_with({(5, 0): "A"})
    tiles = [_pt(5, 1, "T")]
    assert score_placement(board, tiles) == 4


# --- word multipliers ---

def test_score_double_word():
    # existing A(1) at (1,0); new T(1) at (1,1)[DW]
    # word "AT" = (1+1)×2 = 4
    board = _board_with({(1, 0): "A"})
    tiles = [_pt(1, 1, "T")]
    assert score_placement(board, tiles) == 4


def test_score_triple_word():
    # existing A(1) at (0,6); new T(1) at (0,7)[TW]
    # word "AT" = (1+1)×3 = 6
    board = _board_with({(0, 6): "A"})
    tiles = [_pt(0, 7, "T")]
    assert score_placement(board, tiles) == 6


# --- existing tile on premium: premium NOT applied ---

def test_score_existing_tile_on_dl_not_multiplied():
    # A(1) already sits on (7,3)[DL]; new T(1) at (7,4) — no premiums at (7,4)
    # word "AT" = 1+1 = 2
    board = _board_with({(7, 3): "A"})
    tiles = [_pt(7, 4, "T")]
    assert score_placement(board, tiles) == 2


# --- blank tiles ---

def test_score_blank_new_tile_scores_zero():
    # existing A(1) at (7,2); blank plays as T at (7,3)[DL] → 0×2 = 0
    # word "AT" = 1+0 = 1
    board = _board_with({(7, 2): "A"})
    tiles = [_pt(7, 3, " ", plays_as="T")]
    assert score_placement(board, tiles) == 1


def test_score_existing_blank_scores_zero():
    # lowercase letter on board = previously placed blank (0pts)
    # existing blank played as A ("a") at (2,3); new T(1) at (2,4)
    # word = 0+1 = 1
    board = _board_with({(2, 3): "a"})
    tiles = [_pt(2, 4, "T")]
    assert score_placement(board, tiles) == 1


# --- bingo bonus ---

def test_score_bingo_adds_fifty():
    # existing A(1) at (4,5); 7×A at (4,6)-(4,12)
    # (4,10) is DW → word_mult = 2
    # word 8×A(1) × 2 + 50 = 16 + 50 = 66
    board = _board_with({(4, 5): "A"})
    tiles = [_pt(4, c, "A") for c in range(6, 13)]
    assert score_placement(board, tiles) == 66


# --- cross words ---

def test_score_cross_word():
    # existing C(3) at (2,4), T(1) at (4,4), B(3) at (3,3)
    # place A(1) at (3,4) — no premiums at (3,4) or (3,3)
    # vertical "CAT" = 3+1+1 = 5; horizontal cross "BA" = 3+1 = 4 → total 9
    board = _board_with({(2, 4): "C", (4, 4): "T", (3, 3): "B"})
    tiles = [_pt(3, 4, "A")]
    assert score_placement(board, tiles) == 9


# --- stacked word multipliers ---

def test_score_stacked_word_multipliers():
    # existing A(1)s at (4,3),(4,5)-(4,9),(4,11)
    # place A(1) at (4,4)[DW] and A(1) at (4,10)[DW] → word_mult = 2×2 = 4
    # word: 9×A(1) × 4 = 36
    board = _board_with({
        (4, 3): "A", (4, 5): "A", (4, 6): "A",
        (4, 7): "A", (4, 8): "A", (4, 9): "A", (4, 11): "A",
    })
    tiles = [_pt(4, 4, "A"), _pt(4, 10, "A")]
    assert score_placement(board, tiles) == 36
