# ArcticCodex Core Agent

Minimal agent runtime wired to the local Vault with optional LLM HTTP client.

## Quickstart

```bash
# Activate venv
& "D:/ArcticCodex - AGI/.venv/bin/Activate.ps1"

# Run tests
cd "D:/ArcticCodex - AGI/packages/core"
python run_tests.py

# Chat with MockLLM
python -m packages.core.src.cli chat --vault "D:/ArcticCodex - AGI/packages/vault/.tmp"

# Chat with real LLM (llama.cpp/vLLM compatible)
$env:AC_LLM_ENDPOINT = "http://localhost:8000"
python -m packages.core.src.cli chat --vault "D:/ArcticCodex - AGI/packages/vault/.tmp"
```

## Notes
- If `AC_LLM_ENDPOINT` is set, the agent uses the HTTP LLM client; otherwise it falls back to `MockLLM`.
- The CLI prints citations (doc title, chunk id, offset) from Vault evidence.
- The HTTP client follows `/v1/chat/completions` schema (OpenAI-compatible).
