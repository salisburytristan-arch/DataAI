# Legal / IP Readiness Checklist

## IP Ownership
- Contributor/contractor agreements on file (assignments, work-for-hire). Maintain signatures register at docs/legal_signatures.csv (name, role, agreement, date, counterparty).
- Third-party code audit: enumerate dependencies, licenses, versions — see docs/SBOM.json for current inventory; update monthly.
- Model/data licensing: record hosted model terms and dataset provenance; store source URLs and licenses in docs/data_provenance.csv.

## OSS Compliance
- SBOM available at docs/SBOM.json. Generate license report via `pip-licenses --format=json > docs/license_report.json`; review quarterly.
- Check copyleft/AGPL exposure (avoid embedding such code in distributed binaries). Document exceptions in docs/oss_exceptions.md (if any).

## Privacy & Security
- PII handling plan: redaction roadmap; storage policies; retention/deletion procedure documented in docs/retention_runbook.md.
- Data residency: local-first; no cloud requirement by default.
- Threat model: path traversal protections, sandbox posture, HMAC integrity for artifacts (see proofs/).
- Incident response: define contacts, severity levels, response timeline in docs/incident_response.md (owner: Security Lead; review monthly).

## Data Provenance
- Document sources for sample corpora/curriculum; ensure redistribution rights (sheet: docs/data_provenance.csv).
- Maintain hashes for indexes/embeddings/traces used in demos (append to docs/provenance_hashes.md).

## Policies / Terms (draft pointers)
- ToS/Privacy aligned with actual behavior; clarify offline/local mode and any optional telemetry (currently none).
- Export controls: note if any crypto or dual-use concerns (review HMAC usage); capture in docs/export_controls.md.

## Deliverables to Assemble
- SBOM + license report.
- IP assignment packet.
- Security overview + threat model summary.
- Data provenance sheet for demo assets.
- Incident response + retention/deletion runbook.
