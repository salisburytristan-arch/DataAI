# ArcticCodex — Technical Proofs to Lock $100M+ Tier (Firm Floor $85M+)

Date: Dec 20, 2025

This document specifies the four required technical proofs, with reproducible steps, code snippets, expected artifacts, and acceptance criteria. Each proof links to the exact files and includes commands to generate auditable logs.

Ready-to-run harness scripts are provided under [docs/proofs](docs/proofs) to capture logs quickly.

## Proof 1: Integrity Breach Trace (Hard Gate)

Objective: Show that a single-bit flip in an HMAC-signed ForgeNumerics frame triggers a hard verification gate via `FrameVerifier`.

Key files:
- [packages/core/src/frame_verifier.py](packages/core/src/frame_verifier.py)

Procedure:
1) Prepare a minimal FACT frame string.
2) Sign the frame using `FrameVerifier.sign_frame` with a private key.
3) Tamper the content by flipping one byte.
4) Verify with `FrameVerifier.verify_frame` and capture the failure.

Example script (run in a Python shell):
```python
from packages.core.src.frame_verifier import FrameVerifier, DEFAULT_SIGNING_KEY

FACT = """TYPE|FACT
SUBJECT|Bank Capital
PREDICATE|requires
OBJECT|Risk Mitigation
⧈"""

verifier = FrameVerifier(private_key=DEFAULT_SIGNING_KEY, signer_id="acx-agent")
signed = verifier.sign_frame(FACT)
print("Signed frame:\n", signed)

# Tamper: flip one character in the content (e.g., change 'Risk' to 'Risc')
tampered = signed.replace("Risk", "Risc", 1)
result = verifier.verify_frame(tampered, public_key=DEFAULT_SIGNING_KEY)
print("Verification:", result)
assert result.verified is False
```

Expected artifact(s):
- Trace log showing `verified=False` after tamper.
- Optional `FrameDigest` with content hash pre/post tamper.

Acceptance criteria:
- Any content alteration in a signed frame causes `verified=False` and demonstrates hard-gate enforcement.

## Proof 2: Semantic Reach Benchmark (TF‑IDF vs Neural Hybrid)

Objective: Demonstrate that Neural Hybrid Search retrieves semantically relevant chunks (e.g., "risk mitigation") for a query like "financial safety" even without keyword overlap.

Key files:
- [packages/vault/src/retrieval/retriever.py](packages/vault/src/retrieval/retriever.py)
- [packages/vault/src/index/embeddingIndex.py](packages/vault/src/index/embeddingIndex.py)
- [packages/vault/src/index/vectorIndex.py](packages/vault/src/index/vectorIndex.py)
- [packages/vault/src/vault.py](packages/vault/src/vault.py)

Setup:
- Install sentence-transformers and enable embeddings.
```powershell
pip install -U sentence-transformers
$env:ACX_EMBEDDINGS = "1"
```

Benchmark script:
```python
from packages.vault.src.vault import Vault
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    v = Vault(tmp)
    v.import_text("Our treasury policy emphasizes risk mitigation with diversified hedging strategies.", title="Risk Policy", source_path=str(Path(tmp)/"risk.txt"))
    v.import_text("Liquidity buffers are adjusted quarterly to ensure capital resilience.", title="Capital Resilience", source_path=str(Path(tmp)/"cap.txt"))

    # Baseline TF-IDF keyword search
    kw = v.retriever.search_keyword("financial safety", limit=5)
    print("TF-IDF results:", [r["doc_title"] for r in kw])

    # Neural hybrid (prefers embeddings when available)
    hy = v.retriever.search_hybrid("financial safety", limit=5)
    print("Hybrid results:", [(r["doc_title"], r.get("hybrid_score")) for r in hy])

    # Expect hybrid to surface "Risk Policy" due to semantic proximity
    assert any("Risk Policy" == r[0] for r in [(r["doc_title"], r.get("hybrid_score")) for r in hy])
```

Expected artifact(s):
- Side-by-side listing of TF‑IDF vs Hybrid results.
- Evidence that hybrid retrieves "Risk Policy" where TF‑IDF may not.

Acceptance criteria:
- Hybrid search returns semantically relevant chunks without keyword overlap, demonstrating neural reach.

## Proof 3: Autonomous "Operator" Audit (Sandboxed Tool Execution)

Objective: Provide a trace showing the Agent detects a `<tool .../>` tag, validates parameters, executes a sandboxed tool, and enforces path-traversal protection.

Key files:
- [packages/core/src/agent.py](packages/core/src/agent.py)
- [packages/core/src/tools.py](packages/core/src/tools.py)
- [packages/core/src/builtin_tools.py](packages/core/src/builtin_tools.py)

