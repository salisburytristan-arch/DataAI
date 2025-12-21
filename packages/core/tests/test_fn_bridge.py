import unittest
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.vault.src.vault import Vault
from packages.core.src.agent import Agent
from packages.core.src.fn_bridge import export_conversation_fn
from ForgeNumerics_Language.src.canonicalize import is_canonical
from ForgeNumerics_Language.src.frames import Frame

class TestFNBridge(unittest.TestCase):
    def test_export_fn_is_canonical_and_parsable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Vault(tmpdir)
            vault.import_text("Fox is a canine.", title="Zoo", source_path=str(Path(tmpdir)/"zoo.txt"))
            agent = Agent(vault)
            res = agent.respond("fox", persist=True, convo_id="convo-x")

            frames = export_conversation_fn(vault, "convo-x")
            self.assertGreaterEqual(len(frames), 1)
            for s in frames:
                self.assertTrue(is_canonical(s))
                fr = Frame.parse(s)
                # Basic header token check
                self.assertTrue(any(k == "TYPE" for k, _ in fr.header))

if __name__ == "__main__":
    unittest.main()
