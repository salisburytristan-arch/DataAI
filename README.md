# ArcticCodex: Enterprise AI Agents for Regulated Industries

**Status**: PRODUCT PIVOT LIVE (Dec 21, 2025) | Beta Launch (Jan 2026) | Target: $1.5k ARR (Q1)

---

## What Is ArcticCodex?

**ArcticCodex** is a **local-first AI agent runtime** with enterprise policy, audit, and governance.

- ✅ **All inference runs on-premise** — no cloud vendor, no data leaving your network
- ✅ **Policy-driven tool access** — RBAC prevents unauthorized agent actions
- ✅ **Forensic audit trail** — every decision logged, signed, reproducible
- ✅ **Compliance-ready** — HIPAA, SOC2, ISO 27001 narratives built in
- ✅ **Production-ready** — Docker-based, deployable in <5 minutes

## Why ArcticCodex?

**Market reality**: 80% of enterprises want AI agents, but compliance blocks them.

- Cloud LLMs (ChatGPT, Claude) have no audit trails and log data externally
- Custom agents take 6+ months to build and lack compliance narratives
- Frameworks (LangChain) are flexible but not production-ready

**ArcticCodex** solves this: Agents + Compliance + On-Premise + Speed.

---

## Quick Start

### Install & Run (60 seconds)

```bash
# Clone repo
git clone <repo-url>
cd agent-vault

# Start services (Docker required)
docker-compose up -d

# Create admin user
docker-compose exec agent-vault python -m agent_vault.cli create-user \
  --email admin@example.com --role admin --org-id demo_org

# Run a phase (agent reasoning)
docker-compose exec agent-vault python -m agent_vault.cli phase --num 30

# Access UI
open http://localhost:3000
```

For full setup: [INSTALL.md](docs/INSTALL.md)

---

## Architecture

```
┌────────────────────────────────────────────┐
│      ArcticCodex Platform                  │
├────────────┬──────────────┬────────────────┤
│   Agent    │   Policy     │   Audit &      │
│  Runtime   │   Engine     │   Vault        │
│ (40 phases)│  (RBAC/gated)│ (compliance)   │
├────────────┼──────────────┼────────────────┤
│ ForgeNum.  │ Deterministic│ Frame-based    │
│ Frames     │ Ops          │ hash & verify  │
└────────────┴──────────────┴────────────────┘
```

### Components

| Component | Purpose | Tech |
|-----------|---------|------|
| **Agent Runtime** | 40-phase reasoning pipeline | Python, ForgeNumerics frames |
| **Policy Engine** | RBAC + tool execution gating | Python (role-based rules) |
| **Audit Log** | Immutable, hashable audit trail | PostgreSQL + JSON |
| **CLI** | Agent invocation + operations | Click |
| **API** | REST endpoints for agents | FastAPI |

---

## The 40-Phase Pipeline

ArcticCodex includes a complete, deterministic reasoning pipeline:

- **Phases I–X**: Core (search, planning, execution, reflection)
- **Phases XI–XXV**: Specialized (code, language, vision, temporal)
- **Phases XXVI–XXIX**: Perception (vision, audio, omni-modal fusion)
- **Phases XXX–XL**: Advanced (infinite memory, swarms, strategy)

Run a phase:
```bash
python -m agent_vault.cli phase --num 30  # Phase XXX: Infinite Context
python -m agent_vault.cli phase --all --export frames.jsonl  # All phases
```

Each phase produces **ForgeNumerics frames**—deterministic, hashable decision records.

---

## Features

### Policy-Driven Tool Access

Define which tools agents can use by role:

```python
from platform import PolicyEngine, Role

engine = PolicyEngine()
# OPERATOR can query but not execute shell
engine.add_rule(PolicyRule("tool:shell", "deny", Role.OPERATOR))
```

### Forensic Audit Trail

Every decision is logged:
- Timestamp, user, organization, action, result
- Frame hash (verification against tampering)
- Entry hash (chain of custody)

Export for compliance:
```bash
python -m agent_vault.cli audit export \
  --org-id acme_corp --start 2025-12-01 --end 2025-12-31 > audit.jsonl
```

### HIPAA / SOC2 / ISO 27001

See [SECURITY.md](SECURITY.md) for:
- HIPAA compliance narratives
- SOC2 trust service criteria
- ISO 27001 objective mappings
- Threat model
- Incident response procedures

---

## Pricing

