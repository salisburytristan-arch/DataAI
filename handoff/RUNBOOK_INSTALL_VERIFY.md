# Runbook: Install & Verify

This runbook is intended for a buyer’s engineering team to reproduce a known-good baseline quickly.

## A) Prerequisites

- Windows 10/11 or Linux
- Python 3.12+ recommended
- Node.js 18+ recommended (for the website)

## B) ForgeNumerics — install

### Install minimal Python dependency

ForgeNumerics uses a minimal dependency set; `ForgeNumerics_Language/requirements.txt` currently includes PyYAML.

```powershell
cd "D:\ArcticCodex - AGI"
python -m pip install -r .\ForgeNumerics_Language\requirements.txt
```

## C) ForgeNumerics — verify (fast)

### Run included test runner (no pytest required)

```powershell
cd "D:\ArcticCodex - AGI"
python .\ForgeNumerics_Language\run_tests.py
```

Expected: Summary line like `=== Summary: <n> passed, 0 failed ===`.

## D) ForgeNumerics — verify (full suite)

If you want the broader test suite under `ForgeNumerics_Language/tests/`:

```powershell
cd "D:\ArcticCodex - AGI\ForgeNumerics_Language"
python -m pip install pytest
pytest -q
```

## E) CLI smoke test

```powershell
cd "D:\ArcticCodex - AGI"
python .\ForgeNumerics_Language\src\cli.py list
python .\ForgeNumerics_Language\src\cli.py practice-int-u3 --value 42
python .\ForgeNumerics_Language\src\cli.py practice-log --severity INFO --message "≛System_started"
```

## F) Website — run locally

```powershell
cd "D:\ArcticCodex - AGI\arctic-site"
npm install
npm run dev
```

Open `http://localhost:3000`.
