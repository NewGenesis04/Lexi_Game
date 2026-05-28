from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/games", tags=["games"])


# POST /games
@router.post("")
async def create_game(): ...


# POST /games/{code}/join
@router.post("/{code}/join")
async def join_game(code: str): ...


# POST /games/{code}/moves
@router.post("/{code}/moves")
async def submit_move(code: str): ...


# POST /games/{code}/forfeit
@router.post("/{code}/forfeit")
async def forfeit_game(code: str): ...


# GET /games/{code}
@router.get("/{code}")
async def get_game(code: str): ...
