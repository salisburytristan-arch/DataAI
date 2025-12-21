# Meta-Layer Guide: AI-Consumable Features

## Overview

ForgeNumerics-S v2.0 includes a **meta-layer** designed to make the language more learnable and usable for AI systems. This layer provides:

1. **Formal Grammar** (EBNF) for parsing and generation
2. **Self-Describing Schemas** for validation
3. **Introspection Frames** for debugging
4. **Training Task Frames** for curriculum building
5. **Capability Negotiation** for feature discovery
6. **Error Diagnostics** for recovery
7. **Tensor Support** for ML integration
8. **Enhanced Dictionaries** with usage statistics

---

## 1. Formal Grammar (EBNF)

**File:** `ForgeNumerics_Grammar.ebnf`

The complete ForgeNumerics-S syntax is defined in Extended Backus-Naur Form (EBNF). This enables:

- **Strict Parsing:** AI can validate frames against formal rules
- **Valid Generation:** AI can construct guaranteed-valid sequences
- **Auto-Repair:** AI can detect and fix malformed frames

### Example: Grammar-Driven Validation

```python
from pathlib import Path

# Load grammar
grammar_path = Path("ForgeNumerics_Grammar.ebnf")
with open(grammar_path, 'r', encoding='utf-8') as f:
    grammar = f.read()

# Check if a token matches INT_U3 production rule
# INT_U3 = MODE_NUM, SIGN_POS, LENGTH_SELECTOR_SHORT, TRIT_SEQUENCE ;
```

### Self-Referential Storage

The grammar itself can be stored as a ForgeNumerics frame:

```python
from src.meta_frames import build_grammar_frame

grammar_frame = build_grammar_frame(grammar_content, version="2.0")
print(grammar_frame.serialize())
```

Output:
```
⧆≛TYPE⦙≛GRAMMAR∴≛VERSION⦙≛2.0∴≛FORMAT⦙≛EBNF∷≛CONTENT⦙≛⟦...grammar...⟧⧈
```

---

## 2. Schema Frames (TYPE=SCHEMA)

Self-describing schemas define the structure of frame types.

### Example: Define MEASUREMENT Schema

```python
from src.meta_frames import build_schema_frame

fields = [
    {"name": "VALUE", "profile": "FLOAT_T64", "required": "TRUE", 
     "description": "Measured value"},
    {"name": "ERROR", "profile": "FLOAT_T64", "required": "FALSE",
     "description": "Uncertainty"},
    {"name": "UNIT", "profile": "WORD", "required": "TRUE"}
]

schema = build_schema_frame(
    target_type="MEASUREMENT",
    fields=fields,
    description="Physical measurement with uncertainty"
)

print(schema.serialize())
```

**Use Cases:**
- AI validates incoming frames against schema
- Auto-generate parsers from schema definitions
- Negotiate supported schemas between systems

---

## 3. Explain Frames (TYPE=EXPLAIN)

Introspection and debugging commentary.

### Example: Explain a Complex Frame

```python
from src.meta_frames import build_explain_frame

explain = build_explain_frame(
    target_id="matrix_frame_456",
    summary="This frame stores a 100×100 covariance matrix",
    details=[
        "Matrix is symmetric, only upper triangle stored",
        "Values are FLOAT-T64 for numerical precision",
        "Total payload: 5,050 numbers (n(n+1)/2)"
    ]
)
```

**Use Cases:**
- AI explains its encoding decisions
- Debugging why a particular profile was chosen
- Educational commentary for training datasets

---

## 4. Task Frames (TYPE=TASK)

Training curriculum tasks with inputs, outputs, and difficulty ratings.

### Example: Create Encoding Task

```python
from src.meta_frames import build_task_frame

task = build_task_frame(
    task_type="ENCODE_INT",
    instruction="Encode the integer 42 as INT-U3",
    input_data="42",
    expected_output="≗⊙⊙⊗⊗Φ⊙",
    difficulty="BASIC"
)
```

### Example: Multi-Step Task

```python
task = build_task_frame(
    task_type="BUILD_FRAME",
    instruction="Build a LOG frame for the message 'System initialized'",
    input_data="message='System initialized', severity=INFO",
    expected_output="⧆≛TYPE⦙≛LOG∴≛SEVERITY⦙≛INFO∷≛MESSAGE⦙≛System◦initialized⧈",
    difficulty="INTERMEDIATE"
)
```

**Use Cases:**
- Automated training curriculum
- Adaptive difficulty progression
- Validation of AI outputs

---

## 5. Capability Frames (TYPE=CAPS)

Negotiate supported features between systems.

### Example: Declare Capabilities

