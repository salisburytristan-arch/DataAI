"""
Advanced Schema Builders for ForgeNumerics-S (Part 10)

Builders for scientific, mathematical, and structured data frames:
- VECTOR
- MATRIX
- LOG
- FACT (knowledge base triples)
"""

from typing import List, Dict, Any, Optional, Tuple
from src.frames import Frame
from src.numeric import encode_int_u3
from src.data_loader import DataLoader


def build_vector_frame(
    values: List[str],
    vector_type: str = "VECTOR",
    dict_version: Optional[str] = None
) -> Frame:
    """
    Build a VECTOR frame.
    
    Args:
        values: List of numeric tokens (already encoded, e.g., "≗⊙⊙⊗⊗Φ")
        vector_type: TYPE field value (default "VECTOR")
        dict_version: Dictionary version to use in header
        
    Returns:
        A Frame with TYPE=VECTOR
    """
    if dict_version is None:
        dl = DataLoader()
        dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    # Encode length
    length = len(values)
    len_token = encode_int_u3(length)
    
    # Build header
    header_fields = [
        ("TYPE", vector_type),
        ("DICT", dict_version),
        ("LEN", len_token)
    ]
    
    # Build payload: tokens separated by ⦙
    payload = values  # Already a list of tokens
    
    return Frame(header_fields, payload)


def parse_vector_frame(frame: Frame) -> List[str]:
    """
    Parse a VECTOR frame and extract numeric tokens.
    
    Args:
        frame: The VECTOR frame to parse
        
    Returns:
        List of numeric token strings
    """
    # Payload is already a list of tokens
    return frame.payload


def build_matrix_frame(
    rows: List[List[str]],
    dict_version: Optional[str] = None
) -> Frame:
    """
    Build a MATRIX frame.
    
    Args:
        rows: List of rows, where each row is a list of numeric tokens
        dict_version: Dictionary version to use
        
    Returns:
        A Frame with TYPE=MATRIX
    """
    if dict_version is None:
        dl = DataLoader()
        dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    num_rows = len(rows)
    num_cols = len(rows[0]) if rows else 0
    
    # Validate rectangular shape
    for row in rows:
        if len(row) != num_cols:
            raise ValueError("Matrix must have consistent column count")
    
    # Encode dimensions
    rows_token = encode_int_u3(num_rows)
    cols_token = encode_int_u3(num_cols)
    
    # Build header
    header_fields = [
        ("TYPE", "MATRIX"),
        ("DICT", dict_version),
        ("ROWS", rows_token),
        ("COLS", cols_token)
    ]
    
    # Build payload: flatten all rows into single token list
    payload = []
    for row in rows:
        payload.extend(row)
    
    return Frame(header_fields, payload)


def parse_matrix_frame(frame: Frame) -> List[List[str]]:
    """
    Parse a MATRIX frame.
    
    Args:
        frame: The MATRIX frame
        
    Returns:
        List of rows, each row is a list of token strings
    """
    from src.numeric import decode_int_u3
    
    # Get dimensions from header
    rows_token = None
    cols_token = None
    for key, val in frame.header:
        if key == "ROWS":
            rows_token = val
        elif key == "COLS":
            cols_token = val
    
    if not rows_token or not cols_token:
        raise ValueError("MATRIX frame missing ROWS/COLS in header")
    
    num_rows = decode_int_u3(rows_token)
    num_cols = decode_int_u3(cols_token)
    
    # Payload is flat list of all tokens
    all_tokens = frame.payload
    
    # Group into rows
    matrix = []
    idx = 0
    for _ in range(num_rows):
        row = all_tokens[idx:idx+num_cols]
        matrix.append(row)
        idx += num_cols
    
    return matrix


