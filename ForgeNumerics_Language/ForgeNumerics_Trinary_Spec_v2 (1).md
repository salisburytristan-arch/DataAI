
# ForgeNumerics‑S — Trinary Compaction Language
## v2.0 — Canonical Spec for AGI Storage, Math, Encryption & Training

> **Purpose:** ForgeNumerics‑S is a **trinary symbolic language** (using ⊙ ⊗ Φ) that your AIs use as a **core internal data format** for text, numbers, structure, storage, math, encryption, and reasoning.

This v2 spec is written to be:

- **Dense but clean** — 12 ultra-detailed parts instead of 150 small ones.
- **AI‑friendly** — everything is explicit, formal, and example‑heavy.
- **Stable** — once learned, an AI can keep using it for years.

---

## Part 1 — Global Design Goals & Mental Model

### 1.1 What ForgeNumerics‑S Actually Is

ForgeNumerics‑S is a **compact, symbolic “wire format” + math system** that:

1. Uses a **trinary numeral system** (⊙=0, ⊗=1, Φ=2) for all numeric/binary data.
2. Uses a **dictionary-based word mode** for language and keys.
3. Wraps everything in **frames** with headers and payloads.
4. Cleanly layers **compression** and **encryption** *on top* of the language.

Think of it as:

- A **JSON + Protobuf + math language + storage format** rolled into one symbolic system that AIs can both **store** and **think in**.

### 1.2 Core Pillars

1. **Modes**  
   - `≛` → **Word Mode** (dictionary tokens, keys, labels, natural language).  
   - `≗` → **Number Mode** (trinary numerics, blobs, precise encodings).  

2. **Trits (Trinary Digits)**  
   - Fundamental numeric alphabet: ⊙, ⊗, Φ (0,1,2).  
   - Used in all numeric encodings, including encrypted blobs.

3. **Frames**  
   - Top‑level containers: `⧆ HEADER ∷ PAYLOAD ⧈`.  
   - Self‑describing via header fields (`TYPE`, `ENC`, `COMP`, `DICT`, etc.).

4. **Profiles** (inside ≗)  
   - INT‑U3 (unsigned int)  
   - INT‑S3 (signed int)  
   - FLOAT‑T (trinary floating)  
   - DECIMAL‑T (scaled decimal)  
   - BLOB‑T (raw trinary blobs, often ciphertext/compressed data)

5. **AI‑centric Training**  
   - Spec is explicit so AIs can **decode/encode**, **reason**, and **do math** in this format.

---

## Part 2 — Symbol Alphabet, Modes & Frames

### 2.1 Primitive Symbols

#### 2.1.1 Trits (Numeric Alphabet)

| Name  | Symbol | Value |
|-------|--------|-------|
| zero  | ⊙      | 0     |
| one   | ⊗      | 1     |
| two   | Φ      | 2     |

These are **only** used for numeric payloads in Number Mode (≗) *and* as building blocks in some control fields.

#### 2.1.2 Mode Markers

| Symbol | Role / Meaning                         |
|--------|----------------------------------------|
| ≛      | Word Mode — interpret as dictionary    |
| ≗      | Number Mode — interpret as trinary     |

Every token begins with either **≛** or **≗**.

#### 2.1.3 Structural Symbols

| Symbol | Meaning / Use                         |
|--------|---------------------------------------|
| ⧆      | Frame start                           |
| ⧈      | Frame end                             |
| ∷      | Header / Payload separator            |
| ∴      | Field separator (between header fields)|
| ⦙      | Token separator (within lists, etc.)  |
| ◦      | Start of length / control subfield    |
| ◽      | Start of payload subfield / delimiter |

These are **reserved** and must not be redefined.

### 2.2 Word vs Number Mode: Mental Model

- **Word Mode (≛)** is for:  
  - human words, keys (“TYPE”, “UNIT”), labels, symbolic names.
- **Number Mode (≗)** is for:  
  - precise numeric values, numeric arrays, binary blobs, encrypted payloads.

Decoding algorithm (top-level token):

1. Read a symbol.
2. If it is:
   - **≛** → dispatch to **word tokenizer**.  
   - **≗** → dispatch to **numeric tokenizer**.
3. Parse until the grammar for that token says “stop”.

