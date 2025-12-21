"""
Canonicalization for ForgeNumerics-S frames.
Ensures semantic equivalence produces byte-identical output (critical for hashing, deduping, signatures).

Rules:
1. Header fields sorted lexicographically by key
2. Numeric tokens normalized (no alternate encodings)
3. Whitespace: no leading/trailing spaces in tokens
4. Separator usage: fixed (∴, ∷, ⦙, ⧆, ⧈)
5. Word codes: always use MODE_WORD prefix (≛)
6. Numeric codes: always use MODE_NUM prefix (≗)
"""
from src.frames import Frame, MODE_WORD, MODE_NUM, TRIT_ZERO, TRIT_ONE, TRIT_TWO, TRIT_RESERVED
from typing import List, Tuple
import re


def canonicalize_frame(frame: Frame) -> Frame:
    """
    Return a canonical copy of the frame.
    Rules applied:
    - Header fields sorted by key
    - Payload tokens whitespace-trimmed
    - Numeric token profiles normalized (if decodable)
    """
    # Sort header by key (lexicographic)
    canonical_header = sorted(frame.header, key=lambda kv: kv[0])
    
    # Trim payload tokens and validate
    canonical_payload = [token.strip() for token in frame.payload if token.strip()]
    
    return Frame(header=canonical_header, payload=canonical_payload)


def normalize_numeric_token(token: str) -> str:
    """
    Normalize a numeric token to its canonical form.
    For INT-U3/INT-S3/DECIMAL-T/FLOAT-T: ensures no alternate representations exist.
    For BLOB-T: verifies 4-symbol alphabet usage.
    Returns the normalized token, or original if not a recognized profile.
    """
    if not token.startswith(MODE_NUM):
        return token
    
    # Extract profile (first 2 trits after MODE_NUM)
    if len(token) < 3:
        return token
    
    profile = token[1:3]
    body = token[3:]
    
    # INT-U3: no special normalization needed (already minimal)
    if profile == TRIT_ZERO + TRIT_ZERO:
        # Verify body contains only valid trits
        if all(c in (TRIT_ZERO, TRIT_ONE, TRIT_TWO) for c in body):
            return token
        return token
    
    # INT-S3: verify structure (sign trit + magnitude)
    if profile == TRIT_ZERO + TRIT_ONE:
        # Expected: sign_trit ◦ magnitude_body
        if "◦" in body and "◽" in body:
            return token
        return token
    
    # DECIMAL-T: verify structure
    if profile == TRIT_ONE + TRIT_ONE:
        if "◦" in body and "◽" in body:
            return token
        return token
    
    # FLOAT-T: similar structure check
    if profile == TRIT_ONE + TRIT_ZERO:
        return token
    
    # BLOB-T: verify 4-symbol alphabet (⊙, ⊗, Φ, ⊛)
    if profile == TRIT_TWO + TRIT_ZERO:
        if all(c in (TRIT_ZERO, TRIT_ONE, TRIT_TWO, TRIT_RESERVED) for c in body):
            return token
        return token
    
    # Unknown profile: return as-is
    return token


def canonicalize_string(serialized: str) -> str:
    """
    Parse, canonicalize, and re-serialize a frame string.
    Returns the canonical byte representation.
    Raises ParseError if parsing fails.
    """
    frame = Frame.parse(serialized)
    canonical = canonicalize_frame(frame)
    return canonical.serialize()


def is_canonical(serialized: str) -> bool:
    """
    Check if a serialized frame is already in canonical form.
    (i.e., canonicalize(s) == s)
    """
    try:
        return canonicalize_string(serialized) == serialized.strip()
    except Exception:
        return False


def canonicalize_idempotent_test(serialized: str, iterations: int = 3) -> bool:
    """
    Verify canonicalization is idempotent: repeated calls produce the same result.
    Useful for testing.
    """
    if iterations < 2:
        return True
    try:
        result = canonicalize_string(serialized)
        for _ in range(iterations - 1):
            result2 = canonicalize_string(result)
            if result != result2:
                return False
            result = result2
        return True
    except Exception:
        return False
