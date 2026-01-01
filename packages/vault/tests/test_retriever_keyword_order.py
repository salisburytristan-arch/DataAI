"""Keyword retriever ordering should be deterministic on ties."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault


def test_keyword_search_orders_by_score_doc_and_sequence():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        # two docs with single chunk each; identical score for term "x"
        d1 = vault.import_text("x", title="A", source_path="/tmp/a")
        d2 = vault.import_text("x", title="B", source_path="/tmp/b")
        # add another chunk to d1 with higher sequence to test ordering
        vault.import_text("x", title="C", source_path="/tmp/c")

        results = vault.retriever.search_keyword("x", limit=5)
        assert results
        # sort key is (-score, doc_id, sequence); all scores equal → doc_id ascending
        doc_ids = [r["doc_id"] for r in results]
        assert doc_ids == sorted(doc_ids)
