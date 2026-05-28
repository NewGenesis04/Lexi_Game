import pytest
import fakeredis

from game_engine.models import (  # type: ignore
    Dictionary, GamePhase, GameState, Move, MoveType, PlacedTile, Player, Tile,
)
from backend_api.repositories.game_repo import GameRepo  # type: ignore
from backend_api.session import PlayerSession  # type: ignore


@pytest.fixture
async def repo() -> GameRepo:
    client = fakeredis.FakeAsyncRedis(decode_responses=True)
    return GameRepo(client)


def _make_state(code: str = "ABCD12") -> GameState:
    return GameState(
        code=code,
        phase=GamePhase.PLAYING,
        dictionary=Dictionary.TWL06,
        bag=[Tile(letter="E", points=1), Tile(letter="A", points=1)],
        players=[
            Player(
                id="player-1",
                nickname="Alice",
                rack=[Tile(letter="S", points=1), Tile(letter=" ", points=0)],
                time_remaining_secs=180.5,
                score=24,
            ),
            Player(
                id="player-2",
                nickname="Bob",
                rack=[Tile(letter="Q", points=10)],
                time_remaining_secs=300.0,
                score=0,
            ),
        ],
        current_player_index=1,
        consecutive_passes=2,
        paused_time_left=45.0,
    )


def _make_session() -> PlayerSession:
    return PlayerSession(
        token="abc123",
        player_id="player-1",
        game_code="ABCD12",
        nickname="Alice",
    )


# --- save / load game ---

async def test_save_and_load_game_core_fields(repo):
    state = _make_state()
    await repo.save_game(state)
    loaded = await repo.load_game(state.code)
    assert loaded is not None
    assert loaded.code == "ABCD12"
    assert loaded.phase == GamePhase.PLAYING
    assert loaded.dictionary == Dictionary.TWL06
    assert loaded.current_player_index == 1
    assert loaded.consecutive_passes == 2
    assert loaded.paused_time_left == 45.0


async def test_save_and_load_game_bag(repo):
    state = _make_state()
    await repo.save_game(state)
    loaded = await repo.load_game(state.code)
    assert len(loaded.bag) == 2
    assert loaded.bag[0].letter == "E"
    assert loaded.bag[0].points == 1


async def test_save_and_load_game_players(repo):
    state = _make_state()
    await repo.save_game(state)
    loaded = await repo.load_game(state.code)
    assert len(loaded.players) == 2
    alice = loaded.players[0]
    assert alice.id == "player-1"
    assert alice.nickname == "Alice"
    assert alice.score == 24
    assert alice.time_remaining_secs == 180.5
    assert len(alice.rack) == 2
    assert alice.rack[0].letter == "S"
    assert alice.rack[1].letter == " "   # blank


async def test_save_and_load_game_board(repo):
    state = _make_state()
    state.board[7][7] = "A"
    state.board[7][8] = "t"   # lowercase = previously placed blank
    await repo.save_game(state)
    loaded = await repo.load_game(state.code)
    assert loaded.board[7][7] == "A"
    assert loaded.board[7][8] == "t"
    assert loaded.board[0][0] is None


async def test_save_and_load_game_move_history(repo):
    state = _make_state()
    move = Move(
        type=MoveType.PLACE,
        player_id="player-1",
        tiles=[PlacedTile(row=7, col=7, letter="A")],
        letters=[],
    )
    state.last_move = move
    state.move_history = [move]
    await repo.save_game(state)
    loaded = await repo.load_game(state.code)
    assert len(loaded.move_history) == 1
    assert loaded.last_move is not None
    assert loaded.last_move.type == MoveType.PLACE
    assert loaded.last_move.player_id == "player-1"
    assert loaded.last_move.tiles[0].row == 7
    assert loaded.last_move.tiles[0].col == 7


async def test_load_game_missing_returns_none(repo):
    assert await repo.load_game("ZZZZZZ") is None


async def test_delete_game(repo):
    state = _make_state()
    await repo.save_game(state)
    await repo.delete_game(state.code)
    assert await repo.load_game(state.code) is None


async def test_save_overwrites_existing(repo):
    state = _make_state()
    await repo.save_game(state)
    state.players[0].score = 99
    await repo.save_game(state)
    loaded = await repo.load_game(state.code)
    assert loaded.players[0].score == 99


# --- save / load session ---

async def test_save_and_load_session(repo):
    session = _make_session()
    await repo.save_session(session.token, session)
    loaded = await repo.load_session(session.token)
    assert loaded is not None
    assert loaded.token == "abc123"
    assert loaded.player_id == "player-1"
    assert loaded.game_code == "ABCD12"
    assert loaded.nickname == "Alice"


async def test_load_session_missing_returns_none(repo):
    assert await repo.load_session("nonexistent") is None


async def test_delete_session(repo):
    session = _make_session()
    await repo.save_session(session.token, session)
    await repo.delete_session(session.token)
    assert await repo.load_session(session.token) is None


# --- active games set ---

async def test_register_active(repo):
    await repo.register_active("ABCD12")
    assert "ABCD12" in await repo.active_codes()


async def test_deregister_active(repo):
    await repo.register_active("ABCD12")
    await repo.deregister_active("ABCD12")
    assert "ABCD12" not in await repo.active_codes()


async def test_active_codes_multiple(repo):
    for code in ("AAAA11", "BBBB22", "CCCC33"):
        await repo.register_active(code)
    codes = await repo.active_codes()
    assert {"AAAA11", "BBBB22", "CCCC33"} <= codes


async def test_active_codes_empty(repo):
    assert await repo.active_codes() == set()
