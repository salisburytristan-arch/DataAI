"""Vault tombstone and deletion behaviors."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault
from packages.vault.src.types import RecordType


def test_forget_cascades_doc_and_chunks_and_persists():
    """Deleting a document writes tombstones for doc and chunks and survives reload."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        text = "A" * 1500 + "B" * 1500  # ensure multiple chunks
        doc_id = vault.import_text(text, title="Doc", source_path="/tmp/doc.txt")
        chunk_ids = [c.chunk_id for c in vault.get_chunks_for_doc(doc_id)]
        assert len(chunk_ids) >= 2

        ts_id = vault.forget(doc_id, reason="cleanup")
        assert ts_id is not None
        assert vault.index.is_deleted(doc_id)
        for cid in chunk_ids:
            assert vault.index.is_deleted(cid)

        assert len(vault.index.tombstones) == len(chunk_ids) + 1
        doc_ts = [t for t in vault.index.tombstones.values() if t["target_type"] == RecordType.DOC]
        assert len(doc_ts) == 1

        # Reload to ensure tombstones restore deleted IDs
        vault_reloaded = Vault(tmpdir)
        assert vault_reloaded.index.is_deleted(doc_id)
        assert vault_reloaded.get_doc(doc_id) is None
        for cid in chunk_ids:
            assert vault_reloaded.get_chunk(cid) is None


def test_forget_chunk_only_removes_that_chunk():
    """Chunk-only deletion should not delete the parent document."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        doc_id = vault.import_text("short text", title="Doc", source_path="/tmp/doc.txt")
        chunk_id = vault.get_chunks_for_doc(doc_id)[0].chunk_id

        ts_id = vault.forget(chunk_id, reason="drop chunk")
        assert ts_id is not None
        assert not vault.index.is_deleted(doc_id)
        assert vault.index.is_deleted(chunk_id)

        assert vault.get_doc(doc_id) is not None
        assert vault.get_chunk(chunk_id) is None
        assert vault.get_chunks_for_doc(doc_id) == []

        stats = vault.stats()
        assert stats["doc_count"] == 1
        assert stats["chunk_count"] == 0


def test_forget_unknown_returns_none_and_writes_no_tombstone():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        result = vault.forget("missing-id", reason="nothing")
        assert result is None
        assert vault.index.tombstones == {}
