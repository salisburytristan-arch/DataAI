# IP / Transfer Checklist (Practical)

Not legal advice — this is a practical diligence checklist.

## 1) Code & repository

- Confirm the buyer receives:
  - full source tree
  - build/test instructions
  - documentation
  - generated corpora (if included)
- Provide a written statement of authorship/ownership for all code you wrote.

## 2) Third-party dependencies

- Python deps: review `ForgeNumerics_Language/requirements.txt`
- Website deps: review `arctic-site/package.json` and `package-lock.json`
- Ensure the buyer is comfortable with these licenses.

## 3) Content / data

- Confirm ownership/rights for:
  - wordlists, symbol lists, mappings
  - any included specs/docs that may originate from third parties

## 4) Domain

- Confirm registrar account access and transfer steps.
- Ensure domain is not locked / transfer prohibited.

## 5) Vercel

- Buyer either redeploys to their org (recommended) or you transfer the Vercel project.

## 6) Security / secrets

- Confirm there are no embedded credentials in the repo.
- Remove any machine-specific files not intended for buyer.

## 7) Minimal representations most buyers expect

Even for “as-is”, most serious buyers will still require a few baseline reps:
- you have the right to sell the assets
- you’re not knowingly including malware/backdoors
- you are not aware of undisclosed encumbrances

If you refuse all reps entirely, expect a large price discount or a no-deal outcome.
