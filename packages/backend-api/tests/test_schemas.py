from game_engine.models import GamePhase, Dictionary, Player, Tile  # type: ignore
from backend_api.schemas import PlayerOut  # type: ignore


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