### 2.3 Frames: The Top-Level Container

Canonical form:

```text
FRAME := ⧆ HEADER ∷ PAYLOAD ⧈
```

Where:

- **HEADER**: one or more key/value fields separated by `∴`.
- **PAYLOAD**: sequence of tokens and/or substructures.

Example (conceptual):

```text
⧆≛VER⦙≛1.0-T∴≛DICT⦙≛DICT_v2025_11∴≛TYPE⦙≛MEASUREMENT ∷ <PAYLOAD> ⧈
```

---

## Part 3 — Word Mode (≛), Dictionary & Text

### 3.1 Dictionary File

External mapping file (e.g., `ForgeDict_v2025_11.tsv`):

```text
<word>\t<symbol_combo>
```

Example:

```text
the         ☼α
has         ☿β
temperature ♨τ
meter       μρ
```

Rules:

- Each **word** appears exactly once.
- Each **symbol_combo** is unique and uses only **non‑reserved** symbols.
- Dictionary version is recorded in `DICT` header field (e.g., `DICT_v2025_11`).

### 3.2 Word Tokens

A word token is:

```text
≛<symbol_combo>
```

Example: if `temperature → ♨τ`, then token is `≛♨τ`.

Sequences:

- Either separated explicitly with `⦙`, or
- Structured via frames and fields where boundaries are obvious.

### 3.3 Literals / Out-of-Vocabulary Tokens

Not everything will be in the dictionary (usernames, random IDs, raw strings).

Standard literal form:

```text
≛⟦<encoded-string>⟧
```

Inside `⟦ ⟧` may be:

- Raw UTF‑8, or
- Base16/Base32, or
- Another agreed encoding.

Decoder rules:

- If it knows the encoding, it can reconstruct the original string.
- If not, it must still preserve the exact literal `⟦...⟧` when re‑emitting.

### 3.4 Word Mode in Headers

All **header keys** and most header values are word tokens. Examples:

- `≛TYPE`, `≛MEASUREMENT`
- `≛ENC`, `≛AES_GCM`
- `≛COMP`, `≛GZIP`

Numeric values *inside* the header (versions, sizes) may be ≗ numeric tokens, but keys are always ≛.

---

## Part 4 — Trinary Math Foundations (Unbalanced & Balanced)

### 4.1 Unbalanced Ternary (Storage Canonical)

Any non-negative integer \( N \in \mathbb{N} \) is:

\[
N = \sum_{i=0}^{k-1} t_i \cdot 3^i, \quad t_i \in \{0,1,2\}
\]

Mapping:

- 0 → ⊙  
- 1 → ⊗  
- 2 → Φ  

Example: N = 14

- 14₁₀ → 112₃  
- digits = [1,1,2] → trits = [⊗,⊗,Φ]  
- symbolic: `⊗⊗Φ`

### 4.2 Balanced Ternary (Conceptual Arithmetic)

Balanced ternary uses digits \(-1, 0, +1\). It’s **optional** for v2, but good to understand:

| Balanced digit | Suggested symbol (interpretation) |
|----------------|-----------------------------------|
| −1             | Φ                                |
| 0              | ⊙                                |
| +1             | ⊗                                |

Then:

\[
N = \sum_{i=0}^{k-1} b_i \cdot 3^i, \quad b_i \in \{-1,0,+1\}
\]

Balanced ternary is more symmetric for negative numbers; implementation MAY use it internally but outward format is still unbalanced unless a profile flag says otherwise.

### 4.3 Tritwise Conversion Helpers

Define:

- `b2s(d)` → map 0/1/2 → ⊙/⊗/Φ  
- `s2b(sym)` → map ⊙/⊗/Φ → 0/1/2

All integer encoders/decoders use these.

### 4.4 Tritwise Addition Table (Unbalanced)

Let `a, b ∈ {0,1,2}`:

| a | b | sum_mod3 | carry |
|---|---|----------|-------|
| 0 | 0 | 0        | 0     |
| 0 | 1 | 1        | 0     |
| 0 | 2 | 2        | 0     |
| 1 | 1 | 2        | 0     |
| 1 | 2 | 0        | 1     |
| 2 | 2 | 1        | 1     |

