"""
Tests for advanced schemas (Part 10)
"""

from src.schemas import (
    build_vector_frame, parse_vector_frame,
    build_matrix_frame, parse_matrix_frame,
    build_log_frame, parse_log_frame,
    build_fact_frame, parse_fact_frame
)
from src.numeric import encode_int_u3


def test_vector_frame_basic():
    """Test basic VECTOR frame building and parsing."""
    values = [
        encode_int_u3(1),
        encode_int_u3(2),
        encode_int_u3(3),
    ]
    
    frame = build_vector_frame(values)
    
    # Verify serialization
    serialized = frame.serialize()
    assert "⧆" in serialized
    assert "⧈" in serialized
    assert "VECTOR" in serialized
    
    # Parse back
    parsed = parse_vector_frame(frame)
    assert len(parsed) == 3
    assert parsed == values


def test_vector_frame_empty():
    """Test empty VECTOR frame."""
    frame = build_vector_frame([])
    parsed = parse_vector_frame(frame)
    assert parsed == []


def test_matrix_frame_basic():
    """Test basic MATRIX frame building and parsing."""
    rows = [
        [encode_int_u3(1), encode_int_u3(2)],
        [encode_int_u3(3), encode_int_u3(4)],
        [encode_int_u3(5), encode_int_u3(6)],
    ]
    
    frame = build_matrix_frame(rows)
    
    # Verify serialization
    serialized = frame.serialize()
    assert "MATRIX" in serialized
    assert "ROWS" in serialized
    assert "COLS" in serialized
    
    # Parse back
    parsed = parse_matrix_frame(frame)
    assert len(parsed) == 3
    assert len(parsed[0]) == 2
    assert parsed == rows


def test_matrix_frame_square():
    """Test square MATRIX."""
    rows = [
        [encode_int_u3(1), encode_int_u3(2), encode_int_u3(3)],
        [encode_int_u3(4), encode_int_u3(5), encode_int_u3(6)],
        [encode_int_u3(7), encode_int_u3(8), encode_int_u3(9)],
    ]
    
    frame = build_matrix_frame(rows)
    parsed = parse_matrix_frame(frame)
    assert len(parsed) == 3
    assert all(len(row) == 3 for row in parsed)


def test_matrix_frame_invalid_shape():
    """Test that inconsistent column counts raise error."""
    rows = [
        [encode_int_u3(1), encode_int_u3(2)],
        [encode_int_u3(3)],  # Wrong column count
    ]
    
    try:
        frame = build_matrix_frame(rows)
        assert False, "Should raise ValueError for inconsistent columns"
    except ValueError:
        pass  # Expected


def test_log_frame_basic():
    """Test basic LOG frame."""
    frame = build_log_frame(
        severity="INFO",
        message="≛System_started"
    )
    
    serialized = frame.serialize()
    assert "LOG" in serialized
    assert "INFO" in serialized
    assert "System_started" in serialized
    
    parsed = parse_log_frame(frame)
    assert parsed["severity"] == "INFO"
    assert "System_started" in parsed["message"]


def test_log_frame_with_details():
    """Test LOG frame with timestamp and details."""
    timestamp = encode_int_u3(1732896000)
    
    frame = build_log_frame(
        severity="ERROR",
        message="≛Connection_failed",
        timestamp=timestamp,
        details="≛⟦Timeout after 30s⟧"
    )
    
    parsed = parse_log_frame(frame)
    assert parsed["severity"] == "ERROR"
    assert "Connection_failed" in parsed["message"]
    assert parsed["time"] == timestamp
    assert "30s" in parsed["detail"]


def test_fact_frame_basic():
    """Test basic FACT frame (knowledge triple)."""
    frame = build_fact_frame(
        subject="≛Einstein",
        predicate="≛born_in",
        obj="≛Ulm"
    )
    
    serialized = frame.serialize()
    assert "FACT" in serialized
    assert "Einstein" in serialized
    assert "born_in" in serialized
    assert "Ulm" in serialized
    
    parsed = parse_fact_frame(frame)
    assert "Einstein" in parsed["subject"]
    assert "born_in" in parsed["predicate"]
    assert "Ulm" in parsed["object"]


def test_fact_frame_with_metadata():
    """Test FACT frame with confidence and source."""
    from src.numeric import encode_decimal_t
    
    confidence = encode_decimal_t(True, 2, 95)  # 0.95
    
    frame = build_fact_frame(
        subject="≛Einstein",
        predicate="≛born_in",
        obj="≛Ulm",
        confidence=confidence,
        source="≛Wikipedia"
    )
    
    parsed = parse_fact_frame(frame)
    assert parsed["confidence"] == confidence
    assert "Wikipedia" in parsed["source"]


def test_vector_round_trip():
    """Test complete encode→frame→parse→decode cycle for VECTOR."""
    from src.numeric import decode_int_u3
    
    # Original values
    original = [42, 13, 7]
    
    # Encode
    encoded = [encode_int_u3(v) for v in original]
    
    # Build frame
    frame = build_vector_frame(encoded)
    
    # Serialize and parse
    serialized = frame.serialize()
    from src.frames import Frame
    reparsed_frame = Frame.parse(serialized)
    
    # Extract values
    parsed_tokens = parse_vector_frame(reparsed_frame)
    
    # Decode
    decoded = [decode_int_u3(t) for t in parsed_tokens]
    
    assert decoded == original


def test_matrix_round_trip():
    """Test complete encode→frame→parse→decode cycle for MATRIX."""
    from src.numeric import decode_int_u3
    
    # Original 2x3 matrix
    original = [
        [1, 2, 3],
        [4, 5, 6],
    ]
    
    # Encode
    encoded = [[encode_int_u3(v) for v in row] for row in original]
    
    # Build frame
    frame = build_matrix_frame(encoded)
    
    # Serialize and reparse
    serialized = frame.serialize()
    from src.frames import Frame
    reparsed_frame = Frame.parse(serialized)
    
    # Extract and decode
    parsed_tokens = parse_matrix_frame(reparsed_frame)
    decoded = [[decode_int_u3(t) for t in row] for row in parsed_tokens]
    
    assert decoded == original


if __name__ == "__main__":
    # Run tests
    test_vector_frame_basic()
    print("✓ test_vector_frame_basic")
    
    test_vector_frame_empty()
    print("✓ test_vector_frame_empty")
    
    test_matrix_frame_basic()
    print("✓ test_matrix_frame_basic")
    
    test_matrix_frame_square()
    print("✓ test_matrix_frame_square")
    
    test_matrix_frame_invalid_shape()
    print("✓ test_matrix_frame_invalid_shape")
    
    test_log_frame_basic()
    print("✓ test_log_frame_basic")
    
    test_log_frame_with_details()
    print("✓ test_log_frame_with_details")
    
    test_fact_frame_basic()
    print("✓ test_fact_frame_basic")
    
    test_fact_frame_with_metadata()
    print("✓ test_fact_frame_with_metadata")
    
    test_vector_round_trip()
    print("✓ test_vector_round_trip")
    
    test_matrix_round_trip()
    print("✓ test_matrix_round_trip")
    
    print("\nAll schema tests passed!")
