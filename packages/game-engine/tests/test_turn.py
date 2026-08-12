from game_engine.models import (  # type: ignore
    Dictionary, GamePhase, GameState, MoveType, Player, PlacedTile, Tile,
)
from game_engine.turn import (  # type: ignore
    PassRequest, PlaceRequest, SwapRequest, Turn, TurnError, TurnOutcome, apply_elapsed,
)


def _state(p1_letters="CATXYZW", p2_letters="ABCDEFG", *, bag_size=10, phase=GamePhase.PLAYING) -> GameState:
    rack1 = [Tile(letter=l, points=1) for l in p1_letters]
    rack2 = [Tile(letter=l, points=1) for l in p2_letters]
    return GameState(
        code="TURN01",
        phase=phase,
        dictionary=Dictionary.TWL06,
        bag=[Tile(letter="A", points=1)] * bag_size,
        players=[
            Player(id="p1", nickname="Alice", rack=rack1, time_remaining_secs=180.0),
            Player(id="p2", nickname="Bob", rack=rack2, time_remaining_secs=180.0),
        ],
        current_player_index=0,
    )


def _cat() -> list[PlacedTile]:
    return [
        PlacedTile(row=7, col=7, letter="C"),
        PlacedTile(row=7, col=8, letter="A"),
        PlacedTile(row=7, col=9, letter="T"),
    ]


# ---------------------------------------------------------------------------
# place
# ---------------------------------------------------------------------------

def test_place_updates_board_score_and_advances():
    state = _state()
    new_state, result = Turn.apply(state, PlaceRequest(player_id="p1", tiles=_cat()), 0.0)
    assert result.ok and result.outcome == TurnOutcome.OK
    assert new_state.board[7][7] == "C"
    assert new_state.board[7][8] == "A"
    assert new_state.board[7][9] == "T"
    assert new_state.players[0].score > 0
    assert new_state.current_player_index == 1
    assert new_state.consecutive_passes == 0
    assert len(new_state.move_history) == 1


def test_place_invalid_placement_error():
    state = _state()
    _, result = Turn.apply(state, PlaceRequest(player_id="p1", tiles=[PlacedTile(row=0, col=0, letter="C")]), 0.0)
    assert result.error == TurnError.INVALID_PLACEMENT
    assert state.board[0][0] is None  # nothing mutated


def test_place_invalid_word_error():
    state = _state(p1_letters="XXXZZQ")
    tiles = [PlacedTile(row=7, col=7, letter="X"), PlacedTile(row=7, col=8, letter="Z")]
    _, result = Turn.apply(state, PlaceRequest(player_id="p1", tiles=tiles), 0.0)
    assert result.error == TurnError.INVALID_WORD
    assert result.words == ["XZ"]


def test_place_letter_not_in_rack_error():
    state = _state()  # rack "CATXYZW" — only one A
    tiles = [PlacedTile(row=7, col=7, letter="A"), PlacedTile(row=7, col=8, letter="A")]
    _, result = Turn.apply(state, PlaceRequest(player_id="p1", tiles=tiles), 0.0)
    assert result.error == TurnError.LETTER_NOT_IN_RACK


def test_wrong_player_error():
    state = _state()
    _, result = Turn.apply(state, PlaceRequest(player_id="p2", tiles=_cat()), 0.0)
    assert result.error == TurnError.NOT_YOUR_TURN


def test_not_playing_error():
    state = _state(phase=GamePhase.CREATED)
    _, result = Turn.apply(state, PlaceRequest(player_id="p1", tiles=_cat()), 0.0)
    assert result.error == TurnError.NOT_PLAYING


def test_place_empties_rack_ends_game():
    state = _state(p1_letters="CAT", bag_size=0)
    new_state, result = Turn.apply(state, PlaceRequest(player_id="p1", tiles=_cat()), 0.0)
    assert result.outcome == TurnOutcome.ENDED_BAG_EMPTY
    assert new_state.phase == GamePhase.FINISHED


# ---------------------------------------------------------------------------
# swap
# ---------------------------------------------------------------------------

def test_swap_refreshes_rack_and_advances():
    state = _state()
    new_state, result = Turn.apply(state, SwapRequest(player_id="p1", letters=["C", "A", "T"]), 0.0)
    assert result.ok and result.outcome == TurnOutcome.OK
    assert len(new_state.players[0].rack) == 7
    assert new_state.current_player_index == 1
    assert new_state.consecutive_passes == 0


def test_swap_bag_too_small_error():
    state = _state(bag_size=2)
    _, result = Turn.apply(state, SwapRequest(player_id="p1", letters=["C", "A", "T"]), 0.0)
    assert result.error == TurnError.BAG_TOO_SMALL


