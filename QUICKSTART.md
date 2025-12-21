# ArcticCodex Quick Start Guide

## Install & Setup (5 minutes)

### 1. Python Environment
```powershell
cd "d:/ArcticCodex - AGI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pyyaml
```

### 2. Verify ForgeNumerics Installation
```powershell
cd ForgeNumerics_Language
python run_tests.py
# Output: === Summary: 41 passed, 0 failed ===
```

### 3. Verify Vault Installation
```powershell
cd ../packages/vault
python run_tests.py
# Output: === Summary: 5 passed, 0 failed ===
```

---

## Using ForgeNumerics-S (Codec & Language)

### Parse & Validate a Frame
```python
from src.frames import Frame
from src.errors import ParseError

frame_str = "⧆≛TYPE⦙≛VECTOR∷≗⊙⊙⊗⦙≗⊙⊙Φ⧈"
try:
    frame = Frame.parse(frame_str)
    print(f"✓ Valid frame: {frame.serialize()}")
except ParseError as e:
    print(f"✗ Error at {e.location}: {e.message}")
    print(f"  Suggestion: {e.suggestion}")
```

### Canonicalize a Frame
```python
from src.canonicalize import canonicalize_string, is_canonical

frame = "⧆≛Z⦙≛val∴≛A⦙≛val∷token1⧈"  # Out of order
canonical = canonicalize_string(frame)
print(f"Canonical: {canonical}")
print(f"Is canonical: {is_canonical(canonical)}")  # True
```

### CLI Commands
```bash
# Validate a frame
python -m src.cli validate --frame "⧆≛TYPE⦙≛VECTOR∷token1⧈"

# Canonicalize
python -m src.cli canonicalize --frame "⧆≛Z⦙≛val∴≛A⦙≛val∷token1⧈"

# Compare frames
python -m src.cli diff --frame1 "..." --frame2 "..." --semantic
```

---

## Using ArcticCodex Vault (Knowledge Base)

### Create a Vault
```python
from src.vault import Vault

vault = Vault("/path/to/vault")  # Creates vault directory
```

### Import Documents
```python
# Import text
doc_id = vault.import_text(
    text="The quick brown fox jumps over the lazy dog.",
    title="Animal Story",
    source_path="/docs/animals.txt"
)

# List documents
for doc in vault.list_docs():
    print(f"{doc.title}: {doc.chunk_count} chunks, {doc.total_bytes} bytes")
```

### Search & Retrieve
```python
# Keyword search
results = vault.search("fox", limit=5)
for result in results:
    print(f"[{result['doc_title']}] {result['content'][:100]}...")
    print(f"  Score: {result['score']}")

# Get evidence pack for RAG
evidence = vault.retriever.get_evidence_pack("animal", limit=3)
for chunk in evidence["chunks"]:
    print(f"Chunk {chunk['sequence']}: {chunk['content'][:100]}...")
for cite in evidence["citations"]:
    print(f"  → {cite['doc_title']} (offset {cite['offset']})")
```

### Store Knowledge (Facts)
```python
# Add facts
fact_id = vault.put_fact(
    subject="fox",
    predicate="is_a",
    obj="canine",
    confidence=0.95
)

# List facts
for fact in vault.list_facts():
    print(f"{fact.subject} {fact.predicate} {fact.obj} ({fact.confidence:.2f})")
```

### Memory Management
```python
# Soft-delete (write tombstone)
tombstone_id = vault.forget(doc_id, reason="Outdated content")

# Verify deletion (still in index but marked)
assert vault.index.is_deleted(doc_id)
assert vault.get_doc(doc_id) is None

# Vault statistics
stats = vault.stats()
print(f"Vault contains: {stats['doc_count']} docs, {stats['chunk_count']} chunks")

# Integrity check
integrity = vault.verify_integrity()
print(f"Objects verified: {integrity['objects_verified']}/{integrity['objects_verified'] + integrity['objects_failed']}")
```

---

## Architecture Overview

### ForgeNumerics-S
```
Input (text/frame)
    ↓
[Parser] → [Structured Errors with locations]
    ↓
[Frame] (AST)
    ↓
[Canonicalize] (deterministic serialization)
    ↓
Output (canonical bytes)
```

### Vault
```
Documents (text files)
    ↓
[Import + Chunk] (by size or paragraphs)
    ↓
[ObjectStore] (content-addressed by SHA256)
[MetadataIndex] (in-memory + JSON persistence)
    ↓
[Search/Retrieval] (keyword → ranked results)
    ↓
[Citations] (track source chunks for RAG)
    ↓
[Memory] (facts, preferences, summaries)
```

---

## Data Storage Layout

```
vault_root/
├── objects/                     # Content-addressed blobs
│   ├── ab/
│   │   ├── ab12345...           # Document/chunk/fact records (JSON)
│   │   └── ab67890...
│   └── cd/
├── index/                       # Metadata indexes (JSON)
│   ├── docs.json               # Document list
│   ├── chunks.json             # Chunk metadata
│   ├── doc_chunks.json         # Doc→chunks mapping
│   ├── facts.json              # Semantic facts
│   └── tombstones.json         # Deletion markers
```

---

## Common Tasks

### Add Tags/Metadata to Documents
```python
doc = vault.get_doc(doc_id)
# (Metadata is stored in doc.metadata dict)
```

### Export Documents with Citations
```python
results = vault.search("query", limit=10)
for r in results:
    chunk = vault.get_chunk(r["chunk_id"])
    doc = vault.get_doc(r["doc_id"])
    print(f"Source: {doc.source_path}:{chunk.byte_offset}:{chunk.byte_length}")
    print(f"Content: {chunk.content}")
```

### Backup Vault
```python
import shutil
shutil.copytree("/path/to/vault", "/path/to/backup")
```

### Verify Data Integrity
```python
integrity = vault.verify_integrity()
if integrity["objects_failed"] > 0:
    print(f"⚠️  {integrity['objects_failed']} objects failed integrity check")
    for error in integrity["errors"]:
        print(f"  - {error}")
```

---

## Next Steps

### Add an Agent Loop
Once you have the Vault running, the next step is implementing an agent that:
1. Takes user input
2. Retrieves evidence from Vault
3. Calls an LLM
4. Returns citations

### Add Multi-Teacher Training
Use the Vault to collect training data from multiple teacher models:
```
Query → Teacher1 (Vast) → Teacher2 (DeepSeek) → Critic
                    ↓
            Store in Vault as TRAIN_PAIR
                    ↓
            Fine-tune local model (LoRA)
```

---

## Troubleshooting

### "Module not found: yaml"
```bash
python -m pip install pyyaml
```

### Vault tests fail
- Ensure temp directory has write permissions
- Check that `packages/vault/src/` is in `PYTHONPATH`

### Frame parsing fails with unicode issues
- Frames use Unicode symbols: ⧆⧈∷∴⦙≛≗⊙⊗Φ⊛
- Save frames as UTF-8 files
- Don't use Windows ANSI encoding

---

## Resources

- **Roadmap**: `ArcticCodexRoadMap.md` (full specification, 2000+ lines)
- **ForgeNumerics Spec**: `ForgeNumerics_Language/README_PRODUCTION.md`
- **Vault Design**: `packages/vault/src/vault.py` (main API)
- **Tests**: `ForgeNumerics_Language/tests/` and `packages/vault/tests/`

---

Last updated: 2025-12-20
