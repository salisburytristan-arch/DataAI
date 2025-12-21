"""Hybrid search should be deterministic for the same inputs."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault


def test_hybrid_search_is_stable():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        vault.import_text("alpha beta", title="Doc1", source_path="/tmp/doc1.txt")
        vault.import_text("beta gamma", title="Doc2", source_path="/tmp/doc2.txt")

        r1 = vault.retriever.search_hybrid("beta", limit=5)
        r2 = vault.retriever.search_hybrid("beta", limit=5)
        assert r1 == r2
        assert r1
