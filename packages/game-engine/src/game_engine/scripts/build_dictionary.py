"""Compile word list .txt files into pickled frozensets."""
import pickle
from pathlib import Path

WORD_LISTS_DIR = Path(__file__).parents[5] / "word_lists"
OUT_DIR = Path(__file__).parents[1] / "dictionaries"


def build(name: str) -> None:
    words = frozenset(w.upper() for w in (WORD_LISTS_DIR / f"{name}.txt").read_text().split())
    (OUT_DIR / f"{name}.pkl").write_bytes(pickle.dumps(words, protocol=5))
    print(f"Built {name}: {len(words):,} words -> {OUT_DIR / f'{name}.pkl'}")


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    build("TWL06")
    build("CSW21")