```python
from src.meta_frames import build_caps_frame
from src.numeric import encode_int_u3

supports = {
    "FLOAT_T": "YES",
    "DECIMAL_T": "YES",
    "BLOB_T": "YES",
    "ENC_AES_GCM": "NO",  # No encryption support
    "COMPRESSION": "YES"
}

limits = {
    "MAX_TENSOR_SIZE": encode_int_u3(10_000_000),
    "MAX_DICT_SIZE": encode_int_u3(100_000)
}

caps = build_caps_frame(supports, limits)
```

**Use Cases:**
- Protocol negotiation at connection time
- Feature detection before sending complex frames
- Graceful degradation when features unavailable

---

## 6. Error Frames (TYPE=ERROR)

Structured error reporting with recovery suggestions.

### Example: Parse Error

```python
from src.meta_frames import build_error_frame

error = build_error_frame(
    error_type="PARSE_ERROR",
    location="token 23 in payload",
    code="MISSING_FRAME_END",
    detail="Expected ⧈, found ⊙ instead",
    suggestion="Add closing frame marker ⧈ at end"
)
```

### Example: Validation Error

```python
error = build_error_frame(
    error_type="VALIDATION_ERROR",
    location="MATRIX frame header",
    code="DIMENSION_MISMATCH",
    detail="ROWS=3, COLS=4, but payload has 10 values (expected 12)",
    suggestion="Add 2 more values or fix dimensions"
)
```

**Use Cases:**
- AI learns from errors and self-corrects
- Debugging malformed frames
- Automated repair suggestions

---

## 7. Tensor Frames (TYPE=TENSOR)

ML-friendly multidimensional arrays.

### Example: 2D Tensor

```python
from src.meta_frames import build_tensor_frame
from src.numeric import encode_int_u3, encode_float_t

# 2×3 matrix of floats
shape = [2, 3]
data = [encode_float_t(x) for x in [1.5, 2.7, 3.1, 4.0, 5.2, 6.8]]

tensor = build_tensor_frame(
    dtype="FLOAT_T64",
    shape=shape,
    data_tokens=data,
    order="ROW_MAJOR"
)
```

### Example: 3D Tensor (RGB Image)

```python
# 256×256 RGB image (height × width × channels)
shape = [256, 256, 3]
# Flatten in row-major order: R₀₀, G₀₀, B₀₀, R₀₁, G₀₁, B₀₁, ...
data = [encode_int_u3(pixel) for pixel in flattened_rgb_values]

tensor = build_tensor_frame(
    dtype="INT_U3",
    shape=shape,
    data_tokens=data,
    order="ROW_MAJOR"
)
```

**Use Cases:**
- Neural network weights and activations
- Image/video data
- Scientific simulation outputs

---

## 8. Enhanced Dictionary Updates

Extension dictionaries with usage statistics.

### Example: DICT_UPDATE with Statistics

```python
from src.meta_frames import build_dict_update_enhanced

pairs = [
    ("megafauna", "Ωζ"),
    ("hypernode", "Ψχ"),
    ("eigenvalue", "Λμ")
]

stats = [
    {"freq": 142, "source": "WIKIPEDIA"},
    {"freq": 89, "source": "ARXIV"},
    {"freq": 256, "source": "TEXTBOOK"}
]

dict_update = build_dict_update_enhanced(
    extdict_id="EXTDICT_ML_0001",
    pairs=pairs,
    stats=stats
)
```

### Dictionary Policy

```python
from src.meta_frames import build_dict_policy_frame

policy = build_dict_policy_frame(
    min_frequency=10,  # Only allocate words seen 10+ times
    allowed_domains=["TRAINING", "LOGS", "KB"],
    max_growth_per_day=1000
)
```

**Use Cases:**
- Prune low-frequency allocations
- Domain-specific dictionaries (medical, legal, technical)
- Adaptive vocabulary based on corpus statistics

---

## 9. Training Pairs (TYPE=TRAIN_PAIR)

Parallel natural language ↔ ForgeNumerics corpus.

### Example: Translation Pair

```python
from src.meta_frames import build_train_pair_frame

pair = build_train_pair_frame(
    natural_language="The temperature is 23.5 degrees Celsius",
    forgenumerics_frame="⧆≛TYPE⦙≛MEASUREMENT∴≛UNIT⦙≛celsius∷≛VALUE⦙≗⊗⊗Φ⊙⊗Φ⊙◦⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊙⊗Φ⊙⊙⊙⊙⧈"
)
```

### Building a Training Corpus

```python
# Create many pairs covering different constructs
pairs = [
    ("Encode 42", "≗⊙⊙⊗⊗Φ⊙"),
    ("List of [1, 2, 3]", "⧆≛TYPE⦙≛VECTOR∴≛DTYPE⦙≛INT_U3∷≗⊙⊙⊙⊗◦≗⊙⊙⊗⊙◦≗⊙⊙⊗⊗⧈"),
    # ... hundreds more
]

corpus_frames = [build_train_pair_frame(nl, fg) for nl, fg in pairs]
```

