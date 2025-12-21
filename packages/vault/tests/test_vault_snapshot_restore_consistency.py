"""Snapshot/restore consistency when source keeps receiving new docs."""
import shutil
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault


def test_snapshot_restore_consistency_when_source_changes():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dst_dir:
        vault = Vault(src_dir)
        doc1 = vault.import_text("alpha beta gamma", title="Doc1", source_path="/tmp/doc1.txt")
        snapshot_before = vault.search("alpha", limit=3)
        assert snapshot_before

        # Take snapshot
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        restored = Vault(dst_dir)

        # Mutate source after snapshot
        doc2 = vault.import_text("delta epsilon zeta", title="Doc2", source_path="/tmp/doc2.txt")
        assert vault.search("delta")

        # Restored vault should not see doc2
        restored_results = restored.search("delta", limit=3)
        assert restored_results == []
        # Restored still answers for doc1
        restored_alpha = restored.search("alpha", limit=3)
        assert restored_alpha
        assert restored_alpha[0]["doc_id"] == doc1
