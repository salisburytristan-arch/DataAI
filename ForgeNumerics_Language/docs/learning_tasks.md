# Learning Tasks (ForgeNumerics-S v2)

This document provides a staged curriculum for learning ForgeNumerics-S using the CLI and code in `src/`.

## Stage 1 — Trit Basics & INT-U3

**Goal**: Master the fundamental trinary alphabet and unsigned integer encoding.

**Topics**:
- Map ⊙⊗Φ ↔ 0/1/2
- Encode/decode integers (0–100+)
- Understand base-3 conversion
- Detect malformed tokens

**CLI Practice**:

```powershell
python -m src.cli practice-int-u3 --value 42
python -m src.cli practice-int-u3 --value 75
python -m src.cli practice-int-u3 --value 0
```

**Expected Output**: Encoded token (≗⊙⊙...) and decoded integer match

## Stage 2 — INT-S3 (Signed Integers)

**Goal**: Understand sign encoding and signed integer representation.

**Topics**:
- Sign trit (⊙ positive, ⊗ negative)
- Magnitude encoding
- Positive and negative number handling

**CLI Practice**:

```powershell
python -m src.cli practice-int-s3 --value -14
python -m src.cli practice-int-s3 --value 42
python -m src.cli practice-int-s3 --value 0
```

**Expected Output**: Token with sign trit (≗⊙⊗◦...◽...) and correct decoded value

## Stage 3 — Exact Decimals (DECIMAL-T)

**Goal**: Master exact decimal representation for financial/precision values.

**Topics**:
- Sign, scale, and integer components
- 10^(-scale) scaling
- Human-readable value computation

**CLI Practice**:

```powershell
# Encode 12.34 (sign positive, scale 2, integer 1234)
python -m src.cli practice-decimal-t --sign-positive --scale 2 --integer 1234

# Encode -0.005 (sign negative, scale 3, integer 5)
python -m src.cli practice-decimal-t --scale 3 --integer 5
```

**Expected Output**: Encoded token and decoded tuple, plus human value (e.g., 12.34)

## Stage 4 — Floating Point (FLOAT-T)

**Goal**: Understand trinary floating-point approximation.

**Topics**:
- Sign, exponent, mantissa structure
- Base-3 exponentiation
- Approximate value calculation

**CLI Practice**:

```powershell
# Simple float with positive sign, exponent 3, mantissa "⊗Φ⊙⊙"
python -m src.cli practice-float-t --sign-positive --exponent 3 --mantissa "⊗Φ⊙⊙"
```

**Expected Output**: Encoded token, decoded components, approximate numeric value

## Stage 5 — Frames & Headers

**Goal**: Build and parse structured frames with headers.

**Topics**:
- Frame structure (⧆ HEADER ∷ PAYLOAD ⧈)
- Header fields (TYPE, DICT, VER, UNIT, etc.)
- Measurement frames with DECIMAL-T values

**CLI Practice**:

```powershell
# Build a measurement frame (15.0 meters)
python -m src.cli practice-frame-measurement --unit meter --sign-positive --scale 1 --integer 150
```

**Expected Output**: Serialized frame with header and payload, parsed result

## Stage 6 — Advanced Schemas

**Goal**: Work with VECTOR, MATRIX, LOG, and FACT frames.

### 6.1 VECTOR Frames

**Topics**: Numeric sequences, length encoding

**CLI Practice**:

```powershell
python -m src.cli practice-vector --values "≗⊙⊙⊗" "≗⊙⊙Φ" "≗⊙⊙⊙"
```

### 6.2 MATRIX Frames

**Topics**: 2D numeric data, row/column structure

**CLI Practice**:

```powershell
python -m src.cli practice-matrix --rows '[["≗⊙⊙⊗","≗⊙⊙Φ"],["≗⊙⊙⊙","≗⊙⊙⊗"]]'
```

### 6.3 LOG Frames

**Topics**: Telemetry, severity levels, timestamps

**CLI Practice**:

```powershell
python -m src.cli practice-log --severity INFO --message "≛System_started"
python -m src.cli practice-log --severity ERROR --message "≛Connection_failed" --details "≛⟦Timeout after 30s⟧"
```

### 6.4 FACT Frames

**Topics**: Knowledge triples (subject-predicate-object)

**CLI Practice**:

```powershell
python -m src.cli practice-fact --subject "≛Einstein" --predicate "≛born_in" --object "≛Ulm"
```

## Stage 7 — BLOB-T & Compression

**Goal**: Compress files and encode as BLOB-T tokens.

**Topics**:
- Byte to trit conversion (4-symbol alphabet)
- Gzip and zlib compression
- COMPRESSED frame generation
- Compression ratio measurement

**CLI Practice**:

```powershell
# Compress a text file
python -m src.cli compress-file --file .\Compaction_Test.txt --out-dir out

# Decompress BLOB-T back to original
python -m src.cli decompress-file --blob-t .\out\Compaction_Test.blob_t.gzip.txt --codec gzip --out-dir out_decomp
```

**Expected Output**: Compressed files, BLOB-T tokens, compression ratios, decompressed file matching original

## Stage 8 — Extension Dictionaries (Part 14)

**Goal**: Dynamically allocate new words using free symbol combos.

**Topics**:
- Free combo enumeration (~750k available)
- Word allocation policy
- EXTDICT persistence
- DICT_UPDATE frame generation

**CLI Practice**:

```powershell
# List available free symbol combos
python -m src.cli list-free-combos --limit 50

# Allocate a new word
python -m src.cli allocate-word --word megafauna --extdict EXTDICT_TEST_0001

# View extension dictionary
python -m src.cli show-extdict --extdict EXTDICT_TEST_0001

# Generate DICT_UPDATE frame
python -m src.cli generate-dict-update --extdict EXTDICT_TEST_0001
```

**Expected Output**: 
- List of free combos
- Successful allocation message with combo
- Dictionary contents with word→combo mappings
- DICT_UPDATE frame showing allocations

## Stage 9 — Integration & Reasoning

**Goal**: Combine all components for real-world use cases.

**Tasks**:
- Build multi-frame documents with mixed schemas
- Compress and encrypt composite structures
- Reason about encrypted payloads (metadata only)
- Manage multiple extension dictionaries
- Build knowledge bases with FACT frames
- Log analysis with structured LOG frames

## Advanced Topics

- **Error Correction**: Add parity/ECC to BLOB-T (using reserved bit-pair 11 semantically)
- **Complex Numbers**: Design new numeric profile (e.g., ≗Φ⊗)
- **Nested Frames**: Build hierarchical structures
- **Streaming**: Process large datasets incrementally
- **Optimization**: Profile encoding/decoding performance
- **Custom Profiles**: Extend numeric profiles for domain-specific data

## Testing Checklist

For each stage, verify:
- [ ] Encoding produces valid tokens
- [ ] Decoding returns original values
- [ ] Round-trip preserves data perfectly
- [ ] Error cases handled gracefully
- [ ] CLI output matches expectations
- [ ] Frame structure follows spec
- [ ] Headers contain required fields
- [ ] Payloads parse correctly
