import asyncio
import json
import pytest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from game_engine.models import Dictionary, GamePhase  # type: ignore
from backend_api.main import app  # type: ignore
from backend_api.routes.events import _get_repo  # type: ignore
from backend_api.session import PlayerSession  # type: ignore


# ---------------------------------------------------------------------------
# Fake repo
# ---------------------------------------------------------------------------

class FakeGameRepo:
    def __init__(self, session=None, state=None):
        self._session = session
        self._state = state

    async def load_session(self, token): return self._session
    async def load_game(self, code): return self._state
    async def save_game(self, s): pass
    async def save_session(self, t, s): pass
    async def delete_game(self, c): pass
    async def delete_session(self, t): pass
    async def register_active(self, c): pass
    async def deregister_active(self, c): pass
    async def active_codes(self): return set()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_SESSION = PlayerSession(
    token="tok123", player_id="p1", game_code="ABCD12", nickname="Alice"
)


def _make_state():
    from game_engine.models import GameState, Player, Tile
    return GameState(
        code="ABCD12",
        phase=GamePhase.PLAYING,
        dictionary=Dictionary.TWL06,
        bag=[Tile(letter="A", points=1)],
        players=[
            Player(id="p1", nickname="Alice", rack=[], time_remaining_secs=180.0),
            Player(id="p2", nickname="Bob", rack=[], time_remaining_secs=180.0),
        ],
        current_player_index=0,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def authed_client():
    repo = FakeGameRepo(session=_MOCK_SESSION, state=_make_state())
    app.dependency_overrides[_get_repo] = lambda: repo
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def unauthed_client():
    repo = FakeGameRepo(session=None, state=None)
    app.dependency_overrides[_get_repo] = lambda: repo
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_missing_token_returns_401(unauthed_client):
    resp = await unauthed_client.get("/events?token=badtoken")
    assert resp.status_code == 401


async def test_valid_token_content_type(authed_client):
    with patch("backend_api.sse_manager.subscribe") as mock_sub, \
         patch("backend_api.sse_manager.unsubscribe"):
        queue: asyncio.Queue[str] = asyncio.Queue()
        mock_sub.return_value = queue

        async with authed_client.stream("GET", "/events?token=tok123") as resp:
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    break

        mock_sub.assert_called_once_with("ABCD12", "tok123")


async def test_initial_event_contains_game_state(authed_client):
    with patch("backend_api.sse_manager.subscribe") as mock_sub, \
         patch("backend_api.sse_manager.unsubscribe"):
        queue: asyncio.Queue[str] = asyncio.Queue()
        mock_sub.return_value = queue

        async with authed_client.stream("GET", "/events?token=tok123") as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    payload = json.loads(line[len("data:"):].strip())
                    assert payload["code"] == "ABCD12"
                    break


async def test_unsubscribe_called_on_disconnect(authed_client):
    with patch("backend_api.sse_manager.subscribe") as mock_sub, \
         patch("backend_api.sse_manager.unsubscribe") as mock_unsub:
        queue: asyncio.Queue[str] = asyncio.Queue()
        mock_sub.return_value = queue

        async with authed_client.stream("GET", "/events?token=tok123") as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    break

        mock_unsub.assert_called_once_with("ABCD12", "tok123")
