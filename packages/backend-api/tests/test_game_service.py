import pytest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from game_engine.models import (  # type: ignore
    Dictionary, GamePhase, GameState, MoveType, Player, PlacedTile, Tile,
)
from game_engine import PassRequest, PlaceRequest, SwapRequest, Turn
from backend_api import game_manager, sse_manager, turn_clock
from backend_api.connection_lifecycle import lifecycle
from backend_api.services.game_service import GameService  # type: ignore


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
        patch("backend_api.connection_lifecycle.lifecycle.remove_game"),
        patch("backend_api.connection_lifecycle.lifecycle.set_pause_timer"),
        patch("backend_api.connection_lifecycle.lifecycle.cancel_pause_timer"),
        patch("backend_api.sse_manager.broadcast", new_callable=AsyncMock),
    ):
        yield


@pytest.fixture(autouse=True)
def clear_game_manager():
    lifecycle._connections.clear()
    lifecycle._pending_disconnects.clear()
    turn_clock.clock.clear("ABCD12")
    turn_clock.clock.clear("ABCD99")


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


async def test_join_game_broadcasts_to_the_waiting_creator(repo, svc):
    """Regression: join_game used to only return the state to the joiner —
    a creator already sitting on an SSE connection never learned someone
    joined until they refreshed."""
    c = await svc.create_game("Alice", Dictionary.TWL06, 180.0)
    sse_manager.subscribe(c.code, "tok-alice", c.player_id)
    try:
        with patch("backend_api.sse_manager.broadcast", new_callable=AsyncMock) as mock_broadcast:
            await svc.join_game(c.code, "Bob")
        payloads = mock_broadcast.call_args.args[0]
        assert "tok-alice" in payloads
    finally:
        sse_manager.unsubscribe(c.code, "tok-alice")


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
# apply_move — place
# ---------------------------------------------------------------------------

async def test_place_tiles_updates_board_and_score(repo, svc):
    await repo.save_game(_state())
    tiles = [
        PlacedTile(row=7, col=7, letter="C"),
        PlacedTile(row=7, col=8, letter="A"),
        PlacedTile(row=7, col=9, letter="T"),
    ]
    await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
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
        await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=[PlacedTile(row=0, col=0, letter="C")]))
    assert exc.value.status_code == 422


async def test_place_tiles_invalid_word_raises_422(repo, svc):
    await repo.save_game(_state(p1_letters="XXXZZZQ"))
    tiles = [
        PlacedTile(row=7, col=7, letter="X"),
        PlacedTile(row=7, col=8, letter="Z"),
    ]
    with pytest.raises(HTTPException) as exc:
        await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
    assert exc.value.status_code == 422


async def test_place_tiles_wrong_player_raises_403(repo, svc):
    await repo.save_game(_state())
    with pytest.raises(HTTPException) as exc:
        await svc.apply_move("ABCD12", "p2", PlaceRequest(player_id="p2", tiles=[PlacedTile(row=7, col=7, letter="A")]))
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
    await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED


# ---------------------------------------------------------------------------
# apply_move — swap
# ---------------------------------------------------------------------------

async def test_swap_tiles_refreshes_rack(repo, svc):
    await repo.save_game(_state())
    await svc.apply_move("ABCD12", "p1", SwapRequest(player_id="p1", letters=["C", "A", "T"]))
    s = await repo.load_game("ABCD12")
    assert len(s.players[0].rack) == 7
    assert s.current_player_index == 1
    assert s.consecutive_passes == 0


async def test_swap_tiles_insufficient_bag_raises_422(repo, svc):
    state = _state()
    state.bag = [Tile(letter="A", points=1)] * 2  # only 2 tiles, trying to swap 3
    await repo.save_game(state)
    with pytest.raises(HTTPException) as exc:
        await svc.apply_move("ABCD12", "p1", SwapRequest(player_id="p1", letters=["C", "A", "T"]))
    assert exc.value.status_code == 422


# ---------------------------------------------------------------------------
# apply_move — pass
# ---------------------------------------------------------------------------