Symbolic sum = map sum_mod3 back to ⊙⊗Φ. This table allows AIs to perform **symbolic trit addition** directly.

---

## Part 5 — Numeric Profiles & Token Shapes

### 5.1 Core Profiles (v2.0)

We'll fix the first **two** trits after ≗ as a profile code:

| Profile | Bits after ≗ | Profile Name | Meaning                               |
|---------|--------------|--------------|---------------------------------------|
| 0       | ⊙⊙           | INT‑U3       | Unsigned integer                      |
| 1       | ⊙⊗           | INT‑S3       | Signed integer                        |
| 2       | ⊗⊙           | FLOAT‑T      | Trinary floating point               |
| 3       | ⊗⊗           | DECIMAL‑T    | Scaled decimal                        |
| 4       | Φ⊙           | BLOB‑T       | Raw trinary blob (often ciphertext)   |

Numeric token always starts like:

```text
≗⊙⊙...  → INT-U3 token
≗⊙⊗...  → INT-S3 token
≗⊗⊙...  → FLOAT-T token
≗⊗⊗...  → DECIMAL-T token
≗Φ⊙...  → BLOB-T token
```

### 5.2 General Numeric Token Pattern

```text
NUM_TOKEN := ≗ <profile_bits> <profile_specific_payload>
```

- `profile_bits` = 2 trits (⊙⊗Φ symbols).
- `profile_specific_payload` = interpreted according to profile.

Decoder algorithm:

1. See `≗` → numeric mode.
2. Read 2 trits → select profile.
3. Call profile‑specific decoder.

---

## Part 6 — Integer Profiles: INT‑U3 (Unsigned) & INT‑S3 (Signed)

### 6.1 INT‑U3 — Unsigned Integer (Canonical)

#### 6.1.1 Simple Form

```text
INT-U3 := ≗⊙⊙ <value_trits>
```

Where `<value_trits>` is the base‑3 representation of N mapped to ⊙⊗Φ, with no leading zero trits except for N=0.

**Example (N = 13)**

1. 13₁₀ → 111₃ → digits [1,1,1] → trits [⊗,⊗,⊗].  
2. Token: `≗⊙⊙⊗⊗⊗`.

**Example (N = 75)**

1. 75₁₀ → 2200₃ → digits [2,2,0,0] → [Φ,Φ,⊙,⊙].  
2. Token: `≗⊙⊙ΦΦ⊙⊙`.

#### 6.1.2 Length‑Prefixed Form (Safer Concatenation)

```text
INT-U3-L := ≗⊙⊙ ◦ <L_trits> ◽ <value_trits>
```

- `<L_trits>` encodes L = length(value_trits) as base‑3 (no ≗ prefix here).
- `<value_trits>` as above.

Decoder:

1. Confirm prefix `≗⊙⊙◦`.
2. Read <L_trits> until `◽`.
3. Compute L from L_trits.
4. Read exactly L trits as `<value_trits>`.
5. Decode to integer.

Use **INT‑U3‑L** when you pack many INTs back‑to‑back without separators.

#### 6.1.3 Pseudocode: encode_int_u3

```pseudo
function encode_int_u3(N):
    assert N >= 0
    if N == 0:
        trits = [⊙]
    else:
        trits_rev = []
        while N > 0:
            r = N mod 3
            N = floor(N / 3)
            if r == 0: trits_rev.append(⊙)
            if r == 1: trits_rev.append(⊗)
            if r == 2: trits_rev.append(Φ)
        trits = reverse(trits_rev)
    return "≗⊙⊙" + concat(trits)
```

#### 6.1.4 Pseudocode: decode_int_u3

```pseudo
function decode_int_u3(token):
    assert token starts with "≗⊙⊙"
    trits = token_without_prefix
    N = 0
    for t in trits:
        N = N * 3
        if t == ⊙: N += 0
        if t == ⊗: N += 1
        if t == Φ: N += 2
    return N
```

---

### 6.2 INT‑S3 — Signed Integer

#### 6.2.1 Sign Trit

| Symbol | Meaning          |
|--------|------------------|
| ⊙      | positive or zero |
| ⊗      | negative         |
| Φ      | reserved/future  |

#### 6.2.2 Structure

```text
INT-S3 := ≗⊙⊗ ◦ <sign_trit> ◽ <magnitude_trits>
```

