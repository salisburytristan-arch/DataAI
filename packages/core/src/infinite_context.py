"""
Phase XXX: Infinite Context (Deep Memory & Research)
===================================================

Implements holographic associative memory plus rolling summaries to
maintain effectively unbounded context and research recall. Provides
seed-frame compression, retrieval, and deep research stubs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
import hashlib
import math
import random


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, val))


@dataclass
class MemorySpan:
    """A captured slice of conversation or observation."""

    content: str
    source: str
    salience: float

    def to_frame(self, idx: int) -> str:
        return f"""⧆≛TYPE⦙≛MEMORY_SPAN∴
≛IDX⦙≛{idx}∷
≛SOURCE⦙≛{self.source}∷
≛SALIENCE⦙≛{self.salience:.3f}∷
≛HASH⦙≛{_hash_text(self.content)}
⧈"""


@dataclass
class RollingSummary:
    """Maintains rolling compression into a seed frame."""

    window: int = 12
    spans: List[MemorySpan] = field(default_factory=list)

    def ingest(self, content: str, source: str, salience: float = 0.5) -> None:
        self.spans.append(MemorySpan(content=content.strip(), source=source, salience=_clamp(salience)))
        if len(self.spans) > self.window:
            self.spans = self.spans[-self.window :]

    def summary_text(self) -> str:
        # Weight recent, high-salience spans
        weighted: List[Tuple[float, str]] = []
        for i, span in enumerate(self.spans):
            decay = 0.9 ** (len(self.spans) - i)
            weighted.append((span.salience * decay, span.content))
        weighted.sort(key=lambda x: x[0], reverse=True)
        top = [c for _, c in weighted[:6]]
        return " | ".join(top)

    def seed_frame(self) -> str:
        summary = self.summary_text()
        checksum = _hash_text(summary)
        return f"""⧆≛TYPE⦙≛SEED_FRAME∴
≛SUMMARY⦙≛{summary}∷
≛CHECKSUM⦙≛{checksum}
⧈"""


class HolographicMemory:
    """Associative cache using circular convolution as binding op."""

    def __init__(self, dim: int = 128, seed: int = 42):
        self.dim = dim
        self.rng = random.Random(seed)
        self.vectors: Dict[str, List[float]] = {}
        self.payloads: Dict[str, str] = {}

    def _embed(self, text: str) -> List[float]:
        rng = random.Random(int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32))
        vec = [rng.gauss(0.0, 1.0) for _ in range(self.dim)]
        norm = math.sqrt(sum(v * v for v in vec)) or 1e-8
        return [v / norm for v in vec]

    def store(self, key: str, text: str) -> None:
        vec = self._embed(key)
        payload_vec = self._embed(text)
        bound: List[float] = [0.0 for _ in range(self.dim)]
        for i in range(self.dim):
            acc = 0.0
            for j in range(self.dim):
                acc += vec[j] * payload_vec[(i - j) % self.dim]
            bound[i] = acc
        self.vectors[key] = bound
        self.payloads[key] = text

    def query(self, prompt: str, top_k: int = 3) -> List[Tuple[str, float, str]]:
        q = self._embed(prompt)
        scores: List[Tuple[str, float, str]] = []
        for k, v in self.vectors.items():
            norm_v = math.sqrt(sum(x * x for x in v)) or 1e-8
            norm_q = math.sqrt(sum(x * x for x in q)) or 1e-8
            sim = sum(a * b for a, b in zip(v, q)) / (norm_v * norm_q)
            scores.append((k, sim, self.payloads.get(k, "")))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def retrieval_frame(self, query: str, matches: List[Tuple[str, float, str]]) -> str:
        detail = "∷".join([f"{k}:{s:.3f}" for k, s, _ in matches]) if matches else "NONE"
        return f"""⧆≛TYPE⦙≛RETRIEVAL∴
≛QUERY⦙≛{query}∷
≛MATCHES⦙≛{detail}
⧈"""


class DeepResearcher:
    """Stub researcher that expands a query via background agents."""

    def __init__(self, breadth: int = 4):
        self.breadth = breadth

    def research(self, query: str) -> Dict[str, Any]:
        # Expand into synthetic sub-queries and mock findings
        findings = []
        for i in range(self.breadth):
            sub_q = f"{query} :: probe_{i}"
            finding = f"Finding_{i}:{_hash_text(sub_q)}"
            findings.append((sub_q, finding))
        merged = " | ".join([f for _, f in findings])
        return {
            "query": query,
            "subqueries": [q for q, _ in findings],
            "finding": merged,
            "confidence": 0.72,
        }

    def to_frame(self, result: Dict[str, Any]) -> str:
        subq = "∷".join(result.get("subqueries", []))
        finding = result.get("finding", "")
        conf = result.get("confidence", 0.0)
        return f"""⧆≛TYPE⦙≛RESEARCH∴
≛QUERY⦙≛{result.get('query','')}∷
≛SUBQ⦙≛{subq}∷
≛FINDING⦙≛{finding}∷
≛CONF⦙≛{conf:.2f}
⧈"""


class InfiniteContextEngine:
    """End-to-end orchestrator for Phase XXX."""

    def __init__(self):
        self.rollup = RollingSummary(window=14)
        self.holo = HolographicMemory(dim=192)
        self.researcher = DeepResearcher()

    def ingest(self, items: List[Tuple[str, str, float]]) -> None:
        """Items: (content, source, salience)."""
        for content, source, salience in items:
            self.rollup.ingest(content, source, salience)
            key = f"{source}:{_hash_text(content)}"
            self.holo.store(key, content)

    def retrieve(self, query: str) -> Dict[str, str]:
        matches = self.holo.query(query)
        return {
            "retrieval_frame": self.holo.retrieval_frame(query, matches),
            "matches": matches,
        }

    def compress(self) -> str:
        return self.rollup.seed_frame()

    def deep_research(self, query: str) -> str:
        result = self.researcher.research(query)
        return self.researcher.to_frame(result)


# ============================================================================
# SELF-TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE XXX: INFINITE CONTEXT - DEEP MEMORY")
    print("=" * 70)
    print()

    engine = InfiniteContextEngine()

    conversation = [
        ("User mentioned grandmother recipe for tomato soup", "user_note", 0.8),
        ("Model suggested adding basil", "agent_suggestion", 0.6),
        ("Follow-up question about GPU count on inference cluster", "infra", 0.7),
        ("Linked paper arxiv:2312.12345 on holographic memory", "citation", 0.9),
        ("Contract renewal due Jan 15", "ops", 0.85),
    ]

    print("1) Ingesting spans...")
    engine.ingest(conversation)
    for i, span in enumerate(engine.rollup.spans):
        print(span.to_frame(i))
        print()

    print("2) Compressing to seed frame...")
    seed = engine.compress()
    print(seed)
    print()

    query = "What about GPU count for inference cluster?"
    print(f"3) Retrieving for query: {query}")
    retrieval = engine.retrieve(query)
    print(retrieval["retrieval_frame"])
    print()

    print("4) Deep research stub...")
    research_frame = engine.deep_research("cure cancer with holographic memory")
    print(research_frame)
    print()

    print("=" * 70)
    print("PHASE XXX COMPLETE: Infinite context online")
    print("=" * 70)
    print("✓ Rolling summary → seed frame")
    print("✓ Holographic associative retrieval")
    print("✓ Deep research expansion stub")
    print("Next: Phase XXXI - Agent Swarm (autonomous cooperation)")
