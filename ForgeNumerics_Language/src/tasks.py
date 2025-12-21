from typing import Dict, Any
from .numeric import (
    encode_int_u3, decode_int_u3,
    encode_int_s3, decode_int_s3,
    encode_decimal_t, decode_decimal_t,
    encode_float_t, decode_float_t
)
from .schemas import (
    build_vector_frame, parse_vector_frame,
    build_matrix_frame, parse_matrix_frame,
    build_log_frame, parse_log_frame,
    build_fact_frame, parse_fact_frame
)

TASKS = {
    "int-u3": {
        "description": "Encode/decode unsigned integers using INT-U3",
        "practice": lambda value: {
            "encoded": encode_int_u3(int(value)),
            "decoded": decode_int_u3(encode_int_u3(int(value)))
        }
    },
    "int-s3": {
        "description": "Encode/decode signed integers using INT-S3",
        "practice": lambda value: {
            "encoded": encode_int_s3(int(value)),
            "decoded": decode_int_s3(encode_int_s3(int(value)))
        }
    },
    "decimal-t": {
        "description": "Encode/decode DECIMAL-T exact decimals",
        "practice": lambda sign_positive, scale, integer_value: {
            "encoded": encode_decimal_t(bool(sign_positive), int(scale), int(integer_value)),
            "decoded": decode_decimal_t(
                encode_decimal_t(bool(sign_positive), int(scale), int(integer_value))
            )
        }
    },
    "float-t": {
        "description": "Encode/decode FLOAT-T (simplified, fixed widths)",
        "practice": lambda sign_positive, exponent, mantissa, exp_width, man_width: {
            "encoded": encode_float_t(bool(sign_positive), int(exponent), mantissa, int(exp_width), int(man_width)),
            "decoded": decode_float_t(
                encode_float_t(bool(sign_positive), int(exponent), mantissa, int(exp_width), int(man_width))
            )
        }
    },
}

def example_measurement_frame(value_token: str, unit_word: str = "meter") -> dict:
    """Builds a minimal measurement frame string using frames helpers.
    value_token should be a numeric token like DECIMAL-T or FLOAT-T encoded string.
    """
    from .frames import Frame, MODE_WORD
    header = [("VER", "2.0-T"), ("DICT", "DICT_v2025_11"), ("TYPE", "MEASUREMENT"), ("UNIT", unit_word)]
    payload = [f"{MODE_WORD}VALUE", value_token]
    # Keep payload simple: [≛VALUE, <numeric token>]
    f = Frame(header=header, payload=payload)
    s = f.serialize()
    parsed = Frame.parse(s)
    return {"serialized": s, "parsed_header": parsed.header, "parsed_payload": parsed.payload}

TASKS["frame-measurement"] = {
    "description": "Build and parse a measurement frame (TYPE=MEASUREMENT)",
    "practice": lambda unit, sign_positive, scale, integer_value: example_measurement_frame(
        encode_decimal_t(bool(sign_positive), int(scale), int(integer_value)), unit
    )
}

TASKS["schema-vector"] = {
    "description": "Build and parse a VECTOR frame",
    "practice": lambda values: {
        "frame": build_vector_frame(values),
        "serialized": build_vector_frame(values).serialize(),
        "parsed": parse_vector_frame(build_vector_frame(values))
    }
}

TASKS["schema-matrix"] = {
    "description": "Build and parse a MATRIX frame",
    "practice": lambda rows: {
        "frame": build_matrix_frame(rows),
        "serialized": build_matrix_frame(rows).serialize(),
        "parsed": parse_matrix_frame(build_matrix_frame(rows))
    }
}

TASKS["schema-log"] = {
    "description": "Build and parse a LOG frame",
    "practice": lambda severity, message, timestamp=None, details=None: {
        "frame": build_log_frame(severity, message, timestamp, details),
        "serialized": build_log_frame(severity, message, timestamp, details).serialize(),
        "parsed": parse_log_frame(build_log_frame(severity, message, timestamp, details))
    }
}

TASKS["schema-fact"] = {
    "description": "Build and parse a FACT frame (knowledge triple)",
    "practice": lambda subject, predicate, obj, confidence=None, source=None: {
        "frame": build_fact_frame(subject, predicate, obj, confidence, source),
        "serialized": build_fact_frame(subject, predicate, obj, confidence, source).serialize(),
        "parsed": parse_fact_frame(build_fact_frame(subject, predicate, obj, confidence, source))
    }
}

def list_tasks() -> Dict[str, Any]:
    return {name: meta["description"] for name, meta in TASKS.items()}

def run_task(name: str, **kwargs) -> Dict[str, Any]:
    if name not in TASKS:
        raise ValueError("Unknown task")
    meta = TASKS[name]
    return meta["practice"](**kwargs)