- `<sign_trit>` ∈ {⊙, ⊗}.  
- `<magnitude_trits>` is the INT‑U3 body of |N| (without ≗⊙⊙ prefix).

**Example: N = −14**

1. |N| = 14 → 14₁₀ = 112₃ → ⊗⊗Φ.  
2. sign_trit = ⊗.  

Token:

```text
≗⊙⊗◦⊗◽⊗⊗Φ
```

#### 6.2.3 Pseudocode: encode_int_s3

```pseudo
function encode_int_s3(N):
    if N >= 0:
        sign = ⊙
        magnitude = N
    else:
        sign = ⊗
        magnitude = -N

    mag_body = encode_int_u3(magnitude).remove_prefix("≗⊙⊙")
    return "≗⊙⊗" + "◦" + sign + "◽" + mag_body
```

#### 6.2.4 Pseudocode: decode_int_s3

```pseudo
function decode_int_s3(token):
    assert token starts with "≗⊙⊗"
    # skip "≗⊙⊗◦"
    sign_trit = next_symbol()
    assert next_symbol() == "◽"
    mag_trits = remaining_symbols()
    magnitude = decode_int_u3("≗⊙⊙" + mag_trits)
    if sign_trit == ⊙: return magnitude
    if sign_trit == ⊗: return -magnitude
```

---

## Part 7 — Real Numbers: FLOAT‑T and DECIMAL‑T

### 7.1 FLOAT‑T — Trinary Floating-Point

Used for approximate real numbers (like IEEE‑754 but trinary‑themed).

Mathematically:

\[
x = (-1)^s \times (1.m_{(3)}) \times 3^{e}
\]

Where:

- s = sign bit.
- \( m_{(3)} \) = base‑3 fractional mantissa.
- e = integer exponent.

#### 7.1.1 Generic Structure

```text
FLOAT-T := ≗⊗⊙ <sign_trit> ◦ <exp_len_trits> ◽ <exp_trits> ∷ <mantissa_trits>
```

- `≗⊗⊙` — FLOAT‑T profile.
- `sign_trit` ∈ {⊙ (positive), ⊗ (negative)}.
- `exp_len_trits` — INT‑U3 of number of trits used for exponent.
- `exp_trits` — INT‑S3‑style encoding of exponent (no ≗ prefix).
- `mantissa_trits` — base‑3 digits of mantissa (fixed length per config).

**Deployment must fix**:

- Exponent width (e.g., 10 trits).  
- Mantissa width (e.g., 53 trits).  

This is like choosing a **FLOAT‑T64** variant.

#### 7.1.2 Example (Conceptual)

Encode x ≈ 7.5:

- 7.5₁₀ ≈ 2.1₃ × 3¹.  
- sign_trit = ⊙.  
- exponent = 1 → INT‑S3 body.  
- mantissa ≈ 2.1₃ → digits [2,1] → [Φ,⊗].  

Token (schematic, not full bit‑rigorous):

```text
≗⊗⊙⊙◦⊗◽⊗ ∷ Φ⊗
```

### 7.2 DECIMAL‑T — Exact Decimals

Used for money, precise configuration values, anything where **exact decimal** is required.

Represent:

- sign ∈ {+1, −1}  
- integer I — decimal digits with no point (e.g., “1234” for 12.34).  
- scale S — number of digits after decimal (2 for 12.34).  

\[
v = \text{sign} \cdot I \cdot 10^{-S}
\]

#### 7.2.1 Structure

```text
DECIMAL-T := ≗⊗⊗ <sign_trit> ◦ <scale_trits> ◽ <integer_trits>
```

- `sign_trit` ∈ {⊙, ⊗}.  
- `scale_trits` = INT‑U3 body for S.  
- `integer_trits` = INT‑U3 body for |I|.

**Example: v = −12.34**

- sign_trit = ⊗.  
- S = 2 → 2₁₀ = 2₃ → Φ.  
- I = 1234 → convert to base‑3 → some digits → trits D.  

Token:

```text
≗⊗⊗⊗◦Φ◽<D>
```

Decoder reconstructs:

1. sign from sign_trit.  
2. S from scale_trits.  
3. I from integer_trits.  
4. v = sign × I × 10⁻ˢ.