| Tier | Cost | Users | Features |
|------|------|-------|----------|
| **Professional** | $299/mo | 5 | RBAC, audit export, email support |
| **Enterprise** | $5k+/mo | ∞ | Custom policies, real-time audit, SLA |

---

## Use Cases

### Fintech
Autonomous compliance agents with real-time audit trails and approval chains.
> "Agent decided to block trade; frame-signed proof in audit log."

### Healthcare
Clinical decision support agents with HIPAA-audit-ready logging.
> "Every patient interaction logged deterministically; admissible in medical records review."

### Legal
Contract review agents with frame-based decisions for admissibility.
> "All reasoning reproducible; decision frames are evidence."

### Infrastructure
DevOps agents with policy-driven approval and full audit.
> "Agent remediated outage; all actions policy-approved and logged."

---

## Deployment

### Local Development
```bash
python packages/core/src/cli.py agent run
```

### Docker (Recommended)
```bash
docker-compose up -d
# Vault UI: http://localhost:3000
# API: http://localhost:8000
# Postgres: localhost:5432
```

### Kubernetes (Enterprise)
See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for Helm charts and production configs.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [README_PRODUCT.md](README_PRODUCT.md) | Product overview + features |
| [ELEVATOR_PITCH.md](ELEVATOR_PITCH.md) | Sales pitches (15-sec, 1-min, 3-min) |
| [QUICK_REFERENCE.md](AGENT_VAULT_QUICK_REFERENCE.md) | One-sheet summary |
| [SECURITY.md](SECURITY.md) | Compliance narratives + threat model |
| [INSTALL.md](docs/INSTALL.md) | Setup guide |
| [ROADMAP_TO_ARR.md](ROADMAP_TO_ARR.md) | 6-week plan to first customer |
| [SBOM.json](docs/SBOM.json) | Supply chain bill of materials |

---

## Roadmap

### Q1 2026 (Product Launch)
- ✅ Docker-based deployment
- ✅ 3 pilot customers
- ✅ $1.5k ARR
- ✅ 2+ case studies

### Q2 2026 (Growth)
- 8+ paying customers
- $6k+ MRR
- Enterprise feature parity
- Sales engineer hired

### Q3 2026 (Scale)
- 15+ paying customers
- $22.5k+ MRR
- Series A raised
- Kubernetes support

### Q4 2026 (Path to $1M+)
- 30+ paying customers
- $60k+ MRR
- Enterprise customer logos
- Series B ready

---

## Compliance & Security

### Built-In Compliance

- **HIPAA**: Data on-premise; audit logs exportable; BAA template included
- **SOC2 Type II**: Third-party audited (Q1 2026)
- **ISO 27001**: Path to certification clear

### Security Properties

- **Deterministic**: All outputs reproducible via ForgeNumerics frames
- **Immutable audit trail**: SHA256 hashing + entry chaining
- **Policy-driven**: RBAC prevents unauthorized actions before execution
- **Tamper-evident**: Frame signatures catch data modifications

See [SECURITY.md](SECURITY.md) for full threat model, incident response, and compliance narratives.

---

## Support

- **Docs**: https://docs.vaultai.io
- **Support**: https://vaultai.io/support
- **Email**: support@vaultai.io
- **Community**: Slack (contact support for invite)

---

## License

ArcticCodex is proprietary software. See [LICENSE](LICENSE) for terms.

Commercial licenses, source code escrow, and custom deployments available upon request.

---

## Technology Stack

- **Language**: Python 3.10+
- **Core**: 40-phase reasoning (ForgeNumerics frames)
- **API**: FastAPI + uvicorn
- **Database**: PostgreSQL (audit logs)
- **ORM**: SQLAlchemy
- **Deployment**: Docker + docker-compose
- **CLI**: Click
- **Type checking**: Pydantic

**No LLM dependencies**—all reasoning is local and deterministic.

---

## Contributing

ArcticCodex is proprietary. For partnership or feature requests:
- **Sales**: sales@vaultai.io
- **Partnerships**: partners@vaultai.io

---

## Who Uses ArcticCodex?

We're building this for:
- **Compliance officers** who need audit trails
- **CTOs** who want local-first AI with no vendor lock-in
- **CFOs** who want AI ROI without compliance risk
- **Security teams** that need policy-driven governance

---

**ArcticCodex: Where autonomous intelligence meets enterprise discipline.**

*Questions?* [Schedule a demo](https://calendly.com/sales/agent-vault-demo) or email sales@vaultai.io