def test_swap_letters_not_in_rack_error():
    state = _state()
    _, result = Turn.apply(state, SwapRequest(player_id="p1", letters=["J", "K", "L"]), 0.0)
    assert result.error == TurnError.LETTER_NOT_IN_RACK


# ---------------------------------------------------------------------------
# pass
# ---------------------------------------------------------------------------

def test_pass_increments_counter():
    state = _state()
    new_state, result = Turn.apply(state, PassRequest(player_id="p1"), 0.0)
    assert result.ok
    assert new_state.consecutive_passes == 1
    assert new_state.current_player_index == 1


def test_six_passes_end_game():
    state = _state()
    state.consecutive_passes = 5
    new_state, result = Turn.apply(state, PassRequest(player_id="p1"), 0.0)
    assert result.outcome == TurnOutcome.ENDED_SIX_PASSES
    assert new_state.phase == GamePhase.FINISHED


# ---------------------------------------------------------------------------
# clock expiry / overtime (apply_elapsed)
# ---------------------------------------------------------------------------

def test_apply_elapsed_subtracts_remaining():
    player = Player(id="p1", nickname="Alice", time_remaining_secs=180.0)
    forfeit = apply_elapsed(player, 5.0)
    assert forfeit is False
    assert player.time_remaining_secs == 175.0
    assert player.overtime_count == 0


def test_apply_elapsed_first_overtime_grant():
    player = Player(id="p1", nickname="Alice", time_remaining_secs=10.0)
    forfeit = apply_elapsed(player, 999.0)
    assert forfeit is False
    assert player.score == -10
    assert player.overtime_count == 1
    assert player.time_remaining_secs == 60.0


def test_apply_elapsed_three_grants_then_forfeit():
    player = Player(id="p1", nickname="Alice", overtime_count=2, time_remaining_secs=60.0)
    forfeit = apply_elapsed(player, 999.0)
    assert forfeit is False
    assert player.overtime_count == 3
    assert player.score == -10

    player = Player(id="p1", nickname="Alice", overtime_count=3, time_remaining_secs=60.0)
    forfeit = apply_elapsed(player, 999.0)
    assert forfeit is True
    assert player.time_remaining_secs == 0.0


def test_turn_timeout_mid_move():
    state = _state()
    state.players[0].overtime_count = 3
    state.players[0].time_remaining_secs = 1.0
    new_state, result = Turn.apply(state, PlaceRequest(player_id="p1", tiles=_cat()), 999.0)
    assert result.outcome == TurnOutcome.ENDED_TIMEOUT
    assert new_state.phase == GamePhase.FINISHED
    assert new_state.last_move.type == MoveType.TIMEOUT
    assert new_state.players[0].time_remaining_secs == 0.0


def test_turn_timeout_preempts_an_otherwise_valid_move():
    """Running out of the bank is judged before the move content is."""
    state = _state()
    state.players[0].overtime_count = 3
    state.players[0].time_remaining_secs = 1.0
    new_state, result = Turn.apply(state, PassRequest(player_id="p1"), 999.0)
    assert result.outcome == TurnOutcome.ENDED_TIMEOUT
    assert new_state.last_move.type == MoveType.TIMEOUT


def test_rejected_move_still_deducts_elapsed_time():
    """An invalid move still cost the player the seconds they spent on it."""
    state = _state()
    new_state, result = Turn.apply(
        state, PlaceRequest(player_id="p1", tiles=[PlacedTile(row=0, col=0, letter="C")]), 5.0,
    )
    assert result.error == TurnError.INVALID_PLACEMENT
    assert new_state.players[0].time_remaining_secs == 175.0
    assert new_state.current_player_index == 0  # rejected move never advances the turn


def test_rejected_move_elapsed_time_can_trigger_overtime():
    state = _state()
    state.players[0].time_remaining_secs = 10.0
    new_state, result = Turn.apply(
        state, PlaceRequest(player_id="p1", tiles=[PlacedTile(row=0, col=0, letter="C")]), 999.0,
    )
    assert result.error == TurnError.INVALID_PLACEMENT
    assert new_state.players[0].overtime_count == 1
    assert new_state.players[0].time_remaining_secs == 60.0


def test_turn_normal_time_deduction():
    state = _state()
    new_state, result = Turn.apply(state, PlaceRequest(player_id="p1", tiles=_cat()), 5.0)
    assert result.ok
    assert new_state.players[0].time_remaining_secs == 175.0
    assert new_state.players[1].time_remaining_secs == 180.0