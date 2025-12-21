"""EmbeddingIndex should disable cleanly via env flag."""
import os
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.index.embeddingIndex import EmbeddingIndex


def test_embedding_index_disabled_by_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["ACX_EMBEDDINGS"] = "0"
        idx = EmbeddingIndex(tmpdir)
        assert not idx.available
        assert idx.search("anything") == []
        # Indexing should be a no-op, not an error
        idx.index_chunk("cid", "text")
        assert idx.embeddings == {}
    os.environ.pop("ACX_EMBEDDINGS", None)
