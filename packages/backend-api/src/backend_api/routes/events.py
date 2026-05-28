from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend_api import sse_manager
from backend_api.repositories.game_repo import GameRepo
from backend_api.schemas import GameStateOut
from backend_api.session import PlayerSession

router = APIRouter(tags=["events"])


def _get_repo(request: Request) -> GameRepo:
    return GameRepo(request.app.state.redis)


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
) -> AsyncGenerator[str, None]:
    code = session.game_code
    token = session.token

    state = await repo.load_game(code)
    if state is not None:
        view = GameStateOut.from_domain(state, viewer_id=session.player_id)
        yield f"data: {json.dumps(view.model_dump(mode='json'))}\n\n"

    queue = sse_manager.subscribe(code, token)
    try:
        while True:
            get_task = asyncio.create_task(queue.get())
            dc_task = asyncio.create_task(request.is_disconnected())
            done, pending = await asyncio.wait(
                {get_task, dc_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for t in pending:
                t.cancel()
                try:
                    await t
                except asyncio.CancelledError:
                    pass
            if dc_task in done:
                break
            if get_task in done:
                yield f"data: {get_task.result()}\n\n"
    finally:
        sse_manager.unsubscribe(code, token)


@router.get("/events")
async def sse_stream(
    request: Request,
    session: PlayerSession = Depends(_require_session),
    repo: GameRepo = Depends(_get_repo),
) -> StreamingResponse:
    return StreamingResponse(
        _event_generator(request, session, repo),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
