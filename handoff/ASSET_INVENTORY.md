# Asset Inventory (What the Buyer Receives)

This inventory is written as a diligence-friendly checklist.

## 1) Core Python system: `ForgeNumerics_Language/`

### Code (high level)

- Trinary numeric encodings: INT-U3, INT-S3, DECIMAL-T, FLOAT-T, BLOB-T
- Canonical frame format with parsing + deterministic serialization
- Compression/decompression pipelines (gzip, zlib) and round-trip verification
- Extension dictionary allocator (large free-combo pool)
- Schemas (VECTOR, MATRIX, LOG, FACT, TENSOR, etc.)
- Meta-layer frames (GRAMMAR, SCHEMA, EXPLAIN, TASK, CAPS, ERROR, TRAIN_PAIR, DICT_UPDATE, DICT_POLICY)
- Retrieval + orchestrator components (index build, deterministic hash embeddings, distillation outputs)
- CLI entrypoint: `ForgeNumerics_Language/src/cli.py`

### Documentation

- `ForgeNumerics_Language/README.md`
- `ForgeNumerics_Language/README_PRODUCTION.md`
- `ForgeNumerics_Language/PRODUCTION_READY.md`
- `ForgeNumerics_Language/docs/learning_tasks.md`
- `ForgeNumerics_Language/docs/meta_layer_guide.md`
- `ForgeNumerics_Language/ForgeNumerics_Grammar.ebnf`

### Data / outputs (generated artifacts)

- Curriculum + corpora: `ForgeNumerics_Language/out_curriculum/`
- Round-trip / compression outputs: `ForgeNumerics_Language/out*` folders
- Decompression outputs: `ForgeNumerics_Language/out_decomp/`

## 2) Verification assets

- Proof logs: `test_logs/` contains timestamped folders with per-test output logs (useful for audits and buyer verification).

## 3) Website: `arctic-site/`

- Next.js + TypeScript + Tailwind landing page
- Vercel project metadata created by Vercel CLI:
  - `arctic-site/.vercel/project.json`

## 4) Domain + deployment

- Domain: `ArcticCodex.com` (transfer depends on registrar/provider)
- Vercel deployment: project name `arctic-site` (transfer or re-deploy into buyer’s Vercel org)

## 5) What is NOT included by default

- Ongoing support, SLAs, warranties, or maintenance (see `AS_IS_NO_SUPPORT_TERMS.md`)
- Any third-party paid APIs or hosted services (the core Python system is designed to be dependency-light)
