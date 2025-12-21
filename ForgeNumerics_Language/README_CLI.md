# ForgeNumerics CLI Quick Reference

## Build an Index

```powershell
python ForgeNumerics_Language/src/cli.py vault-build-index --source ".\docs" --out ".\ForgeNumerics_Language\out_curriculum\vault_index.json"
```

Optional: generate a hash-embedding sidecar while building the index (works without any embedding model):

```powershell
python ForgeNumerics_Language/src/cli.py vault-build-index --source ".\docs" --out ".\ForgeNumerics_Language\out_curriculum\vault_index.json" --hash-embedding-dim 128
```

This writes `vault_index.json` and `vault_index.json.embeddings.json`.

Optional: attach embeddings sidecar for fusion.

```powershell
python ForgeNumerics_Language/src/cli.py orchestrator-distill \
  --project-id "proj-001" \
  --tasks-json ".\ForgeNumerics_Language\out_curriculum\forge_curriculum_full.json" \
  --out-dir ".\out_distill" \
  --index ".\ForgeNumerics_Language\out_curriculum\vault_index.json" \
  --embed-index ".\ForgeNumerics_Language\out_curriculum\vault_index.json.embeddings.json" \
  --query-embedding ".\ForgeNumerics_Language\out_curriculum\q_emb.json" \
  --hash-embedding-dim 128 \
  --max-turns 50
```

Notes:
- If `--query-embedding` is omitted and `--hash-embedding-dim` is set, the CLI auto-generates a deterministic hash embedding for the query (works even without a model).
- Fusion only applies when embeddings are present on both query and indexed chunks; otherwise BM25 runs alone.

Outputs:
- JSONL: `train_pairs.jsonl`, `repair_pairs.jsonl` (citations, evidence_meta, memory_proposals, answer_frame)
- Forge frames: `train_pairs.forge.txt`, `repair_pairs.forge.txt` (TRAIN_PAIR/REPAIR_PAIR)

## Search the Index

```powershell
python ForgeNumerics_Language/src/cli.py vault-search --index ".\ForgeNumerics_Language\out_curriculum\vault_index.json" --query "Tier-1 roadmap" --k 5 --embed-index ".\ForgeNumerics_Language\out_curriculum\vault_index_emb.json" --hash-embedding-dim 128
```

Notes:
- Provide `--query-embedding` to read a JSON embedding, or `--hash-embedding-dim` to auto-generate a deterministic hash embedding for the query.
- Embedding fusion requires both query embedding and indexed chunk embeddings; otherwise BM25-only search runs.

## Vault Ops (stubs)

```powershell
python ForgeNumerics_Language/src/cli.py vault-ingest --path ".\docs"
python ForgeNumerics_Language/src/cli.py vault-snapshot --store ".\vault_store" --out-dir ".\snapshots"
python ForgeNumerics_Language/src/cli.py vault-restore --snapshot ".\snapshots\vault_snapshot" --store ".\vault_store"
```