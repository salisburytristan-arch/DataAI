# GTM Pricing & Metrics (Draft)

## Packaging (draft tiers)
- Core (Tier-0): Local vault + orchestration CLI, citations/frames, hash embeddings; support docs + deterministic demos.
- Governance Add-on (Tier-1): PII redaction, approval queue, teacher router policies, audit logging, studio UI.
- Training Add-on (Tier-1): Fine-tune harness, adapter registry/versioning, rollback; dataset curation tools.
- Enterprise bundle: SSO, on-prem support, SLAs, dedicated onboarding, runbook transfer.

## Pricing Model (illustrative)
- Core: annual license + support; per-seat optional for studio; usage caps minimal (local inference assumed).
- Governance/Training add-ons: uplift % over core; priced per deployment with optional per-seat for reviewers.
- Services: onboarding package, integration assistance, eval customization.

## Activation & Retention Definitions
- Activation: index built + first successful `vault-search` + first `orchestrator-distill` run producing TRAIN/REPAIR JSONL with citations.
- Retention: monthly active org with >=N searches and >=M distill turns; sustained studio logins once UI ships.

## Metrics Dashboard
**Scope**: Single view for weekly exec review; sources from product logs, sales CRM, and support tickets.

- **Adoption**: orgs onboarded, active orgs (last 28d), searches/day, distill turns/day.
- **Quality**: retrieval recall@k trend, rubric score (0–5), citation coverage (% turns with ≥1 citation).
- **Cost**: tokens by model, API spend vs local, infra uptime (%), average turn latency (p50/p95).
- **Sales**: pipeline ($), pilot conversions (%), time-to-value (days: ingest → first cited answer).
- **Support**: incidents (#/wk), MTTR (hours), top blockers (tagged categories).

### Targets (Q1 2026)
- Adoption: 3 orgs live; ≥2 active; ≥50 searches/day cumulative.
- Quality: recall@10 ≥0.70; citation coverage ≥80%; rubric ≥4.0.
- Cost: uptime ≥99.5%; p95 latency ≤3s; API spend ≤$300/mo if remote models used.
- Sales: 3 pilots → 2 paid (≥66% conversion); TTV ≤10 days.
- Support: MTTR ≤24h; ≤2 P1 incidents/week.

### Instrumentation Plan
- Emit event logs: `search_performed`, `distill_turn_completed` with org_id, counts, latency.
- Record quality: persist `retrieval_eval` (recall@k), `citation_emitted` boolean per turn.
- Cost telemetry: tokens consumed (if remote), uptime from health checks; store in `metrics` table.
- Sales/support: sync weekly from CRM and ticketing into `ops_metrics.csv` for dashboard ingest.

### Dashboard Layout
- Top row: KPI tiles (adoption, quality, uptime, conversion, MTTR).
- Left: time-series (searches/day, turns/day, recall@k, latency p50/p95).
- Right: funnel (pilots → paid), TTV distribution, blockers bar chart.
- Bottom: org-level breakdown table with thresholds highlighting.

## Enterprise Readiness Notes
- On-prem/offline path available; SBOM + IP docs to accompany; runbooks planned.
- Deterministic demo kit for security review; hash embeddings avoid data egress.
