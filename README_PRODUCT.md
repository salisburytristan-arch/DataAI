# Agent Vault

**Local-first AI agent runtime with enterprise policy, audit, and governance.**

Agent Vault is a production-ready platform for deploying autonomous AI agents in regulated environments. Built for compliance-first organizations that need deterministic auditing, role-based control, and policy-driven tool access.

## Why Agent Vault?

- **Local-first**: All inference runs on-premise. No cloud lockdown.
- **Policy-driven**: Define exactly which tools agents can use, when, and with approval chains.
- **Deterministic**: Every decision is hashable and reproducible via ForgeNumerics frames.
- **Audit-ready**: HIPAA/SOC2/ISO 27001 compliance narratives built in.
- **Multi-agent**: Autonomous swarms with consensus voting for high-stakes decisions.

## Quick Start

### Install

```bash
pip install -e .
```

### Run Agent Vault

```bash
python -m agent_vault.cli agent run --policy default --audit logs/
```

### Deploy with Docker

```bash
docker-compose up -d
# Agent runtime on :8000, UI on :3000, Audit DB on postgres:5432
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Vault Platform                  │
├──────────────────┬──────────────────┬────────────────────┤
│   Agent Runtime  │   Policy Engine  │   Audit & Vault    │
│  (40-phase AGI)  │  (RBAC/rules)    │  (compliance logs) │
├──────────────────┼──────────────────┼────────────────────┤
│  ForgeNumerics   │  DeterministicOps│  Frame-based hash  │
│  frame system    │  (no LLM calls)  │  & verification    │
└──────────────────┴──────────────────┴────────────────────┘
```

### Core Components

| Component | Purpose | Files |
|-----------|---------|-------|
| **Agent Runtime** | 40-phase autonomous reasoning pipeline | `packages/core/src/phase_*.py`, `phase_manager.py` |
| **Policy Engine** | RBAC + tool execution gating | `platform.py` → `PolicyEngine`, `Role`, `PolicyRule` |
| **Audit Log** | Immutable, hashable audit trail | `platform.py` → `AuditLog`, `AuditEntry` |
| **CLI** | Agent invocation + policy enforcement | `cli.py` |
| **Orchestrator** | Multi-phase dispatch + frame export | `phase_manager.py` → `PhaseManager` |

## Features

### 40-Phase Agent Pipeline

Agent Vault includes a complete, deterministic reasoning pipeline across 40 phases:

- **Phases I–X**: Core reasoning (search, planning, execution, reflection)
- **Phases XI–XXV**: Specialized domains (code, language, visual, temporal)
- **Phases XXVI–XXIX**: Perception layer (vision, audio, omni-modal fusion)
- **Phases XXX–XL**: Advanced capabilities (infinite memory, swarms, deployment, strategy)

Each phase produces **ForgeNumerics frames**—deterministic, hashable decision records.

Run a phase:
```bash
python -m agent_vault.cli phase --num 30  # Run Phase XXX (Infinite Context)
python -m agent_vault.cli phase --all --export frames.jsonl  # Run all phases, export frames
```

### Enterprise Policy Control

Define org-wide policies for agent behavior:

```python
from platform import PolicyEngine, PolicyRule, Role

engine = PolicyEngine()
# OPERATOR can query but not execute shell
engine.add_rule(PolicyRule("tool:shell", "deny", Role.OPERATOR))
# VIEWER can only read memory
engine.add_rule(PolicyRule("memory:*", "allow", Role.VIEWER, requires_approval=True))
```

### Audit Trail

Every agent decision is logged with:
- Timestamp, user, organization, action, result
- Frame hash (verification against tampering)
- Entry hash (chain of custody)

Export for compliance audits:
```bash
python -m agent_vault.cli audit export --org-id acme_corp --start 2025-12-01 --end 2025-12-31 > acme_audit_2025.jsonl
```

## Use Cases

### 1. Fintech Compliance
Autonomous trading agents with real-time audit trails and policy override approval chains.

### 2. Healthcare Operations
Clinical decision support agents with HIPAA-audit-ready logging and role-based access to patient data.

### 3. Legal Discovery
Paralegal agents that autonomously review contracts, with every decision frame-signed for admissibility.

### 4. Autonomous Infrastructure
DevOps agents that deploy, monitor, and remediate infrastructure while maintaining SOC2 compliance.

## Deployment

### Local Development
```bash
python packages/core/src/cli.py agent run
```

### Docker (Recommended)
```bash
cd docker/
docker-compose up -d
# Vault UI: http://localhost:3000
# API: http://localhost:8000
# Postgres: localhost:5432
```

### Kubernetes (Enterprise)
See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for Helm charts and production configs.

## Pricing

| Tier | Cost | Features |
|------|------|----------|
| **Community** | $0/mo | Single-user, local agent, no audit export |
| **Professional** | $299/mo | 5 users, RBAC, audit export, email support |
| **Enterprise** | $5,000/mo | Unlimited users, custom policies, dedicated audit, phone support, SLA |

[Request Demo](mailto:acrticasters@gmail.com) | [Website](https://arcticcodex.com) | [FAQ](docs/FAQ.md)

## Compliance & Security

- **SOC2 Type II**: Third-party audited (audit report available under NDA)
- **HIPAA Ready**: BAA included; encryption at-rest and in-transit
- **ISO 27001**: Path to certification in progress
- **SBOM**: [Software Bill of Materials](docs/SBOM.json) available for supply chain review

See [SECURITY.md](SECURITY.md) for threat model and compliance narrative.

## Support

- **Website**: https://arcticcodex.com
- **Docs**: https://github.com/salisburytristan-arch/ArcticCodex/wiki
- **Issues**: [GitHub Issues](https://github.com/salisburytristan-arch/ArcticCodex/issues)
- **Email**: acrticasters@gmail.com
- **Community**: [Slack](https://join.slack.com/t/vaultai/shared_invite/...)

## License

Agent Vault is proprietary software. See [LICENSE](LICENSE) for terms.

Commercial licenses, source code escrow, and custom deployments available upon request.

---

**Agent Vault: Where autonomous intelligence meets enterprise discipline.**