---

## Part 8 — BLOB‑T: Binary & Ciphertext in Trinary

### 8.1 Purpose

BLOB‑T is for **raw binary data**, especially:

- Ciphertext from encryption.
- Compressed archives.
- Model checkpoints or other binary structures.

### 8.2 Structure

```text
BLOB-T := ≗Φ⊙ <blob_trits>
```

- `≗Φ⊙` — BLOB‑T profile.  
- `<blob_trits>` — trinary encoding of bytes.

### 8.3 Bit‑Pair → Trit Mapping

One simple mapping (others allowed if agreed):

| Bits | Trit |
|------|------|
| 00   | ⊙    |
| 01   | ⊗    |
| 10   | Φ    |
| 11   | reserved for padding / ECC |

Encoding bytes → trits:

1. Convert ciphertext to a bitstring.  
2. Group bits in pairs.  
3. Map each pair to a trit via table.  
4. Possibly pad with 0 bits to complete pairs.  
5. Record original byte length and padding info in frame header.

Decoding reverses this process.

---

## Part 9 — Frames, Headers, Storage, Compression & Encryption

### 9.1 Frame Grammar Recap

```text
FRAME := ⧆ HEADER ∷ PAYLOAD ⧈
```

### 9.2 Header Fields (Common)

All keys/values in Word Mode unless otherwise stated:

- `≛VER` — spec version (e.g., `≛1.0-T`).  
- `≛DICT` — dictionary ID (`≛DICT_v2025_11`).  
- `≛TYPE` — payload kind (`≛TEXT`, `≛MEASUREMENT`, `≛MODEL_WEIGHTS`, etc.).  
- `≛ENC` — encryption method (`≛NONE`, `≛AES_GCM`, `≛CHACHA20`).  
- `≛COMP` — compression (`≛NONE`, `≛GZIP`, `≛LZ4`).  
- `≛NUM_PROFILE` — optional name for numeric config (e.g., `≛FLOAT_T64`).  

You may add extra application‑specific fields:

- `≛UNIT`, `≛TIMEZONE`, `≛SOURCE`, `≛KEY_ID`, etc.

### 9.3 Storage & Compression Order

#### Unencrypted

1. Original structure/data → encode as ForgeNumerics‑S.  
2. Optionally compress entire frame or just payload.  
3. Store/transmit.

#### Encrypted

1. Original data → optionally compress.  
2. Encrypt → ciphertext bytes.  
3. Encode ciphertext as BLOB‑T (≗Φ⊙…).  
4. Put BLOB‑T in frame payload; mark ENC accordingly.  

### 9.4 Encryption (Conceptual Pipeline)

1. Encode a payload (text/numeric) as one or more frames.  
2. Serialize a frame or a group of frames to bytes.  
3. Encrypt with standard crypto (AES‑GCM etc.).  
4. Wrap ciphertext in a new frame:

   ```text
   ⧆≛TYPE⦙≛ENCRYPTED∴≛ENC⦙≛AES_GCM∴≛KEY_ID⦙≛K123 ∷ ≗Φ⊙<ciphertrits> ⧈
   ```

AIs with **no keys**:

- Treat payload as **opaque**.  
- Only reason over headers/meta.

AIs **with keys**:

1. Decode BLOB‑T → bytes.  
2. Decrypt using KEY_ID.  
3. Parse resulting ForgeNumerics‑S frame(s).

---

## Part 10 — Scientific, Mathematical & Real‑World Schemas

### 10.1 Scientific Measurements

Canonical measurement frame:

```text
⧆
  ≛VER⦙≛2.0-T ∴
  ≛DICT⦙≛DICT_v2025_11 ∴
  ≛TYPE⦙≛MEASUREMENT ∴
  ≛UNIT⦙≛meter
∷
  ≛VALUE⦙≗⊗⊗... ⦙
  ≛ERROR⦙≗⊗⊙... ⦙
  ≛TIME⦙≗⊙⊙...
⧈
```

- VALUE and ERROR as FLOAT‑T or DECIMAL‑T.  
- TIME as INT‑U3 or DECIMAL‑T (UNIX time, etc.).

### 10.2 Vectors & Matrices

**Vector frame:**

