# Operations Runbook (Day-1)

## Deploy/Setup
- Requirements: Python, local filesystem access; optional GPU; no cloud required.
- Install deps; activate venv; ensure paths accessible.

## Core Commands
- Build index: `vault-build-index --source <dir> --out <path> --hash-embedding-dim 128`
- Search: `vault-search --index <path> --query "..." --k 6 --embed-index <sidecar> --hash-embedding-dim 128`
- Distill: `orchestrator-distill --project-id X --tasks-json <tasks> --out-dir <out> --index <idx> --embed-index <sidecar> --hash-embedding-dim 128 --max-turns N`

## Monitoring (manual for now)
- Check JSONL outputs for evidence_meta/citations present.
- Track latency manually via timestamps; record in eval report.

## Backup/Restore (vault stubs)
- Snapshot: `vault-snapshot --store <store> --out-dir <dst>` (stub; roadmap to full).
- Restore: `vault-restore --snapshot <snap> --store <store>` (stub).

## Incident Response (initial)
- Data integrity concerns: rerun integrity proof scripts; validate hashes of index/embeddings.
- Model issues: rollback to last-known-good adapter (keep copy); switch to hash embeddings if embed service fails.
- Safety issue: halt teacher calls; run safety eval subset; review outputs.

## Runbooks To Flesh Out
- On-call rotations, alerting hooks (not yet wired).
- PII redaction/gov queue procedures (Tier-1).
- Vault ingest/reindex/verify full implementations.
