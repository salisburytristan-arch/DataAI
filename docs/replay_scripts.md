# Deterministic Replay Scripts (Commands)

## Integrity Proof
- From `docs/proofs`: `python integrity_breach_demo.py > proofs_integrity_log.txt 2>&1`
- Attach `proofs_integrity_log.txt` in the package.

## Index Build (with hash embeddings)
- `python ForgeNumerics_Language/src/cli.py vault-build-index --source ./docs --out ./ForgeNumerics_Language/out_curriculum/vault_index.json --hash-embedding-dim 128`

## Search
- `python ForgeNumerics_Language/src/cli.py vault-search --index ./ForgeNumerics_Language/out_curriculum/vault_index.json --query "Tier-1 roadmap" --k 5 --embed-index ./ForgeNumerics_Language/out_curriculum/vault_index.json.embeddings.json --hash-embedding-dim 128`

## Distill (stub student/teachers)
- `python ForgeNumerics_Language/src/cli.py orchestrator-distill --project-id proj-001 --tasks-json ./ForgeNumerics_Language/out_curriculum/forge_curriculum_full.json --out-dir ./out_distill --index ./ForgeNumerics_Language/out_curriculum/vault_index.json --embed-index ./ForgeNumerics_Language/out_curriculum/vault_index.json.embeddings.json --hash-embedding-dim 128 --max-turns 50`

## Eval Report Generation (manual fill)
- After a run, fill metrics in [docs/eval_report_sample.md](eval_report_sample.md) using collected logs and outputs.
