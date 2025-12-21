import hashlib
import json
from typing import Any, Dict, Optional, Tuple
from src.determinism import now


_CACHE: Dict[Tuple[str, str, str], Dict[str, Any]] = {}


def cacheKeyFrom(*parts: Any) -> str:
    """Build a deterministic cache key from arbitrary parts.

    Serializes to JSON with sorted keys, then hashes to a short hex string.
    """
    try:
        payload = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    except Exception:
        payload = repr(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def get_block(project_id: str, block_name: str, key: str) -> Optional[Any]:
    entry = _CACHE.get((project_id, block_name, key))
    if not entry:
        return None
    return entry.get("value")


def set_block(project_id: str, block_name: str, key: str, value: Any) -> None:
    _CACHE[(project_id, block_name, key)] = {
        "value": value,
        "ts": now(),
    }


def invalidate(project_id: Optional[str] = None, block_name: Optional[str] = None) -> int:
    """Invalidate cached entries by optional project and block filters.

    Returns number of entries removed.
    """
    to_delete = []
    for (pid, bname, key) in _CACHE.keys():
        if project_id and pid != project_id:
            continue
        if block_name and bname != block_name:
            continue
        to_delete.append((pid, bname, key))
    for k in to_delete:
        _CACHE.pop(k, None)
    return len(to_delete)