```text
⧆≛TYPE⦙≛VECTOR∴≛LEN⦙≗⊙⊙⊗… ∷ <list of ≗ tokens separated by ⦙> ⧈
```

**Matrix frame:**

```text
⧆≛TYPE⦙≛MATRIX∴≛ROWS⦙≗⊙⊙…∴≛COLS⦙≗⊙⊙… ∷
   <row_1_vector_frame> ⦙ <row_2_vector_frame> ⦙ ... 
⧈
```

### 10.3 Logs & Telemetry

Example log entry:

```text
⧆
  ≛TYPE⦙≛LOG ∴
  ≛SEVERITY⦙≛INFO ∴
  ≛TIME⦙≗⊙⊙...
∷
  ≛MSG⦙≛System_started ⦙
  ≛DETAIL⦙≛⟦extra text⟧
⧈
```

### 10.4 Knowledge Base Facts

Simple triple:

```text
⧆≛TYPE⦙≛FACT ∷
  ≛SUBJ⦙≛Einstein ⦙
  ≛PRED⦙≛born_in ⦙
  ≛OBJ⦙≛Ulm
⧈
```

More complex facts add qualifiers like time, source, confidence.

---

## Part 11 — AI Training Curriculum & Examples

### 11.1 Training Stages

1. **Trit Basics & INT‑U3**  
   - Map ⊙⊗Φ ↔ 0/1/2.  
   - Encode/decode integers 0–100.  
   - Check for malformed tokens.

2. **Signed INT‑S3 & Lists**  
   - Encode/decode positive/negative integers.  
   - Build simple lists (frames) of integers.  
   - Sum lists by decode → compute → encode.

3. **Floats & Decimals**  
   - Understand FLOAT‑T skeleton.  
   - Understand DECIMAL‑T structure.  
   - Compare values, convert between approximate (FLOAT‑T) and exact (DECIMAL‑T) when possible.

4. **Frames & Headers**  
   - Decode frames, extract TYPE, DICT, ENC, etc.  
   - Encode small objects like user profiles, config records.

5. **Encryption Awareness**  
   - Recognize BLOB‑T ciphertext.  
   - Explain what can/can’t be known without keys.  
   - Outline decrypt steps conceptually.

6. **Scientific & Real‑world Schemas**  
   - Encode measurement series, logs, model weights.  
   - Build small KBs.

### 11.2 Example Training Pair — INT‑U3 Encoding

**Instruction:** “Encode 42 as INT‑U3.”

- 42₁₀ → 1120₃ → digits [1,1,2,0] → [⊗,⊗,Φ,⊙].  
- Token: `≗⊙⊙⊗⊗Φ⊙`.

### 11.3 Example Training Pair — Mixed Sentence

**Instruction:** “Encode: PLAYER has 3 lives.”

Assume dictionary:

- PLAYER → `P_PLAYER`  
- has → `P_HAS`  
- lives → `P_LIVES`  

3₁₀ → 10₃ → `⊗⊙` → `≗⊙⊙⊗⊙`.

Result (conceptual):

```text
≛P_PLAYER⦙≛P_HAS⦙≗⊙⊙⊗⊙⦙≛P_LIVES
```

### 11.4 Example Training Pair — Encrypted Frame Reasoning

Given:

```text
⧆≛TYPE⦙≛ENCRYPTED∴≛ENC⦙≛AES_GCM∴≛KEY_ID⦙≛K123 ∷ ≗Φ⊙Φ⊗⊙Φ... ⧈
```

The AI should answer:
- “This is an encrypted payload; I cannot see its plaintext without KEY_ID K123 and the decryption function. I can still see that ENC=AES_GCM and TYPE=ENCRYPTED.”

---

## Part 12 — Best Practices & Extension Hooks

### 12.1 Best Practices

- Always set `VER` and `DICT` in headers.  
- Use **INT‑U3‑L** when packing many integers into a dense numeric block.  
- Compress before encrypting large payloads.  
- For money/finance → use **DECIMAL‑T**, not FLOAT‑T.  
- For logs & telemetry → keep schemas simple and consistent.  
- Train AIs with **parallel corpora**: natural language ↔ ForgeNumerics‑S frames.

### 12.2 Extension Ideas

