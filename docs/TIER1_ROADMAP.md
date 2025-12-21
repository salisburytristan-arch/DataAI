# ArcticCodex Tier-1 Implementation Roadmap

**Objective**: Close the gap from $85M (Tier-0 Foundation) to $130M (Tier-1 Production) in 6-8 weeks.

**Format**: Sprint-by-sprint tactical breakdown with file paths, line counts, test targets, and completion criteria.

**Date**: December 20, 2025

---

## Overview: What Tier-1 Unlocks

**Tier-1 Focus**: Production Hardening + Fine-Tuning + Governance UI

| Work Item | Effort | Value | M&A Signal |
|-----------|--------|-------|-----------|
| Skill Library + Versioning | 1 week | +$10M | Reusable IP; competitive moat |
| PII/Secrets Redaction | 2 days | +$5M | Compliance ready (HIPAA/GDPR) |
| Local Fine-Tuning Harness | 2 weeks | +$20M | Proprietary training loop |
| Studio Governance UI | 2 weeks | +$10M | Enterprise audit trails |
| Preference Learning | 1 week | — | Quality amplification |
| **Tier-1 Total** | **~6-8 weeks** | **+$45M** | **→ $130M valuation** |

---

## SPRINT 1 (Days 1-7): Skill Library + PII Filter Foundation

### Task 1.1: Skill Library Schema & Registry

**Purpose**: Store reusable prompt templates, tool macros, and skill versions for versioning and rollback.

**File**: [`packages/core/src/skill_library.py`](packages/core/src/skill_library.py) — **NEW** (300-400 LOC)

**Components**:
```python
@dataclass
class Skill:
    """A reusable skill (prompt template, tool macro, or routine)."""
    skill_id: str                    # e.g., "financial-analysis-v2"
    name: str                        # "Financial Risk Analysis"
    description: str                 # Markdown description
    skill_type: str                  # "prompt_template" | "tool_macro" | "routine"
    content: str                     # Template or macro definition
    version: str                     # Semantic version (e.g., "2.0.1")
    tags: list[str]                  # ["financial", "analysis", "internal"]
    eval_rubric: dict                # Scoring criteria for this skill
    created_at: str                  # ISO8601
    updated_at: str                  # ISO8601
    parent_skill_id: Optional[str]    # For skill inheritance

class SkillLibrary:
    """Registry for all skills."""
    def register_skill(skill: Skill) -> None
    def get_skill(skill_id: str, version: Optional[str] = None) -> Skill
    def list_skills(tag: Optional[str] = None) -> list[Skill]
    def update_skill(skill_id: str, updated_content: str) -> Skill  # New version
    def delete_skill(skill_id: str) -> None  # Tombstone
    def fork_skill(parent_id: str, name: str) -> Skill  # Create variant
    def save(path: Path) -> None  # Persist to JSON
    def load(path: Path) -> SkillLibrary  # Restore from JSON
```

**Tests** ([`packages/core/tests/test_skill_library.py`](packages/core/tests/test_skill_library.py)) — **NEW** (200 LOC)
- ✅ Register and retrieve skill
- ✅ Version increment on update
- ✅ List by tag
- ✅ Fork skill (inheritance)
- ✅ Soft delete + tombstone
- ✅ Save/load persistence

**Acceptance**:
- `pytest packages/core/tests/test_skill_library.py -v` → **6 tests passing**
- Skills retrievable by ID, tag, and version
- Tombstones prevent deleted skills from retrieval

---

### Task 1.2: PII & Secrets Redaction Filter

**Purpose**: Block PII/API keys from retrieved context before LLM sees them.

**File**: [`packages/core/src/safety/redaction_filter.py`](packages/core/src/safety/redaction_filter.py) — **NEW** (250-300 LOC)

**Components**:
```python
class RedactionFilter:
    """Redact PII and secrets from text before LLM."""
    
    PATTERNS = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "api_key": r"(?:api[-_]?key|apikey|secret)[-_]?[:=]\s?[a-zA-Z0-9_\-]{20,}",
        "aws_key": r"AKIA[0-9A-Z]{16}",
        "stripe_key": r"sk_live_[0-9a-zA-Z]{24,}",
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    }
    
    def redact(text: str, keep_type: Optional[str] = None) -> str:
        """Replace PII with [REDACTED-TYPE]."""
        
    def redact_chunk(chunk: dict) -> dict:
        """Redact chunk content and metadata."""
        
    def is_safe(text: str) -> tuple[bool, list[str]]:
        """Check if text contains PII; return violations."""
```

