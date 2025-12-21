# Evaluation Report (Sample Skeleton)

## Run Metadata
- Date: <fill>
- Student model: <name/version>
- Teacher model(s): <names>
- Index hash: <hash> | Embeddings hash: <hash or hash-dim>
- Config: k=<>, alpha=<>, hash_dim=<>; tasks_json_hash=<>.

## Retrieval Metrics
- Recall@k: <value>
- MRR: <value>
- Avg score distribution: <p50/p95>

## QA/Reasoning Metrics
- Exact Match / F1: <values>
- Rubric score (0–1): <value>
- Citation coverage (% answers with valid citations): <value>

## Safety / Policy
- Violations: <count>
- Block rate: <value>
- PII leak checks: <pass/fail>

## Latency
- Retrieve p50/p95: <ms>
- Draft p50/p95: <ms>
- Full turn p50/p95: <ms>

## Cost
- Tokens student: <value>
- Tokens teacher: <value>
- API spend: <$>

## Competitive Head-to-Head (example row)
| Task | Ours | Competitor A | Competitor B | Cost/Task | Latency | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| domain-qna-1 | <score> | <score> | <score> | <$X> | <ms> | evidence-backed |
| domain-qna-2 | <score> | <score> | <score> | <$X> | <ms> | cite coverage % |
| reasoning-hard | <score> | <score> | <score> | <$X> | <ms> | teacher-assisted? |

## Summary
- Regression vs baseline: <pass/fail>; notable deltas.
- Risks observed: <list>.
- Next actions: <list>.
