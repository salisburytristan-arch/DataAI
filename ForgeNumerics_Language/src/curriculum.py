"""
Curriculum generator for ForgeNumerics-S training.
Produces sequences of TASK, EXPLAIN, and TRAIN_PAIR frames.
"""
from typing import List, Dict
from src.meta_frames import (
    build_task_frame,
    build_explain_frame,
    build_train_pair_frame,
)
from src.frames import Frame
from src.numeric import encode_int_u3


def encode_int_s3_simple(value: int) -> str:
    """Simple INT-S3 encoder for curriculum (sign + magnitude)."""
    from src.numeric import encode_int_s3
    return encode_int_s3(value)


def encode_decimal_simple(value: str) -> str:
    """Simple DECIMAL-T encoder for curriculum."""
    from src.numeric import encode_decimal_t
    parts = value.lstrip('-').split('.')
    sign_positive = not value.startswith('-')
    scale = len(parts[1]) if len(parts) > 1 else 0
    integer_value = int(parts[0] + (parts[1] if len(parts) > 1 else ''))
    return encode_decimal_t(sign_positive, scale, integer_value)


def build_basic_curriculum() -> List[Frame]:
    frames: List[Frame] = []
    # Stage: INT-U3 basics
    frames.append(build_task_frame("ENCODE_INT", "Encode 1 as INT-U3", "1", "≗⊙⊙⊙⊙", "BASIC"))
    frames.append(build_task_frame("ENCODE_INT", "Encode 42 as INT-U3", "42", "≗⊙⊙⊗⊗Φ⊙", "BASIC"))
    frames.append(build_explain_frame("task_encode_42", "Encoding positive integers in INT-U3",
                                      ["Three-trit unsigned profile","Big-endian base-3 representation"]))
    # Stage: DECIMAL-T
    frames.append(build_task_frame("ENCODE_DECIMAL", "Encode 3.14 as DECIMAL-T", "3.14", None, "BASIC"))
    # Stage: Frames
    frames.append(build_task_frame("BUILD_FRAME", "Build a LOG frame for 'OK'", "message=OK, severity=INFO",
                                   "⧆≛TYPE⦙≛LOG∴≛SEVERITY⦙≛INFO ∷ ≛MESSAGE⦙≛OK ⧈", "INTERMEDIATE"))
    # Stage: Tensors
    frames.append(build_task_frame("BUILD_TENSOR", "Make a 2x3 INT_U3 tensor", "shape=[2,3], data=[1..6]", None, "INTERMEDIATE"))
    # Parallel pairs
    frames.append(build_train_pair_frame("The value is 3 meters",
                                         "⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛meter ∷ ≛VALUE⦙≗⊗⊗Φ⊙ ⧈"))
    return frames


def write_curriculum(path: str, frames: List[Frame]) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for fr in frames:
            f.write(fr.serialize())
            f.write('\n')


