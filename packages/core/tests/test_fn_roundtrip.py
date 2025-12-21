import unittest
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.vault.src.vault import Vault
from packages.core.src.agent import Agent
from packages.core.src.fn_bridge import export_conversation_fn, to_fn_train_pair

class TestFNRoundtrip(unittest.TestCase):
    def test_fn_import_export_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            vault.import_text("Fox is a canine.", title="Zoo", source_path=str(Path(tmpdir)/"zoo.txt"))
            agent = Agent(vault)
            res = agent.respond("fox", persist=True, convo_id="convo-rt")

            # Export to FN
            frames = export_conversation_fn(vault, "convo-rt")
            self.assertGreaterEqual(len(frames), 1)

            # Create a new vault and import frames
            vault2 = Vault(str(Path(tmpdir)/"vault2"))
            for frame in frames:
                vault2.import_fn_frame(frame)

            # Verify records exist
            summaries2 = vault2.list_summaries()
            facts2 = vault2.list_facts()
            self.assertGreaterEqual(len(summaries2), 1)
            self.assertEqual(summaries2[0].convo_id, "convo-rt")

    def test_train_pair_export(self):
        instr = "Explain what a fox is."
        comp = "A fox is a canine mammal known for agility."
        frame = to_fn_train_pair(instr, comp, metadata={"source": "test"})
        self.assertIn("TRAIN_PAIR", frame)
        self.assertIn("SOURCE", frame)

if __name__ == "__main__":
    unittest.main()
