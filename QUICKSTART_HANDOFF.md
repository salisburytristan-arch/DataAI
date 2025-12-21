# QUICKSTART_HANDOFF.md

Get ArcticCodex running in your environment in under 10 minutes.

## Prerequisites

- Python 3.12 or higher
- Node.js 18+ (for the website)
- Git (optional, for version control)

## Installation

### 1. Install Python Dependencies

```powershell
python -m pip install -r requirements.lock
```

### 2. Install Node Dependencies (for website)

```powershell
cd arctic-site
npm install
```

## Verification

### Run Core Tests

```powershell
python .\ForgeNumerics_Language\run_tests.py
```

**Expected Output:**
```
=== Summary: 41 passed, 0 failed ===
```

If you see `41 passed, 0 failed`, the core system is working.

### Run the Website Locally

```powershell
cd arctic-site
npm run dev
```

Visit `http://localhost:3000` — you should see the ArcticCodex landing page.

## What You Own

- **ForgeNumerics_Language/**: The symbolic protocol, numeric encoders, frame system, curriculum, and CLI.
- **arctic-site/**: The Next.js landing page (deployed to ArcticCodex.com).
- **packages/**: Additional components (vault, studio, testkit, core).
- **docs/**: Architecture specs and technical documentation.

## Next Steps

1. Review `ARCHITECTURE_MANIFEST.md` for a breakdown of modules.
2. Read `DATA_PROVENANCE.md` to understand data sources and licensing.
3. Consult `ForgeNumerics_Language/README_PRODUCTION.md` for detailed API documentation.

## Support

This is an "as-is" asset sale. For questions about the codebase, refer to source code comments and the included documentation. No ongoing support is provided by the Seller.

---

**Timestamp**: 2025-12-21  
**Test Status**: 41/41 passing (see `final_test_pass_log_2025-12-21.txt`)