**Use Cases:**
- Train sequence-to-sequence models
- Fine-tune LLMs on ForgeNumerics
- Validate AI understanding with held-out test pairs

---

## Complete Workflow Example

### AI Training Pipeline

```python
from pathlib import Path
from src.meta_frames import *
from src.training_examples import *

# Step 1: Load grammar
grammar_path = Path("ForgeNumerics_Grammar.ebnf")
with open(grammar_path) as f:
    grammar = f.read()

grammar_frame = build_grammar_frame(grammar)

# Step 2: Define schemas
measurement_schema = build_schema_frame(
    "MEASUREMENT",
    [
        {"name": "VALUE", "profile": "FLOAT_T64", "required": "TRUE"},
        {"name": "UNIT", "profile": "WORD", "required": "TRUE"}
    ]
)

# Step 3: Create training tasks
tasks = [
    build_task_frame("ENCODE_INT", "Encode 42", "42", "≗⊙⊙⊗⊗Φ⊙", "BASIC"),
    build_task_frame("BUILD_FRAME", "Make VECTOR of [1,2,3]", ..., ..., "INTERMEDIATE"),
    # ... more tasks
]

# Step 4: Negotiate capabilities
caps = build_caps_frame(
    {"FLOAT_T": "YES", "TENSOR": "YES"},
    {"MAX_TENSOR_SIZE": encode_int_u3(1000000)}
)

# Step 5: Train AI, collect errors
try:
    # AI attempts task
    result = ai_encode_function("42")
except Exception as e:
    error = build_error_frame(
        "EXECUTION_ERROR",
        "task_42_encoding",
        "INVALID_OUTPUT",
        str(e),
        "Review INT-U3 encoding rules"
    )

# Step 6: Build parallel corpus
train_pairs = [
    build_train_pair_frame("The value is 3.14", "⧆...⧈"),
    # ... thousands more
]
```

---

## Best Practices

### For AI Systems Learning ForgeNumerics

1. **Start with Grammar**: Parse EBNF to understand syntax rules
2. **Use Task Frames**: Progress from BASIC → INTERMEDIATE → ADVANCED
3. **Validate with Schemas**: Check output frames against SCHEMA definitions
4. **Introspect with EXPLAIN**: Generate commentary for your encoding decisions
5. **Handle Errors Gracefully**: Parse ERROR frames and apply suggestions
6. **Negotiate Capabilities**: Check CAPS before using advanced features

### For Humans Building Training Data

1. **Define Schemas First**: Document frame types before creating instances
2. **Build Task Sequences**: Order tasks by difficulty and dependencies
3. **Annotate with EXPLAIN**: Add reasoning for complex encodings
4. **Track Statistics**: Use enhanced DICT_UPDATE to prioritize common terms
5. **Create Balanced Corpora**: Mix simple and complex examples in TRAIN_PAIR datasets

---

## CLI Integration

```bash
# Build a schema frame
python -m src.cli build-schema MEASUREMENT measurement_fields.json

# Create a training task
python -m src.cli build-task ENCODE_INT "Encode 42 as INT-U3" --difficulty BASIC

# Generate capability declaration
python -m src.cli build-caps --supports FLOAT_T,DECIMAL_T --limit MAX_TENSOR_SIZE=1000000

# Wrap grammar as frame
python -m src.cli build-grammar-frame ForgeNumerics_Grammar.ebnf
```

---

## Testing

Run meta-frame tests:

```bash
python tests/test_meta_frames.py
```

Expected output:
```
=== Meta-Frame Tests ===

✓ test_grammar_frame
✓ test_schema_frame
✓ test_explain_frame
✓ test_task_frame
✓ test_caps_frame
✓ test_error_frame
✓ test_tensor_frame
✓ test_dict_update_enhanced
✓ test_train_pair_frame
✓ test_dict_policy_frame
✓ test_grammar_frame_self_describing

All meta-frame tests passed!
```

---

## Summary

The meta-layer transforms ForgeNumerics-S from a compact encoding format into a **self-documenting, AI-learnable language** with:

- ✅ Formal grammar for strict validation
- ✅ Self-describing schemas
- ✅ Introspection and debugging support
- ✅ Structured training curricula
- ✅ Capability negotiation
- ✅ Error recovery mechanisms
- ✅ ML-native tensor support
- ✅ Usage-driven dynamic dictionaries

This makes ForgeNumerics-S suitable for:
- AI training datasets
- Protocol negotiation
- Self-validating data pipelines
- Scientific data archival
- ML model interchange formats
