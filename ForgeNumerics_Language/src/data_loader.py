import os
from typing import Dict, List, Tuple
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(ROOT, os.pardir))
CONFIG_PATH = os.path.join(WORKSPACE_ROOT, "config.yml")

FILES = {
    "symbols": os.path.join(WORKSPACE_ROOT, "symbols.txt"),
    "words": os.path.join(WORKSPACE_ROOT, "Words.txt"),
    "combos": os.path.join(WORKSPACE_ROOT, "symbol_combinations_len1-4.txt"),
    "mapping": os.path.join(WORKSPACE_ROOT, "word_to_symbol_combos_mapping.txt"),
}

class DataLoader:
    def __init__(self, paths: Dict[str, str] | None = None):
        cfg = self._load_config()
        default_paths = FILES.copy()
        if cfg and "paths" in cfg:
            for k in default_paths:
                if k in cfg["paths"]:
                    default_paths[k] = os.path.join(WORKSPACE_ROOT, cfg["paths"][k])
        self.paths = paths or default_paths

    def _load_config(self) -> Dict[str, Dict[str, str]] | None:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return None

    def defaults(self) -> Dict[str, str]:
        cfg = self._load_config() or {}
        return cfg.get("defaults", {})

    def _read_lines(self, path: str) -> List[str]:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def load_words(self) -> List[str]:
        return self._read_lines(self.paths["words"])  # one word per line

    def load_symbols(self) -> List[str]:
        return self._read_lines(self.paths["symbols"])  # one symbol per line or spec

    def load_combos(self) -> List[str]:
        return self._read_lines(self.paths["combos"])  # precomputed symbol combos

    def load_word_to_combo(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for line in self._read_lines(self.paths["mapping"]):
            # allow both TSV and space-separated: "word\tcombo" or "word combo"
            parts = [p for p in line.replace("\t", " ").split(" ") if p]
            if len(parts) >= 2:
                word = parts[0]
                combo = parts[1]
                mapping[word] = combo
        return mapping

    def free_combos(self) -> List[str]:
        # Free combos = combos not used in mapping
        combos = set(self.load_combos())
        used = set(self.load_word_to_combo().values())
        return sorted(list(combos - used))
