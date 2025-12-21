"""Snapshot/restore preserves basic stats."""
import shutil
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault


def test_snapshot_restore_preserves_stats():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dst_dir:
        vault = Vault(src_dir)
        vault.import_text("alpha beta gamma delta", title="Doc", source_path="/tmp/doc.txt")
        before_stats = vault.stats()

        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        restored = Vault(dst_dir)
        after_stats = restored.stats()

        assert before_stats["doc_count"] == after_stats["doc_count"]
        assert before_stats["chunk_count"] == after_stats["chunk_count"]
        assert before_stats.get("fact_count", 0) == after_stats.get("fact_count", 0)