async def test_pass_turn_increments_counter(repo, svc):
    await repo.save_game(_state())
    await svc.apply_move("ABCD12", "p1", PassRequest(player_id="p1"))
    s = await repo.load_game("ABCD12")
    assert s.consecutive_passes == 1
    assert s.current_player_index == 1


async def test_six_passes_ends_game(repo, svc):
    state = _state()
    state.consecutive_passes = 5
    await repo.save_game(state)
    await svc.apply_move("ABCD12", "p1", PassRequest(player_id="p1"))
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED


# ---------------------------------------------------------------------------
# connect_player / disconnect_player / pause / resume
# ---------------------------------------------------------------------------

async def test_connect_player_marks_connected(repo, svc):
    state = _state()
    await repo.save_game(state)
    assert lifecycle.is_player_connected("ABCD12", "p1") is False
    await svc.connect_player("ABCD12", "p1", "tok1")
    assert lifecycle.is_player_connected("ABCD12", "p1") is True
    assert lifecycle.is_player_connected("ABCD12", "p2") is False
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PLAYING


async def test_connect_player_resumes_when_both_connected(repo, svc):
    state = _state()
    state.phase = GamePhase.PAUSED
    state.paused_time_left = 90.0
    state.paused_at = 1000.0
    state.players[0].time_remaining_secs = 90.0
    await repo.save_game(state)
    lifecycle.add_connection("ABCD12", "p1", "tok_p1")
    await svc.connect_player("ABCD12", "p2", "tok2")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PLAYING
    assert lifecycle.is_player_connected("ABCD12", "p1") is True
    assert lifecycle.is_player_connected("ABCD12", "p2") is True
    assert s.players[0].time_remaining_secs == 90.0  # restored from paused_time_left
    assert s.paused_time_left is None
    assert s.paused_at is None


