from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["events"])


# GET /events?token=<session>
@router.get("/events")
async def sse_stream(token: str) -> StreamingResponse: ...
