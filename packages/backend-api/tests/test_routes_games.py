import pytest
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from game_engine.models import Dictionary, GamePhase  # type: ignore
from backend_api.main import app  # type: ignore
from backend_api.routes.games import _require_session, get_service  # type: ignore
from backend_api.schemas import (  # type: ignore
    CreateGameOut, GameStateOut, JoinGameOut, PlayerOut,
)
from backend_api.services.game_service import GameService  # type: ignore
from backend_api.session import PlayerSession  # type: ignore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_SESSION = PlayerSession(
    token="tok123", player_id="p1", game_code="ABCD12", nickname="Alice"
)


def _state_out(code: str = "ABCD12") -> GameStateOut:
    return GameStateOut(
        code=code,
        phase=GamePhase.PLAYING,
        dictionary=Dictionary.TWL06,
        board=[[None] * 15 for _ in range(15)],
        bag_size=86,
        players=[
            PlayerOut(id="p1", nickname="Alice", score=0, time_remaining_secs=180.0, overtime_count=0, rack=[]),
            PlayerOut(id="p2", nickname="Bob", score=0, time_remaining_secs=180.0, overtime_count=0, rack=[]),
        ],
        current_player_index=0,
        consecutive_passes=0,
        last_move=None,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_svc():
    svc = AsyncMock(spec=GameService)
    svc.create_game.return_value = CreateGameOut(code="ABCD12", token="tok123", player_id="p1")
    svc.join_game.return_value = JoinGameOut(token="tok456", player_id="p2", state=_state_out())
    svc.get_game.return_value = _state_out()
    svc.place_tiles.return_value = _state_out()
    svc.swap_tiles.return_value = _state_out()
    svc.pass_turn.return_value = _state_out()
    svc.forfeit.return_value = _state_out()
    return svc


@pytest.fixture
async def client(mock_svc):
    app.dependency_overrides[get_service] = lambda: mock_svc
    app.dependency_overrides[_require_session] = lambda: _MOCK_SESSION
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def unauthed_client(mock_svc):
    async def _deny():
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    app.dependency_overrides[get_service] = lambda: mock_svc
    app.dependency_overrides[_require_session] = _deny
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /games
# ---------------------------------------------------------------------------

async def test_create_game_returns_201(client, mock_svc):
    resp = await client.post("/games", json={
        "nickname": "Alice",
        "dictionary": "TWL06",
        "time_per_player_secs": 180.0,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "ABCD12"
    assert data["token"] == "tok123"
    mock_svc.create_game.assert_awaited_once_with("Alice", Dictionary.TWL06, 180.0)


# ---------------------------------------------------------------------------
# POST /games/{code}/join
# ---------------------------------------------------------------------------

async def test_join_game_returns_200(client, mock_svc):
    resp = await client.post("/games/ABCD12/join", json={"nickname": "Bob"})
    assert resp.status_code == 200
    assert resp.json()["token"] == "tok456"
    mock_svc.join_game.assert_awaited_once_with("ABCD12", "Bob")


# ---------------------------------------------------------------------------
# GET /games/{code}
# ---------------------------------------------------------------------------

async def test_get_game_returns_state(client, mock_svc):
    resp = await client.get("/games/ABCD12")
    assert resp.status_code == 200
    assert resp.json()["code"] == "ABCD12"
    mock_svc.get_game.assert_awaited_once_with("ABCD12", "p1")


async def test_get_game_without_token_returns_401(unauthed_client):
    resp = await unauthed_client.get("/games/ABCD12")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /games/{code}/moves — place
# ---------------------------------------------------------------------------

async def test_submit_place_move(client, mock_svc):
    resp = await client.post("/games/ABCD12/moves", json={
        "type": "place",
        "tiles": [
            {"row": 7, "col": 7, "letter": "C"},
            {"row": 7, "col": 8, "letter": "A"},
            {"row": 7, "col": 9, "letter": "T"},
        ],
    })
    assert resp.status_code == 200
    mock_svc.place_tiles.assert_awaited_once()
    args = mock_svc.place_tiles.call_args
    assert args[0][0] == "ABCD12"
    assert args[0][1] == "p1"
    assert len(args[0][2]) == 3


# ---------------------------------------------------------------------------
# POST /games/{code}/moves — swap
# ---------------------------------------------------------------------------

async def test_submit_swap_move(client, mock_svc):
    resp = await client.post("/games/ABCD12/moves", json={
        "type": "swap",
        "letters": ["C", "A", "T"],
    })
    assert resp.status_code == 200
    mock_svc.swap_tiles.assert_awaited_once_with("ABCD12", "p1", ["C", "A", "T"])


# ---------------------------------------------------------------------------
# POST /games/{code}/moves — pass
# ---------------------------------------------------------------------------

async def test_submit_pass_move(client, mock_svc):
    resp = await client.post("/games/ABCD12/moves", json={"type": "pass"})
    assert resp.status_code == 200
    mock_svc.pass_turn.assert_awaited_once_with("ABCD12", "p1")


# ---------------------------------------------------------------------------
# POST /games/{code}/moves — invalid type
# ---------------------------------------------------------------------------

async def test_submit_move_invalid_type_returns_422(client):
    resp = await client.post("/games/ABCD12/moves", json={"type": "explode"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /games/{code}/forfeit
# ---------------------------------------------------------------------------

async def test_forfeit_returns_200(client, mock_svc):
    resp = await client.post("/games/ABCD12/forfeit")
    assert resp.status_code == 200
    mock_svc.forfeit.assert_awaited_once_with("ABCD12", "p1")


async def test_forfeit_without_token_returns_401(unauthed_client):
    resp = await unauthed_client.post("/games/ABCD12/forfeit")
    assert resp.status_code == 401
