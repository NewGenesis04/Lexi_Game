from __future__ import annotations

import pickle
from pathlib import Path

from game_engine.models import Dictionary

_DICTIONARIES_DIR = Path(__file__).parent / "dictionaries"
_cache: dict[Dictionary, frozenset[str]] = {}


def load(dictionary: Dictionary) -> frozenset[str]:
    if dictionary not in _cache:
        path = _DICTIONARIES_DIR / f"{dictionary.value}.pkl"
        _cache[dictionary] = pickle.loads(path.read_bytes())
    return _cache[dictionary]


def is_valid_word(word: str, dictionary: Dictionary) -> bool:
    return word.upper() in load(dictionary)
