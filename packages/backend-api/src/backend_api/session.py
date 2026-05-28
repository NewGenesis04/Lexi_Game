from __future__ import annotations

import secrets
from dataclasses import dataclass


@dataclass
class PlayerSession:
    token: str
    player_id: str
    game_code: str
    nickname: str


def generate_token() -> str:
    return secrets.token_hex(16)
