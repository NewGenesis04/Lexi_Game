from unittest.mock import patch

from game_engine.models import Dictionary, GamePhase, GameState, Player, Tile  # type: ignore
from backend_api import turn_clock  # type: ignore
from backend_api.schemas import GameStateOut, PlayerOut  # type: ignore


def _make_player(pid: str = "p1", nickname: str = "Alice") -> Player:
    return Player(
        id=pid,
        nickname=nickname,
        rack=[Tile(letter="A", points=1), Tile(letter="B", points=3)],
        time_remaining_secs=180.0,
        score=10,
    )


def test_player_out_self_includes_rack():
    player = _make_player()
    out = PlayerOut.from_domain(player, is_self=True)
    assert len(out.rack) == 2
    assert out.rack[0].letter == "A"
    assert out.rack[1].letter == "B"


def test_player_out_opponent_strips_rack():
    player = _make_player()
    out = PlayerOut.from_domain(player, is_self=False)
    assert out.rack == []


def test_player_out_other_fields_always_present():
    player = _make_player(pid="p2", nickname="Bob")
    out = PlayerOut.from_domain(player, is_self=False)
    assert out.id == "p2"
    assert out.nickname == "Bob"
    assert out.score == 10
    assert out.time_remaining_secs == 180.0
    assert out.connected is False


def test_player_out_connected_propagates():
    player = _make_player()
    out = PlayerOut.from_domain(player, is_self=False, connected=True)
    assert out.connected is True


def test_player_out_connected_defaults_false():
    player = _make_player()
    out = PlayerOut.from_domain(player, is_self=False)
    assert out.connected is False


# ---------------------------------------------------------------------------
# Live clock: the active player's view time is stored − elapsed
# ---------------------------------------------------------------------------

def _make_state(phase: GamePhase = GamePhase.PLAYING) -> GameState:
    return GameState(
        code="ABCD12",
        phase=phase,
        dictionary=Dictionary.TWL06,
        bag=[Tile(letter="A", points=1)],
        players=[_make_player("p1", "Alice"), _make_player("p2", "Bob")],
        current_player_index=0,
    )


def _view(state: GameState) -> GameStateOut:
    """Serialize with a fixed 30s of turn already burned."""
    with patch.object(turn_clock.clock, "elapsed", return_value=30.0):
        return GameStateOut.from_domain(state, viewer_id="p1")


def test_active_player_time_is_live():
    out = _view(_make_state())
    assert out.players[0].time_remaining_secs == 150.0


def test_inactive_player_time_is_untouched():
    out = _view(_make_state())
    assert out.players[1].time_remaining_secs == 180.0


def test_active_player_time_never_goes_negative():
    state = _make_state()
    with patch.object(turn_clock.clock, "elapsed", return_value=9999.0):
        out = GameStateOut.from_domain(state, viewer_id="p1")
    assert out.players[0].time_remaining_secs == 0.0


def test_paused_game_serializes_stored_time():
    out = _view(_make_state(GamePhase.PAUSED))
    assert [p.time_remaining_secs for p in out.players] == [180.0, 180.0]


def test_finished_game_serializes_stored_time():
    out = _view(_make_state(GamePhase.FINISHED))
    assert [p.time_remaining_secs for p in out.players] == [180.0, 180.0]


def test_created_game_serializes_stored_time():
    out = _view(_make_state(GamePhase.CREATED))
    assert [p.time_remaining_secs for p in out.players] == [180.0, 180.0]


def test_live_time_follows_current_player_index():
    state = _make_state()
    state.current_player_index = 1
    out = _view(state)
    assert out.players[0].time_remaining_secs == 180.0
    assert out.players[1].time_remaining_secs == 150.0
