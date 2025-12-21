# Training Runbook (Adapters/Fine-tune Ready)

## Inputs
- TRAIN_PAIR / REPAIR_PAIR JSONL with evidence_meta and citations.
- Index/embedding hashes; tasks JSON hash; config (k, alpha, hash dim).

## Steps
1) Curate tasks: select domain tasks; ensure coverage; version tasks JSON.
2) Distill: run `orchestrator-distill` with hash embeddings or model embeddings; cap `max_turns` by budget.
3) Quality filter: drop low-scoring pairs; dedupe on prompt hash; ensure citations present.
4) Split: train/valid/test; keep provenance.
5) Train adapters (LoRA or similar): set seed, hyperparams, dataset hash; log run metadata.
6) Eval gate: run regression suite + safety set; compare to baseline; require lift.
7) Package: save adapter weights, config, dataset hash, eval report; version in registry.
8) Rollout: deploy to local student; smoke test retrieval + distill; monitor metrics.
9) Rollback plan: keep last-known-good adapter; flag to switch if regression detected.

## Artifacts to Capture
- Run log: model versions, dataset hash, hyperparams, seed, date, hardware, cost.
- Eval report: scores, latency, cost, safety outcomes.
- Adapter binary + checksum.
- Release notes: changes, risks, mitigation.

## Budget Controls
- Set `max_turns`; limit teacher calls per task; reuse cached answers when possible; prefer local student when acceptable.

## Repro Checklist
- Pin model versions; store tasks JSON and index/embedding files; record hash embedding dim.
- Seed all random ops; log environment (Python version, packages).
