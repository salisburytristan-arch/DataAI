# SBOM / Licensing Plan

## Steps
1) Generate dependency list (pip freeze) and run license scanner.
2) Produce SBOM (CycloneDX/Syft) and store under `docs/sbom/`.
3) Review copyleft/AGPL exposure; document none/any exceptions.
4) Record versions/hashes of key artifacts (index, embeddings, tasks JSON) for demos.
5) Package IP assignments and license report together.

## Commands (local examples)
- `pip freeze > docs/sbom/pip-freeze.txt`
- `pip-licenses --format=markdown > docs/sbom/license-summary.md` (install tool first if needed)
- `syft . -o json > docs/sbom/sbom.json` (if syft available)
- Hash artifacts: `certutil -hashfile ForgeNumerics_Language/out_curriculum/vault_index.json SHA256 > docs/sbom/index.sha256`

## Outputs to include
- docs/sbom/sbom.json
- docs/sbom/license-summary.md
- docs/sbom/pip-freeze.txt
- docs/sbom/*.sha256 for key artifacts (index, embeddings, tasks JSON)

## Tools (suggested)
- `pip-licenses` or `licensecheck` for quick view.
- `syft . -o json > docs/sbom/sbom.json` (if available locally).

## Deliverables
- SBOM JSON
- License summary table
- IP assignment packet (stored with legal docs)
