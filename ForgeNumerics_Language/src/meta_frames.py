"""
Advanced Meta-Frames for ForgeNumerics-S

Implements:
- GRAMMAR frames (machine-readable grammar)
- SCHEMA frames (self-describing data schemas)
- EXPLAIN frames (introspection and debugging)
- TASK frames (training curriculum)
- CAPS frames (capability negotiation)
- ERROR frames (validation and recovery)
- TENSOR frames (ML-friendly data)
- Enhanced DICT_UPDATE with stats
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from src.frames import Frame
from src.numeric import encode_int_u3
from src.data_loader import DataLoader


def build_grammar_frame(grammar_content: str, version: str = "2.0") -> Frame:
    """
    Build a GRAMMAR frame containing EBNF grammar definition.
    
    Args:
        grammar_content: EBNF grammar text
        version: Grammar version
        
    Returns:
        Frame with TYPE=GRAMMAR
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", "GRAMMAR"),
        ("DICT", dict_version),
        ("VERSION", version),
        ("FORMAT", "EBNF")
    ]
    
    # Grammar content as literal
    payload = [f"≛CONTENT⦙≛⟦{grammar_content}⟧"]
    
    return Frame(header, payload)


def build_schema_frame(
    target_type: str,
    fields: List[Dict[str, str]],
    description: Optional[str] = None
) -> Frame:
    """
    Build a SCHEMA frame describing the structure of another frame type.
    
    Args:
        target_type: The TYPE this schema describes (e.g., "MEASUREMENT")
        fields: List of field definitions, each with:
            - name: field name
            - profile: numeric profile or "WORD"
            - required: "TRUE" or "FALSE"
            - description (optional)
        description: Optional schema description
        
    Returns:
        Frame with TYPE=SCHEMA
    
    Example:
        fields = [
            {"name": "VALUE", "profile": "FLOAT_T64", "required": "TRUE"},
            {"name": "ERROR", "profile": "FLOAT_T64", "required": "FALSE"},
            {"name": "TIME", "profile": "INT_U3", "required": "FALSE"}
        ]
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", "SCHEMA"),
        ("DICT", dict_version),
        ("TARGET_TYPE", target_type)
    ]
    
    if description:
        header.append(("DESC", f"≛⟦{description}⟧"))
    
    # Build payload: list of field definitions
    payload = []
    for field in fields:
        payload.extend([
            "≛FIELD",
            f"≛{field['name']}",
            "≛PROFILE",
            f"≛{field['profile']}",
            "≛REQUIRED" if field.get("required", "FALSE") == "TRUE" else "≛OPTIONAL"
        ])
        if "description" in field:
            payload.extend(["≛DESC", f"≛⟦{field['description']}⟧"])
    
    return Frame(header, payload)


def build_explain_frame(
    target_id: str,
    summary: str,
    details: Optional[List[str]] = None
) -> Frame:
    """
    Build an EXPLAIN frame for introspection and debugging.
    
    Args:
        target_id: Identifier of the target frame/token
        summary: Brief summary explanation
        details: Optional list of detailed explanations
        
    Returns:
        Frame with TYPE=EXPLAIN
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", "EXPLAIN"),
        ("DICT", dict_version),
        ("TARGET_ID", f"≛⟦{target_id}⟧")
    ]
    
    payload = [
        "≛SUMMARY",
        f"≛⟦{summary}⟧"
    ]
    
    if details:
        for detail in details:
            payload.extend(["≛DETAIL", f"≛⟦{detail}⟧"])
    
    return Frame(header, payload)


