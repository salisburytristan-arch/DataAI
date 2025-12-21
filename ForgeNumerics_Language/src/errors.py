"""
Structured error taxonomy for ForgeNumerics-S parsing and validation.
Errors include: type, code, location (offset in input), context, and recovery hints.
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for ForgeNumerics parsing/validation."""
    
    # Parse errors
    PARSE_INVALID_FRAME_START = "PARSE_001"
    PARSE_INVALID_FRAME_END = "PARSE_002"
    PARSE_MISSING_HEADER_PAYLOAD_SEP = "PARSE_003"
    PARSE_MALFORMED_HEADER_FIELD = "PARSE_004"
    PARSE_UNKNOWN_NUMERIC_PROFILE = "PARSE_005"
    PARSE_INVALID_TRIT_SEQUENCE = "PARSE_006"
    PARSE_UNEXPECTED_TOKEN = "PARSE_007"
    
    # Validation errors
    VALIDATE_UNKNOWN_DICT_CODE = "VALIDATE_001"
    VALIDATE_UNSUPPORTED_PROFILE = "VALIDATE_002"
    VALIDATE_TYPE_MISMATCH = "VALIDATE_003"
    VALIDATE_REQUIRED_FIELD_MISSING = "VALIDATE_004"
    VALIDATE_SCHEMA_MISMATCH = "VALIDATE_005"
    
    # Encoding/Decoding errors
    ENCODE_OUT_OF_RANGE = "ENCODE_001"
    ENCODE_INVALID_ARGUMENT = "ENCODE_002"
    DECODE_INVALID_INPUT = "DECODE_001"
    DECODE_CHECKSUM_MISMATCH = "DECODE_002"
    
    # Canonicalization errors
    CANON_NORMALIZATION_FAILED = "CANON_001"
    CANON_AMBIGUOUS_FORMAT = "CANON_002"


@dataclass
class ParseLocation:
    """Precise location in input string."""
    offset: int  # byte offset
    line: int    # 1-indexed line number
    column: int  # 1-indexed column number
    
    def __str__(self) -> str:
        return f"line {self.line}, col {self.column} (offset {self.offset})"


@dataclass
class ParseError(Exception):
    """Structured parse error with location, code, and recovery suggestions."""
    code: ErrorCode
    message: str
    location: Optional[ParseLocation] = None
    context: Optional[str] = None  # snippet of input around error
    suggestion: Optional[str] = None  # recovery hint
    
    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.location:
            parts.append(f"  at {self.location}")
        if self.context:
            parts.append(f"  context: {self.context}")
        if self.suggestion:
            parts.append(f"  suggestion: {self.suggestion}")
        return "\n".join(parts)


class ValidationError(Exception):
    """Validation error (schema/logic)."""
    def __init__(self, code: ErrorCode, message: str, suggestion: Optional[str] = None):
        self.code = code
        self.message = message
        self.suggestion = suggestion
        super().__init__(f"[{code}] {message}" + (f" ({suggestion})" if suggestion else ""))


def compute_location(text: str, offset: int) -> ParseLocation:
    """Compute line/column from byte offset in text."""
    line = 1
    column = 1
    for i, ch in enumerate(text[:offset]):
        if ch == '\n':
            line += 1
            column = 1
        else:
            column += 1
    return ParseLocation(offset=offset, line=line, column=column)


def extract_context(text: str, offset: int, window: int = 40) -> str:
    """Extract a window of text around the error location."""
    start = max(0, offset - window)
    end = min(len(text), offset + window)
    context = text[start:end]
    # Mark error position with ▼
    rel_offset = offset - start
    return context[:rel_offset] + "▼" + context[rel_offset:]
