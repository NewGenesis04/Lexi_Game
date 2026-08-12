from __future__ import annotations

import json

from game_engine.models import GameState

from backend_api import sse_manager
from backend_api.schemas import GameStateOut


class GameBroadcaster:
    """The one seam that turns a GameState into per-viewer SSE payloads and
    pumps them onto each connected player's queue.

    connected_map is passed in per call rather than stored, so this module
    stays decoupled from ConnectionLifecycle (which owns that map) and
    neither needs to import the other."""

    def serialize(self, state: GameState, connected_map: dict[str, bool]) -> dict[str, str]:
        """Per-recipient JSON payloads for a full game-state broadcast.
        Callers that need to release the game lock before pushing should
        call this inside the lock and pass the result to sse_manager.broadcast()
        outside it."""
        tokens = sse_manager.tokens_for_game(state.code)
        payloads: dict[str, str] = {}
        for token in tokens:
            pid = sse_manager.player_id_for_token(token)
            if pid is None:
                continue
            view = GameStateOut.from_domain(state, viewer_id=pid, connected_map=connected_map)
            payloads[token] = json.dumps(view.model_dump(mode="json"))
        return payloads

    async def broadcast(self, state: GameState, connected_map: dict[str, bool]) -> None:
        await sse_manager.broadcast(self.serialize(state, connected_map))

    async def notify(
        self, code: str, text: str, notif_type: str = "error", skip_player_id: str | None = None,
    ) -> None:
        """Send a lightweight notification event to all connected players except skip_player_id."""
        tokens = sse_manager.tokens_for_game(code)
        payloads: dict[str, str] = {}
        for token in tokens:
            pid = sse_manager.player_id_for_token(token)
            if pid is None or pid == skip_player_id:
                continue
            payloads[token] = json.dumps(
                {"type": "notification", "payload": {"text": text, "type": notif_type}},
            )
        if payloads:
            await sse_manager.broadcast(payloads)


# Process-scoped singleton — shared across all games and all requests.
broadcaster = GameBroadcaster()
