import unittest
import tempfile
from pathlib import Path
import sys

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault

class TestHybridSearch(unittest.TestCase):
    def test_hybrid_search_returns_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            v = Vault(tmpdir)
            v.import_text("The quick brown fox jumps over the lazy dog.", title="Doc1", source_path=str(Path(tmpdir)/"d1.txt"))
            v.import_text("Foxes are agile animals and canines.", title="Doc2", source_path=str(Path(tmpdir)/"d2.txt"))

            res = v.retriever.search_hybrid("fox canine", limit=5)
            self.assertTrue(len(res) >= 1)
            # Top result should be one of the fox/canine chunks
            self.assertTrue(any("fox" in r["content"].lower() or "canine" in r["content"].lower() for r in res))

if __name__ == "__main__":
    unittest.main()
