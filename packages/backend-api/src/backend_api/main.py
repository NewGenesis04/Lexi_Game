from fastapi import FastAPI

from backend_api.routes import events, games

app = FastAPI(title="NEO Scrabble")

app.include_router(games.router)
app.include_router(events.router)