def build_log_frame(
    severity: str,
    message: str,
    timestamp: Optional[str] = None,
    details: Optional[str] = None,
    dict_version: Optional[str] = None
) -> Frame:
    """
    Build a LOG frame for telemetry/logging.
    
    Args:
        severity: Log level (INFO, WARN, ERROR, etc.)
        message: Main log message (word token or literal)
        timestamp: Optional timestamp (numeric token)
        details: Optional detail string (literal)
        dict_version: Dictionary version
        
    Returns:
        A Frame with TYPE=LOG
    """
    if dict_version is None:
        dl = DataLoader()
        dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    # Build header
    header_fields = [
        ("TYPE", "LOG"),
        ("DICT", dict_version),
        ("SEVERITY", severity)
    ]
    
    if timestamp:
        header_fields.append(("TIME", timestamp))
    
    # Build payload as list of tokens
    payload = ["≛MSG", message]
    
    if details:
        payload.extend(["≛DETAIL", details])
    
    return Frame(header_fields, payload)


def parse_log_frame(frame: Frame) -> Dict[str, Any]:
    """
    Parse a LOG frame.
    
    Args:
        frame: The LOG frame
        
    Returns:
        Dict with severity, time, message, detail
    """
    result = {
        "severity": None,
        "time": None,
        "message": None,
        "detail": None
    }
    
    # Extract from header
    for key, val in frame.header:
        if key == "SEVERITY":
            result["severity"] = val
        elif key == "TIME":
            result["time"] = val
    
    # Parse payload (list of tokens)
    i = 0
    while i < len(frame.payload):
        token = frame.payload[i]
        if token == "≛MSG" and i+1 < len(frame.payload):
            result["message"] = frame.payload[i+1]
            i += 2
        elif token == "≛DETAIL" and i+1 < len(frame.payload):
            result["detail"] = frame.payload[i+1]
            i += 2
        else:
            i += 1
    
    return result


def build_fact_frame(
    subject: str,
    predicate: str,
    obj: str,
    confidence: Optional[str] = None,
    source: Optional[str] = None,
    dict_version: Optional[str] = None
) -> Frame:
    """
    Build a FACT frame (knowledge base triple).
    
    Args:
        subject: Subject word token (e.g., "≛Einstein")
        predicate: Predicate word token (e.g., "≛born_in")
        obj: Object word token (e.g., "≛Ulm")
        confidence: Optional confidence score (numeric token)
        source: Optional source identifier (word token)
        dict_version: Dictionary version
        
    Returns:
        A Frame with TYPE=FACT
    """
    if dict_version is None:
        dl = DataLoader()
        dict_version = dl.defaults().get('DICT', 'DICT_v2025_11')
    
    # Build header
    header_fields = [
        ("TYPE", "FACT"),
        ("DICT", dict_version)
    ]
    
    if confidence:
        header_fields.append(("CONFIDENCE", confidence))
    if source:
        header_fields.append(("SOURCE", source))
    
    # Build payload: simple triple as token list
    payload = ["≛SUBJ", subject, "≛PRED", predicate, "≛OBJ", obj]
    
    return Frame(header_fields, payload)


def parse_fact_frame(frame: Frame) -> Dict[str, Any]:
    """
    Parse a FACT frame.
    
    Args:
        frame: The FACT frame
        
    Returns:
        Dict with subject, predicate, object, confidence, source
    """
    result = {
        "subject": None,
        "predicate": None,
        "object": None,
        "confidence": None,
        "source": None
    }
    
    # Extract from header
    for key, val in frame.header:
        if key == "CONFIDENCE":
            result["confidence"] = val
        elif key == "SOURCE":
            result["source"] = val
    
    # Parse payload (list of tokens)
    i = 0
    while i < len(frame.payload):
        token = frame.payload[i]
        if token == "≛SUBJ" and i+1 < len(frame.payload):
            result["subject"] = frame.payload[i+1]
            i += 2
        elif token == "≛PRED" and i+1 < len(frame.payload):
            result["predicate"] = frame.payload[i+1]
            i += 2
        elif token == "≛OBJ" and i+1 < len(frame.payload):
            result["object"] = frame.payload[i+1]
            i += 2
        else:
            i += 1
    
    return result
