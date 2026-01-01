"""Forgetting a fact writes a tombstone and hides it from retrieval."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.vault import Vault


def test_forget_fact_marks_deleted():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Vault(tmpdir)
        fact_id = vault.put_fact("Alice", "knows", "Bob")
        assert vault.list_facts()

        ts_id = vault.forget(fact_id, reason="cleanup")
        assert ts_id is not None
        # list_facts should exclude the deleted fact
        assert vault.list_facts() == []
        # index knows it's deleted
        assert vault.index.is_deleted(fact_id)
