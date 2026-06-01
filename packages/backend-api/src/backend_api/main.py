from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_api.repositories.game_repo import GameRepo
from backend_api.routes import events, games

load_dotenv()

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_CORS_ORIGINS = [
    s.strip() for s in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
]


async def _gc_sweep(repo: GameRepo) -> None:
    """Every 60 seconds, garbage-collect paused games older than 30 minutes."""
    while True:
        await asyncio.sleep(60.0)
        codes = await repo.active_codes()
        for code in codes:
            state = await repo.load_game(code)
            if state is None:
                continue
            if state.phase != "paused" or state.paused_at is None:
                continue
            elapsed = time.time() - state.paused_at
            if elapsed >= 1800.0:  # 30 minutes
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(events.router)
