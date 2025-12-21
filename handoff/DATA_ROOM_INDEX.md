# ArcticCodex — Data Room Index (One-Pager)

This index is designed so a buyer can diligence the asset quickly, reproduce key proofs, and take operational ownership.

## 0) Fast verification (15 minutes)

1) Install minimal dependency:

```powershell
cd "D:\ArcticCodex - AGI"
python -m pip install -r .\ForgeNumerics_Language\requirements.txt
```

2) Run ForgeNumerics tests (no pytest required):

```powershell
cd "D:\ArcticCodex - AGI"
python .\ForgeNumerics_Language\run_tests.py
```

3) Run website locally:

```powershell
cd "D:\ArcticCodex - AGI\arctic-site"
npm install
npm run dev
```

## 1) What is being acquired

- Handoff overview: [README.md](README.md)
- Exact asset inventory: [ASSET_INVENTORY.md](ASSET_INVENTORY.md)

## 2) System documentation (ForgeNumerics)

- Overview: [../ForgeNumerics_Language/README.md](../ForgeNumerics_Language/README.md)
- Production guide (primary): [../ForgeNumerics_Language/README_PRODUCTION.md](../ForgeNumerics_Language/README_PRODUCTION.md)
- Production readiness checklist: [../ForgeNumerics_Language/PRODUCTION_READY.md](../ForgeNumerics_Language/PRODUCTION_READY.md)
- CLI reference: [../ForgeNumerics_Language/README_CLI.md](../ForgeNumerics_Language/README_CLI.md)
- Formal grammar (EBNF): [../ForgeNumerics_Language/ForgeNumerics_Grammar.ebnf](../ForgeNumerics_Language/ForgeNumerics_Grammar.ebnf)
- Meta-layer guide: [../ForgeNumerics_Language/docs/meta_layer_guide.md](../ForgeNumerics_Language/docs/meta_layer_guide.md)
- Learning tasks/curriculum guide: [../ForgeNumerics_Language/docs/learning_tasks.md](../ForgeNumerics_Language/docs/learning_tasks.md)

## 3) Architecture map

- Buyer-oriented architecture overview: [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)

## 4) Corpora / curriculum artifacts

- Regenerate & validate corpora: [CURRICULUM_AND_CORPUS.md](CURRICULUM_AND_CORPUS.md)
- Generated outputs location: `../ForgeNumerics_Language/out_curriculum/`

## 5) Tests and proof logs

- **Fresh diligence log (2025-12-21)**: [../DILIGENCE_TEST_LOG_2025-12-21.md](../DILIGENCE_TEST_LOG_2025-12-21.md) — 41 tests passed via `run_tests.py`
- How to interpret/regenerate proof logs: [TEST_PROOFS.md](TEST_PROOFS.md)
- Existing proof logs (timestamped): `../test_logs/`

Notes:
- `run_tests.py` is the authoritative, no-dependency test runner; **use this for diligence**.
- Additional pytest-style tests exist in `../ForgeNumerics_Language/tests/`; pytest collection discovered 72 tests (full suite validation in buyer environment).

## 6) Website + deployment

- Website deployment & transfer guidance: [WEBSITE_DEPLOYMENT.md](WEBSITE_DEPLOYMENT.md)
- Website source: `../arctic-site/`
- Vercel linkage file (created by Vercel CLI): `../arctic-site/.vercel/project.json`

## 7) Transfer / IP / as-is terms

- Practical transfer checklist: [IP_TRANSFER_CHECKLIST.md](IP_TRANSFER_CHECKLIST.md)
- Suggested “as-is / no support” language: [AS_IS_NO_SUPPORT_TERMS.md](AS_IS_NO_SUPPORT_TERMS.md)

## 8) Suggested diligence flow (buyer)

- Step 1: Run the fast verification (Section 0)
- Step 2: Review the production guide and readiness checklist (Section 2)
- Step 3: Spot-check proof logs and/or regenerate them (Section 5)
- Step 4: Confirm operational ownership: domain + Vercel + repo transfer (Section 6–7)

## 9) Redaction guidance (seller)

Before sharing externally:
- Remove machine-specific caches/artifacts if desired (`arctic-site/.next/`, `node_modules/`).
- Keep `package-lock.json`, `package.json`, and all source.
- Confirm no credentials are present.

## 10) Current website contact

- The live site’s mailto contact is configured as: `ArctiCasters@gmail.com`
