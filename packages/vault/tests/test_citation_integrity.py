"""Citation integrity should surface object hashes and detect corruption."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault


def test_citation_includes_object_hash_and_verifies():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        vault.import_text("alpha beta gamma", title="Doc", source_path="/tmp/doc.txt")

        pack = vault.retriever.get_evidence_pack("beta", limit=1)
        cite = pack["citations"][0]
        assert cite["object_hash"]
        assert cite["object_verified"] is True


def test_citation_flags_corrupted_object():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        vault.import_text("alpha beta gamma", title="Doc", source_path="/tmp/doc.txt")
        pack = vault.retriever.get_evidence_pack("beta", limit=1)
        cite = pack["citations"][0]
        obj_path = vault.objects._get_object_path(cite["object_hash"])
        obj_path.write_text("corrupt", encoding="utf-8")

        pack2 = vault.retriever.get_evidence_pack("beta", limit=1)
        cite2 = pack2["citations"][0]
        assert cite2["object_hash"] == cite["object_hash"]
        assert cite2["object_verified"] is False
