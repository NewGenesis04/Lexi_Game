from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_api.routes import events, games

load_dotenv()

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.redis = aioredis.from_url(_REDIS_URL, decode_responses=True)
    yield
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
