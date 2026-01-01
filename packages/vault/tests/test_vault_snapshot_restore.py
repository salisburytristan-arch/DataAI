"""Snapshot/restore equivalence for search results."""
import shutil
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault


def test_snapshot_restore_preserves_search_results():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dst_dir:
        vault = Vault(src_dir)
        doc_id = vault.import_text("alpha beta gamma delta", title="Doc", source_path="/tmp/doc.txt")
        results_before = vault.search("beta", limit=3)
        assert results_before
        top_before = results_before[0]["chunk_id"]

        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        restored = Vault(dst_dir)
        results_after = restored.search("beta", limit=3)
        assert results_after
        assert results_after[0]["chunk_id"] == top_before
        # ensure chunk content matches
        restored_chunk = restored.get_chunk(results_after[0]["chunk_id"])
        assert restored_chunk is not None
        assert "beta" in restored_chunk.content
