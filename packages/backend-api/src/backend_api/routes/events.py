from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend_api import sse_manager
from backend_api.connection_lifecycle import lifecycle
from backend_api.repositories.game_repo import GameRepo
from backend_api.schemas import GameStateOut
from backend_api.services.game_service import GameService
from backend_api.session import PlayerSession

router = APIRouter(tags=["events"])

_KEEPALIVE_INTERVAL = 15.0


def _get_repo(request: Request) -> GameRepo:
    return GameRepo(request.app.state.redis)


def get_service(repo: GameRepo = Depends(_get_repo)) -> GameService:
    return GameService(repo)


async def _require_session(
    token: str,
    repo: GameRepo = Depends(_get_repo),
) -> PlayerSession:
    session = await repo.load_session(token)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return session


async def _event_generator(
    request: Request,
    session: PlayerSession,
    repo: GameRepo,
    svc: GameService,
) -> AsyncGenerator[str, None]:
    code = session.game_code
    token = session.token

    try:
        await svc.connect_player(code, session.player_id, token)
    except Exception:
        return

    state = await repo.load_game(code)
    if state is not None:
        view = GameStateOut.from_domain(
            state,
            viewer_id=session.player_id,
            connected_map=lifecycle.connected_map(code),
        )
        yield f"data: {json.dumps(view.model_dump(mode='json'))}\n\n"

    queue = sse_manager.subscribe(code, token, session.player_id)
    try:
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=_KEEPALIVE_INTERVAL)
            except asyncio.TimeoutError:
                if await request.is_disconnected():
                    break
                yield ": keepalive\n\n"
            else:
                yield f"data: {payload}\n\n"
    finally:
        sse_manager.unsubscribe(code, token)
        try:
            await svc.disconnect_player(code, session.player_id, token)
        except Exception:
            pass


@router.get("/events")
async def sse_stream(
    request: Request,
    session: PlayerSession = Depends(_require_session),
    repo: GameRepo = Depends(_get_repo),
    svc: GameService = Depends(get_service),
) -> StreamingResponse:
    return StreamingResponse(
        _event_generator(request, session, repo, svc),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
