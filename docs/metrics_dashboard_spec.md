# Metrics Dashboard Spec (Stub)

## Views
- Adoption: #orgs, active orgs, searches/day, distill turns/day, activation rate.
- Quality: retrieval recall@k trend, rubric scores, citation coverage.
- Cost: tokens by model, API spend vs local, infra uptime.
- Safety: violation counts, block rate, PII check results.
- Performance: latency p50/p95 by stage (retrieve/draft/critique/compose).
- Sales: pipeline, pilots, time-to-value (ingest→first cited answer).
- Support: incidents, MTTR, top blockers.

## Data Sources
- JSONL outputs with metadata; run logs; optional tracing.
- Manual entries for pilots/LOIs until instrumented.

## Implementation Notes
- Start with static report (md/pdf) generated from run logs; upgrade to dashboard later.
- Hash/ID every run artifact (index, embeddings, tasks JSON) for comparability.
