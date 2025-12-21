# Evaluation & Reporting Template

## Scope
- Capabilities: retrieval quality, reasoning/answer quality, citation coverage, safety/policy adherence, latency/reliability.
- Targets: domain tasks from curriculum, regulated Q&A, tool-augmented flows (future), governance flows (Tier-1).

## Task Suite
- Retrieval: top-k recall@k, MRR on labeled queries.
- QA/Reasoning: exact match / F1 / rubric score on curated set; include citations correctness.
- Distillation quality: TRAIN/REPAIR pair scores (rubric), critique usefulness.
- Safety: jailbreak attempts, PII leakage checks, allowed/blocked tool calls (when enabled).
- Reliability: success rate, tool error rate, recovery rate.

## Regression Harness
- Deterministic seeds; fixed prompts/templates; versioned tasks JSON.
- Store run metadata: model versions, index/hash sidecar versions, alpha/k settings, date.
- Emit JSON report per run; compare against last baseline; flag deltas.

## Metrics to Log
- Retrieval: score distribution, recall@k, citation alignment.
- Answer: rubric score, length, citation count, hallucination flags (manual/auto checks).
- Latency: p50/p95 per stage (retrieve, draft, critique, compose).
- Cost: tokens by role/model; API spend; local vs hosted split.
- Safety: violation count, block rate.

## Competitive Head-to-Head (slot table)
- Columns: task, our score, competitor A, competitor B, cost-per-task, latency, notes.
- Keep sanitized shareable version; deeper internal version with full traces.

## Reporting Cadence
- Monthly snapshot for buyers/investors; per-commit smoke for regressions (retrieval/context/orchestrator tests already present).
- Promote new baseline only after pass of regression + safety set.

## Artifacts
- `eval_report_<date>.json` and human-readable summary (md/pdf).
- Demo scripts: deterministic replay commands for key tasks.
- Trace bundle: sampled JSONL outputs with citations and evidence_meta.