def build_task_frame(
    task_type: str,
    instruction: str,
    input_data: Any,
    expected_output: Optional[Any] = None,
    difficulty: Optional[str] = None
) -> Frame:
    """
    Build a TASK frame for training curriculum.
    
    Args:
        task_type: Type of task (ENCODE_INT, DECODE_FRAME, etc.)
        instruction: Natural language instruction
        input_data: Input (NL string or ForgeNumerics token/frame)
        expected_output: Expected output (for supervised learning)
        difficulty: Optional difficulty level (BASIC, INTERMEDIATE, ADVANCED)
        
    Returns:
        Frame with TYPE=TASK
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", "TASK"),
        ("DICT", dict_version),
        ("TASK_TYPE", task_type)
    ]
    
    if difficulty:
        header.append(("DIFFICULTY", difficulty))
    
    payload = [
        "≛INSTRUCTION",
        f"≛⟦{instruction}⟧",
        "≛INPUT",
        f"≛⟦{str(input_data)}⟧"
    ]
    
    if expected_output is not None:
        payload.extend([
            "≛EXPECTED",
            f"≛⟦{str(expected_output)}⟧"
        ])
    
    return Frame(header, payload)


def build_caps_frame(
    supports: Dict[str, str],
    limits: Optional[Dict[str, str]] = None
) -> Frame:
    """
    Build a CAPS (capabilities) frame for agent negotiation.
    
    Args:
        supports: Dict of capability -> YES/NO
            e.g., {"FLOAT_T": "YES", "ENC_AES_GCM": "NO"}
        limits: Optional dict of limit names -> values
            e.g., {"MAX_TENSOR_SIZE": "≗⊙⊙ΦΦ..."}
        
    Returns:
        Frame with TYPE=CAPS
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", "CAPS"),
        ("DICT", dict_version)
    ]
    
    payload = []
    
    # Add support declarations
    for feature, supported in supports.items():
        payload.extend([
            f"≛SUPPORTS_{feature}",
            f"≛{supported}"
        ])
    
    # Add limits
    if limits:
        for limit_name, limit_value in limits.items():
            payload.extend([
                f"≛{limit_name}",
                limit_value if limit_value.startswith("≗") else f"≛{limit_value}"
            ])
    
    return Frame(header, payload)


def build_error_frame(
    error_type: str,
    location: str,
    code: str,
    detail: str,
    suggestion: Optional[str] = None
) -> Frame:
    """
    Build an ERROR frame for validation and diagnostics.
    
    Args:
        error_type: PARSE_ERROR, VALIDATION_ERROR, etc.
        location: Where the error occurred
        code: Error code (MISSING_FRAME_END, INVALID_TRIT, etc.)
        detail: Detailed error message
        suggestion: Optional suggestion for fixing
        
    Returns:
        Frame with TYPE=ERROR
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", error_type),
        ("DICT", dict_version),
        ("CODE", code)
    ]
    
    payload = [
        "≛WHERE",
        f"≛⟦{location}⟧",
        "≛DETAIL",
        f"≛⟦{detail}⟧"
    ]
    
    if suggestion:
        payload.extend([
            "≛SUGGESTION",
            f"≛⟦{suggestion}⟧"
        ])
    
    return Frame(header, payload)


def build_tensor_frame(
    dtype: str,
    shape: List[int],
    data_tokens: List[str],
    order: str = "ROW_MAJOR"
) -> Frame:
    """
    Build a TENSOR frame for ML-friendly data storage.
    
    Args:
        dtype: Data type (FLOAT_T64, DECIMAL_T, INT_U3, etc.)
        shape: Tensor dimensions as list of ints
        data_tokens: Flattened data as encoded numeric tokens
        order: Memory layout (ROW_MAJOR or COL_MAJOR)
        
    Returns:
        Frame with TYPE=TENSOR
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    # Encode shape
    shape_tokens = [encode_int_u3(dim) for dim in shape]
    
    header = [
        ("TYPE", "TENSOR"),
        ("DICT", dict_version),
        ("DTYPE", dtype),
        ("ORDER", order),
        ("NDIM", encode_int_u3(len(shape)))
    ]
    
    # Payload: shape followed by data
    payload = ["≛SHAPE"] + shape_tokens + ["≛DATA"] + data_tokens
    
    return Frame(header, payload)


