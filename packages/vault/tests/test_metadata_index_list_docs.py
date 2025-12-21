"""MetadataIndex should not list deleted docs."""
import sys
import tempfile
from datetime import datetime
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.storage.metadataIndex import MetadataIndex
from src.types import DocRecord, TombstoneRecord, RecordType


def test_list_docs_excludes_deleted():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = MetadataIndex(tmpdir)
        now = datetime.now()
        d1 = DocRecord(
            doc_id="d1",
            title="Doc1",
            source_path="/tmp/1",
            doc_type="text",
            created_at=now,
            updated_at=now,
            chunk_count=0,
            total_bytes=1,
        )
        idx.put_doc(d1)
        assert len(idx.list_docs()) == 1

        ts = TombstoneRecord(
            tombstone_id="ts",
            target_id="d1",
            target_type=RecordType.DOC,
            reason="del",
        )
        idx.put_tombstone(ts)
        assert idx.is_deleted("d1")
        assert idx.list_docs() == []