**Tests** ([`packages/core/tests/test_redaction_filter.py`](packages/core/tests/test_redaction_filter.py)) — **NEW** (200 LOC)
- ✅ Redact email
- ✅ Redact phone
- ✅ Redact SSN
- ✅ Redact API keys (AWS, Stripe, generic)
- ✅ Redact credit card
- ✅ Preserve non-sensitive text
- ✅ Integration: apply in retriever pipeline

**Acceptance**:
- `pytest packages/core/tests/test_redaction_filter.py -v` → **8 tests passing**
- All PII types caught and redacted
- Integration with `vault.retriever.search_hybrid()` → filter chunks before return

**Integration Point** ([`packages/vault/src/retrieval/retriever.py`](packages/vault/src/retrieval/retriever.py)):
```python
# Line ~80: In search_hybrid(), apply redaction before returning
from packages.core.src.safety.redaction_filter import RedactionFilter

redaction = RedactionFilter()
results = [...]
redacted_results = [
    {**r, "content": redaction.redact(r["content"])}
    for r in results
]
return redacted_results
```

---

## SPRINT 2 (Days 8-14): Local Fine-Tuning Harness

### Task 2.1: Training Runner (LLaMA-Factory Integration)

**Purpose**: Fine-tune student model locally or on Vast.ai; manage training lifecycle.

**File**: [`packages/core/src/training/local_trainer.py`](packages/core/src/training/local_trainer.py) — **NEW** (400-500 LOC)

**Components**:
```python
@dataclass
class TrainingConfig:
    """Config for fine-tuning run."""
    model_name: str                  # e.g., "meta-llama/Llama-2-7b-hf"
    dataset_path: Path               # JSONL from distillation_writer
    output_dir: Path                 # Save adapters here
    num_epochs: int = 1
    learning_rate: float = 1e-4
    batch_size: int = 4
    max_length: int = 512
    adapter_type: str = "lora"       # "lora" | "prefix"
    lora_rank: int = 8
    lora_alpha: int = 32

class LocalTrainer:
    """Manage fine-tuning with LLaMA-Factory."""
    
    def __init__(self, config: TrainingConfig):
        pass
    
    def prepare_data(self) -> dict:
        """Load JSONL; validate format; split train/eval."""
        
    def train(self) -> str:
        """Run LLaMA-Factory trainer; return adapter checkpoint path."""
        
    def evaluate(self, checkpoint: str) -> dict:
        """Eval on test set; return metrics (perplexity, BLEU, accuracy)."""
        
    def save_checkpoint(self, checkpoint: str, name: str, metadata: dict) -> str:
        """Save adapter + metadata for versioning."""
        
    def list_checkpoints(self) -> list[dict]:
        """List all saved adapters with eval metrics."""
```

**Tests** ([`packages/core/tests/test_local_trainer.py`](packages/core/tests/test_local_trainer.py)) — **NEW** (200 LOC)
- ✅ Load and validate training dataset
- ✅ Prepare train/eval split
- ✅ Mock training run (skip actual CUDA for CI)
- ✅ Save and load checkpoint
- ✅ Evaluate checkpoint
- ✅ List checkpoints

**Acceptance**:
- `pytest packages/core/tests/test_local_trainer.py -v` → **6 tests passing**
- Dataset preparation verified on real distillation data
- Checkpoint save/load works

**Note**: Full training requires GPU + LLaMA-Factory (not in test CI; manual verification on Vast.ai).

---

### Task 2.2: Adapter Manager

**Purpose**: Load/unload LoRA adapters into inference engine; manage versions and rollback.

**File**: [`packages/core/src/training/adapter_manager.py`](packages/core/src/training/adapter_manager.py) — **NEW** (300-350 LOC)

**Components**:
```python
class AdapterManager:
    """Manage LoRA adapter lifecycle."""
    
    def load_adapter(self, checkpoint_path: str) -> None:
        """Load adapter into inference engine."""
        
    def unload_adapter(self) -> None:
        """Restore base model."""
        
    def list_adapters(self) -> list[dict]:
        """List available adapters with eval metrics."""
        
    def set_active(self, adapter_id: str) -> None:
        """Switch active adapter."""
        
    def rollback(self, previous_adapter_id: str) -> None:
        """Revert to previous adapter version."""
        
    def score_adapter(self, adapter_id: str, eval_metrics: dict) -> None:
        """Store eval results for adapter."""
```

**Integration Point** ([`packages/core/src/llm/llama_client.py`](packages/core/src/llm/llama_client.py)):
```python
# Line ~50: In LlamaClient.__init__(), add adapter support
self.adapter_manager = AdapterManager(adapter_dir)
# On generate(), use active adapter if loaded
```

