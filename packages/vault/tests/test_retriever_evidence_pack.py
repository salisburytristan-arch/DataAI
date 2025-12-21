"""Retriever evidence pack should include citations with offsets."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault


def test_evidence_pack_includes_citations_and_offsets():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        doc_id = vault.import_text("alpha beta gamma", title="Doc", source_path="/tmp/doc.txt")

        pack = vault.retriever.get_evidence_pack("beta", limit=3)
        assert pack["chunk_count"] == len(pack["chunks"]) == len(pack["citations"])
        assert pack["chunks"]

        for chunk, cite in zip(pack["chunks"], pack["citations"]):
            assert chunk["chunk_id"] == cite["chunk_id"]
            assert chunk["doc_id"] == cite["doc_id"] == doc_id
            assert cite["offset"] == 0
            assert "doc_title" in cite
            assert cite["relevance_score"] > 0
