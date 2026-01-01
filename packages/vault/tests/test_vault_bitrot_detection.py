"""Bit-rot style corruption should be detected by integrity scan."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault


def test_bitrot_corruption_detected():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        vault.import_text("alpha beta gamma", title="Doc", source_path="/tmp/doc.txt")
        obj_hash = vault.objects.list_objects()[0]
        obj_path = vault.objects._get_object_path(obj_hash)

        # Flip a byte to simulate bit-rot
        data = obj_path.read_bytes()
        flipped = bytes([data[0] ^ 0xFF]) + data[1:]
        obj_path.write_bytes(flipped)

        result = vault.verify_integrity()
        assert result["objects_failed"] == 1
        assert obj_hash in "".join(result["errors"])
