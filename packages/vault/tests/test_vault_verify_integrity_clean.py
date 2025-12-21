"""Vault verify_integrity should pass on clean store."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault


def test_verify_integrity_clean():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        vault.import_text("alpha beta gamma", title="Doc", source_path="/tmp/doc.txt")

        result = vault.verify_integrity()
        assert result["objects_failed"] == 0
        assert result["objects_verified"] == len(vault.objects.list_objects())
        assert result["errors"] == []
