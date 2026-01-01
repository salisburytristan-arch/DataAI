"""Chunking by paragraphs respects size limits and determinism."""
import sys
import tempfile
from pathlib import Path

vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from packages.vault.src.ingest.chunker import chunk_by_paragraphs


def test_chunk_by_paragraphs_respects_bounds_and_is_repeatable():
    text = "para1" + "\n\n" + "para2 longer" + "\n\n" + "para3 even longer content"

    chunks1 = chunk_by_paragraphs(text, min_size=5, max_size=30)
    chunks2 = chunk_by_paragraphs(text, min_size=5, max_size=30)

    assert chunks1 == chunks2
    assert len(chunks1) >= 2

    # Byte lengths should not exceed max_size
    for chunk_text, offset, byte_len in chunks1:
        assert byte_len <= 30
        assert len(chunk_text.encode("utf-8")) == byte_len
        assert offset >= 0

    # Offsets should be non-decreasing
    offsets = [c[1] for c in chunks1]
    assert offsets == sorted(offsets)
