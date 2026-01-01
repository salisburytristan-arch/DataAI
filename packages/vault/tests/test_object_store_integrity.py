"""ObjectStore integrity and dedup behavior."""
import tempfile
from pathlib import Path
import sys

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.storage.objectStore import ObjectStore


def test_put_deduplicates_and_integrity_detects_corruption():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ObjectStore(tmpdir)
        payload = {"a": 1, "b": "text"}

        h1 = store.put(payload)
        h2 = store.put(payload)
        assert h1 == h2
        assert store.exists(h1)
        assert store.verify_integrity(h1)

        # Corrupt the stored file and ensure verification fails
        obj_path = store._get_object_path(h1)
        obj_path.parent.mkdir(parents=True, exist_ok=True)
        obj_path.write_text("corrupted", encoding="utf-8")
        assert not store.verify_integrity(h1)
