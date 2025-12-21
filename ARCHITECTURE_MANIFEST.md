# ARCHITECTURE_MANIFEST.md

## What You Are Buying

A complete Python agent infrastructure system with deterministic transport, local-first memory, and training pipeline.

## Core Components

### 1. ForgeNumerics Language System
**Location:** `ForgeNumerics_Language/`  
**Purpose:** Symbolic protocol with formal EBNF grammar for deterministic agent communication.

**Includes:**
- Numeric profiles (INT-U3, INT-S3, DECIMAL-T, FLOAT-T, BLOB-T)
- Frame serialization (canonical ⧆ HEADER ∷ PAYLOAD ⧈)
- Compression/decompression (gzip, zlib)
- Extension dictionaries (~750k free symbol combos)
- Schema builders (VECTOR, MATRIX, LOG, FACT, TENSOR)
- Meta-layer frames (GRAMMAR, SCHEMA, EXPLAIN, TASK, CAPS, ERROR, TRAIN_PAIR)
- CLI with 30+ commands
- Curriculum (1000 training examples + splits)

**Tests:** 41 passing via `run_tests.py`

### 2. Knowledge Vault
**Location:** `packages/vault/`  
**Purpose:** File-based, content-addressed storage with cryptographic integrity checking.

**Includes:**
- SHA256-based content addressing
- Chunking and embedding pipelines
- Hybrid search (TF-IDF + optional vector)
- Tombstone soft-delete for compliance
- Citation tracking and verification

### 3. Studio UI (Next.js)
**Location:** `arctic-site/`  
**Purpose:** Web interface and landing page.

**Includes:**
- Landing page (defense-contractor aesthetic)
- Terminal demo (live animation)
- Responsive design (Tailwind CSS)
- Deployed to ArcticCodex.com (Vercel)

### 4. Core Agent Logic
**Location:** `packages/core/`  
**Purpose:** Agent orchestration, reasoning, and tool execution.

**Includes:**
- Teacher/student distillation
- Deterministic hash embeddings
- Frame validation and signing
- Orchestration workflows

### 5. Test Suite
**Location:** `ForgeNumerics_Language/tests/` and root `run_tests.py`

**Coverage:**
- Unit tests for all numeric profiles
- Frame parsing and serialization
- Schema validation
- Round-trip compression
- Meta-frame generation

## Dependency Summary

| Layer | Language | Dependencies |
|-------|----------|--------------|
| **Core** | Python 3.12+ | PyYAML |
| **Vault** | Python 3.12+ | None (stdlib only) |
| **ForgeNumerics** | Python 3.12+ | None (stdlib only) |
| **Studio** | JavaScript/TypeScript | Next.js, Tailwind, Framer Motion, Lucide React |

## Files Included

```
ArcticCodex/
├── ForgeNumerics_Language/       (Protocol + curriculum)
├── packages/
│   ├── core/                     (Agent logic)
│   ├── vault/                    (Storage engine)
│   ├── studio/                   (UI components)
│   └── testkit/                  (Test utilities)
├── arctic-site/                  (Next.js website)
├── docs/                         (Technical specifications)
├── requirements.lock             (Python deps)
├── final_test_pass_log_2025-12-21.txt
├── AS_IS_TERMS.md
├── DATA_PROVENANCE.md
├── QUICKSTART_HANDOFF.md
└── LICENSE
```

## What's NOT Included

- No external AI model weights (uses hash embeddings instead)
- No third-party SaaS dependencies
- No proprietary plugins or extensions
- No pre-trained neural networks

## To Get Started

See `QUICKSTART_HANDOFF.md` for installation and verification steps.

---

**Buyer Responsibilities:**
- Maintenance and bug fixes
- Security patching
- Performance optimization
- Future enhancements

**Seller Provides:** Source code, documentation, and test proof at time of transfer only.
