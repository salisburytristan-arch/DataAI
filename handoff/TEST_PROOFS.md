# Test Proofs (Audit-Friendly)

## What exists

The workspace contains a `test_logs/` directory with timestamped folders. These were produced by running tests individually and capturing full stdout/stderr per test into separate log files.

This is useful for:
- Buyer diligence (“show me what it does, not just a green checkmark”)
- Reproducibility audits
- Comparing behavior across machines/versions

## Where to look

- `test_logs/<timestamp>/forge_nodeids.txt` — collected Forge test node IDs
- `test_logs/<timestamp>/vault_nodeids.txt` — collected Vault test node IDs
- `test_logs/<timestamp>/*.log` — per-test output logs

## How to re-generate proof logs (suggested approach)

If the buyer wants to re-run the proof capture, use the same pattern:

1) Collect node IDs:

```powershell
cd "D:\ArcticCodex - AGI"
python -m pytest -q --collect-only > nodeids.txt
```

2) Run each nodeid individually with verbose output and stdout capture, teeing to a log file.

Notes:
- On Windows, enforce UTF-8 (`chcp 65001` + `PYTHONIOENCODING=utf-8`) so symbols render correctly.
- Use `-s` so print output is shown.

## Interpreting logs

Each per-test log should show:
- pytest session header (platform, Python version)
- the specific test node id
- pass/fail result and runtime

If you see encoding artifacts, re-run with UTF-8 forced.
