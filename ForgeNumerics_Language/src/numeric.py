from typing import List

TRIT_ZERO = "⊙"
TRIT_ONE = "⊗"
TRIT_TWO = "Φ"

PROFILE_INT_U3 = TRIT_ZERO + TRIT_ZERO  # ⊙⊙
PROFILE_INT_S3 = TRIT_ZERO + TRIT_ONE   # ⊙⊗
PROFILE_DECIMAL_T = TRIT_ONE + TRIT_ONE # ⊗⊗
PROFILE_FLOAT_T = TRIT_ONE + TRIT_ZERO  # ⊗⊙

MODE_NUM = "≗"

# Helpers

def b2s(d: int) -> str:
    if d == 0:
        return TRIT_ZERO
    if d == 1:
        return TRIT_ONE
    if d == 2:
        return TRIT_TWO
    raise ValueError("digit must be 0,1,2")

def s2b(sym: str) -> int:
    if sym == TRIT_ZERO:
        return 0
    if sym == TRIT_ONE:
        return 1
    if sym == TRIT_TWO:
        return 2
    raise ValueError("unknown trit symbol")

# INT-U3

def encode_int_u3(n: int) -> str:
    if n < 0:
        raise ValueError("INT-U3 requires non-negative integer")
    if n == 0:
        trits = [TRIT_ZERO]
    else:
        trits_rev: List[str] = []
        v = n
        while v > 0:
            r = v % 3
            v //= 3
            trits_rev.append(b2s(r))
        trits = list(reversed(trits_rev))
    return MODE_NUM + PROFILE_INT_U3 + "".join(trits)

def decode_int_u3(token: str) -> int:
    if not token.startswith(MODE_NUM + PROFILE_INT_U3):
        raise ValueError("Token is not INT-U3")
    body = token[len(MODE_NUM + PROFILE_INT_U3):]
    n = 0
    for ch in body:
        n *= 3
        n += s2b(ch)
    return n

# INT-S3

def encode_int_s3(n: int) -> str:
    sign_trit = TRIT_ZERO if n >= 0 else TRIT_ONE
    mag = n if n >= 0 else -n
    mag_body = encode_int_u3(mag)[len(MODE_NUM + PROFILE_INT_U3):]
    return MODE_NUM + PROFILE_INT_S3 + "◦" + sign_trit + "◽" + mag_body

def decode_int_s3(token: str) -> int:
    prefix = MODE_NUM + PROFILE_INT_S3 + "◦"
    if not token.startswith(prefix):
        raise ValueError("Token is not INT-S3")
    rest = token[len(prefix):]
    if not rest:
        raise ValueError("Missing sign trit")
    sign = rest[0]
    if len(rest) < 2 or rest[1] != "◽":
        raise ValueError("Missing magnitude separator")
    mag_trits = rest[2:]
    magnitude = decode_int_u3(MODE_NUM + PROFILE_INT_U3 + mag_trits)
    return magnitude if sign == TRIT_ZERO else -magnitude

# DECIMAL-T: ≗⊗⊗ <sign_trit> ◦ <scale_trits> ◽ <integer_trits>

def encode_decimal_t(sign_positive: bool, scale: int, integer_value: int) -> str:
    if scale < 0:
        raise ValueError("scale must be non-negative")
    if integer_value < 0:
        raise ValueError("integer_value must be non-negative (magnitude)")
    sign_trit = TRIT_ZERO if sign_positive else TRIT_ONE
    scale_body = encode_int_u3(scale)[len(MODE_NUM + PROFILE_INT_U3):]
    int_body = encode_int_u3(integer_value)[len(MODE_NUM + PROFILE_INT_U3):]
    return MODE_NUM + PROFILE_DECIMAL_T + sign_trit + "◦" + scale_body + "◽" + int_body

