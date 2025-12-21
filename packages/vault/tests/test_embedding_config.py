import unittest
import tempfile
from pathlib import Path
import json
import sys

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault

class TestEmbeddingConfig(unittest.TestCase):
    def test_disable_embeddings_via_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            idx_dir = Path(tmpdir) / "index"
            idx_dir.mkdir(parents=True, exist_ok=True)
            cfg = {"enabled": False, "model_name": "sentence-transformers/all-MiniLM-L6-v2"}
            with open(idx_dir / "embeddings_config.json", 'w', encoding='utf-8') as f:
                json.dump(cfg, f)
            v = Vault(tmpdir)
            # Should be disabled
            self.assertTrue(hasattr(v, 'embeddings'))
            self.assertFalse(v.embeddings.enabled)
            self.assertFalse(v.embeddings.available)
            # Ingest and hybrid search should still work via fallback
            v.import_text("Cats and dogs.", title="X", source_path=str(Path(tmpdir)/"x.txt"))
            res = v.retriever.search_hybrid("dogs", limit=5)
            self.assertTrue(len(res) >= 1)

    def test_env_override_disable(self):
        import os
        os.environ["ACX_EMBEDDINGS"] = "0"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                v = Vault(tmpdir)
                self.assertFalse(v.embeddings.enabled)
                self.assertFalse(v.embeddings.available)
                v.import_text("Hello embeddings.", title="Y", source_path=str(Path(tmpdir)/"y.txt"))
                res = v.retriever.search_hybrid("embeddings", limit=5)
                self.assertTrue(len(res) >= 1)
        finally:
            del os.environ["ACX_EMBEDDINGS"]

if __name__ == "__main__":
    unittest.main()