- New numeric profiles (e.g., `≗Φ⊗` for complex numbers).  
- Error‑correcting trits and parity frames.  
- Domain‑specific TYPEs for:  
  - Quantum experiments.  
  - Genomics.  
  - Game state snapshots.

### 12.3 Philosophy

ForgeNumerics‑S is meant to be:

- **Compact** enough to be efficient.  
- **Explicit** enough for AIs to learn fully.  
- **Flexible** enough to model almost any data.  

Once your AIs internalize this spec, ForgeNumerics‑S becomes a **shared language of storage and thought** across your entire AGI ecosystem.


---

## Part 14 — Dynamic Extension Using ~750,000 Unused Symbol Combinations

> **Goal:** Allow ForgeNumerics-S to keep growing its vocabulary over time by using the large pool of remaining **unassigned symbol combinations** as **future dictionary slots**, so the language never “runs out of words”.

### 14.1 Assumption: Huge Symbol Space, Sparse Initial Dictionary

By design, your symbol-space for word codes (the combos used under `≛`) is huge — on the order of **hundreds of thousands to millions of possible combinations**.

- The **initial dictionary** (from your `Words.txt` + symbol mapping) only occupies a **subset** of that space.
- Roughly **750,000+ combinations are intentionally left unused** at v2 launch.
- These unused combos are **reserved for future vocabulary growth** and for environment-specific words your AI encounters over time.

So ForgeNumerics-S treats the dictionary as:

- A **core static base** (initial mapping), plus
- A **dynamic extension layer** (growing over time using free symbol combos).

### 14.2 Two-Layer Dictionary Model

We define two conceptual layers:

1. **Base Dictionary (STATIC)**  
   - Comes from your curated `Words.txt` + `symbols.txt` mapping.  
   - Versioned, read-only: `DICT_vYYYY_MM` (e.g., `DICT_v2025_11`).  
   - Contains all common words, technical terms, control tokens.

2. **Extension Dictionary (DYNAMIC)**  
   - Uses the **unused symbol combos** as new entries.  
   - Can grow as the AI sees novel words/names/identifiers.  
   - Is itself versioned and/or sharded (e.g., `EXTDICT_SITE_A_0001`).

The AI **always** resolves a word token in this order:

1. Check **base dictionary**.  
2. Check **extension dictionaries** referenced in the frame header.  
3. If not found → treat as OOV (literal `≛⟦...⟧`) or allocate a new dynamic entry.

### 14.3 Reserving and Enumerating Free Combos

From your symbol-space design:

- Let **S** = full set of allowed symbol combos for word codes (excluding reserved characters).  
- Let **B** ⊂ S = set of combos already used by base dictionary.  
- Let **F** = S \\ B = **free set** ≈ 750,000 combos.

You can precompute an **ordered list** of F:

```text
F = [C_0, C_1, C_2, ..., C_(N-1)]   # N ≈ 750,000
```

The order can be:

- Lexicographic on symbol strings, or
- Deterministic pseudo-random (but reproducible), or
- Grouped by “tiers” (e.g., short codes first).

This sequence defines the **allocation order** for the dynamic dictionary.

### 14.4 Extension Dictionary Allocation Algorithm

When the AI meets a new word W that:

- is not in base dictionary, and  
- is not already in any extension dictionary referenced in the current frame,

then the system may **allocate** a new code.

**High-level process:**

1. Compute a **canonical form** of W (e.g., lowercased, trimmed).  
2. Check all known dictionary layers for W.  
3. If missing and allocation allowed in this context:
   - Pop the next unused symbol combo `C_k` from free list F.
   - Add mapping: `W → C_k` to **extension dictionary** `EXTDICT_X`.  
   - Mark that `EXTDICT_X` is used in this frame’s header.

The new mapping is persisted in:

- A **dictionary file** for `EXTDICT_X`, and/or  
- A **special dictionary-update frame** that can be shared with other systems.

### 14.5 Declaring Extension Dictionaries in Frames

Frames that rely on extension dictionaries must declare them explicitly in headers.

Example:

```text
⧆
  ≛VER⦙≛2.0-T ∴
  ≛DICT⦙≛DICT_v2025_11 ∴
  ≛EXTDICT⦙≛EXTDICT_SITE_A_0001 ∴
  ≛TYPE⦙≛TEXT
∷
  <payload using ≛ base and extension codes>
⧈
```

