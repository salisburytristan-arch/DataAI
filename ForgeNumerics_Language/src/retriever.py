import os
import re
import json
import math
import random
from typing import Dict, List, Tuple, Any, Optional
from src.determinism import ACX_TEST_MODE, apply_seed
from src.embeddings import hash_embed


_STOP = set(
    "the a an and or of to in on for with without from by at as is are was were be been being this that those these it its".split()
)


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return [t for t in tokens if t not in _STOP]


def _read_text_files(root: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for dirpath, _dirs, files in os.walk(root):
        for fname in files:
            if not fname.lower().endswith((".md", ".txt")):
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    out.append((path, f.read()))
            except Exception:
                # Skip unreadable files
                continue
    return out


def _chunk_text(text: str, max_chars: int = 600) -> List[str]:
    # Simple paragraph-split, then size-bound concatenation
    paras = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks: List[str] = []
    buf: List[str] = []
    cur = 0
    for p in paras:
        if cur + len(p) + 2 <= max_chars:
            buf.append(p)
            cur += len(p) + 2
        else:
            if buf:
                chunks.append("\n\n".join(buf))
            buf = [p]
            cur = len(p)
    if buf:
        chunks.append("\n\n".join(buf))
    # Fallback if no paragraphs
    if not chunks:
        text = text.strip()
        for i in range(0, len(text), max_chars):
            chunks.append(text[i : i + max_chars])
    return chunks


def build_index(source_dir: str, max_chars: int = 600) -> Dict[str, Any]:
    if ACX_TEST_MODE:
        apply_seed()
    docs = _read_text_files(source_dir)
    chunks: List[Dict[str, Any]] = []
    vocab_df: Dict[str, int] = {}
    for doc_id, (path, text) in enumerate(docs):
        for ci, chunk in enumerate(_chunk_text(text, max_chars=max_chars)):
            toks = _tokenize(chunk)
            tf: Dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            # update document frequency per term (count once per chunk)
            seen = set()
            for t in toks:
                if t in seen:
                    continue
                vocab_df[t] = vocab_df.get(t, 0) + 1
                seen.add(t)
            chunks.append({"doc_id": doc_id, "path": path, "chunk_id": ci, "text": chunk, "tf": tf, "len": len(toks)})
    N = max(1, len(chunks))
    # Use (N+1)/(df+1) to avoid negative IDF when N=df
    idf: Dict[str, float] = {t: math.log((N + 1.0) / (df + 1.0)) for t, df in vocab_df.items()}
    avg_len = sum(ch["len"] for ch in chunks) / float(N)
    return {"chunks": chunks, "idf": idf, "doc_count": len(docs), "avg_len": avg_len}


def build_hash_embeddings(index: Dict[str, Any], dim: int = 128) -> List[Dict[str, Any]]:
    """Generate deterministic hash embeddings for each chunk in the index.

    Returns a list of {"path", "chunk_id", "embedding"} suitable for save_embeddings().
    """
    out: List[Dict[str, Any]] = []
    for ch in index.get("chunks", []):
        emb = hash_embed(ch.get("text", ""), dim=dim)
        out.append({"path": ch.get("path"), "chunk_id": ch.get("chunk_id"), "embedding": emb})
    return out


def attach_embeddings(index: Dict[str, Any], emb_path: str) -> Dict[str, Any]:
    """Attach precomputed embeddings to index chunks.

    Expects emb_path JSON list of {"path": str, "chunk_id": int, "embedding": [float,..]}.
    """
    if not os.path.exists(emb_path):
        return index
    with open(emb_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    emb_map: Dict[Tuple[str, int], List[float]] = {}
    for it in items:
        try:
            key = (it["path"], int(it["chunk_id"]))
            emb_map[key] = it.get("embedding", [])
        except Exception:
            continue
    for ch in index.get("chunks", []):
        key = (ch.get("path"), ch.get("chunk_id"))
        if key in emb_map:
            ch["embedding"] = emb_map[key]
    return index


def save_index(index: Dict[str, Any], path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    return os.path.abspath(path)


def save_embeddings(embeddings: List[Dict[str, Any]], path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(embeddings, f, ensure_ascii=False)
    return os.path.abspath(path)


def load_index(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def search(index: Dict[str, Any], query: str, k: int = 6, query_embedding: Optional[List[float]] = None, alpha: float = 0.2) -> List[Dict[str, Any]]:
    if ACX_TEST_MODE:
        apply_seed()
    qtoks = _tokenize(query)
    qtf: Dict[str, int] = {}
    for t in qtoks:
        qtf[t] = qtf.get(t, 0) + 1
    idf = index.get("idf", {})
    avg_len = float(index.get("avg_len", 1.0))
    k1 = 1.5
    b = 0.75
    scores: List[Tuple[float, Dict[str, Any]]] = []
    for ch in index.get("chunks", []):
        score = 0.0
        dl = max(1, ch.get("len", 1))
        for t, qf in qtf.items():
            tf = ch["tf"].get(t, 0)
            if tf:
                idf_t = idf.get(t, 0.0)
                denom = tf + k1 * (1 - b + b * (dl / avg_len))
                score += idf_t * ((tf * (k1 + 1)) / denom)
        # Optional embedding fusion
        if query_embedding is not None:
            emb = ch.get("embedding")
            if emb:
                score = (1 - alpha) * score + alpha * _cosine(query_embedding, emb)
        if score >= 0:
            scores.append((score, ch))
    # Deterministic tie-break: score desc (negative for sort), then path asc, then chunk_id asc
    scores.sort(key=lambda x: (-x[0], x[1].get("path"), x[1].get("chunk_id")))
    top = scores[:k]
    # Map to evidence strings with minimal citation metadata
    out = []
    for s, ch in top:
        out.append({
            "score": s,
            "path": ch["path"],
            "chunk_id": ch["chunk_id"],
            "text": ch["text"],
        })
    return out
