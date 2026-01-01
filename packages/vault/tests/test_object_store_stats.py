"""ObjectStore stats and listing."""
import tempfile
from pathlib import Path
import sys

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.storage.objectStore import ObjectStore


def test_object_store_stats_and_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ObjectStore(tmpdir)
        payload = {"foo": "bar"}
        h = store.put(payload)

        hashes = store.list_objects()
        assert hashes == [h]
        stats = store.stats()
        assert stats["object_count"] == 1
        assert stats["total_bytes"] > 0