def build_dict_update_enhanced(
    extdict_id: str,
    word_combo_pairs: List[Tuple[str, str]],
    stats: Optional[List[Dict[str, Any]]] = None
) -> Frame:
    """
    Build enhanced DICT_UPDATE frame with frequency and source stats.
    
    Args:
        extdict_id: Extension dictionary ID
        word_combo_pairs: List of (word, combo) tuples
        stats: Optional list of stat dicts with keys:
            - freq: frequency count (int)
            - source: source identifier (str)
            
    Returns:
        Frame with TYPE=DICT_UPDATE
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", "DICT_UPDATE"),
        ("DICT", dict_version),
        ("EXTDICT", extdict_id),
        ("COUNT", encode_int_u3(len(word_combo_pairs)))
    ]
    
    payload = []
    for i, (word, combo) in enumerate(word_combo_pairs):
        word_literal = f"≛⟦{word}⟧"
        combo_token = f"≛{combo}"
        
        payload.extend([
            "≛WORD", word_literal,
            "≛CODE", combo_token
        ])
        
        # Add stats if provided
        if stats and i < len(stats):
            if "freq" in stats[i]:
                payload.extend([
                    "≛FREQ",
                    encode_int_u3(stats[i]["freq"])
                ])
            if "source" in stats[i]:
                payload.extend([
                    "≛SOURCE",
                    f"≛{stats[i]['source']}"
                ])
    
    return Frame(header, payload)


def build_train_pair_frame(
    natural_language: str,
    forgenumerics_frame: str
) -> Frame:
    """
    Build a parallel NL ↔ ForgeNumerics training pair.
    
    Args:
        natural_language: Natural language description
        forgenumerics_frame: Corresponding ForgeNumerics representation
        
    Returns:
        Frame with TYPE=TRAIN_PAIR
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", "TRAIN_PAIR"),
        ("DICT", dict_version)
    ]
    
    payload = [
        "≛NATLANG",
        f"≛⟦{natural_language}⟧",
        "≛FORGE",
        f"≛⟦{forgenumerics_frame}⟧"
    ]
    
    return Frame(header, payload)


def build_repair_pair_frame(
    draft_nl: str,
    critique_summary: str,
    revised_nl: str
) -> Frame:
    """
    Build a REPAIR_PAIR frame capturing draft → critique → revised triplet.

    Args:
        draft_nl: Original draft natural language
        critique_summary: Teacher critique summary (could include citations)
        revised_nl: Final revised natural language

    Returns:
        Frame with TYPE=REPAIR_PAIR
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')

    header = [
        ("TYPE", "REPAIR_PAIR"),
        ("DICT", dict_version)
    ]

    payload = [
        "≛DRAFT",
        f"≛⟦{draft_nl}⟧",
        "≛CRITIQUE",
        f"≛⟦{critique_summary}⟧",
        "≛REVISED",
        f"≛⟦{revised_nl}⟧",
    ]

    return Frame(header, payload)


def build_dict_policy_frame(
    min_frequency: int,
    allowed_domains: List[str],
    max_growth_per_day: int
) -> Frame:
    """
    Build a DICT_POLICY frame describing allocation rules.
    
    Args:
        min_frequency: Minimum occurrences before allocation
        allowed_domains: List of domains where allocation is permitted
        max_growth_per_day: Maximum new allocations per day
        
    Returns:
        Frame with TYPE=DICT_POLICY
    """
    dl = DataLoader()
    dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    header = [
        ("TYPE", "DICT_POLICY"),
        ("DICT", dict_version),
        ("MIN_FREQ", encode_int_u3(min_frequency)),
        ("MAX_GROWTH", encode_int_u3(max_growth_per_day))
    ]
    
    payload = ["≛ALLOWED_DOMAINS"]
    for domain in allowed_domains:
        payload.append(f"≛{domain}")
    
    return Frame(header, payload)
