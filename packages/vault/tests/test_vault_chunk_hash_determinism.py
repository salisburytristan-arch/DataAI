"""Chunk hash should be deterministic and match content SHA256."""
import hashlib
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault


def test_chunk_hash_matches_content_sha256():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        doc_id = vault.import_text("hello world this is deterministic", title="Doc", source_path="/tmp/doc.txt")
        chunk = vault.get_chunks_for_doc(doc_id)[0]

        expected = hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()
        assert chunk.chunk_id == expected
