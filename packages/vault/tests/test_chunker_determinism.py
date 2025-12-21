"""Chunker determinism and boundary behavior."""
import tempfile
from pathlib import Path
import sys

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.ingest.chunker import chunk_by_size


def test_chunk_by_size_is_deterministic_and_respects_overlap():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10

    chunks1 = chunk_by_size(text, chunk_size=120, overlap=20)
    chunks2 = chunk_by_size(text, chunk_size=120, overlap=20)

    assert chunks1 == chunks2
    assert len(chunks1) > 1

    # All chunks must respect chunk_size
    for chunk_text, _, byte_len in chunks1:
        assert byte_len <= 120
        assert len(chunk_text.encode("utf-8")) == byte_len

    # Offsets advance with the expected overlap
    for i in range(len(chunks1) - 1):
        _, offset, byte_len = chunks1[i]
        next_offset = chunks1[i + 1][1]
        expected = offset + byte_len - 20
        assert next_offset == expected or next_offset == offset + byte_len
