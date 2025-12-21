"""MetadataIndex persistence and tombstone restoration."""
import sys
import tempfile
from datetime import datetime
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.storage.metadataIndex import MetadataIndex
from src.types import DocRecord, ChunkRecord, TombstoneRecord, RecordType


def test_metadata_index_persists_and_restores_tombstones():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = MetadataIndex(tmpdir)
        now = datetime.now()
        doc = DocRecord(
            doc_id="doc1",
            title="Doc",
            source_path="/tmp/doc.txt",
            doc_type="text",
            created_at=now,
            updated_at=now,
            chunk_count=1,
            total_bytes=10,
        )
        chunk = ChunkRecord(
            chunk_id="chunk1",
            doc_id="doc1",
            sequence=0,
            content="hello",
            content_hash="hash1",
            byte_offset=0,
            byte_length=5,
            created_at=now,
        )

        idx.put_doc(doc)
        idx.put_chunk(chunk)
        assert idx.get_doc("doc1") is not None
        assert idx.get_chunk("chunk1") is not None

        ts = TombstoneRecord(
            tombstone_id="ts1",
            target_id="doc1",
            target_type=RecordType.DOC,
            reason="delete",
        )
        idx.put_tombstone(ts)
        assert idx.is_deleted("doc1")
        assert idx.get_doc("doc1") is None
        # Chunks should still exist until explicitly tombstoned
        assert idx.get_chunk("chunk1") is not None

        # Reload from disk; tombstone should rebuild deleted set
        idx2 = MetadataIndex(tmpdir)
        assert idx2.is_deleted("doc1")
        assert idx2.get_doc("doc1") is None
        # Chunk still exists (doc deletion doesn't cascade in index)
        assert idx2.get_chunk("chunk1") is not None
