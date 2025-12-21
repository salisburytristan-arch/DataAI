import unittest
import tempfile
from pathlib import Path
import sys

# Ensure workspace root is on sys.path to import sibling packages
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.vault.src.vault import Vault
from packages.core.src.agent import Agent


class TestAgent(unittest.TestCase):
    def test_agent_responds_with_citations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            doc_text = "The quick brown fox jumps over the lazy dog. Foxes are agile animals."
            vault.import_text(doc_text, title="Animals", source_path=str(Path(tmpdir) / "animals.txt"))

            agent = Agent(vault)
            result = agent.respond("fox", evidence_limit=3)

            self.assertIn("You asked:", result["text"])  # echo
            self.assertTrue(len(result["citations"]) >= 1)
            self.assertTrue(any("chunk_id" in c for c in result["citations"]))
            self.assertTrue(len(result["used_chunks"]) >= 1)


if __name__ == "__main__":
    unittest.main()
