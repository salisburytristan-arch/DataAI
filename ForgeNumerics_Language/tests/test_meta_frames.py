"""
Tests for Meta-Frames and Advanced Features
"""

from src.meta_frames import (
    build_grammar_frame,
    build_schema_frame,
    build_explain_frame,
    build_task_frame,
    build_caps_frame,
    build_error_frame,
    build_tensor_frame,
    build_dict_update_enhanced,
    build_train_pair_frame,
    build_dict_policy_frame
)
from src.numeric import encode_int_u3, encode_float_t
from pathlib import Path


def test_grammar_frame():
    """Test GRAMMAR frame with EBNF content."""
    grammar = "TRIT = '⊙' | '⊗' | 'Φ' ;"
    frame = build_grammar_frame(grammar, version="2.0")
    
    serialized = frame.serialize()
    assert "GRAMMAR" in serialized
    assert grammar in serialized
    print("✓ test_grammar_frame")


def test_schema_frame():
    """Test SCHEMA frame for MEASUREMENT type."""
    fields = [
        {"name": "VALUE", "profile": "FLOAT_T64", "required": "TRUE", 
         "description": "Measured value"},
        {"name": "ERROR", "profile": "FLOAT_T64", "required": "FALSE"},
        {"name": "TIME", "profile": "INT_U3", "required": "FALSE"}
    ]
    
    frame = build_schema_frame(
        "MEASUREMENT",
        fields,
        description="Schema for scientific measurements"
    )
    
    serialized = frame.serialize()
    assert "SCHEMA" in serialized
    assert "MEASUREMENT" in serialized
    assert "VALUE" in serialized
    assert "FLOAT_T64" in serialized
    print("✓ test_schema_frame")


def test_explain_frame():
    """Test EXPLAIN frame for debugging."""
    frame = build_explain_frame(
        target_id="frame_123",
        summary="This frame stores a 2×3 matrix of FLOAT-T values",
        details=[
            "Field VALUE uses DECIMAL-T because exact precision is required",
            "Matrix is stored in row-major order"
        ]
    )
    
    serialized = frame.serialize()
    assert "EXPLAIN" in serialized
    assert "frame_123" in serialized
    assert "2×3 matrix" in serialized
    print("✓ test_explain_frame")


def test_task_frame():
    """Test TASK frame for training."""
    frame = build_task_frame(
        task_type="ENCODE_INT",
        instruction="Encode the integer 42 as INT-U3",
        input_data="42",
        expected_output="≗⊙⊙⊗⊗Φ⊙",
        difficulty="BASIC"
    )
    
    serialized = frame.serialize()
    assert "TASK" in serialized
    assert "ENCODE_INT" in serialized
    assert "42" in serialized
    assert "BASIC" in serialized
    print("✓ test_task_frame")


def test_caps_frame():
    """Test CAPS frame for capability negotiation."""
    supports = {
        "FLOAT_T": "YES",
        "DECIMAL_T": "YES",
        "ENC_AES_GCM": "NO"
    }
    
    limits = {
        "MAX_TENSOR_SIZE": encode_int_u3(1000000)
    }
    
    frame = build_caps_frame(supports, limits)
    
    serialized = frame.serialize()
    assert "CAPS" in serialized
    assert "SUPPORTS_FLOAT_T" in serialized
    assert "YES" in serialized
    assert "NO" in serialized
    print("✓ test_caps_frame")


def test_error_frame():
    """Test ERROR frame for diagnostics."""
    frame = build_error_frame(
        error_type="PARSE_ERROR",
        location="token 23 in payload",
        code="MISSING_FRAME_END",
        detail="Expected ⧈, found ⊙ instead",
        suggestion="Add closing frame marker ⧈"
    )
    
    serialized = frame.serialize()
    assert "PARSE_ERROR" in serialized
    assert "MISSING_FRAME_END" in serialized
    assert "token 23" in serialized
    print("✓ test_error_frame")


def test_tensor_frame():
    """Test TENSOR frame for ML data."""
    # Create a 2x3 tensor of small integers
    shape = [2, 3]
    data = [encode_int_u3(i) for i in [1, 2, 3, 4, 5, 6]]
    
    frame = build_tensor_frame(
        dtype="INT_U3",
        shape=shape,
        data_tokens=data,
        order="ROW_MAJOR"
    )
    
    serialized = frame.serialize()
    assert "TENSOR" in serialized
    assert "INT_U3" in serialized
    assert "ROW_MAJOR" in serialized
    assert "SHAPE" in serialized
    print("✓ test_tensor_frame")


def test_dict_update_enhanced():
    """Test enhanced DICT_UPDATE with stats."""
    pairs = [
        ("megafauna", "Ωζ"),
        ("hypernode", "Ψχ")
    ]
    
    stats = [
        {"freq": 42, "source": "WIKIPEDIA"},
        {"freq": 15, "source": "ARXIV"}
    ]
    
    frame = build_dict_update_enhanced(
        "EXTDICT_TEST_0001",
        pairs,
        stats
    )
    
    serialized = frame.serialize()
    assert "DICT_UPDATE" in serialized
    assert "megafauna" in serialized
    assert "FREQ" in serialized
    assert "WIKIPEDIA" in serialized
    print("✓ test_dict_update_enhanced")


def test_train_pair_frame():
    """Test parallel NL ↔ ForgeNumerics training pair."""
    frame = build_train_pair_frame(
        natural_language="The sensor is 3.2 meters from the wall",
        forgenumerics_frame="⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛meter∷≛VALUE⦙≗⊗⊗...⧈"
    )
    
    serialized = frame.serialize()
    assert "TRAIN_PAIR" in serialized
    assert "sensor" in serialized
    assert "3.2 meters" in serialized
    print("✓ test_train_pair_frame")


def test_dict_policy_frame():
    """Test DICT_POLICY frame."""
    frame = build_dict_policy_frame(
        min_frequency=10,
        allowed_domains=["TRAINING", "LOGS", "KB"],
        max_growth_per_day=1000
    )
    
    serialized = frame.serialize()
    assert "DICT_POLICY" in serialized
    assert "MIN_FREQ" in serialized
    assert "TRAINING" in serialized
    assert "LOGS" in serialized
    print("✓ test_dict_policy_frame")


def test_grammar_frame_self_describing():
    """Test that the grammar can be stored as a ForgeNumerics frame."""
    # Load actual EBNF grammar
    grammar_path = Path("ForgeNumerics_Grammar.ebnf")
    if grammar_path.exists():
        with open(grammar_path, 'r', encoding='utf-8') as f:
            grammar_content = f.read()
        
        frame = build_grammar_frame(grammar_content)
        serialized = frame.serialize()
        
        # Verify it's a valid frame
        assert serialized.startswith("⧆")
        assert serialized.endswith("⧈")
        assert "GRAMMAR" in serialized
        print("✓ test_grammar_frame_self_describing")
    else:
        print("⊗ test_grammar_frame_self_describing (grammar file not found)")


if __name__ == "__main__":
    print("=== Meta-Frame Tests ===\n")
    
    test_grammar_frame()
    test_schema_frame()
    test_explain_frame()
    test_task_frame()
    test_caps_frame()
    test_error_frame()
    test_tensor_frame()
    test_dict_update_enhanced()
    test_train_pair_frame()
    test_dict_policy_frame()
    test_grammar_frame_self_describing()
    
    print("\nAll meta-frame tests passed!")