Rules:

- `≛DICT` always refers to the **base** dictionary.  
- `≛EXTDICT` (or a list of them) refers to one or more **dynamic extension layers**.  
- Tokens in the payload may use symbol combos from both layers.

### 14.6 Forward & Backward Compatibility

**Forward compatibility:**

- Older decoders that do **not** know `EXTDICT_SITE_A_0001` cannot fully interpret those new word codes.  
- They must still preserve tokens as raw symbol combos or treat them as opaque, possibly emitting a fallback literal like:  
  - `≛⟦UNKNOWN_CODE_☉ψ⟧` when re-encoding.

**Backward compatibility:**

- Newer systems that know the extension dictionaries can decode data produced by older systems without issue.  
- Base dictionary remains stable; extension layers are additive.

### 14.7 Dynamic Allocation vs Literal OOV Tokens

There are two main strategies for unknown words:

1. **Literal-only approach**
   - Always encode unknown words as `≛⟦word⟧`.  
   - Simple, but no long-term compression or reuse.

2. **Dynamic dictionary approach (this section)**  
   - Allocate a new code for frequently-seen novel words.  
   - Achieves compaction and stable symbol-level patterns.  

You can combine both:

- First few occurrences: literal `≛⟦word⟧`.  
- After frequency threshold (e.g., 10 occurrences), allocate a new code in an extension dictionary and gradually migrate.

### 14.8 AI Behavior: When to Allocate New Codes

AI agents should follow **policy rules** for dynamic mapping, e.g.:

- Only allocate in certain environments (e.g., “training corpora”, “KB building”).  
- Only allocate after **supporting evidence** that the word will recur (frequency threshold).  
- Log all allocations in a **dictionary-update log** (frames of TYPE=DICT_UPDATE).

Example dictionary-update frame:

```text
⧆
  ≛TYPE⦙≛DICT_UPDATE ∴
  ≛EXTDICT⦙≛EXTDICT_SITE_A_0001
∷
  ≛WORD⦙≛⟦megafauna⟧⦙≛CODE⦙≛Ωζ ∴
  ≛WORD⦙≛⟦hypernode⟧⦙≛CODE⦙≛Ψχ
⧈
```

This frame says: in `EXTDICT_SITE_A_0001`, map:

- `megafauna → Ωζ`  
- `hypernode → Ψχ`

### 14.9 Handling Collisions & Exhaustion

- **Collisions** (accidental reuse of same combo):  
  - Prevented by construction if extension allocator reads from a **central free list** F or a lock-protected registry.  
  - If multiple agents allocate locally, they must sync or use partitioned ranges of F (e.g., ranges per site or keyspace).

- **Exhaustion** (running out of free combos):  
  - With ~750,000 free codes, this is unlikely in the near term.  
  - If ever nearing exhaustion, you can:
    - Increase allowed combo length (e.g., from up to N symbols to up to N+1).  
    - Introduce a new *generation* of codes with a prefix marker that’s still valid in word mode.

### 14.10 Training AIs to Use the Extension Layer

Training examples should include:

1. Frames that **declare** extension dictionaries in headers.  
2. Payloads that mix base and extension word codes.  
3. DICT_UPDATE frames explaining new allocations.  
4. Reasoning tasks that require the AI to:
   - Identify which dictionary (base vs which extension) a code belongs to.  
   - Decide whether an unknown word should be treated as:  
     - a one-off literal `≛⟦word⟧`, or  
     - a candidate for extension dictionary allocation.
   - Keep dynamic dictionaries **internally consistent** across sessions for the same environment.

### 14.11 Why This Matters

Using the ~750k unused combos as dynamic dictionary space gives ForgeNumerics-S:

- **Open-ended growth**: new words, names, tokens, concepts can be integrated without redesigning the language.  
- **Compression over time**: frequently used new terms are compacted into short symbol combos.  
- **Stable internal representations**: once a mapping is established and logged, all future frames can reuse the same symbol combo for that concept.

This turns ForgeNumerics-S into a **living language** that your AGI can extend as it discovers new domains, while still staying fully compatible with the core trinary and framing rules defined in Parts 1–12.
