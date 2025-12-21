import unittest
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.vault.src.vault import Vault
from packages.core.src.agent import Agent
from packages.core.src.export import export_conversation

class TestExport(unittest.TestCase):
    def test_export_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            vault.import_text("Fox is a canine. Cats are animals.", title="Zoo", source_path=str(Path(tmpdir)/"zoo.txt"))
            agent = Agent(vault)
            res = agent.respond("fox", persist=True, convo_id="convo-1")
            out = Path(tmpdir)/"out.jsonl"
            stats = export_conversation(vault, "convo-1", str(out))
            self.assertGreaterEqual(stats["summaries"], 1)
            self.assertGreaterEqual(stats["facts"], 1)
            # Verify file has at least two lines
            with open(out, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self.assertGreaterEqual(len(lines), 2)

if __name__ == "__main__":
    unittest.main()
