# Model Strategy & Cost Sheet

## Model Inventory (current posture)
- Student model: pluggable; local-friendly (e.g., Llama 7B/13B quantized) or remote API.
- Teachers: configurable external endpoints (e.g., higher-capacity LLMs) — optional in Tier-0; roadmap to teacher router.
- Embeddings: optional external provider; deterministic hash embeddings built-in for offline mode.

## Cost-Per-Capability (illustrative)
- Retrieval (BM25+hash emb): CPU-only; negligible marginal cost.
- Generation local: depends on model; example Llama-7B-q4 ~5–10 tok/s on consumer GPU; cost = hardware amortization.
- Generation API: $/1K tok passthrough; recommend caching and concise prompts; retrieve-to-reduce tokens.
- Distillation loop: dominated by teacher calls; budget control via `max_turns` and task set sizing.
- Storage: indexes + JSONL frames + sidecar embeddings; minimal disk footprint; compaction via ForgeNumerics (roadmap) reduces cold storage 80–90%.

## Local Hardware Guidance (starter)
- CPU-only: OK for indexing/search; slow for generation.
- Single GPU (>=12GB VRAM): viable for 7B quantized student; faster draft responses.
- Multi-GPU or remote: for heavier teacher models; or use hosted APIs.

## Training / Fine-Tune Pipeline (roadmap hooks)
- Inputs: TRAIN_PAIR/REPAIR_PAIR JSONL; evidence_meta for provenance; filter/dedupe before training.
- Steps: curate tasks → distill → quality score → dedupe → adapter training (LoRA) → eval gate → registry/versioning → rollback path.
- Repro: capture model/version, dataset hash, hyperparams; store in run log.

## Model Cards (template)
- Fields: model name/version, provider, context length, modalities, safety notes, license, hardware assumptions, latency (p50/p95), cost/1K tok, eval scores (task set), known limitations.
- Student card: include local throughput, memory footprint, quantization level.
- Teacher card: include pricing, max rate limits, alignment properties.

## Risk & Mitigation
- Vendor drift: support multiple providers; keep hash embeddings fallback; document config.
- Cost blow-up: cap turns, cache prompts/answers, use local student where possible.
- Repro gaps: store configs + seeds; standardize model card updates per release.
