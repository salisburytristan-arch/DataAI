"""Vault integrity scan should detect corrupted objects."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault


def test_vault_verify_integrity_flags_corruption():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        vault.import_text("alpha beta gamma", title="Doc", source_path="/tmp/doc.txt")

        # corrupt a stored object
        obj_hash = vault.objects.list_objects()[0]
        obj_path = vault.objects._get_object_path(obj_hash)
        obj_path.write_text("corrupt", encoding="utf-8")

        result = vault.verify_integrity()
        assert result["objects_failed"] == 1
        assert result["errors"]
