from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from backend_api.repositories.game_repo import GameRepo
from backend_api.schemas import (
    CreateGameOut, CreateGameRequest, GameStateOut, JoinGameOut, JoinGameRequest,
    MoveRequest, PlaceMoveRequest, SwapMoveRequest,
)
from backend_api.services.game_service import GameService
from backend_api.session import PlayerSession

router = APIRouter(prefix="/games", tags=["games"])


def _get_repo(request: Request) -> GameRepo:
    return GameRepo(request.app.state.redis)


def get_service(repo: GameRepo = Depends(_get_repo)) -> GameService:
    return GameService(repo)


async def _require_session(
    authorization: str = Header(...),
    repo: GameRepo = Depends(_get_repo),
) -> PlayerSession:
    token = authorization.removeprefix("Bearer ").strip()
    session = await repo.load_session(token)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return session


@router.post("", response_model=CreateGameOut, status_code=201)
async def create_game(
    body: CreateGameRequest,
    svc: GameService = Depends(get_service),
) -> CreateGameOut:
    return await svc.create_game(body.nickname, body.dictionary, body.time_per_player_secs, body.avatar)


@router.post("/{code}/join", response_model=JoinGameOut)
async def join_game(
    code: str,
    body: JoinGameRequest,
    svc: GameService = Depends(get_service),
) -> JoinGameOut:
    return await svc.join_game(code, body.nickname, body.avatar)


@router.get("/{code}", response_model=GameStateOut)
async def get_game(
    code: str,
    session: PlayerSession = Depends(_require_session),
    svc: GameService = Depends(get_service),
) -> GameStateOut:
    return await svc.get_game(code, session.player_id)


@router.post("/{code}/moves", response_model=GameStateOut)
async def submit_move(
    code: str,
    body: MoveRequest,
    session: PlayerSession = Depends(_require_session),
    svc: GameService = Depends(get_service),
) -> GameStateOut:
    if isinstance(body, PlaceMoveRequest):
        return await svc.place_tiles(code, session.player_id, [t.to_domain() for t in body.tiles])
    if isinstance(body, SwapMoveRequest):
        return await svc.swap_tiles(code, session.player_id, body.letters)
    return await svc.pass_turn(code, session.player_id)


@router.post("/{code}/forfeit", response_model=GameStateOut)
async def forfeit_game(
    code: str,
    session: PlayerSession = Depends(_require_session),
    svc: GameService = Depends(get_service),
) -> GameStateOut:
    return await svc.forfeit(code, session.player_id)
