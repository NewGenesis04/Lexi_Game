import pickle
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _word_lists_dir(root: Path) -> Path:
    for candidate in (root / "word_lists", root.parents[1] / "word_lists"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"word_lists not found under {root}")


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        out_dir = Path(self.directory) / "game_engine" / "dictionaries"
        out_dir.mkdir(parents=True, exist_ok=True)
        force_include = build_data.setdefault("force_include", {})
        for name in ("TWL06", "CSW21"):
            words = frozenset(
                w.upper() for w in (_word_lists_dir(root) / f"{name}.txt").read_text().split()
            )
            out = out_dir / f"{name}.pkl"
            out.write_bytes(pickle.dumps(words, protocol=5))
            force_include[str(out)] = f"game_engine/dictionaries/{name}.pkl"