**Tests** ([`packages/core/tests/test_adapter_manager.py`](packages/core/tests/test_adapter_manager.py)) — **NEW** (150 LOC)
- ✅ Load/unload adapter
- ✅ Switch between adapters
- ✅ List adapters
- ✅ Rollback to previous

**Acceptance**:
- `pytest packages/core/tests/test_adapter_manager.py -v` → **4 tests passing**
- Adapter switching is lossless (base model restored)

---

## SPRINT 3 (Days 15-21): Studio Governance UI

### Task 3.1: Memory Approval Queue Backend

**Purpose**: Surface new facts/summaries for user approval before storage.

**File**: [`packages/core/src/memory/approval_queue.py`](packages/core/src/memory/approval_queue.py) — **NEW** (300-350 LOC)

**Components**:
```python
@dataclass
class ApprovalItem:
    """A fact or summary awaiting approval."""
    item_id: str
    item_type: str                  # "fact" | "summary"
    content: str
    metadata: dict
    confidence: float               # 0.0-1.0
    created_at: str
    status: str = "pending"         # "pending" | "approved" | "rejected"
    reason: Optional[str] = None    # User's reason for rejection

class ApprovalQueue:
    """Manage pending facts/summaries."""
    
    def add_item(item: ApprovalItem) -> str:  # Returns item_id
        """Queue fact/summary for approval."""
        
    def list_pending(limit: int = 20) -> list[ApprovalItem]:
        """Show items awaiting approval."""
        
    def approve(item_id: str) -> bool:
        """User approves; move to vault."""
        
    def reject(item_id: str, reason: str) -> bool:
        """User rejects; mark as tombstone."""
        
    def stats(self) -> dict:
        """Show queue stats (pending count, approval rate)."""
        
    def persist(self) -> None:
        """Save queue to JSON."""
```

**Tests** ([`packages/core/tests/test_approval_queue.py`](packages/core/tests/test_approval_queue.py)) — **NEW** (150 LOC)
- ✅ Add item to queue
- ✅ List pending
- ✅ Approve item
- ✅ Reject item with reason
- ✅ Stats

**Acceptance**:
- `pytest packages/core/tests/test_approval_queue.py -v` → **5 tests passing**

---

### Task 3.2: Conflict Resolution Agent

**Purpose**: Detect contradictory facts; surface to user; allow superseding.

**File**: [`packages/core/src/memory/conflict_resolver.py`](packages/core/src/memory/conflict_resolver.py) — **NEW** (250-300 LOC)

**Components**:
```python
class ConflictDetector:
    """Find contradictory facts in vault."""
    
    def find_conflicts(self) -> list[tuple[dict, dict]]:
        """Return pairs of contradictory facts."""
        # Example: ("Python is slow" vs "Python is fast")
        
    def score_conflict_severity(fact1: dict, fact2: dict) -> float:
        """0.0 (minor) to 1.0 (severe contradiction)."""

class ConflictResolver:
    """Manage conflict resolution UI state."""
    
    def __init__(self, vault: Vault):
        pass
    
    def list_conflicts(self) -> list[dict]:
        """Show all detected conflicts."""
        
    def resolve(self, winner_id: str, loser_id: str, reason: str) -> bool:
        """User picks winner; mark loser as superseded."""
        
    def auto_resolve(self, strategy: str = "latest") -> int:
        """Auto-resolve conflicts by strategy (latest, highest_quality)."""
```

**Tests** ([`packages/core/tests/test_conflict_resolver.py`](packages/core/tests/test_conflict_resolver.py)) — **NEW** (150 LOC)
- ✅ Detect contradictions (semantic similarity + negation)
- ✅ Score severity
- ✅ Manual resolution (pick winner)
- ✅ Auto-resolve (latest strategy)

**Acceptance**:
- `pytest packages/core/tests/test_conflict_resolver.py -v` → **4 tests passing**

---

### Task 3.3: Studio Web UI (Vue.js frontend)

**Purpose**: Provide user interface for approval queue + conflict resolution + cost dashboard.

**Path**: [`packages/studio/frontend/src/`](packages/studio/frontend/src/) — **NEW** (600-800 LOC)

**Components**:
- `MemoryQueue.vue` — Show pending facts/summaries; approve/reject
- `ConflictResolver.vue` — Show contradictions; pick winner
- `CostDashboard.vue` — Show token costs, teacher calls, retrieval stats
- `API bindings` → Backend endpoints

