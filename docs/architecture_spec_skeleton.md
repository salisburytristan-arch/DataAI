# Architecture Spec (Skeleton)

## 1) High-Level Diagram (describe)
- Components: Orchestrator, Vault (ingest/index/retrieve), Memory layers, Teacher pool, Student client, Compaction (ForgeNumerics), CLI/Studio (future), Observability hooks.
- Data flow: Ingest → chunk/index → retrieve → build context → student draft → teachers critique/verify → compose → memory updates (frames) → outputs (JSONL + Forge).
- Trust boundaries: local file system (vault), external LLM endpoints (optional), sandboxed tools.

## 2) Runtime Topology
- Default local mode: Python CLI processes; local file store for vault/index; optional local model server.
- Optional remote LLM: HTTP endpoint configured per run; network boundary noted.
- Queues/workers (future): teacher router + task queue for parallel critiques; dataset writer.

## 3) Modules (inventory)
- `src/retriever.py`: build_index, search (BM25 + optional embedding fusion, hash fallback), save/load, embedding attach.
- `src/context_builder.py`: evidence packing with metadata, prompt assembly.
- `src/orchestrator.py`: run_distillation_job; builds ANSWER/TRAIN/REPAIR frames; citations and memory proposals.
- `src/cli.py`: commands for index/search/distill/vault ops/frames; hash embeddings.
- `src/embeddings.py`: deterministic hash embeddings.
- `src/frames.py` + `src/meta_frames.py`: ForgeNumerics frame builders/parsers.
- `src/vault_ops.py`: ingest/reindex/verify/snapshot/restore (MVP commands defined; implementation tracked in roadmap).

## 4) Interfaces / Contracts
- Inputs: tasks JSON, index JSON (+embedding sidecar), optional query embedding or hash dim; source docs (.md/.txt).
- Outputs: JSONL (train_pairs.jsonl, repair_pairs.jsonl) with evidence_meta, citations, answer_frame, memory_proposals; Forge frame text files.
- CLI contracts: `vault-build-index`, `vault-search`, `orchestrator-distill`, frame builders, vault ops (MVP).
- Data schemas: evidence items {path, chunk_id, text, score}; frames conform to ForgeNumerics schema (TRAIN_PAIR, REPAIR_PAIR, ANSWER, etc.).

## 5) Trust / Security Posture
- Local-first execution; no outbound network required unless pointing to external LLM.
- Sandbox/tooling: allowlists and audit logs planned; enforce via policy engine and immutable audit.
- Integrity: HMAC/path traversal protections referenced in proofs; deterministic hashing for embeddings.

## 6) Dependency Map
- External: Python stdlib; no vector DB; optional external LLM endpoint.
- OSS licenses: see docs/SBOM.json for inventory and licenses.
- Runtime criticality: retriever/orchestrator/frames are critical; vault_ops MVP non-critical until hardened.

## 7) Observability (roadmap hooks)
- Logs/metrics/traces: add structured logs for retrieval scores, teacher decisions, citations emitted.
- Replay: deterministic JSONL outputs; plan to add trace viewer (studio).

## 8) Open Risks & Plan
- Tool sandboxing & policy enforcement; PII redaction; vault ops hardening; teacher router maturity.
- Runbooks for deployment, monitoring, restore drills (see operations_runbook.md).
