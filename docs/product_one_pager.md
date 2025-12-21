# Product One-Pager

## What It Is
- ArcticCodex: On-prem / air-gapped autonomous learning assistant with retrieval, memory tiers, and distillation loop.
- Form factors: CLI + local services; optional studio UI (roadmap).
- Core loop: retrieve → draft → critique/verify → revise → store TRAIN/REPAIR pairs + memory updates.

## Boundaries
- Included: Vault (ingest, chunk, index, retrieve), orchestrator (teacher loop), ForgeNumerics frames, CLI workflows, local proof scripts/tests, hash-embedding fallback, compaction language stubs.
- Excluded: Third-party hosted LLMs (optional), external SaaS dependencies, proprietary customer data, GPUs (buyer-supplied), UI beyond basic CLI.
- Deployment: Local-only default; supports hybrid by pointing to external LLM endpoints.

## Top 5 Jobs-To-Be-Done (JTBD)
1) **Regulated Q&A with provenance**: Answer policy/tech questions with citations from local vault; baseline: manual doc search; improved: deterministic citations, faster retrieval.
2) **Knowledge base bootstrap**: Ingest docs, index, and produce TRAIN/REPAIR pairs for downstream fine-tuning; baseline: ad-hoc prompt crafting; improved: structured datasets ready for adapters.
3) **Governed reasoning loops**: Run draft→critique→revise with audit trails; baseline: opaque LLM outputs; improved: traceable frames + memory proposals.
4) **Offline/air-gapped assistant**: Operate without cloud connectivity; baseline: no AI in secure environments; improved: local retrieval + student model, deterministic hash embeddings.
5) **Compaction-ready storage**: Prepare cold storage via ForgeNumerics frames; baseline: bulky/raw text; improved: provenance-preserving, compact payloads.

## ROI Snapshots (baseline → improved)
- Retrieval time: minutes of manual search → seconds with top-k evidence + citations.
- Distillation prep: hours of dataset wrangling → automated TRAIN/REPAIR pairs from tasks JSON.
- Compliance risk: unverifiable answers → audited outputs with evidence_meta and HMAC/sandbox posture.
- Token cost (local mode): API-dependent spend → fixed local inference; embeddings optional hash fallback.

## Time-to-Value
- Day 1: Build index (`vault-build-index`), run `vault-search`, run `orchestrator-distill` against curriculum JSON; produce JSONL + Forge frames.
- Week 1–2: Add domain docs; enable embedding fusion (sidecar or hash); tune k/alpha; integrate TRAIN/REPAIR pairs into fine-tune harness (roadmap).

## Packaging (draft)
- Core (Tier-0): Local vault + orchestration CLI; citations, frames, hash embeddings; no external dependencies.
- Governance Add-on (Tier-1): PII redaction, approval queue, teacher router policies, studio UI (roadmap).
- Training Add-on (Tier-1): Fine-tune harness, adapter registry, rollback/versioning (roadmap).

## Assumptions / Requirements
- Buyer provides model endpoint (or local model weights) and optional GPU.
- Docs available in .md/.txt for indexing; hash embeddings work without model.
- Air-gapped environments: allow local Python runtime + file I/O.

## Proof Hooks (how to demo)
- Run integrity demo + vault search + distill on sample curriculum; show JSONL with citations/evidence_meta and Forge TRAIN/REPAIR frames.