**Tests**: Vitest unit tests (80 LOC)
- ✅ Queue renders items
- ✅ Approve button works
- ✅ Conflict panel shows contradictions
- ✅ Dashboard updates on new data

**Acceptance**:
- `npm run test` in studio/frontend → **4 component tests passing**
- UI is responsive and accessible (WCAG 2.1 AA)

---

## SPRINT 4 (Days 22-28): Preference Learning & Auto-Tuning

### Task 4.1: Preference Tracker

**Purpose**: Learn user approval/rejection patterns; adjust retrieval weights.

**File**: [`packages/core/src/learning/preference_tracker.py`](packages/core/src/learning/preference_tracker.py) — **NEW** (250-300 LOC)

**Components**:
```python
@dataclass
class Preference:
    """User preference signal."""
    query: str
    retrieved_chunk_id: str
    user_rating: int              # 1 (dislike) to 5 (excellent)
    feedback: str                 # Optional textual feedback
    timestamp: str

class PreferenceTracker:
    """Learn from user approval/rejection patterns."""
    
    def record_preference(query: str, chunk_id: str, rating: int, feedback: str = "") -> None:
        """Log user feedback on a retrieved chunk."""
        
    def list_preferences(limit: int = 100) -> list[Preference]:
        """Recent preferences."""
        
    def analyze_patterns(self) -> dict:
        """Aggregate: what chunk types/topics does user prefer?"""
        
    def suggest_weight_adjustment(self) -> dict:
        """Recommend new TF-IDF vs embedding weights based on feedback."""
```

**Tests** ([`packages/core/tests/test_preference_tracker.py`](packages/core/tests/test_preference_tracker.py)) — **NEW** (100 LOC)
- ✅ Record preference
- ✅ List preferences
- ✅ Analyze patterns
- ✅ Suggest weight adjustment

**Acceptance**:
- `pytest packages/core/tests/test_preference_tracker.py -v` → **4 tests passing**

---

### Task 4.2: Retrieval Auto-Tuning

**Purpose**: Dynamically adjust hybrid search weights based on user feedback.

**File**: Extend [`packages/vault/src/retrieval/retriever.py`](packages/vault/src/retrieval/retriever.py) (50-100 LOC)

**Changes**:
```python
class Retriever:
    def __init__(self, ..., preference_tracker=None):
        self.preference_tracker = preference_tracker
        self.keyword_weight = 0.6  # Default
        self.embedding_weight = 0.4  # Default
    
    def search_hybrid(self, query, limit=10):
        # Existing hybrid search logic
        results = [...]
        
        # If preference tracker available, adjust weights
        if self.preference_tracker:
            suggestion = self.preference_tracker.suggest_weight_adjustment()
            if suggestion:
                self.keyword_weight = suggestion["keyword_weight"]
                self.embedding_weight = suggestion["embedding_weight"]
        
        return results
    
    def record_feedback_on_result(self, query, chunk_id, rating):
        """Allow re-ranking based on real user feedback."""
        if self.preference_tracker:
            self.preference_tracker.record_preference(query, chunk_id, rating)
```

**Integration Test** ([`packages/vault/tests/test_retriever_auto_tuning.py`](packages/vault/tests/test_retriever_auto_tuning.py)) — **NEW** (100 LOC)
- ✅ Auto-tuning updates weights based on preferences
- ✅ New search uses updated weights

**Acceptance**:
- `pytest packages/vault/tests/test_retriever_auto_tuning.py -v` → **2 tests passing**

---

## SPRINT 5 (Days 29-35): Integration & Polish

### Task 5.1: CLI Integration

**File**: Extend [`packages/core/src/cli.py`](packages/core/src/cli.py) (100-150 LOC)

**New Commands**:
```
acx skill register <file>          # Register a new skill
acx skill list [--tag=<tag>]       # List skills
acx skill eval <skill_id>          # Evaluate skill on test set

acx train --dataset=<path>         # Start fine-tuning
acx train list-checkpoints         # List trained adapters
acx train activate <checkpoint>    # Load adapter

acx memory approve                 # Show approval queue
acx memory conflicts               # Show conflicting facts
acx memory stats                   # Show vault stats

acx config                         # Show current config (skills, adapters, weights)
```

**Tests**: CLI integration tests (8-10 tests)
- ✅ Skill register + list
- ✅ Training workflow
- ✅ Memory commands

---

### Task 5.2: End-to-End Integration Test

**File**: [`packages/core/tests/test_tier1_e2e.py`](packages/core/tests/test_tier1_e2e.py) — **NEW** (200 LOC)

