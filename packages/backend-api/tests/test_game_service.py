import pytest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from game_engine.models import (  # type: ignore
    Dictionary, GamePhase, GameState, Move, MoveType, Player, PlacedTile, Tile,
)
from backend_api.services.game_service import GameService  # type: ignore
from backend_api.session import PlayerSession  # type: ignore


# ---------------------------------------------------------------------------
# Fake repo
# ---------------------------------------------------------------------------

class FakeGameRepo:
    def __init__(self):
        self._games: dict = {}
        self._sessions: dict = {}
        self._active: set = set()

    async def save_game(self, state): self._games[state.code] = state
    async def load_game(self, code): return self._games.get(code)
    async def delete_game(self, code): self._games.pop(code, None)
    async def save_session(self, token, session): self._sessions[token] = session
    async def load_session(self, token): return self._sessions.get(token)
    async def delete_session(self, token): self._sessions.pop(token, None)
    async def register_active(self, code): self._active.add(code)
    async def deregister_active(self, code): self._active.discard(code)
    async def active_codes(self): return set(self._active)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state(code="ABCD12", p1_letters="CATXYZW", p2_letters="ABCDEFG") -> GameState:
    rack1 = [Tile(letter=l, points=1) for l in p1_letters]
    rack2 = [Tile(letter=l, points=1) for l in p2_letters]
    return GameState(
        code=code,
        phase=GamePhase.PLAYING,
        dictionary=Dictionary.TWL06,
        bag=[Tile(letter="A", points=1)] * 10,
        players=[
            Player(id="p1", nickname="Alice", rack=rack1, time_remaining_secs=180.0),
            Player(id="p2", nickname="Bob", rack=rack2, time_remaining_secs=180.0),
        ],
        current_player_index=0,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo():
    return FakeGameRepo()


@pytest.fixture
def svc(repo):
    return GameService(repo)


@pytest.fixture(autouse=True)
def mock_side_effects():
    with (
        patch("backend_api.game_manager.set_timer"),
        patch("backend_api.game_manager.cancel_timer"),
        patch("backend_api.game_manager.remove_game"),
        patch("backend_api.sse_manager.broadcast", new_callable=AsyncMock),
    ):
        yield


# ---------------------------------------------------------------------------
# create_game
# ---------------------------------------------------------------------------

async def test_create_game_returns_identifiers(svc):
    out = await svc.create_game("Alice", Dictionary.TWL06, 180.0)
    assert len(out.code) == 6
    assert out.token
    assert out.player_id


async def test_create_game_saves_state(repo, svc):
    out = await svc.create_game("Alice", Dictionary.TWL06, 180.0)
    state = await repo.load_game(out.code)
    assert state.phase == GamePhase.CREATED
    assert len(state.players) == 1
    assert len(state.players[0].rack) == 7
    assert state.players[0].time_remaining_secs == 180.0


async def test_create_game_registers_active(repo, svc):
    out = await svc.create_game("Alice", Dictionary.TWL06, 180.0)
    assert out.code in await repo.active_codes()


# ---------------------------------------------------------------------------
# join_game
# ---------------------------------------------------------------------------

async def test_join_game_starts_playing(repo, svc):
    c = await svc.create_game("Alice", Dictionary.TWL06, 180.0)
    j = await svc.join_game(c.code, "Bob")
    state = await repo.load_game(c.code)
    assert state.phase == GamePhase.PLAYING
    assert len(state.players) == 2
    assert len(state.players[1].rack) == 7
    assert j.token != c.token
    assert j.player_id != c.player_id


async def test_join_game_not_found(svc):
    with pytest.raises(HTTPException) as exc:
        await svc.join_game("ZZZZZZ", "Bob")
    assert exc.value.status_code == 404


async def test_join_game_already_full(repo, svc):
    c = await svc.create_game("Alice", Dictionary.TWL06, 180.0)
    await svc.join_game(c.code, "Bob")
    with pytest.raises(HTTPException) as exc:
        await svc.join_game(c.code, "Carol")
    assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# get_game
# ---------------------------------------------------------------------------

async def test_get_game_sanitizes_opponent_rack(repo, svc):
    c = await svc.create_game("Alice", Dictionary.TWL06, 180.0)
    j = await svc.join_game(c.code, "Bob")
    view = await svc.get_game(c.code, c.player_id)
    alice = next(p for p in view.players if p.id == c.player_id)
    bob = next(p for p in view.players if p.id == j.player_id)
    assert len(alice.rack) == 7
    assert bob.rack == []


# ---------------------------------------------------------------------------
# place_tiles
# ---------------------------------------------------------------------------

async def test_place_tiles_updates_board_and_score(repo, svc):
    await repo.save_game(_state())
    tiles = [
        PlacedTile(row=7, col=7, letter="C"),
        PlacedTile(row=7, col=8, letter="A"),
        PlacedTile(row=7, col=9, letter="T"),
    ]
    await svc.place_tiles("ABCD12", "p1", tiles)
    s = await repo.load_game("ABCD12")
    assert s.board[7][7] == "C"
    assert s.board[7][8] == "A"
    assert s.board[7][9] == "T"
    assert s.players[0].score > 0
    assert s.current_player_index == 1
    assert s.consecutive_passes == 0


async def test_place_tiles_invalid_placement_raises_422(repo, svc):
    await repo.save_game(_state())
    with pytest.raises(HTTPException) as exc:
        await svc.place_tiles("ABCD12", "p1", [PlacedTile(row=0, col=0, letter="C")])
    assert exc.value.status_code == 422


async def test_place_tiles_invalid_word_raises_422(repo, svc):
    await repo.save_game(_state(p1_letters="XXXZZZQ"))
    tiles = [
        PlacedTile(row=7, col=7, letter="X"),
        PlacedTile(row=7, col=8, letter="Z"),
    ]
    with pytest.raises(HTTPException) as exc:
        await svc.place_tiles("ABCD12", "p1", tiles)
    assert exc.value.status_code == 422


async def test_place_tiles_wrong_player_raises_403(repo, svc):
    await repo.save_game(_state())
    with pytest.raises(HTTPException) as exc:
        await svc.place_tiles("ABCD12", "p2", [PlacedTile(row=7, col=7, letter="A")])
    assert exc.value.status_code == 403


async def test_place_tiles_empties_rack_ends_game(repo, svc):
    state = _state(p1_letters="CAT")
    state.bag = []
    await repo.save_game(state)
    tiles = [
        PlacedTile(row=7, col=7, letter="C"),
        PlacedTile(row=7, col=8, letter="A"),
        PlacedTile(row=7, col=9, letter="T"),
    ]
    await svc.place_tiles("ABCD12", "p1", tiles)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED


# ---------------------------------------------------------------------------
# swap_tiles
# ---------------------------------------------------------------------------

async def test_swap_tiles_refreshes_rack(repo, svc):
    await repo.save_game(_state())
    await svc.swap_tiles("ABCD12", "p1", ["C", "A", "T"])
    s = await repo.load_game("ABCD12")
    assert len(s.players[0].rack) == 7
    assert s.current_player_index == 1
    assert s.consecutive_passes == 0


async def test_swap_tiles_insufficient_bag_raises_422(repo, svc):
    state = _state()
    state.bag = [Tile(letter="A", points=1)] * 2  # only 2 tiles, trying to swap 3
    await repo.save_game(state)
    with pytest.raises(HTTPException) as exc:
        await svc.swap_tiles("ABCD12", "p1", ["C", "A", "T"])
    assert exc.value.status_code == 422


# ---------------------------------------------------------------------------
# pass_turn
# ---------------------------------------------------------------------------

async def test_pass_turn_increments_counter(repo, svc):
    await repo.save_game(_state())
    await svc.pass_turn("ABCD12", "p1")
    s = await repo.load_game("ABCD12")
    assert s.consecutive_passes == 1
    assert s.current_player_index == 1


async def test_six_passes_ends_game(repo, svc):
    state = _state()
    state.consecutive_passes = 5
    await repo.save_game(state)
    await svc.pass_turn("ABCD12", "p1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED


# ---------------------------------------------------------------------------
# forfeit
# ---------------------------------------------------------------------------

async def test_forfeit_ends_game(repo, svc):
    await repo.save_game(_state())
    await svc.forfeit("ABCD12", "p1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED
    assert s.last_move.type == MoveType.FORFEIT
