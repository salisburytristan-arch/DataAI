import unittest
import tempfile
from pathlib import Path
import sys

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault

class TestEmbeddingIndex(unittest.TestCase):
    def test_embeddings_graceful_unavailable(self):
        # On machines without sentence-transformers, EmbeddingIndex should not break ingestion
        with tempfile.TemporaryDirectory() as tmpdir:
            v = Vault(tmpdir)
            # Embeddings may be unavailable; ensure property exists
            self.assertTrue(hasattr(v, 'embeddings'))
            # Import a simple document
            v.import_text("Hello world", title="T1", source_path=str(Path(tmpdir)/"t1.txt"))
            # Searching via hybrid should still return something with keyword fallback
            res = v.retriever.search_hybrid("Hello", limit=5)
            self.assertTrue(len(res) >= 1)
            self.assertTrue(any("hello" in r["content"].lower() for r in res))

    def test_hybrid_fallback_without_embeddings(self):
        # Regardless of embeddings availability, hybrid search should produce results for matching content
        with tempfile.TemporaryDirectory() as tmpdir:
            v = Vault(tmpdir)
            v.import_text("The quick brown fox.", title="D1", source_path=str(Path(tmpdir)/"d1.txt"))
            v.import_text("Foxes are canines.", title="D2", source_path=str(Path(tmpdir)/"d2.txt"))
            res = v.retriever.search_hybrid("fox canine", limit=5)
            self.assertTrue(len(res) >= 1)
            # result structure includes hybrid_score
            self.assertTrue(all("hybrid_score" in r for r in res))

if __name__ == "__main__":
    unittest.main()
