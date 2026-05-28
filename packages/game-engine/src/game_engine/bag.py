from __future__ import annotations

import random

from game_engine.models import Tile

# (letter, points, count)
_DISTRIBUTION: list[tuple[str, int, int]] = [
    ("A", 1, 9),  ("B", 3, 2),  ("C", 3, 2),  ("D", 2, 4),  ("E", 1, 12),
    ("F", 4, 2),  ("G", 2, 3),  ("H", 4, 2),  ("I", 1, 9),  ("J", 8, 1),
    ("K", 5, 1),  ("L", 1, 4),  ("M", 3, 2),  ("N", 1, 6),  ("O", 1, 8),
    ("P", 3, 2),  ("Q", 10, 1), ("R", 1, 6),  ("S", 1, 4),  ("T", 1, 6),
    ("U", 1, 4),  ("V", 4, 2),  ("W", 4, 2),  ("X", 8, 1),  ("Y", 4, 2),
    ("Z", 10, 1), (" ", 0, 2),  # blank
]


def build_bag() -> list[Tile]:
    tiles = [
        Tile(letter=letter, points=points)
        for letter, points, count in _DISTRIBUTION
        for _ in range(count)
    ]
    random.shuffle(tiles)
    return tiles


def draw_tiles(bag: list[Tile], count: int) -> tuple[list[Tile], list[Tile]]:
    """Returns (drawn, remaining_bag). Draws min(count, len(bag)) tiles."""
    n = min(count, len(bag))
    return bag[:n], bag[n:]


def exchange_tiles(
    bag: list[Tile], returned: list[Tile], count: int
) -> tuple[list[Tile], list[Tile]]:
    """Return tiles to bag, reshuffle, draw count. Returns (drawn, new_bag)."""
    new_bag = bag + returned
    random.shuffle(new_bag)
    return draw_tiles(new_bag, count)
