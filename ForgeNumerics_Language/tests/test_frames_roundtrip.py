import pytest
from src.frames import Frame, bytes_to_trits, trits_to_bytes, FRAME_START


def test_frame_roundtrip():
    f = Frame(header=[("TYPE", "ANSWER"), ("CITATIONS", "1,2")], payload=["≛NATLANG", "≛⟦hello⟧"])
    s = f.serialize()
    parsed = Frame.parse(s)
    assert parsed.header == f.header
    assert parsed.payload == f.payload


def test_frame_parse_missing_start_raises():
    bad = "not_a_frame"
    with pytest.raises(Exception):
        Frame.parse(bad)


def test_trits_bytes_roundtrip():
    data = b"hello world"
    trits = bytes_to_trits(data)
    out = trits_to_bytes(trits)
    assert out == data