from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from game_engine.models import GamePhase

from backend_api import game_manager
from backend_api.repositories.game_repo import GameRepo
from backend_api.routes import events, games

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_CORS_ORIGINS = [
    s.strip() for s in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
]


async def _gc_sweep(repo: GameRepo) -> None:
    """Every 60 seconds, garbage-collect paused games older than 30 minutes.
    Cleans up both repo records and game_manager runtime state."""
    while True:
        await asyncio.sleep(60.0)
        codes = await repo.active_codes()
        for code in codes:
            async with game_manager.get_lock(code):
                state = await repo.load_game(code)
                if state is None:
                    game_manager.remove_game(code)
                    continue
                if state.phase != GamePhase.PAUSED or state.paused_at is None:
                    continue
                elapsed = time.time() - state.paused_at
                if elapsed >= 1800.0:  # 30 minutes
                    game_manager.remove_game(code)
                    await repo.delete_game(code)
                    await repo.deregister_active(code)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.redis = aioredis.from_url(_REDIS_URL, decode_responses=True)
    repo = GameRepo(app.state.redis)
    sweep = asyncio.create_task(_gc_sweep(repo))
    yield
    sweep.cancel()
    try:
        await sweep
    except asyncio.CancelledError:
        pass
    await app.state.redis.aclose()


app = FastAPI(title="NEO Scrabble", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(events.router)
