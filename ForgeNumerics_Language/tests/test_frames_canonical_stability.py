from src.frames import Frame


def test_canonical_serialization_stable_order():
    f = Frame(header=[("B", "2"), ("A", "1")], payload=["x", "y"])
    s1 = f.serialize()
    s2 = f.serialize()
    assert s1 == s2