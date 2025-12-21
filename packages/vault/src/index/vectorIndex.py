"""
Simple bag-of-words vector index for Vault chunks.
Computes TF-IDF-like weights and supports cosine-similar search.
Persists to JSON under vault/index/.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple
import math


def tokenize(text: str) -> List[str]:
    tokens: List[str] = []
    for raw in text.lower().split():
        t = ''.join(ch for ch in raw if ch.isalnum())
        if len(t) >= 2:
            tokens.append(t)
    return tokens


class VectorIndex:
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.index_dir = self.root / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.vectors_path = self.index_dir / "vectors.json"
        self.df_path = self.index_dir / "df.json"
        self.meta_path = self.index_dir / "vectors_meta.json"

        self.vectors: Dict[str, Dict[str, float]] = {}
        self.df: Dict[str, int] = {}
        self.n_docs: int = 0
        self._load()

    def _load(self):
        try:
            if self.vectors_path.exists():
                with open(self.vectors_path, 'r', encoding='utf-8') as f:
                    self.vectors = json.load(f)
            if self.df_path.exists():
                with open(self.df_path, 'r', encoding='utf-8') as f:
                    self.df = json.load(f)
            if self.meta_path.exists():
                with open(self.meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    self.n_docs = int(meta.get('n_docs', 0))
        except Exception as e:
            print(f"Warning: vector index load failed: {e}")

    def _persist(self):
        with open(self.vectors_path, 'w', encoding='utf-8') as f:
            json.dump(self.vectors, f, indent=2, ensure_ascii=False)
        with open(self.df_path, 'w', encoding='utf-8') as f:
            json.dump(self.df, f, indent=2, ensure_ascii=False)
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump({"n_docs": self.n_docs}, f, indent=2, ensure_ascii=False)

    def _tfidf_vector(self, tokens: List[str]) -> Dict[str, float]:
        # term frequencies
        tf: Dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        max_tf = max(tf.values()) if tf else 1

        # compute weights: (0.5 + 0.5 * tf/max_tf) * idf
        vec: Dict[str, float] = {}
        for t, count in tf.items():
            df_t = self.df.get(t, 0)
            idf = math.log((self.n_docs + 1) / (df_t + 1)) + 1.0
            wt = (0.5 + 0.5 * (count / max_tf)) * idf
            vec[t] = wt
        return vec

    def index_chunk(self, chunk_id: str, content: str) -> None:
        tokens = tokenize(content)
        # Update document frequency with unique tokens
        seen = set(tokens)
        for t in seen:
            self.df[t] = self.df.get(t, 0) + 1
        self.n_docs = max(self.n_docs, len(set(self.vectors.keys()) | {chunk_id}))
        # Build and store vector
        vec = self._tfidf_vector(tokens)
        self.vectors[chunk_id] = vec
        self._persist()

    def ensure_index(self, chunks: List[Tuple[str, str]]) -> None:
        # chunks: list of (chunk_id, content)
        for cid, content in chunks:
            if cid not in self.vectors:
                self.index_chunk(cid, content)

    @staticmethod
    def _dot(a: Dict[str, float], b: Dict[str, float]) -> float:
        s = 0.0
        # iterate over smaller vector for performance
        if len(a) < len(b):
            items = a.items()
            other = b
        else:
            items = b.items()
            other = a
        for t, w in items:
            s += w * other.get(t, 0.0)
        return s

    @staticmethod
    def _norm(a: Dict[str, float]) -> float:
        return math.sqrt(sum(w * w for w in a.values()))

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        q_vec = self._tfidf_vector(tokenize(query))
        q_norm = self._norm(q_vec) or 1e-9
        scores: List[Tuple[str, float]] = []
        for cid, vec in self.vectors.items():
            v_norm = self._norm(vec) or 1e-9
            sim = self._dot(q_vec, vec) / (q_norm * v_norm)
            if sim > 0.0:
                scores.append((cid, sim))
        scores.sort(key=lambda x: -x[1])
        return scores[:limit]
