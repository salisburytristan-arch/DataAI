# Model Cards (Templates + Samples)

## Template Fields
- Name/Version
- Provider/License
- Context Length
- Modalities
- Safety Notes / Alignment
- Hardware Assumptions
- Throughput (tok/s) p50/p95
- Latency p50/p95 (per 1K tok)
- Cost per 1K tok (API) or amortized local cost
- Eval Scores (task set + date + config)
- Known Limitations

## Sample: Student (Local)
- Name: local-llama-7b-q4 (example)
- Provider/License: Meta Llama 2 (per license), quantized; ensure compliance.
- Context: 4K tokens (example; set per build).
- Hardware: 12–16GB VRAM recommended; CPU fallback slower.
- Throughput: ~5–10 tok/s on consumer GPU (illustrative).
- Cost: hardware amortization; no API fee.
- Safety: rely on prompt/guardrails; PII redaction pending.
- Eval: (populate after next run) — record tasks JSON hash, index hash, hash-embedding dim, k, alpha.
- Limits: reasoning depth vs larger models; may need teacher assist for critical claims.

## Sample: Teacher (Remote)
- Name: teacher-high-capacity (placeholder)
- Provider/License: TBD (e.g., commercial API); ensure ToS allows this use.
- Context: 8K–16K depending on model.
- Hardware/Endpoint: Hosted.
- Cost: per-1K tok (fill actual rates); monitor rate limits.
- Safety: vendor policies; add verification gate.
- Eval: capture scores on rubric tasks; note date/model version.
- Limits: latency; cost controls via `max_turns` and task sizing.

## Embeddings
- Default: hash embeddings (deterministic, offline, dim configurable).
- Optional: external embedding model; store as sidecar JSON with {path, chunk_id, embedding}.

## Logging for Repro
- Record: model name/version, quantization, provider, context length, seed (if applicable), date, config flags (k, alpha, hash dim), index/embedding hashes, tasks JSON hash.