def decode_decimal_t(token: str) -> tuple[bool, int, int]:
    # returns (sign_positive, scale, integer_value)
    prefix = MODE_NUM + PROFILE_DECIMAL_T
    if not token.startswith(prefix):
        raise ValueError("Token is not DECIMAL-T")
    rest = token[len(prefix):]
    if not rest:
        raise ValueError("Missing sign trit")
    sign_trit = rest[0]
    if len(rest) < 2 or rest[1] != "◦":
        raise ValueError("Missing scale marker")
    after_scale_marker = rest[2:]
    # split at first '◽'
    sep_index = after_scale_marker.find("◽")
    if sep_index == -1:
        raise ValueError("Missing integer separator ◽")
    scale_trits = after_scale_marker[:sep_index]
    int_trits = after_scale_marker[sep_index+1:]
    scale = decode_int_u3(MODE_NUM + PROFILE_INT_U3 + scale_trits)
    integer_value = decode_int_u3(MODE_NUM + PROFILE_INT_U3 + int_trits)
    return (sign_trit == TRIT_ZERO, scale, integer_value)

# FLOAT-T (simplified): ≗⊗⊙ <sign_trit> ◦ <exp_len_trits> ◽ <exp_trits_fixed> ∷ <mantissa_trits_fixed>
# We fix widths via config; exp_len_trits echoes exponent width for clarity.

def encode_float_t(value_sign_positive: bool, exponent_value: int, mantissa_trits: str, exp_width: int, man_width: int) -> str:
    # mantissa_trits must be exactly man_width and characters in {⊙,⊗,Φ}
    if len(mantissa_trits) != man_width:
        raise ValueError("mantissa_trits length mismatch")
    if any(ch not in (TRIT_ZERO, TRIT_ONE, TRIT_TWO) for ch in mantissa_trits):
        raise ValueError("mantissa contains invalid symbols")
    sign_trit = TRIT_ZERO if value_sign_positive else TRIT_ONE
    exp_len_body = encode_int_u3(exp_width)[len(MODE_NUM + PROFILE_INT_U3):]
    # encode exponent as INT-S3 body without prefix
    exp_token = encode_int_s3(exponent_value)
    # strip ≗⊙⊗◦<sign>◽ to get magnitude body; we need full signed body, so we reconstruct body after the '◽'
    # For simplicity, use INT-U3 for |exponent| and prepend sign marker locally
    exp_sign = TRIT_ZERO if exponent_value >= 0 else TRIT_ONE
    exp_mag_body = encode_int_u3(abs(exponent_value))[len(MODE_NUM + PROFILE_INT_U3):]
    exp_body = exp_sign + exp_mag_body
    return MODE_NUM + PROFILE_FLOAT_T + sign_trit + "◦" + exp_len_body + "◽" + exp_body + " ∷ " + mantissa_trits

def decode_float_t(token: str) -> tuple[bool, int, str]:
    prefix = MODE_NUM + PROFILE_FLOAT_T
    if not token.startswith(prefix):
        raise ValueError("Token is not FLOAT-T")
    rest = token[len(prefix):]
    if not rest:
        raise ValueError("Missing sign trit")
    sign_trit = rest[0]
    if len(rest) < 2 or rest[1] != "◦":
        raise ValueError("Missing exp len marker")
    after = rest[2:]
    sep = after.find("◽")
    if sep == -1:
        raise ValueError("Missing exponent separator")
    exp_len_trits = after[:sep]
    tail = after[sep+1:]
    # split payload sep ' ∷ '
    parts = tail.split(" ∷ ")
    if len(parts) != 2:
        raise ValueError("Missing mantissa separator ∷")
    exp_body, mantissa = parts
    if not exp_body:
        raise ValueError("Empty exponent body")
    exp_sign = exp_body[0]
    exp_mag_trits = exp_body[1:]
    exponent_value = decode_int_u3(MODE_NUM + PROFILE_INT_U3 + exp_mag_trits)
    if exp_sign != TRIT_ZERO:
        exponent_value = -exponent_value
    return (sign_trit == TRIT_ZERO, exponent_value, mantissa)

def float_t_value(sign_positive: bool, exponent: int, mantissa_trits: str) -> float:
    """Approximate numeric value: (-1)^s * (1.m) * 3^e where mantissa_trits are base-3 fractional digits.
    """
    # Convert mantissa trits to fractional in base-3
    frac = 0.0
    for i, ch in enumerate(mantissa_trits, start=1):
        digit = s2b(ch)
        frac += digit / (3 ** i)
    val = (1.0 + frac) * (3 ** exponent)
    return val if sign_positive else -val