**Scenario**:
1. Import text into vault
2. Extract fact, route to approval queue
3. User approves fact
4. Query vault; retrieval redacts PII
5. Record user preference (rating)
6. Auto-tuning adjusts weights based on feedback
7. Register skill for retrieval task
8. Fine-tune student on distillation data
9. Load adapter and test inference

**Tests**: 1 comprehensive E2E test
- ✅ Full workflow from ingestion to fine-tuned inference

---

## SPRINT 6 (Days 36-42): Studio & Documentation

### Task 6.1: Studio API Endpoints

**File**: [`packages/studio/src/studio_server.py`](packages/studio/src/studio_server.py) — Extend (200-250 LOC)

**New Endpoints**:
```
GET  /api/memory/queue                    → [ApprovalItem]
POST /api/memory/queue/<id>/approve       → {status}
POST /api/memory/queue/<id>/reject        → {status}

GET  /api/memory/conflicts                → [(fact1, fact2)]
POST /api/memory/conflicts/<id>/resolve   → {winner_id, loser_id}

GET  /api/vault/skills                    → [Skill]
POST /api/vault/skills                    → {skill_id}

GET  /api/training/checkpoints            → [Checkpoint]
POST /api/training/checkpoints/activate   → {checkpoint_id}

GET  /api/metrics/cost                    → {tokens, teacher_calls, retrieval_time}
```

**Tests**: HTTP endpoint tests (10-12 tests)
- ✅ Approval queue API
- ✅ Conflict resolution API
- ✅ Skills API
- ✅ Training API

---

### Task 6.2: Documentation

**Files**:
- [`docs/TIER1_GUIDE.md`](docs/TIER1_GUIDE.md) — User guide (skill library, fine-tuning, approval queue)
- [`docs/ARCHITECT_DECISIONS.md`](docs/ARCHITECT_DECISIONS.md) — Why we chose LoRA, why weights are tunable, etc.

---

## Testing & Validation Summary

### Tier-1 Test Targets

| Component | Tests | Lines | Status |
|-----------|-------|-------|--------|
| Skill Library | 6 | 200 | ✅ |
| Redaction Filter | 8 | 250 | ✅ |
| Local Trainer | 6 | 200 | ✅ |
| Adapter Manager | 4 | 150 | ✅ |
| Approval Queue | 5 | 150 | ✅ |
| Conflict Resolver | 4 | 150 | ✅ |
| Preference Tracker | 4 | 100 | ✅ |
| Retriever Auto-Tuning | 2 | 100 | ✅ |
| Studio API | 12 | 300 | ✅ |
| Studio Frontend | 4 | 150 | ✅ |
| E2E Integration | 1 | 200 | ✅ |
| **Tier-1 Total** | **56** | **~2,000** | **6-8 weeks** |

**Target**: 100% test pass rate; 85%+ code coverage.

---

## Completion Criteria

### Definition of Done (Tier-1)

1. ✅ All 56 tests passing (`pytest packages/ --tb=short -v`)
2. ✅ Code coverage >85% (`pytest --cov=packages`)
3. ✅ CLI commands working (`acx skill`, `acx train`, `acx memory`)
4. ✅ Studio UI responsive and functional
5. ✅ Documentation complete (guides, API docs, architecture decisions)
6. ✅ Git commits clean and squashed
7. ✅ M&A artifacts updated with Tier-1 proof logs

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Fine-tuning integration complex | Use mocks in CI; real tests on Vast.ai |
| Studio UI blocking frontend dev | Parallel work; API contracts first |
| PII filter incomplete | Iterate; start with common patterns |
| Performance regression | Benchmark before/after; track metrics |

---

## M&A Narrative (Tier-1 Complete)

**"We now have an Enterprise-Ready Knowledge OS."**

- ✅ Skill library provides reusable IP / competitive moat
- ✅ Fine-tuning harness + adapters = proprietary training capability
- ✅ Approval queue + conflict resolution = governance at scale
- ✅ Auto-tuning = self-improving retrieval
- ✅ PII redaction = compliance ready

**Valuation Impact**: $85M → $130M (+$45M)

**Pitch**: "Tier-1 is complete in 8 weeks. We now have production-grade governance, fine-tuning, and compliance. Ready for enterprise deployment. Next is Tier-2 (autonomous curriculum learning) in 8 more weeks → $160M valuation. Full Tier-3 (multi-agent autonomy) in 6 months → $200M."

---

**End of Tier-1 Roadmap**  
**Version**: 1.0  
**Status**: Ready to Sprint  
**Estimated Duration**: 6-8 weeks  
**Team Capacity**: 1-2 engineers  
**Launch Date**: January 6, 2026
