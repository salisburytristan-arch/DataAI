import unittest
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.vault.src.vault import Vault
from packages.core.src.agent import Agent

class TestPersistence(unittest.TestCase):
    def test_agent_persist_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            vault.import_text("Cats are animals. They purr.", title="Cats", source_path=str(Path(tmpdir)/"cats.txt"))

            agent = Agent(vault)
            res = agent.respond("cats", evidence_limit=2, persist=True, convo_id="test-convo")
            self.assertIn("persist", res)

            # Verify summary stored
            summaries = vault.list_summaries()
            self.assertTrue(len(summaries) >= 1)
            self.assertEqual(summaries[-1].convo_id, "test-convo")
            self.assertTrue("You asked:" in summaries[-1].summary_text)

if __name__ == "__main__":
    unittest.main()
