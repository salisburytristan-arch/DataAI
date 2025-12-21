# ArcticCodex Vault Retrieval Modes

Vault supports two complementary retrieval modes:

- TF‑IDF Vector search (default): lightweight bag‑of‑words vectors computed from chunk text. No external dependencies.
- Embedding search (optional): semantic vectors via sentence‑transformers (default model: `all-MiniLM-L6-v2`).

## Enabling Embeddings

Install the library:

```powershell
pip install -U sentence-transformers
```

Embeddings are indexed on import when enabled. Hybrid search prefers embeddings when ready and falls back to TF‑IDF otherwise.

## Configuration

- Per‑vault config file: create `index/embeddings_config.json` under your vault directory:

```json
{ "enabled": true, "model_name": "sentence-transformers/all-MiniLM-L6-v2" }
```

- Per‑run environment variables:
  - `ACX_EMBEDDINGS=1` to enable, `ACX_EMBEDDINGS=0` to disable
  - `ACX_EMBEDDINGS_MODEL` to override model name (e.g., `sentence-transformers/all-mpnet-base-v2`)

## CLI Toggle (Agent Chat)

The ArcticCodex Agent CLI supports per‑run toggles:

```powershell
python -m packages.core.src.cli chat --vault "D:\VaultPath" --embeddings on --embedding-model sentence-transformers/all-MiniLM-L6-v2
```

To disable embeddings for a run:

```powershell
python -m packages.core.src.cli chat --vault "D:\VaultPath" --embeddings off
```

## Notes

- If embeddings are unavailable or disabled, hybrid search remains functional using TF‑IDF vectors.
- Embeddings are stored as JSON under `index/embeddings.json`; metadata under `index/embeddings_meta.json`.
- Model selection and enabled state can be mixed: env vars override for a single run; config applies to the vault persistently.
