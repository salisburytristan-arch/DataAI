import hashlib
import re
from typing import List

_STOP = set(
    "the a an and or of to in on for with without from by at as is are was were be been being this that those these it its".split()
)


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return [t for t in tokens if t not in _STOP]


def _stable_bucket(token: str, dim: int) -> int:
    digest = hashlib.sha1(token.encode("utf-8", errors="ignore")).digest()
    # Use first 8 bytes for a consistent bucket assignment
    value = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return value % dim


def hash_embed(text: str, dim: int = 128) -> List[float]:
    """Create a deterministic hash-based embedding.

    This is a lightweight fallback when no model-based embeddings are available.
    Tokens are bucketed into a fixed dimension using SHA1 for stability, then
    L2-normalized.
    """
    if dim <= 0:
        raise ValueError("dim must be positive")
    vec = [0.0] * dim
    tokens = _tokenize(text)
    for tok in tokens:
        bucket = _stable_bucket(tok, dim)
        vec[bucket] += 1.0
    # L2 normalize
    norm = sum(x * x for x in vec) ** 0.5
    if norm == 0:
        return vec
    return [x / norm for x in vec]
