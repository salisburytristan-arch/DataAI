"""
Tests for canonicalization and error handling.
"""
from src.canonicalize import canonicalize_string, canonicalize_idempotent_test, is_canonical
from src.frames import Frame
from src.errors import ParseError, ErrorCode


def test_canonicalize_sorts_headers():
    """Headers should be sorted lexicographically."""
    # Create frame with headers in reverse order
    fr = Frame(
        header=[("Z_LAST", "val"), ("A_FIRST", "val"), ("M_MID", "val")],
        payload=["token1", "token2"]
    )
    serialized = fr.serialize()
    canonical = canonicalize_string(serialized)
    # Parse canonical and check header order
    parsed = Frame.parse(canonical)
    keys = [k for k, v in parsed.header]
    assert keys == sorted(keys), f"Headers not sorted: {keys}"
    print("✓ test_canonicalize_sorts_headers")


def test_canonicalize_idempotent():
    """Repeated canonicalization should produce identical results."""
    original = "⧆≛TYPE⦙≛VECTOR∴≛DTYPE⦙≛INT_U3∷≗⊙⊙⊗⦙≗⊙⊙Φ⧈"
    assert canonicalize_idempotent_test(original, iterations=5), "Canonicalization not idempotent"
    print("✓ test_canonicalize_idempotent")


def test_is_canonical():
    """Check if frame is already in canonical form."""
    # Already canonical
    canonical_frame = "⧆≛A⦙≛val∴≛Z⦙≛val∷token1⧈"
    assert is_canonical(canonical_frame), "Should be canonical"
    
    # Not canonical (headers out of order)
    non_canonical = "⧆≛Z⦙≛val∴≛A⦙≛val∷token1⧈"
    assert not is_canonical(non_canonical), "Should not be canonical"
    
    print("✓ test_is_canonical")


def test_parse_error_with_location():
    """ParseError should include location info."""
    bad_frame = "invalid_start_symbol_here"
    try:
        Frame.parse(bad_frame)
        assert False, "Should have raised ParseError"
    except ParseError as e:
        assert e.code == ErrorCode.PARSE_INVALID_FRAME_START
        assert e.location is not None
        assert e.location.line == 1
        assert e.location.column == 1
        assert e.suggestion is not None
        print(f"✓ test_parse_error_with_location: {e}")


def test_parse_error_missing_separator():
    """ParseError for missing header/payload separator."""
    bad_frame = "⧆≛TYPE⦙≛VECTORtoken1⧈"  # Missing ∷
    try:
        Frame.parse(bad_frame)
        assert False, "Should have raised ParseError"
    except ParseError as e:
        assert e.code == ErrorCode.PARSE_MISSING_HEADER_PAYLOAD_SEP
        assert e.suggestion is not None
        print(f"✓ test_parse_error_missing_separator: {e}")


def test_canonicalize_with_whitespace():
    """Canonicalization should trim whitespace from tokens."""
    frame = Frame(
        header=[("TYPE", "VECTOR")],
        payload=["  token1  ", "token2  "]
    )
    serialized = frame.serialize()
    canonical = canonicalize_string(serialized)
    parsed = Frame.parse(canonical)
    assert all(" " not in t for t in parsed.payload), "Tokens should not have leading/trailing spaces"
    print("✓ test_canonicalize_with_whitespace")


if __name__ == "__main__":
    test_canonicalize_sorts_headers()
    test_canonicalize_idempotent()
    test_is_canonical()
    test_parse_error_with_location()
    test_parse_error_missing_separator()
    test_canonicalize_with_whitespace()
    print("\n✓ All canonicalization tests passed")
