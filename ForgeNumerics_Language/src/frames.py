from dataclasses import dataclass, field
from typing import List, Tuple
from src.errors import ParseError, ErrorCode, compute_location, extract_context

FRAME_START = "⧆"
FRAME_END = "⧈"
HEADER_PAYLOAD_SEP = "∷"
FIELD_SEP = "∴"
TOKEN_SEP = "⦙"
MODE_WORD = "≛"
MODE_NUM = "≗"
TRIT_ZERO = "⊙"
TRIT_ONE = "⊗"
TRIT_TWO = "Φ"

@dataclass
class Frame:
    header: List[Tuple[str, str]] = field(default_factory=list)
    payload: List[str] = field(default_factory=list)

    def serialize(self) -> str:
        # Canonical: no extra spaces, fixed separator usage
        header_parts = [f"{MODE_WORD}{k}{TOKEN_SEP}{MODE_WORD}{v}" for k, v in self.header]
        header_str = FIELD_SEP.join(header_parts)
        payload_str = TOKEN_SEP.join(self.payload)
        return f"{FRAME_START}{header_str}{HEADER_PAYLOAD_SEP}{payload_str}{FRAME_END}"

    @staticmethod
    def parse(s: str) -> "Frame":
        s = s.strip()
        if not s.startswith(FRAME_START):
            loc = compute_location(s, 0)
            raise ParseError(
                ErrorCode.PARSE_INVALID_FRAME_START,
                f"Frame must start with '{FRAME_START}'",
                location=loc,
                context=extract_context(s, 0),
                suggestion="Ensure frame starts with ⧆"
            )
        if not s.endswith(FRAME_END):
            loc = compute_location(s, len(s) - 1)
            raise ParseError(
                ErrorCode.PARSE_INVALID_FRAME_END,
                f"Frame must end with '{FRAME_END}'",
                location=loc,
                context=extract_context(s, len(s) - 1),
                suggestion="Ensure frame ends with ⧈"
            )
        inner = s[len(FRAME_START):-len(FRAME_END)]
        if HEADER_PAYLOAD_SEP not in inner:
            loc = compute_location(s, len(FRAME_START))
            raise ParseError(
                ErrorCode.PARSE_MISSING_HEADER_PAYLOAD_SEP,
                f"Frame missing header/payload separator '{HEADER_PAYLOAD_SEP}'",
                location=loc,
                context=extract_context(s, len(FRAME_START)),
                suggestion=f"Insert '{HEADER_PAYLOAD_SEP}' to separate header from payload"
            )
        header_part, payload_part = inner.split(HEADER_PAYLOAD_SEP, 1)
        header_fields = []
        if header_part:
            for field in header_part.split(FIELD_SEP):
                kv = field.split(TOKEN_SEP)
                if len(kv) == 2:
                    k = kv[0].lstrip(MODE_WORD)
                    v = kv[1].lstrip(MODE_WORD)
                    header_fields.append((k, v))
                elif len(kv) > 1:
                    # Malformed header field
                    field_offset = s.find(field)
                    if field_offset < 0:
                        field_offset = len(FRAME_START)
                    loc = compute_location(s, field_offset)
                    raise ParseError(
                        ErrorCode.PARSE_MALFORMED_HEADER_FIELD,
                        f"Header field has {len(kv)} parts, expected 2 (key⦙value)",
                        location=loc,
                        context=extract_context(s, field_offset),
                        suggestion="Ensure header fields are formatted as ≛KEY⦙≛VALUE"
                    )
        payload_tokens = [t for t in payload_part.split(TOKEN_SEP) if t]
        return Frame(header_fields, payload_tokens)

TRIT_RESERVED = "⊛"  # Extension: used for bit-pair 11 to enable perfect round-trip

def bytes_to_trits(data: bytes) -> str:
    """Encode each byte into 4 trits by mapping consecutive bit-pairs:
    pairs: (b7,b6),(b5,b4),(b3,b2),(b1,b0) → 00/01/10/11 → ⊙/⊗/Φ/⊛
    This is deterministic and per-byte, ensuring exact round-trip.
    """
    out = []
    for b in data:
        for shift in (6, 4, 2, 0):
            pair = (b >> shift) & 0b11
            if pair == 0:
                out.append(TRIT_ZERO)
            elif pair == 1:
                out.append(TRIT_ONE)
            elif pair == 2:
                out.append(TRIT_TWO)
            else:
                out.append(TRIT_RESERVED)
    return "".join(out)

def make_blob_t(data: bytes) -> str:
    """Create a BLOB-T numeric token from bytes: ≗Φ⊙<blob_trits>"""
    blob_trits = bytes_to_trits(data)
    return MODE_NUM + TRIT_TWO + TRIT_ZERO + blob_trits

def trits_to_bytes(trits: str) -> bytes:
    """Decode trits back into bytes. Requires length multiple of 4.
    ⊙→00, ⊗→01, Φ→10, ⊛→11 mapped into byte as (b7,b6),(b5,b4),(b3,b2),(b1,b0).
    Unknown symbols are treated as 00.
    """
    # Map symbols to pair values
    def sym_to_pair(ch: str) -> int:
        if ch == TRIT_ZERO:
            return 0
        elif ch == TRIT_ONE:
            return 1
        elif ch == TRIT_TWO:
            return 2
        elif ch == TRIT_RESERVED:
            return 3
        else:
            return 0

    # If length not multiple of 4, truncate excess to avoid padding artifacts
    usable_len = (len(trits) // 4) * 4
    trits = trits[:usable_len]
    out = bytearray()
    for i in range(0, len(trits), 4):
        p0 = sym_to_pair(trits[i])
        p1 = sym_to_pair(trits[i+1])
        p2 = sym_to_pair(trits[i+2])
        p3 = sym_to_pair(trits[i+3])
        byte = (p0 << 6) | (p1 << 4) | (p2 << 2) | p3
        out.append(byte)
    return bytes(out)
