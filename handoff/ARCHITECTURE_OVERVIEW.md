# Architecture Overview (High Level)

This is a buyer-facing map of what the system is and how to navigate it.

## ForgeNumerics Language System

### Concept

ForgeNumerics is a **trinary symbolic language** with:
- numeric encodings (multiple profiles)
- a canonical **frame** format for structured data
- validation + curriculum tooling intended for AI training/operation

### Frame model

Frames follow:

```
⧆ HEADER ∷ PAYLOAD ⧈
```

Headers are key/value pairs; payload is token sequence. Canonicalization yields deterministic serialization.

### Key modules (practical map)

- `ForgeNumerics_Language/src/numeric.py`
  - Numeric profile encode/decode utilities
- `ForgeNumerics_Language/src/frames.py`
  - Frame parse/serialize + helpers
- `ForgeNumerics_Language/src/compaction.py`
  - gzip/zlib compression pipelines + BLOB-T flows
- `ForgeNumerics_Language/src/extdict.py`
  - Extension dictionary allocation and persistence
- `ForgeNumerics_Language/src/schemas.py`
  - Schema builders for VECTOR/MATRIX/LOG/FACT/TENSOR etc.
- `ForgeNumerics_Language/src/meta_frames.py`
  - Meta-layer frames (GRAMMAR/SCHEMA/EXPLAIN/TASK/CAPS/ERROR/TRAIN_PAIR…)
- `ForgeNumerics_Language/src/curriculum.py`
  - Curriculum generation
- `ForgeNumerics_Language/src/validator.py`
  - Parse/round-trip/schema validation
- `ForgeNumerics_Language/src/cli.py`
  - CLI entry point (commands for practice, corpus generation, compression, dict ops)

### Vault / retrieval / orchestrator components

There are CLI commands and modules supporting:
- index build
- deterministic hash embeddings (no model required)
- retriever fusion when embeddings are present
- orchestrator distillation job runner

See `ForgeNumerics_Language/README_CLI.md` for the operational command examples.