async def test_connect_player_stays_paused_if_other_offline(repo, svc):
    state = _state()
    state.phase = GamePhase.PAUSED
    await repo.save_game(state)
    await svc.connect_player("ABCD12", "p1", "tok1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PAUSED
    assert lifecycle.is_player_connected("ABCD12", "p1") is True
    assert lifecycle.is_player_connected("ABCD12", "p2") is False


async def test_connect_player_does_nothing_for_created(repo, svc):
    state = _state()
    state.phase = GamePhase.CREATED
    await repo.save_game(state)
    await svc.connect_player("ABCD12", "p1", "tok1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.CREATED


async def test_connect_player_does_nothing_for_finished(repo, svc):
    state = _state()
    state.phase = GamePhase.FINISHED
    await repo.save_game(state)
    await svc.connect_player("ABCD12", "p1", "tok1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED


async def test_disconnect_player_pauses_playing_game(repo, svc):
    state = _state()
    await repo.save_game(state)
    lifecycle.add_connection("ABCD12", "p1", "tok_p1")
    lifecycle.add_connection("ABCD12", "p2", "tok_p2")
    with (
        patch("backend_api.turn_clock.clock.elapsed", return_value=5.0),
        patch("backend_api.connection_lifecycle.lifecycle.set_pause_timer"),
    ):
        await svc.disconnect_player("ABCD12", "p1", "tok_p1")
        # Grace timer was scheduled; fire it manually to check the pause logic
        await lifecycle._pause_after_grace("ABCD12", "p1", repo, grace_secs=0)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PAUSED
    assert lifecycle.is_player_connected("ABCD12", "p1") is False
    assert lifecycle.is_player_connected("ABCD12", "p2") is True
    assert s.paused_time_left is not None
    assert s.paused_at is not None
    assert s.paused_time_left == 175.0  # 180 - 5 elapsed


async def test_disconnect_player_does_nothing_for_created(repo, svc):
    state = _state()
    state.phase = GamePhase.CREATED
    await repo.save_game(state)
    await svc.disconnect_player("ABCD12", "p1", "tok1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.CREATED


async def test_disconnect_player_does_nothing_for_finished(repo, svc):
    state = _state()
    state.phase = GamePhase.FINISHED
    await repo.save_game(state)
    await svc.disconnect_player("ABCD12", "p1", "tok1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED


async def test_disconnect_player_does_not_pause_if_player_never_connected(repo, svc):
    """Regression: SSE connect during CREATED phase never marks player connected.
    When that SSE later disconnects, disconnect_player must NOT pause the game,
    because the player wasn't actually playing."""
    state = _state()  # phase = PLAYING, players = [p1, p2]
    await repo.save_game(state)
    # p1's SSE connected while game was CREATED — connect_player returned early,
    # so p1 was never marked connected in game_manager.
    # Now p1's SSE disconnects:
    await svc.disconnect_player("ABCD12", "p1", "tok1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PLAYING  # must NOT be PAUSED
    assert lifecycle.is_player_connected("ABCD12", "p1") is False


async def test_disconnect_player_unknown_player_is_noop(repo, svc):
    state = _state()
    await repo.save_game(state)
    await svc.disconnect_player("ABCD12", "unknown", "tok_unknown")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PLAYING


async def test_pause_game_freezes_clock_for_active_player(repo, svc):
    state = _state()
    state.current_player_index = 0  # Alice is active
    await repo.save_game(state)
    with patch("backend_api.turn_clock.clock.elapsed", return_value=5.0):
        lifecycle.pause(state)
    assert state.phase == GamePhase.PAUSED
    assert state.paused_time_left == 175.0
    assert state.paused_at is not None


async def test_resume_game_restores_clock(repo, svc):
    state = _state()
    state.phase = GamePhase.PAUSED
    state.paused_time_left = 90.0
    state.paused_at = 1000.0
    lifecycle.resume(state)
    assert state.phase == GamePhase.PLAYING
    assert state.players[0].time_remaining_secs == 90.0
    assert state.paused_time_left is None
    assert state.paused_at is None


async def test_disconnect_grace_task_forfeit_when_one_player_connected(repo, svc):
    state = _state()
    state.phase = GamePhase.PAUSED
    await repo.save_game(state)
    lifecycle.add_connection("ABCD12", "p1", "tok_p1")
    await lifecycle._disconnect_grace_task("ABCD12", repo, grace_secs=0.001)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED
    assert s.last_move.type == MoveType.TIMEOUT
    assert s.last_move.player_id == "p2"  # p2 is the loser (disconnected)


async def test_disconnect_grace_task_both_offline_stays_paused(repo, svc):
    state = _state()
    state.phase = GamePhase.PAUSED
    await repo.save_game(state)
    await lifecycle._disconnect_grace_task("ABCD12", repo, grace_secs=0.001)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PAUSED  # stays paused for GC


async def test_disconnect_grace_task_no_op_if_game_resumed(repo, svc):
    state = _state()
    state.phase = GamePhase.PLAYING  # game was resumed
    await repo.save_game(state)
    await lifecycle._disconnect_grace_task("ABCD12", repo, grace_secs=0.001)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PLAYING  # no change


async def test_disconnect_grace_task_no_op_if_game_deleted(repo, svc):
    # No game saved — task should not crash
    await lifecycle._disconnect_grace_task("ABCD12", repo, grace_secs=0.001)


# ---------------------------------------------------------------------------
# forfeit
# ---------------------------------------------------------------------------

async def test_forfeit_ends_game(repo, svc):
    await repo.save_game(_state())
    await svc.forfeit("ABCD12", "p1")
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED
    assert s.last_move.type == MoveType.FORFEIT


# ---------------------------------------------------------------------------
# time deduction (engine apply_elapsed via apply_move)
# ---------------------------------------------------------------------------

async def test_deduct_time_subtracts_from_active_player(repo, svc):
    await repo.save_game(_state())
    tiles = [
        PlacedTile(row=7, col=7, letter="C"),
        PlacedTile(row=7, col=8, letter="A"),
        PlacedTile(row=7, col=9, letter="T"),
    ]
    with patch("backend_api.turn_clock.clock.elapsed", return_value=5.0):
        await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
    s = await repo.load_game("ABCD12")
    assert s.players[0].time_remaining_secs == pytest.approx(175.0, abs=0.01)
    assert s.players[1].time_remaining_secs == 180.0


async def test_deduct_time_floor_at_zero(repo, svc):
    """Huge elapsed triggers first overtime: +60s extension, overtime_count=1."""
    await repo.save_game(_state())
    tiles = [
        PlacedTile(row=7, col=7, letter="C"),
        PlacedTile(row=7, col=8, letter="A"),
        PlacedTile(row=7, col=9, letter="T"),
    ]
    with patch("backend_api.turn_clock.clock.elapsed", return_value=999.0):
        await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
    s = await repo.load_game("ABCD12")
    assert s.players[0].time_remaining_secs == 60.0
    assert s.players[0].overtime_count == 1


async def test_apply_move_clears_turn_started(repo, svc):
    await repo.save_game(_state())
    turn_clock.clock.mark_turn_started("ABCD12")
    tiles = [PlacedTile(row=7, col=7, letter="C")]
    with patch("backend_api.services.game_service.bag_module.draw_tiles") as mock_draw:
        mock_draw.return_value = ([], [])
        await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
    assert turn_clock.clock.elapsed("ABCD12") < 1.0  # was reset, so elapsed is near-zero


async def test_rejected_move_still_deducts_and_persists_time(repo, svc):
    """Regression: an invalid move used to skip the clock deduction entirely,
    leaving the player's bank artificially high after any rejected attempt."""
    await repo.save_game(_state())
    with patch("backend_api.turn_clock.clock.elapsed", return_value=5.0):
        with pytest.raises(HTTPException):
            await svc.apply_move(
                "ABCD12", "p1", PlaceRequest(player_id="p1", tiles=[PlacedTile(row=0, col=0, letter="C")]),
            )
    s = await repo.load_game("ABCD12")
    assert s.players[0].time_remaining_secs == pytest.approx(175.0, abs=0.01)


async def test_rejected_move_reanchors_clock_instead_of_losing_elapsed_time(repo, svc):
    """Regression: clearing (rather than re-anchoring) the clock after a
    rejected move made every subsequent elapsed() read ~0 until the next
    successful move, silently losing all the real time spent in between."""
    await repo.save_game(_state())
    with patch("backend_api.turn_clock.clock.elapsed", return_value=5.0):
        with pytest.raises(HTTPException):
            await svc.apply_move(
                "ABCD12", "p1", PlaceRequest(player_id="p1", tiles=[PlacedTile(row=0, col=0, letter="C")]),
            )

    tiles = [PlacedTile(row=7, col=7, letter="C"), PlacedTile(row=7, col=8, letter="A"), PlacedTile(row=7, col=9, letter="T")]
    with patch("backend_api.turn_clock.clock.elapsed", return_value=3.0):
        await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
    s = await repo.load_game("ABCD12")
    assert s.players[0].time_remaining_secs == pytest.approx(172.0, abs=0.01)  # 180 - 5 - 3


async def test_invalid_word_error_names_the_word(repo, svc):
    await repo.save_game(_state(p1_letters="XXXZZZQ"))
    tiles = [PlacedTile(row=7, col=7, letter="X"), PlacedTile(row=7, col=8, letter="Z")]
    with pytest.raises(HTTPException) as exc:
        await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
    assert exc.value.status_code == 422
    assert "XZ" in exc.value.detail


async def test_invalid_word_does_not_notify_the_opponent(repo, svc):
    """Rejected-move feedback stays private to the mover — the opponent
    doesn't need to know about a move that never actually happened."""
    await repo.save_game(_state(p1_letters="XXXZZZQ"))
    sse_manager.subscribe("ABCD12", "tok-p2", "p2")
    try:
        tiles = [PlacedTile(row=7, col=7, letter="X"), PlacedTile(row=7, col=8, letter="Z")]
        with patch("backend_api.sse_manager.broadcast", new_callable=AsyncMock) as mock_broadcast:
            with pytest.raises(HTTPException):
                await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
        mock_broadcast.assert_not_called()
    finally:
        sse_manager.unsubscribe("ABCD12", "tok-p2")


async def test_successful_place_broadcasts_play_announcement(repo, svc):
    """Unlike rejected moves, a scored word is public — everyone (including
    the mover) gets a pill announcing it."""
    await repo.save_game(_state())
    tiles = [
        PlacedTile(row=7, col=7, letter="C"),
        PlacedTile(row=7, col=8, letter="A"),
        PlacedTile(row=7, col=9, letter="T"),
    ]
    with patch("backend_api.services.game_service.broadcaster.notify", new_callable=AsyncMock) as mock_notify:
        await svc.apply_move("ABCD12", "p1", PlaceRequest(player_id="p1", tiles=tiles))
    mock_notify.assert_awaited_once()
    args, kwargs = mock_notify.call_args
    assert args[0] == "ABCD12"
    assert args[1] == "Alice played CAT for 10 pts"
    assert kwargs["notif_type"] == "success"


async def test_swap_does_not_broadcast_play_announcement(repo, svc):
    await repo.save_game(_state())
    with patch("backend_api.services.game_service.broadcaster.notify", new_callable=AsyncMock) as mock_notify:
        await svc.apply_move("ABCD12", "p1", SwapRequest(player_id="p1", letters=["C", "A", "T"]))
    mock_notify.assert_not_awaited()


async def test_pass_does_not_broadcast_play_announcement(repo, svc):
    await repo.save_game(_state())
    with patch("backend_api.services.game_service.broadcaster.notify", new_callable=AsyncMock) as mock_notify:
        await svc.apply_move("ABCD12", "p1", PassRequest(player_id="p1"))
    mock_notify.assert_not_awaited()


# ---------------------------------------------------------------------------
# time bank / overtime (_time_bank_task)
# ---------------------------------------------------------------------------

async def test_overtime_first_timeout_penalty(repo, svc):
    """1st timeout: -10 points, reset to 60s, overtime_count=1."""
    await repo.save_game(_state())
    with patch("asyncio.sleep", new=AsyncMock()), \
         patch("asyncio.create_task") as mock_ct:
        await svc._time_bank_task("ABCD12", "p1", 180.0)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PLAYING
    assert s.players[0].score == -10
    assert s.players[0].time_remaining_secs == 60.0
    assert s.players[0].overtime_count == 1
    mock_ct.assert_called_once()


async def test_overtime_second_timeout_grant(repo, svc):
    """2nd timeout still grants overtime (-10, +60s); forfeit only on the 4th."""
    state = _state()
    state.players[0].score = -10
    state.players[0].overtime_count = 1
    state.players[0].time_remaining_secs = 60.0
    await repo.save_game(state)
    with patch("asyncio.sleep", new=AsyncMock()), \
         patch("asyncio.create_task") as mock_ct:
        await svc._time_bank_task("ABCD12", "p1", 60.0)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PLAYING
    assert s.players[0].score == -20
    assert s.players[0].time_remaining_secs == 60.0
    assert s.players[0].overtime_count == 2
    mock_ct.assert_called_once()


async def test_overtime_fourth_timeout_forfeit(repo, svc):
    """4th timeout (3 OT already used): forfeit the player."""
    state = _state()
    state.players[0].score = -30
    state.players[0].overtime_count = 3
    state.players[0].time_remaining_secs = 60.0
    await repo.save_game(state)
    with patch("asyncio.sleep", new=AsyncMock()):
        await svc._time_bank_task("ABCD12", "p1", 60.0)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED
    assert s.players[0].time_remaining_secs == 0.0
    assert s.last_move.type == MoveType.TIMEOUT


async def test_overtime_no_op_when_wrong_player(repo, svc):
    """Timeout fires but current player has changed — should be a no-op."""
    state = _state()
    state.current_player_index = 1
    await repo.save_game(state)
    await svc._time_bank_task("ABCD12", "p1", 0.001)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.PLAYING
    assert s.players[0].score == 0
    assert s.players[0].overtime_count == 0


async def test_overtime_no_op_when_game_over(repo, svc):
    """Timeout fires after game has already ended — should be a no-op."""
    state = _state()
    state.phase = GamePhase.FINISHED
    await repo.save_game(state)
    await svc._time_bank_task("ABCD12", "p1", 0.001)
    s = await repo.load_game("ABCD12")
    assert s.phase == GamePhase.FINISHED
