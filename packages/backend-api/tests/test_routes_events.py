import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient

from game_engine.models import Dictionary, GamePhase  # type: ignore

from backend_api import sse_manager
from backend_api.main import app  # type: ignore
from backend_api.routes import events as events_module
from backend_api.routes.events import _get_repo, _event_generator  # type: ignore
from backend_api.services.game_service import GameService
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


class FakeDisconnectRequest:
    """Minimal Request stand-in; the generator only calls `is_disconnected`."""

    def __init__(self, disconnected: bool = False):
        self._disconnected = disconnected

    async def is_disconnected(self) -> bool:
        return self._disconnected


def _payload(event: str) -> dict:
    return json.loads(event[len("data:"):].strip())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


async def test_initial_event_contains_game_state():
    repo = FakeGameRepo(session=_MOCK_SESSION, state=_make_state())
    svc = GameService(repo)
    gen = _event_generator(FakeDisconnectRequest(), _MOCK_SESSION, repo, svc)

    event = await gen.__anext__()
    assert event.startswith("data: ")
    assert _payload(event)["code"] == "ABCD12"

    await gen.aclose()


async def test_broadcast_event_is_delivered_promptly():
    repo = FakeGameRepo(session=_MOCK_SESSION, state=_make_state())
    svc = GameService(repo)
    sse_manager.subscribe("ABCD12", "tok123", "p1")
    with patch.object(svc, "disconnect_player", new=AsyncMock()):
        try:
            gen = _event_generator(FakeDisconnectRequest(), _MOCK_SESSION, repo, svc)

            assert (await gen.__anext__()).startswith("data: ")

            task = asyncio.create_task(gen.__anext__())
            await asyncio.sleep(0)  # let the generator subscribe and park on queue.get
            await sse_manager.broadcast({"tok123": '{"move": "pass"}'})
            event = await task
            assert event == 'data: {"move": "pass"}\n\n'

            await gen.aclose()
        finally:
            sse_manager.unsubscribe("ABCD12", "tok123")


async def test_unsubscribe_and_disconnect_player_called_on_disconnect():
    repo = FakeGameRepo(session=_MOCK_SESSION, state=_make_state())
    svc = GameService(repo)
    sse_manager.subscribe("ABCD12", "tok123", "p1")
    try:
        with patch.object(sse_manager, "unsubscribe") as mock_unsub, \
             patch.object(svc, "disconnect_player", new=AsyncMock()) as mock_disconnect:
            req = FakeDisconnectRequest(disconnected=False)
            gen = _event_generator(req, _MOCK_SESSION, repo, svc)

            await gen.__anext__()  # consume initial state

            req._disconnected = True
            with patch.object(events_module, "_KEEPALIVE_INTERVAL", 0.05):
                with pytest.raises(StopAsyncIteration):
                    await gen.__anext__()

            mock_unsub.assert_called_once_with("ABCD12", "tok123")
            mock_disconnect.assert_awaited_once()
    finally:
        sse_manager.unsubscribe("ABCD12", "tok123")