# ArcticCodex — Buyer Handoff Package

This folder is a self-contained “how to take ownership” bundle for **ArcticCodex** (ForgeNumerics language + Vault/Orchestrator tooling + deployed website).

## Quick start (verify it works)

### 1) ForgeNumerics: install minimal deps

```powershell
cd "D:\ArcticCodex - AGI"
python -m pip install -r .\ForgeNumerics_Language\requirements.txt
```

### 2) Run the no-dependency test runner

```powershell
cd "D:\ArcticCodex - AGI"
python .\ForgeNumerics_Language\run_tests.py
```

### 3) Optional: run the full pytest suite (if you use pytest)

```powershell
cd "D:\ArcticCodex - AGI\ForgeNumerics_Language"
python -m pip install pytest
pytest -q
```

### 4) Website: run locally

```powershell
cd "D:\ArcticCodex - AGI\arctic-site"
npm install
npm run dev
```

## What’s inside this folder

- `ASSET_INVENTORY.md` — exactly what you are acquiring
- `RUNBOOK_INSTALL_VERIFY.md` — install + verification runbook
- `TEST_PROOFS.md` — how to interpret / regenerate test proof logs
- `ARCHITECTURE_OVERVIEW.md` — module map + data flow
- `CURRICULUM_AND_CORPUS.md` — how to regenerate and validate curricula/splits
- `WEBSITE_DEPLOYMENT.md` — Next.js + Vercel ownership transfer guidance
- `IP_TRANSFER_CHECKLIST.md` — practical checklist for a clean handoff
- `AS_IS_NO_SUPPORT_TERMS.md` — suggested “as-is” language (not legal advice)

## Key locations in the workspace

- Core system: `ForgeNumerics_Language/`
- Website: `arctic-site/`
- Test proof logs: `test_logs/` (timestamped run folders)

## Contact

Inbound email configured on site: `ArctiCasters@gmail.com`
