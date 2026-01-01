"""VectorIndex persistence and ranking stability."""
import tempfile
from pathlib import Path
import sys

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.index.vectorIndex import VectorIndex


def test_vector_index_persists_and_ranks_by_score():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = VectorIndex(tmpdir)
        idx.index_chunk("c1", "apple apple")
        idx.index_chunk("c2", "apple banana")

        first = idx.search("apple", limit=2)
        assert first[0][0] == "c1"

        # Reload index to ensure persistence
        idx2 = VectorIndex(tmpdir)
        second = idx2.search("apple", limit=2)
        assert second[0][0] == "c1"
        assert first == second
