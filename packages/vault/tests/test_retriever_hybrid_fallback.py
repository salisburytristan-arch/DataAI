"""Hybrid retrieval should fall back to vector search when embeddings are unavailable."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault


def test_hybrid_search_falls_back_to_vector():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        doc1 = vault.import_text("alpha beta gamma", title="Doc1", source_path="/tmp/doc1.txt")
        doc2 = vault.import_text("beta beta delta", title="Doc2", source_path="/tmp/doc2.txt")

        results = vault.retriever.search_hybrid("beta", limit=3)
        assert results
        top = results[0]
        assert top["doc_id"] in {doc1, doc2}
        # doc with higher beta frequency should rank first
        assert top["doc_id"] == doc2
        assert top.get("hybrid_score", 0) > 0
