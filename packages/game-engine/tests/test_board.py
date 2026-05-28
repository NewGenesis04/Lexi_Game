from game_engine.board import apply_placement, formed_words, validate_placement  # type: ignore
from game_engine.models import Board, Dictionary, GamePhase, GameState, PlacedTile  # type: ignore


def _empty_state() -> GameState:
    return GameState(code="TEST01", phase=GamePhase.PLAYING, dictionary=Dictionary.TWL06)


def _state_with(placements: dict[tuple[int, int], str]) -> GameState:
    state = _empty_state()
    for (r, c), letter in placements.items():
        state.board[r][c] = letter
    return state


def _pt(row: int, col: int, letter: str, plays_as: str | None = None) -> PlacedTile:
    return PlacedTile(row=row, col=col, letter=letter, plays_as=plays_as)


def _blank_board() -> Board:
    return [[None] * 15 for _ in range(15)]


# --- apply_placement ---

def test_apply_sets_letter():
    board = apply_placement(_blank_board(), [_pt(7, 7, "A")])
    assert board[7][7] == "A"

def test_apply_blank_uses_plays_as():
    # blanks stored as lowercase to distinguish them from regular tiles during scoring
    board = apply_placement(_blank_board(), [_pt(7, 7, " ", plays_as="Z")])
    assert board[7][7] == "z"

def test_apply_does_not_mutate_original():
    original = _blank_board()
    snapshot = [row[:] for row in original]
    apply_placement(original, [_pt(7, 7, "A")])
    assert original == snapshot

def test_apply_returns_new_board():
    original = _blank_board()
    new_board = apply_placement(original, [_pt(7, 7, "A")])
    assert new_board is not original


# --- validate_placement: early guards ---

def test_validate_empty_tiles():
    assert validate_placement(_empty_state(), []) is False

def test_validate_out_of_bounds_row():
    assert validate_placement(_empty_state(), [_pt(15, 7, "A")]) is False

def test_validate_out_of_bounds_col():
    assert validate_placement(_empty_state(), [_pt(7, -1, "A")]) is False

def test_validate_duplicate_positions():
    assert validate_placement(_empty_state(), [_pt(7, 7, "A"), _pt(7, 7, "B")]) is False

def test_validate_occupied_cell():
    state = _state_with({(7, 7): "A"})
    assert validate_placement(state, [_pt(7, 7, "B")]) is False

def test_validate_blank_without_plays_as():
    assert validate_placement(_empty_state(), [_pt(7, 7, " ")]) is False

def test_validate_blank_with_plays_as_accepted():
    tiles = [_pt(7, 7, " ", plays_as="A"), _pt(7, 8, "T")]
    assert validate_placement(_empty_state(), tiles) is True


# --- validate_placement: linearity ---

def test_validate_diagonal_rejected():
    tiles = [_pt(7, 7, "A"), _pt(8, 8, "B")]
    assert validate_placement(_empty_state(), tiles) is False

def test_validate_single_tile_at_center_is_valid():
    assert validate_placement(_empty_state(), [_pt(7, 7, "A")]) is True


# --- validate_placement: contiguity ---

def test_validate_gap_no_bridge():
    tiles = [_pt(7, 7, "A"), _pt(7, 9, "B")]  # gap at (7,8), board empty
    assert validate_placement(_empty_state(), tiles) is False

def test_validate_gap_bridged_by_existing_tile():
    state = _state_with({(7, 8): "X"})
    tiles = [_pt(7, 7, "A"), _pt(7, 9, "B")]
    assert validate_placement(state, tiles) is True


# --- validate_placement: first move ---

def test_validate_first_move_covers_center():
    tiles = [_pt(7, 6, "A"), _pt(7, 7, "B")]
    assert validate_placement(_empty_state(), tiles) is True

def test_validate_first_move_misses_center():
    tiles = [_pt(6, 7, "A"), _pt(6, 8, "B")]
    assert validate_placement(_empty_state(), tiles) is False


# --- validate_placement: adjacency ---

def test_validate_not_adjacent_to_existing():
    state = _state_with({(7, 7): "A"})
    tiles = [_pt(5, 5, "B"), _pt(5, 6, "C")]
    assert validate_placement(state, tiles) is False

def test_validate_adjacent_horizontally():
    state = _state_with({(7, 7): "A"})
    tiles = [_pt(7, 8, "B"), _pt(7, 9, "C")]
    assert validate_placement(state, tiles) is True

def test_validate_adjacent_vertically():
    state = _state_with({(7, 7): "A"})
    tiles = [_pt(8, 7, "B"), _pt(9, 7, "C")]
    assert validate_placement(state, tiles) is True


# --- formed_words ---

def test_formed_words_horizontal():
    tiles = [_pt(7, 7, "C"), _pt(7, 8, "A"), _pt(7, 9, "T")]
    board = apply_placement(_blank_board(), tiles)
    assert "CAT" in formed_words(board, tiles)

def test_formed_words_vertical():
    tiles = [_pt(7, 7, "C"), _pt(8, 7, "A"), _pt(9, 7, "T")]
    board = apply_placement(_blank_board(), tiles)
    assert "CAT" in formed_words(board, tiles)

def test_formed_words_cross_word():
    base = _blank_board()
    base[7][7] = "C"
    base[7][8] = "A"
    base[7][9] = "T"
    new_tiles = [_pt(6, 8, "D"), _pt(8, 8, "G")]
    board = apply_placement(base, new_tiles)
    assert "DAG" in formed_words(board, new_tiles)

def test_formed_words_single_tile_no_neighbours():
    tiles = [_pt(7, 7, "A")]
    board = apply_placement(_blank_board(), tiles)
    assert formed_words(board, tiles) == []

def test_formed_words_single_tile_extends_row():
    base = _blank_board()
    base[7][7] = "C"
    base[7][8] = "A"
    new_tiles = [_pt(7, 9, "T")]
    board = apply_placement(base, new_tiles)
    assert "CAT" in formed_words(board, new_tiles)