Procedure:
1) Initialize an Agent with a mock LLM that returns a tool tag (e.g., `calculate`).
2) Register builtin tools in the `ToolRegistry`.
3) Call `Agent.respond()` and capture `tool_calls` and `tool_results`.
4) Attempt a path traversal in a `read_file` tool call and verify denial.

Audit script:
```python
from packages.core.src.agent import Agent
from packages.core.src.llm.llama_client import MockLLM
from packages.vault.src.vault import Vault
import tempfile
from pathlib import Path
import importlib.util

# Load builtin_tools
spec = importlib.util.spec_from_file_location("builtin_tools_module", Path(__file__).resolve().parents[3] / "packages/core/src/builtin_tools.py")
builtin_tools_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(builtin_tools_module)

class ToolLLM(MockLLM):
    def generate(self, system, user, prompt, evidence):
        return '<tool name="calculate" expression="2 + 2" />'

with tempfile.TemporaryDirectory() as tmp:
    v = Vault(tmp)
    agent = Agent(v, llm=ToolLLM())
    if agent.tool_registry:
        builtin_tools_module.register_builtin_tools(agent.tool_registry)

    res = agent.respond("Compute test", evidence_limit=1)
    print("Tool calls:", res.get("tool_calls"))
    print("Tool results:", res.get("tool_results"))

    # Path traversal negative test (should be blocked / error)
    bad = '<tool name="read_file" file_path="../secret.txt" />'
    calls = agent._detect_tool_calls(bad)
    out = agent._execute_tool(calls[0]["name"], calls[0]["params"])
    print("Traversal test:", out)
    assert out["success"] is False
```

Expected artifact(s):
- Trace capturing tool detection, parameter parsing, execution, and result.
- Denial log for traversal attempt (error message or explicit block).

Acceptance criteria:
- Agent detects and executes tools; path-traversal attempts fail with no file access.

## Proof 4: Distillation ROI (Vast.ai Cycle)

Objective: Show performance improvement of a student model after one distillation cycle orchestrated via the distillation writer and Vast.ai provisioning.

Key files:
- [packages/core/src/distillation_writer.py](packages/core/src/distillation_writer.py)
- [packages/core/src/teacher_client.py](packages/core/src/teacher_client.py)
- [packages/core/src/vast_provisioner.py](packages/core/src/vast_provisioner.py)

Methodology:
1) Use `DistillationDatasetWriter` to export a high-quality training set from vault interactions.
2) Provision a Vast.ai instance and run a student fine-tuning job (external training script).
3) Evaluate pre- and post-training performance on a held-out validation set.
4) Log ROI metrics (e.g., accuracy/F1/perplexity improvement).

Example (dataset preparation skeleton):
```python
from packages.core.src.distillation_writer import DistillationDatasetWriter
from packages.vault.src.vault import Vault
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmp:
    v = Vault(tmp)
    # (Populate vault with summaries and facts here)
    writer = DistillationDatasetWriter(quality_threshold=0.7)
    # Example frame generation
    frames = writer.generate_frames(v)
    out = Path(tmp)/"distill.jsonl"
    writer.export_dataset_to_jsonl(frames, out)
    print("Exported:", out)
    # Run external training; capture metrics before/after
    # (Attach training logs and evaluation report here)
```

Expected artifact(s):
- Distillation dataset JSONL, training logs, evaluation report with pre/post metrics.
- Vast.ai provisioning details (instance type, time, cost).

Acceptance criteria:
- Clear, quantitative improvement of student model performance after distillation.

---

## Attachments & Audit Notes

- Include raw logs (stdout/stderr) and JSON artifacts alongside this doc for review.
- For reproducibility, record the exact commit hash and environment (Python version, packages).
- For embeddings, note the model used (default: `sentence-transformers/all-MiniLM-L6-v2`).

## Quick Commands

- Core tests:
```powershell
cd "D:\ArcticCodex - AGI"
python -m pytest packages/core/tests/ -v --tb=no -k "not slow"
```
- Vault tests:
```powershell
python -m pytest packages/vault/tests/ -v --tb=no
```
- ForgeNumerics tests:
```powershell
python -m pytest ForgeNumerics_Language/tests/ -v --tb=no
```

## Harness Scripts (Run & Log)

Run individual proofs directly:

```powershell
cd "D:\ArcticCodex - AGI\docs\proofs"
python integrity_breach_demo.py > ../proofs_integrity_log.txt
python operator_audit_demo.py > ../proofs_operator_log.txt
python semantic_reach_benchmark.py > ../proofs_semantic_log.txt
python distillation_roi_prep.py > ../proofs_distill_log.txt
```

Notes:
- For the semantic benchmark, install and enable embeddings beforehand:
```powershell
pip install -U sentence-transformers
$env:ACX_EMBEDDINGS = "1"
```
- Attach the generated `proofs_*.txt` logs with this document for the audit package.

This document provides the blueprint and scripts to capture the four proofs required for the firm valuation floor. Attach the outputs to finalize the audit package.
