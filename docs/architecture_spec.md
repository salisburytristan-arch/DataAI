# Architecture Spec (Detailed Draft)

## 1. Components & Responsibilities
- Orchestrator: runs distillation turns, calls retriever, assembles context, invokes student/teachers, emits ANSWER/TRAIN/REPAIR frames, citations, memory proposals.
- Retriever: BM25 with optional embedding fusion; hash embeddings fallback; index builder/loader; embedding sidecar attach; hash sidecar generator.
- Context Builder: packs evidence + metadata into prompts; preserves evidence_meta.
- Frames/Meta-frames: ForgeNumerics builders/parsers for structured outputs; supports TRAIN_PAIR/REPAIR_PAIR/ANSWER, etc.
- Vault Ops: ingest/reindex/verify/snapshot/restore (MVP commands; hardening planned).
- Embeddings: deterministic hash embeddings for offline; accepts external embeddings.
- CLI: surface commands for index/search/distill/vault/frames; hash options baked in.

## 2. Data Flow (Turn)
1) Input: tasks JSON item (prompt/context spec).
2) Retrieve: load index (+optional embeddings); search(query,k,query_embedding,alpha).
3) Context: build prompt with evidence text + metadata.
4) Student draft: pluggable client (local/remote; default local client provided).
5) Teachers (optional): critique/verify; citations.
6) Compose: answer frame + citations + memory proposals.
7) Persist: JSONL outputs; Forge frames for TRAIN/REPAIR.

## 3. Trust Boundaries
- Local file system: vault/index/outputs.
- External LLM endpoints: only if configured; boundary noted.
- Tooling: sandbox to be enforced; path traversal mitigations referenced in proofs.

## 4. Runtime Topologies
- Local mode: Python CLI + local model; no network required.
- Hybrid: local retrieval + remote teacher/student endpoints.
- Future: worker queue for parallel teacher critiques; studio UI.

## 5. Interfaces & Schemas
- Evidence item: {path, chunk_id, text, score}.
- Embedding sidecar: list of {path, chunk_id, embedding}.
- Query embedding: JSON list of floats or hash-generated vector.
- Outputs: train_pairs.jsonl, repair_pairs.jsonl with evidence_meta, citations, answer_frame, memory_proposals; Forge text files.

## 6. Configurability
- Retrieval: k, alpha (BM25 vs embedding weight), hash dim, embed sidecar path.
- Orchestrator: max_turns; teacher functions; student client; index paths.
- CLI flags expose these parameters.

## 7. Observability & Logging (roadmap)
- Add structured logs for retrieval scores, chosen citations, teacher decisions, latencies.
- Emit run metadata (model versions, index hash) alongside JSONL outputs.
- Studio trace viewer planned.

## 8. Security & Safety Posture
- Local-first to avoid egress; hash embeddings avoid sending content to embed APIs.
- Integrity proofs: HMAC/path traversal demos exist (in proofs folder).
- Roadmap: PII redaction, tool allowlists, audit log, approval queue.

## 9. Dependencies & Criticality
- External: Python stdlib + minimal deps (no vector DB); optional remote LLM.
- Critical modules: retriever, orchestrator, frames; vault_ops MVP non-critical until hardened.
- License/SBOM to be finalized (see sbom_plan.md).

## 10. Maturity (per capability)
- Retrieval: stable (BM25 + hash fusion). Embedding fusion present; can accept model embeddings.
- Context building: stable.
- Distillation orchestration: student/teacher clients pluggable; full data flow; outputs structured frames.
- Vault ops: MVP available; full hardening on roadmap.
- Safety: basic integrity posture; advanced safety/PII pending Tier-1.

## 11. Operations
- Build index: `vault-build-index --hash-embedding-dim 128`.
- Search: `vault-search --embed-index ... --hash-embedding-dim 128`.
- Distill: `orchestrator-distill --index ... --embed-index ... --hash-embedding-dim 128 --tasks-json ...`.
- Outputs: JSONL + Forge frames under specified out-dir.

## 12. Roadmap Hooks
- Teacher router + policies; governance UI; PII redaction; full vault ops; trace viewer; run metadata capture; fine-tune harness integration.