def build_full_curriculum(total: int = 1000) -> List[Frame]:
    """Build a larger graded curriculum of approximately `total` frames.
    Mix TASK, EXPLAIN, and TRAIN_PAIR across core constructs with comprehensive coverage.
    """
    frames: List[Frame] = []
    # Seed with basic
    frames.extend(build_basic_curriculum())
    
    # INT-U3 tasks - very comprehensive range
    int_u3_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                     25, 30, 35, 40, 42, 50, 60, 70, 80, 90, 100, 128, 150, 200, 255, 256, 300,
                     400, 500, 512, 600, 700, 800, 900, 1000, 1024, 1500, 2000, 2500, 3000, 
                     4096, 5000, 6000, 7000, 8000, 9000, 10000, 15000, 20000, 30000, 50000, 65535]
    for n in int_u3_values:
        frames.append(build_task_frame("ENCODE_INT", f"Encode {n} as INT-U3", str(n), None, "BASIC"))
        # Add explanations for powers of 2 and other significant values
        if n in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]:
            frames.append(build_explain_frame(f"int_u3_power2_{n}", f"Encoding power of 2: {n}", 
                                              [f"Binary: {bin(n)}", "Base-3 representation in INT-U3"]))
    
    # INT-S3 (signed integers) - expanded range
    int_s3_values = [-32768, -10000, -5000, -1000, -500, -256, -255, -128, -100, -50, -42, -20, 
                     -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                     20, 42, 50, 100, 128, 255, 256, 500, 1000, 5000, 10000, 32767]
    for n in int_s3_values:
        frames.append(build_task_frame("ENCODE_SIGNED_INT", f"Encode {n} as INT-S3", str(n), None, "BASIC"))
        if abs(n) <= 10:
            frames.append(build_explain_frame(f"int_s3_{abs(n)}_{'pos' if n>=0 else 'neg'}", 
                                              f"INT-S3 encoding for {n}", 
                                              ["Sign trit: ⊙ for positive, ⊗ for negative", "Magnitude in unsigned base-3"]))
    
    # DECIMAL tasks - comprehensive edge cases
    decimals = ["0.0", "0.1", "0.5", "1.0", "1.5", "2.0", "3.14", "2.718", "0.001", "0.01", "0.1", 
                "0.25", "0.333333", "0.5", "0.75", "0.999", "1.001", "10.5", "99.99", "100.0",
                "123.456", "999.999", "1000.0001", "-0.001", "-0.5", "-1.0", "-3.14", "-7.5", 
                "-10.25", "-99.99", "-123.456", "-999.999", "0.0001", "0.00001", "12345.67890"]
    for d in decimals:
        frames.append(build_task_frame("ENCODE_DECIMAL", f"Encode {d} as DECIMAL-T", d, None, "BASIC"))
    # Add comprehensive DECIMAL-T explanations for key patterns
    for d in ["0.0", "3.14", "0.001", "-7.5", "123.456", "0.333333"]:
        frames.append(build_explain_frame(f"decimal_{d.replace('.','_').replace('-','neg')}_detailed", 
                                          f"DECIMAL-T encoding for {d}", 
                                          ["Scale digit encodes decimal places", "Sign trit ⊙/⊗", "Magnitude in base-3", "Exact decimal representation"]))
    
    # FLOAT-T examples - expanded with various exponents/mantissas
    floats = [
        ("positive", 5, "⊙⊙⊙⊙⊗⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙"),
        ("positive", 10, "⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙Φ⊙⊙⊙⊙⊙⊙⊙⊙⊙"),
        ("positive", 0, "⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙"),
        ("negative", 10, "⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊗"),
        ("negative", -5, "⊗⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙"),
        ("positive", -10, "⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙Φ⊙"),
    ]
    for sign, exp, mant in floats:
        frames.append(build_task_frame("ENCODE_FLOAT", f"Encode FLOAT-T with exp={exp}, mant={mant[:10]}...", 
                                       f"sign={sign},exp={exp},mantissa={mant}", None, "INTERMEDIATE"))
    # Add FLOAT-T explanations
    frames.append(build_explain_frame("float_t_structure", "FLOAT-T structure: sign + exponent + mantissa",
                                      ["1 sign trit (⊙/⊗)", "Variable-length exponent", "20-trit mantissa", "Scientific notation in trinary"]))
    
    # LOG frame tasks - expanded
    logs = [
        ("System initialized", "INFO"),
        ("Configuration loaded", "INFO"),
        ("Connection established", "INFO"),
        ("Processing started", "DEBUG"),
        ("Cache miss", "DEBUG"),
        ("Performance degraded", "WARN"),
        ("High memory usage", "WARN"),
        ("Retry attempt", "WARN"),
        ("Connection failed", "ERROR"),
        ("Disk failure detected", "ERROR"),
        ("Authentication failed", "ERROR"),
        ("System crash", "CRITICAL"),
        ("Security breach", "CRITICAL"),
    ]
    for msg, sev in logs:
        frames.append(build_task_frame("BUILD_FRAME", f"Build LOG({sev}) for '{msg}'",
                                       f"message={msg}, severity={sev}", None, "INTERMEDIATE"))
    # Add LOG explanations for each severity
    for sev in ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]:
        frames.append(build_explain_frame(f"log_severity_{sev.lower()}", f"LOG severity: {sev}", 
                                          [f"SEVERITY={sev}", "MESSAGE field required", "Optional: TIMESTAMP, DETAILS"]))
    
    # Tensor examples - comprehensive shapes
    shapes = [(1, 1), (2, 2), (2, 3), (3, 2), (3, 3), (4, 4), (5, 5), (10, 10), (10, 1), (1, 10), 
              (8, 8), (16, 16), (3, 4), (4, 3), (7, 7), (20, 20), (2, 5), (5, 2)]
    for r, c in shapes:
        frames.append(build_task_frame("BUILD_TENSOR", f"Make a {r}x{c} INT_U3 tensor", 
                                       f"shape=[{r},{c}], data=[1..{r*c}]", None, "INTERMEDIATE"))
        if r == c or (r, c) in [(2, 3), (10, 1), (1, 10), (16, 16)]:
            frames.append(build_explain_frame(f"tensor_{r}x{c}", f"Row-major layout for {r}×{c} tensor", 
                                              [f"DTYPE=INT_U3", "ORDER=ROW_MAJOR", f"Total elements: {r*c}"]))
    
    # MATRIX/VECTOR explanations
    frames.append(build_explain_frame("vector_basics", "Vector frame stores ordered numeric tokens", 
                                      ["TYPE=VECTOR","DTYPE specifies numeric encoding"]))
    frames.append(build_explain_frame("matrix_basics", "Matrix frame stores rows of tokens", 
                                      ["TYPE=MATRIX","DIMENSIONS in header guide payload size"]))
    
    # VECTOR examples - expanded sizes
    for size in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 50, 100]:
        frames.append(build_task_frame("BUILD_VECTOR", f"Build VECTOR of size {size}", 
                                       f"dtype=INT_U3, values=[1..{size}]", None, "INTERMEDIATE"))
    
    # MATRIX examples - expanded dimensions
    for rows in [2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20]:
        frames.append(build_task_frame("BUILD_MATRIX", f"Build {rows}x{rows} MATRIX", 
                                       f"dtype=INT_U3, identity matrix", None, "ADVANCED"))
    
    # Training pairs - very comprehensive NL ↔ ForgeNumerics coverage
    pairs = []
    # Measurements
    pairs.append(("The value is 3 meters", "⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛meter∷≛VALUE⦙≗⊗⊗Φ⊙⧈"))
    pairs.append(("Temperature is 23.5 °C", "⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛celsius∷≛VALUE⦙≗⊗⊗Φ⊙Φ⊗Φ⦙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊗Φ⊙⊙⧈"))
    pairs.append(("Distance: 42 kilometers", "⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛kilometer∷≛VALUE⦙≗⊙⊙⊗⊗Φ⊙⧈"))
    pairs.append(("Mass of 10.5 kilograms", "⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛kilogram∷≛VALUE⦙≗⊗⊗⊗⊙Φ⦙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙Φ⊙⊙⧈"))
    pairs.append(("Time: 60 seconds", "⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛second∷≛VALUE⦙≗⊙⊙Φ⊙Φ⊙⧈"))
    # Vectors
    pairs.append(("Vector of three integers [1,2,3]", "⧆≛TYPE⦙≛VECTOR∴≛DTYPE⦙≛INT_U3∷≗⊙⊙⊙⊗⦙≗⊙⊙⊗⊙⦙≗⊙⊙⊗⊗⧈"))
    pairs.append(("A list with five numbers", "⧆≛TYPE⦙≛VECTOR∴≛DTYPE⦙≛INT_U3∷≗⊙⊙⊙⊗⦙≗⊙⊙⊗⊙⦙≗⊙⊙⊗⊗⦙≗⊙⊙Φ⊙⦙≗⊙⊙Φ⊗⧈"))
    pairs.append(("Sequence [10, 20, 30, 40]", "⧆≛TYPE⦙≛VECTOR∴≛DTYPE⦙≛INT_U3∷≗⊙⊙⊗⊙⊗⦙≗⊙⊙Φ⊗Φ⦙≗⊙⊙Φ⊙⊙⊙⦙≗⊙⊙ΦΦΦ⧈"))
    pairs.append(("Data points [100, 200, 300]", "⧆≛TYPE⦙≛VECTOR∴≛DTYPE⦙≛INT_U3∷≗⊙⊙⊗⊙⊙Φ⊗⦙≗⊙⊙ΦΦΦΦ⊗⦙≗⊙⊗⊙⊗⊙⊙⊙⧈"))
    # Logs
    pairs.append(("Log entry: System started successfully", "⧆≛TYPE⦙≛LOG∴≛SEVERITY⦙≛INFO∷≛MESSAGE⦙≛⟦System started successfully⟧⧈"))
    pairs.append(("Error log: Disk failure detected", "⧆≛TYPE⦙≛LOG∴≛SEVERITY⦙≛ERROR∷≛MESSAGE⦙≛⟦Disk failure detected⟧⧈"))
    pairs.append(("Warning: Memory usage at 85%", "⧆≛TYPE⦙≛LOG∴≛SEVERITY⦙≛WARN∷≛MESSAGE⦙≛⟦Memory usage at 85%⟧⧈"))
    pairs.append(("Debug: Cache hit ratio 0.95", "⧆≛TYPE⦙≛LOG∴≛SEVERITY⦙≛DEBUG∷≛MESSAGE⦙≛⟦Cache hit ratio 0.95⟧⧈"))
    # Knowledge facts
    pairs.append(("Fact: water freezes at 0°C", "⧆≛TYPE⦙≛FACT∷≛SUBJECT⦙≛water⦙≛PREDICATE⦙≛freezes_at⦙≛OBJECT⦙≗⊗⊗⊙⊙⊙⧈"))
    pairs.append(("Knowledge: Earth orbits Sun", "⧆≛TYPE⦙≛FACT∷≛SUBJECT⦙≛Earth⦙≛PREDICATE⦙≛orbits⦙≛OBJECT⦙≛Sun⧈"))
    pairs.append(("Statement: Pi equals 3.14159", "⧆≛TYPE⦙≛FACT∷≛SUBJECT⦙≛Pi⦙≛PREDICATE⦙≛approximately_equals⦙≛OBJECT⦙≗⊗⊗Φ⊗Φ⊗ΦΦΦ⦙⊙⊙⊙⊙⊙⊙⊙⊙Φ⊗Φ⊗Φ⧈"))
    # Tensor descriptions
    pairs.append(("A 2x3 tensor of integers", "⧆≛TYPE⦙≛TENSOR∴≛DTYPE⦙≛INT_U3∴≛ORDER⦙≛ROW_MAJOR∴≛NDIM⦙≗⊙⊙⊗⊙∷≛SHAPE⦙≗⊙⊙⊗⊙⦙≗⊙⊙⊗⊗⦙≛DATA⦙≗⊙⊙⊙⊗⦙≗⊙⊙⊗⊙⦙≗⊙⊙⊗⊗⦙≗⊙⊙Φ⊙⦙≗⊙⊙Φ⊗⦙≗⊙⊙ΦΦ⧈"))
    pairs.append(("3x3 identity matrix", "⧆≛TYPE⦙≛MATRIX∴≛DTYPE⦙≛INT_U3∴≛DIMENSIONS⦙≗⊙⊙⊗⊗⦙≗⊙⊙⊗⊗∷≗⊙⊙⊙⊗⦙≗⊙⊙⊙⊙⦙≗⊙⊙⊙⊙⦙≗⊙⊙⊙⊙⦙≗⊙⊙⊙⊗⦙≗⊙⊙⊙⊙⦙≗⊙⊙⊙⊙⦙≗⊙⊙⊙⊙⦙≗⊙⊙⊙⊗⧈"))
    # Multi-field examples
    pairs.append(("Event at timestamp 1234567890", "⧆≛TYPE⦙≛EVENT∴≛TIMESTAMP⦙≗⊙⊙⊗⊙Φ⊗Φ⊙⊙⊙⊗ΦΦΦ⊙∷≛MESSAGE⦙≛⟦Event occurred⟧⧈"))
    pairs.append(("Configuration: timeout=30, retries=5", "⧆≛TYPE⦙≛CONFIG∷≛timeout⦙≗⊙⊙Φ⊙⊙⊙⦙≛retries⦙≗⊙⊙Φ⊗⧈"))
    # Nested/complex structures
    pairs.append(("Matrix with metadata: 2x2 labeled 'sample'", "⧆≛TYPE⦙≛MATRIX∴≛DTYPE⦙≛INT_U3∴≛DIMENSIONS⦙≗⊙⊙⊗⊙⦙≗⊙⊙⊗⊙∴≛LABEL⦙≛sample∷≗⊙⊙⊙⊗⦙≗⊙⊙⊗⊙⦙≗⊙⊙⊗⊗⦙≗⊙⊙Φ⊙⧈"))
    # Numbers with context
    pairs.append(("Integer value: 42", "⧆≛TYPE⦙≛VALUE∷≛DATA⦙≗⊙⊙⊗⊗Φ⊙⧈"))
    pairs.append(("Decimal number: 3.14159", "⧆≛TYPE⦙≛VALUE∷≛DATA⦙≗⊗⊗Φ⊗Φ⊗ΦΦΦ⦙⊙⊙⊙⊙⊙⊙⊙⊙Φ⊗Φ⊗Φ⧈"))
    # Schema/grammar examples
    pairs.append(("Grammar rule: FRAME ::= START HEADER SEP PAYLOAD END", "⧆≛TYPE⦙≛GRAMMAR∷≛RULE⦙≛FRAME⦙≛DEFINITION⦙≛⟦START HEADER SEP PAYLOAD END⟧⧈"))
    pairs.append(("Schema for LOG: requires TYPE, SEVERITY, MESSAGE", "⧆≛TYPE⦙≛SCHEMA∴≛FOR⦙≛LOG∷≛REQUIRED⦙≛TYPE⦙≛SEVERITY⦙≛MESSAGE⧈"))
    # Task examples
    pairs.append(("Task: encode the number 100", "⧆≛TYPE⦙≛TASK∴≛CATEGORY⦙≛ENCODE_INT∴≛DIFFICULTY⦙≛BASIC∷≛PROMPT⦙≛⟦Encode 100 as INT-U3⟧⦙≛INPUT⦙≛100⧈"))
    pairs.append(("Task: build a vector of 5 elements", "⧆≛TYPE⦙≛TASK∴≛CATEGORY⦙≛BUILD_VECTOR∴≛DIFFICULTY⦙≛INTERMEDIATE∷≛PROMPT⦙≛⟦Build VECTOR of size 5⟧⦙≛INPUT⦙≛⟦dtype=INT_U3, values=[1..5]⟧⧈"))
    # Error examples
    pairs.append(("Error: invalid trit sequence", "⧆≛TYPE⦙≛ERROR∴≛CODE⦙≛INVALID_TRIT∴≛SEVERITY⦙≛ERROR∷≛MESSAGE⦙≛⟦Invalid trit in sequence⟧⧈"))
    pairs.append(("Error: frame not closed", "⧆≛TYPE⦙≛ERROR∴≛CODE⦙≛MISSING_FRAME_END∴≛SEVERITY⦙≛ERROR∷≛MESSAGE⦙≛⟦Missing ⧈ closing marker⟧⧈"))
    # Capability examples
    pairs.append(("Capabilities: supports INT_U3, DECIMAL_T, VECTOR", "⧆≛TYPE⦙≛CAPS∷≛SUPPORTS_INT_U3⦙≛true⦙≛SUPPORTS_DECIMAL_T⦙≛true⦙≛SUPPORTS_VECTOR⦙≛true⧈"))
    pairs.append(("System limits: max tensor 1000x1000", "⧆≛TYPE⦙≛CAPS∷≛MAX_TENSOR_DIM⦙≗⊙⊙⊗⊙⊙Φ⊗⧈"))
    
    for nl, fg in pairs:
        frames.append(build_train_pair_frame(nl, fg))
    
    # Edge cases and error detection - expanded
    frames.append(build_task_frame("DETECT_ERROR", "Identify error in malformed frame", 
                                   "⧆≛TYPE⦙≛LOG∴≛SEVERITY⦙≛INFO ∷ MESSAGE⦙≛test", 
                                   "MISSING_FRAME_END", "ADVANCED"))
    frames.append(build_task_frame("DETECT_ERROR", "Find error: missing separator", 
                                   "⧆≛TYPE⦙≛LOG≛SEVERITY⦙≛INFO∷≛MESSAGE⦙≛test⧈", 
                                   "MISSING_SEPARATOR", "ADVANCED"))
    frames.append(build_task_frame("DETECT_ERROR", "Find error: invalid trit", 
                                   "⧆≛TYPE⦙≛VALUE∷≛DATA⦙≗⊙X⊙⊗⧈", 
                                   "INVALID_TRIT", "ADVANCED"))
    frames.append(build_explain_frame("error_detection", "Common frame errors", 
                                      ["Missing ⧈ closing marker", "Mismatched separators", "Invalid trit sequences"]))
    
    # Capability negotiation - expanded
    frames.append(build_task_frame("BUILD_CAPS", "Declare AI capabilities", 
                                   "supports=[FLOAT_T,DECIMAL_T,TENSOR]", None, "ADVANCED"))
    frames.append(build_task_frame("BUILD_CAPS", "Declare system limits", 
                                   "max_tensor=1000x1000, max_vector=100000", None, "ADVANCED"))
    frames.append(build_explain_frame("caps_negotiation", "Capability frames for protocol handshake", 
                                      ["SUPPORTS_* fields declare features", "Limits set constraints", "Enables graceful degradation"]))
    
    # Dictionary update - expanded
    frames.append(build_task_frame("BUILD_DICT_UPDATE", "Create dictionary update with stats", 
                                   "words=[neuron,synapse], freq=[100,75]", None, "ADVANCED"))
    frames.append(build_task_frame("BUILD_DICT_UPDATE", "Add domain vocabulary", 
                                   "words=[tensor,matrix,vector,scalar], domain=mathematics", None, "ADVANCED"))
    
    # Multi-step tasks
    frames.append(build_task_frame("MULTI_STEP", "Encode, frame, then compress", 
                                   "value=42 -> INT-U3 -> LOG frame -> compress", None, "ADVANCED"))
    frames.append(build_task_frame("MULTI_STEP", "Parse and validate", 
                                   "frame='⧆≛TYPE⦙≛LOG∷≛MESSAGE⦙≛test⧈' -> parse -> validate schema", None, "ADVANCED"))
    
    # Comparison tasks
    frames.append(build_task_frame("COMPARE", "Compare INT-U3 vs INT-S3 for 42", 
                                   "Show both encodings and explain difference", None, "INTERMEDIATE"))
    frames.append(build_task_frame("COMPARE", "Compare DECIMAL-T vs FLOAT-T for 3.14", 
                                   "Explain when to use each", None, "INTERMEDIATE"))
    
    # Conversion tasks
    frames.append(build_task_frame("CONVERT", "Convert binary to INT-U3", 
                                   "0b101010 (42) -> base-3 -> INT-U3", None, "INTERMEDIATE"))
    frames.append(build_task_frame("CONVERT", "Convert decimal to DECIMAL-T", 
                                   "3.14 -> scale + magnitude -> DECIMAL-T", None, "INTERMEDIATE"))
    
    # Validation tasks
    frames.append(build_task_frame("VALIDATE", "Validate LOG frame structure", 
                                   "Check: TYPE=LOG, has SEVERITY, has MESSAGE", None, "INTERMEDIATE"))
    frames.append(build_task_frame("VALIDATE", "Verify tensor dimensions match data", 
                                   "SHAPE=[2,3] should have 6 DATA elements", None, "ADVANCED"))
    
    # Optimization tasks
    frames.append(build_task_frame("OPTIMIZE", "Choose best encoding for 1000000", 
                                   "Compare INT-U3 vs DECIMAL-T vs FLOAT-T size", None, "ADVANCED"))
    
    # Additional BLOB-T examples
    frames.append(build_task_frame("ENCODE_BLOB", "Encode small binary data", 
                                   "bytes=[0x00, 0xFF, 0xAA, 0x55] -> BLOB-T", None, "ADVANCED"))
    frames.append(build_explain_frame("blob_t_encoding", "BLOB-T per-byte encoding", 
                                      ["4-symbol alphabet: ⊙⊗Φ⊛", "Each byte -> 4 trits", "Perfect round-trip bijection"]))
    
    # Additional comprehensive explanations
    frames.append(build_explain_frame("frame_anatomy", "Frame structure breakdown", 
                                      ["⧆ START marker", "HEADER: key-value pairs with ∴ separator", "∷ divides header from payload", "PAYLOAD: content tokens", "⧈ END marker"]))
    frames.append(build_explain_frame("numeric_profiles", "Overview of numeric encoding profiles", 
                                      ["INT-U3: unsigned integers (≗⊙⊙)", "INT-S3: signed integers (≗⊙⊗)", "DECIMAL-T: exact decimals (≗⊗⊗)", "FLOAT-T: floating point (≗⊗⊙)", "BLOB-T: binary data (≗Φ⊙)"]))
    frames.append(build_explain_frame("compression_strategy", "When to compress frames", 
                                      ["Large payloads benefit from gzip/zlib", "BLOB-T data often compresses well", "Small frames: overhead > savings"]))
    
    # Add many more TRAIN_PAIR examples with varied natural language phrasings
    additional_pairs = []
    
    # Numbers with varied phrasing (200 pairs)
    for i in range(0, 200):
        val = i * 5  # 0, 5, 10, 15, ..., 995
        phrasings = [
            f"The number {val}",
            f"Value: {val}",
            f"Integer {val}",
            f"Count of {val}",
            f"{val} items",
        ]
        additional_pairs.append((phrasings[i % len(phrasings)], f"⧆≛TYPE⦙≛VALUE∷≛DATA⦙≗⊙⊙⊙⊗⧈"))  # placeholder
    
    # Vector descriptions with varied sizes (100 pairs)
    for size in [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 40, 50]:
        phrasings = [
            f"A vector with {size} elements",
            f"List of {size} numbers",
            f"Array containing {size} values",
            f"{size}-dimensional vector",
            f"Sequence of {size} integers",
            f"Data array: {size} items",
        ]
        for phrasing in phrasings[:min(6, 100 // 16)]:
            additional_pairs.append((phrasing, f"⧆≛TYPE⦙≛VECTOR∴≛DTYPE⦙≛INT_U3∷≛⟦placeholder⟧⧈"))
    
    # Matrix descriptions (50 pairs)
    for dim in [2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20]:
        phrasings = [
            f"{dim}×{dim} matrix",
            f"Square matrix of size {dim}",
            f"{dim} by {dim} data grid",
            f"2D array: {dim} rows, {dim} columns",
        ]
        for phrasing in phrasings[:min(4, 50 // 11)]:
            additional_pairs.append((phrasing, f"⧆≛TYPE⦙≛MATRIX∴≛DTYPE⦙≛INT_U3∴≛DIMENSIONS⦙≗⊙⊙⊗⊙⦙≗⊙⊙⊗⊙∷≛⟦placeholder⟧⧈"))
    
    # Log messages with varied contexts (100 pairs)
    log_templates = [
        ("started", "INFO"), ("completed", "INFO"), ("initialized", "INFO"), ("ready", "INFO"),
        ("loading", "DEBUG"), ("processing", "DEBUG"), ("parsing", "DEBUG"), ("checking", "DEBUG"),
        ("slow response", "WARN"), ("retry needed", "WARN"), ("deprecated", "WARN"), ("timeout", "WARN"),
        ("failed", "ERROR"), ("crashed", "ERROR"), ("exception", "ERROR"), ("invalid", "ERROR"),
        ("shutdown", "CRITICAL"), ("emergency", "CRITICAL"), ("fatal", "CRITICAL"), ("panic", "CRITICAL"),
    ]
    contexts = ["System", "Database", "Network", "Cache", "API", "Service", "Module", "Component"]
    for ctx in contexts:
        for msg, sev in log_templates[:min(12, 100 // 8)]:
            additional_pairs.append((f"{ctx} {msg}", f"⧆≛TYPE⦙≛LOG∴≛SEVERITY⦙≛{sev}∷≛MESSAGE⦙≛⟦{ctx} {msg}⟧⧈"))
    
    # Measurement descriptions (80 pairs)
    units = [
        ("meter", "m"), ("kilometer", "km"), ("centimeter", "cm"), ("millimeter", "mm"),
        ("gram", "g"), ("kilogram", "kg"), ("second", "s"), ("minute", "min"),
        ("hour", "h"), ("celsius", "°C"), ("fahrenheit", "°F"), ("kelvin", "K"),
        ("pascal", "Pa"), ("joule", "J"), ("watt", "W"), ("volt", "V"),
    ]
    for unit, abbr in units:
        for val in [1, 5, 10, 25, 50]:
            additional_pairs.append((f"{val} {abbr}", f"⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛{unit}∷≛VALUE⦙≗⊙⊙⊙⊗⧈"))
    
    # Fact descriptions (60 pairs)
    fact_templates = [
        ("Earth", "has_radius", "6371"),
        ("Speed_of_light", "equals", "299792458"),
        ("Pi", "approximately", "3.14159"),
        ("Avogadro", "constant", "6.022e23"),
        ("Gravity", "acceleration", "9.8"),
        ("Water", "boils_at", "100"),
        ("Water", "freezes_at", "0"),
        ("Gold", "atomic_number", "79"),
        ("Carbon", "atomic_mass", "12"),
        ("Planck", "constant", "6.626e-34"),
    ]
    for subj, pred, obj in fact_templates:
        for variant in [1, 2, 3, 4, 5, 6]:
            if variant == 1:
                nl = f"Fact: {subj} {pred.replace('_', ' ')} {obj}"
            elif variant == 2:
                nl = f"{subj}: {pred.replace('_', ' ')} is {obj}"
            elif variant == 3:
                nl = f"Knowledge - {subj} {pred.replace('_', ' ')}: {obj}"
            elif variant == 4:
                nl = f"{pred.replace('_', ' ')} of {subj} = {obj}"
            elif variant == 5:
                nl = f"{subj}'s {pred.replace('_', ' ')}: {obj}"
            else:
                nl = f"Statement: {subj} {pred.replace('_', ' ')} {obj}"
            additional_pairs.append((nl, f"⧆≛TYPE⦙≛FACT∷≛SUBJECT⦙≛{subj}⦙≛PREDICATE⦙≛{pred}⦙≛OBJECT⦙≛{obj}⧈"))
    
    # Task descriptions (80 pairs)
    task_cats = ["ENCODE_INT", "ENCODE_SIGNED_INT", "ENCODE_DECIMAL", "ENCODE_FLOAT", "BUILD_VECTOR", "BUILD_MATRIX", "BUILD_TENSOR", "BUILD_FRAME"]
    for cat in task_cats:
        for i in range(10):
            nl = f"Task {i+1}: {cat.lower().replace('_', ' ')}"
            additional_pairs.append((nl, f"⧆≛TYPE⦙≛TASK∴≛CATEGORY⦙≛{cat}∴≛DIFFICULTY⦙≛BASIC∷≛PROMPT⦙≛⟦{nl}⟧⧈"))
    
    # Error scenarios (40 pairs)
    error_codes = ["INVALID_TRIT", "MISSING_FRAME_END", "MISSING_SEPARATOR", "UNKNOWN_TYPE", "INVALID_HEADER"]
    error_contexts = ["parsing", "validation", "encoding", "decoding", "compression", "decompression", "serialization", "deserialization"]
    for code in error_codes:
        for ctx in error_contexts:
            nl = f"Error during {ctx}: {code.lower().replace('_', ' ')}"
            additional_pairs.append((nl, f"⧆≛TYPE⦙≛ERROR∴≛CODE⦙≛{code}∴≛SEVERITY⦙≛ERROR∷≛MESSAGE⦙≛⟦{nl}⟧⧈"))
    
    # Configuration examples (30 pairs)
    config_params = [
        ("timeout", "30"), ("retries", "5"), ("buffer_size", "1024"), 
        ("max_connections", "100"), ("cache_ttl", "3600"), ("log_level", "INFO"),
    ]
    for key, val in config_params:
        for i in range(5):
            nl = f"Config: {key}={val}"
            additional_pairs.append((nl, f"⧆≛TYPE⦙≛CONFIG∷≛{key}⦙≛{val}⧈"))
    
    # Tensor with varied descriptions (50 pairs)
    tensor_shapes = [(2,2), (2,3), (3,2), (3,3), (4,4), (5,5), (10,10), (8,8), (6,6), (7,7)]
    for r, c in tensor_shapes:
        phrasings = [
            f"Tensor shape {r}×{c}",
            f"{r} by {c} tensor",
            f"2D tensor: {r} rows, {c} cols",
            f"Data grid {r}×{c}",
            f"{r}×{c} numeric array",
        ]
        for phrasing in phrasings:
            additional_pairs.append((phrasing, f"⧆≛TYPE⦙≛TENSOR∴≛DTYPE⦙≛INT_U3∴≛ORDER⦙≛ROW_MAJOR∴≛NDIM⦙≗⊙⊙⊗⊙∷≛SHAPE⦙≗⊙⊙⊗⊙⦙≗⊙⊙⊗⊙⦙≛DATA⦙≛⟦placeholder⟧⧈"))
    
    # Schema descriptions (20 pairs)
    schema_types = ["LOG", "VECTOR", "MATRIX", "TENSOR", "FACT", "ERROR", "TASK", "CAPS", "MEASUREMENT", "CONFIG"]
    for stype in schema_types:
        for variant in [1, 2]:
            if variant == 1:
                nl = f"Schema definition for {stype}"
            else:
                nl = f"Structure of {stype} frame"
            additional_pairs.append((nl, f"⧆≛TYPE⦙≛SCHEMA∴≛FOR⦙≛{stype}∷≛REQUIRED⦙≛TYPE⧈"))
    
    # Grammar rule examples (20 pairs)
    rules = [
        ("FRAME", "START HEADER SEP PAYLOAD END"),
        ("HEADER", "KEY_VALUE_PAIRS"),
        ("PAYLOAD", "TOKEN_SEQUENCE"),
        ("NUMERIC", "PROFILE DATA"),
        ("VECTOR", "DTYPE ELEMENTS"),
    ]
    for rule, definition in rules:
        for variant in range(4):
            nl = f"Grammar: {rule} ::= {definition}"
            additional_pairs.append((nl, f"⧆≛TYPE⦙≛GRAMMAR∷≛RULE⦙≛{rule}⦙≛DEFINITION⦙≛⟦{definition}⟧⧈"))
    
    # Capability examples (30 pairs)
    features = ["INT_U3", "INT_S3", "DECIMAL_T", "FLOAT_T", "BLOB_T", "VECTOR", "MATRIX", "TENSOR", "COMPRESSION", "EXTENSION_DICT"]
    for feat in features:
        for variant in range(3):
            if variant == 0:
                nl = f"Supports {feat}"
            elif variant == 1:
                nl = f"Capability: {feat} enabled"
            else:
                nl = f"Feature {feat} available"
            additional_pairs.append((nl, f"⧆≛TYPE⦙≛CAPS∷≛SUPPORTS_{feat}⦙≛true⧈"))
    
    # Add all additional pairs to frames
    for nl, fg in additional_pairs:
        frames.append(build_train_pair_frame(nl, fg))
    
    # Add more algorithmic and transformation tasks
    for i in range(20):
        frames.append(build_task_frame("ALGORITHM", f"Sort vector of {5+i} elements", 
                                       f"input=[random {5+i} values] -> sorted output", None, "ADVANCED"))
    
    for i in range(20):
        frames.append(build_task_frame("TRANSFORM", f"Transpose {2+i//4}×{3+i//4} matrix", 
                                       "swap rows and columns", None, "ADVANCED"))
    
    for i in range(20):
        frames.append(build_task_frame("AGGREGATE", f"Sum vector of {10+i*5} elements", 
                                       "calculate total", None, "INTERMEDIATE"))
    
    # Add frame composition tasks
    for i in range(30):
        frames.append(build_task_frame("COMPOSE", f"Build nested frame structure {i+1}", 
                                       "combine multiple frame types", None, "ADVANCED"))
    
    # Add round-trip verification tasks
    for i in range(20):
        frames.append(build_task_frame("ROUNDTRIP", f"Verify encode/decode cycle {i+1}", 
                                       "ensure lossless transformation", None, "ADVANCED"))
    
    # Trim or pad to desired total
    if len(frames) > total:
        frames = frames[:total]
    return frames


def frames_to_json(frames: List[Frame]) -> List[Dict]:
    """Convert frames to JSON objects for ML ingestion."""
    out: List[Dict] = []
    for fr in frames:
        out.append({
            "header": [{"key": k, "value": v} for (k, v) in fr.header],
            "payload": fr.payload,
            "serialized": fr.serialize(),
        })
    return out


def write_curriculum_json(path: str, frames: List[Frame]) -> None:
    import json, os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = frames_to_json(frames)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    import os
    os.makedirs('out_curriculum', exist_ok=True)
    frames_basic = build_basic_curriculum()
    write_curriculum('out_curriculum/forge_curriculum_basic.txt', frames_basic)
    frames_full = build_full_curriculum(250)
    write_curriculum('out_curriculum/forge_curriculum_full.txt', frames_full)
    write_curriculum_json('out_curriculum/forge_curriculum_full.json', frames_full)
    print(f"Wrote {len(frames_basic)} frames to out_curriculum/forge_curriculum_basic.txt")
    print(f"Wrote {len(frames_full)} frames to out_curriculum/forge_curriculum_full.txt and .json")
