"""
Optional embedding-based index for Vault chunks.
Uses sentence-transformers when available; otherwise gracefully disables.
Persists embeddings to JSON under vault/index/.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math

class EmbeddingIndex:
    def __init__(self, root_path: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.root = Path(root_path)
        self.index_dir = self.root / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.emb_path = self.index_dir / "embeddings.json"
        self.meta_path = self.index_dir / "embeddings_meta.json"
        self.cfg_path = self.index_dir / "embeddings_config.json"
        self.model_name = model_name

        self.embeddings: Dict[str, List[float]] = {}
        self.dim: int = 0
        self.available: bool = False
        self.enabled: bool = True
        self._model = None

        # Load config if present (enabled flag and model override)
        self._load_config()
        # Env override (e.g., ACX_EMBEDDINGS=0 to disable)
        import os
        env_flag = os.environ.get("ACX_EMBEDDINGS")
        if env_flag is not None:
            self.enabled = env_flag not in ("0", "false", "False")
        env_model = os.environ.get("ACX_EMBEDDINGS_MODEL")
        if env_model:
            self.model_name = env_model

        # Try to import sentence-transformers lazily if enabled
        if self.enabled:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                # mark available after successful load
                self.available = True
            except Exception:
                # Library or model not available; operate in disabled mode
                self.available = False
                self._model = None
        else:
            self.available = False
        self._load()

    def _load(self) -> None:
        try:
            if self.emb_path.exists():
                with open(self.emb_path, 'r', encoding='utf-8') as f:
                    self.embeddings = json.load(f)
            if self.meta_path.exists():
                with open(self.meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    self.dim = int(meta.get('dim', 0))
                    # if meta lists a model_name, prefer it for consistency
                    stored_model = meta.get('model_name')
                    if stored_model:
                        self.model_name = stored_model
        except Exception as e:
            print(f"Warning: embedding index load failed: {e}")

    def _persist(self) -> None:
        try:
            with open(self.emb_path, 'w', encoding='utf-8') as f:
                json.dump(self.embeddings, f)
            with open(self.meta_path, 'w', encoding='utf-8') as f:
                json.dump({"dim": self.dim, "model_name": self.model_name}, f)
        except Exception as e:
            print(f"Warning: embedding index persist failed: {e}")

    def _load_config(self) -> None:
        try:
            if self.cfg_path.exists():
                with open(self.cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    if isinstance(cfg, dict):
                        if "enabled" in cfg:
                            self.enabled = bool(cfg.get("enabled"))
                        if "model_name" in cfg and cfg.get("model_name"):
                            self.model_name = str(cfg.get("model_name"))
        except Exception as e:
            print(f"Warning: embedding config load failed: {e}")

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        # compute cosine similarity; guard against zero vectors
        dot = 0.0
        na = 0.0
        nb = 0.0
        # iterate in lockstep
        for i in range(min(len(a), len(b))):
            av = a[i]
            bv = b[i]
            dot += av * bv
            na += av * av
            nb += bv * bv
        if na <= 1e-12 or nb <= 1e-12:
            return 0.0
        return dot / (math.sqrt(na) * math.sqrt(nb))

    def _embed(self, text: str) -> Optional[List[float]]:
        if not self.available or self._model is None:
            return None
        try:
            vec = self._model.encode([text], convert_to_numpy=True)[0]
            # convert to plain python list for JSON
            lst = [float(x) for x in vec.tolist()] if hasattr(vec, 'tolist') else [float(x) for x in vec]
            if self.dim == 0:
                self.dim = len(lst)
            return lst
        except Exception:
            return None

    def index_chunk(self, chunk_id: str, content: str) -> None:
        if not self.available:
            return
        vec = self._embed(content)
        if vec is None:
            return
        self.embeddings[chunk_id] = vec
        self._persist()

    def ensure_index(self, chunks: List[Tuple[str, str]]) -> None:
        if not self.available:
            return
        for cid, content in chunks:
            if cid not in self.embeddings:
                self.index_chunk(cid, content)

    def is_ready(self) -> bool:
        return self.available and self.dim > 0 and len(self.embeddings) > 0

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        if not self.available or not self.is_ready():
            return []
        q = self._embed(query)
        if q is None:
            return []
        scores: List[Tuple[str, float]] = []
        for cid, vec in self.embeddings.items():
            sim = self._cosine(q, vec)
            if sim > 0.0:
                scores.append((cid, sim))
        scores.sort(key=lambda x: -x[1])
        return scores[:limit]
