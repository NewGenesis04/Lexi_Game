from __future__ import annotations

from game_engine.models import GameState

from backend_api.repositories.game_repo import GameRepo
from backend_api.session import PlayerSession
from backend_api import game_manager, sse_manager


class GameService:
    def __init__(self, repo: GameRepo) -> None:
        self._repo = repo

    async def create_game(
        self, nickname: str, dictionary: str, time_limit_secs: float
    ) -> PlayerSession: ...

    async def join_game(self, code: str, nickname: str) -> PlayerSession: ...

    async def handle_move(self, code: str, token: str, move: dict) -> None: ...

    async def handle_forfeit(self, code: str, token: str) -> None: ...

    async def get_state(self, code: str, token: str) -> GameState: ...
