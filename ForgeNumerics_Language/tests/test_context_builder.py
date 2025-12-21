import os
from src import context_builder as cb
from src import conversation_cache as cache
from src.context_builder import build_context


def test_cache_key_deterministic():
    k1 = cache.cacheKeyFrom("state", "proj", 1)
    k2 = cache.cacheKeyFrom("state", "proj", 1)
    assert k1 == k2


def test_context_caches_evidence():
    calls = {"count": 0}

    def fake_retriever(q: str, k: int):
        calls["count"] += 1
        return [{"text": f"chunk for {q}"}]

    os.environ["ACX_TEST_MODE"] = "1"
    cache.invalidate()
    ctx1 = cb.build_context("proj", "q1", retriever=fake_retriever, top_k=3)
    ctx2 = cb.build_context("proj", "q1", retriever=fake_retriever, top_k=3)

    assert calls["count"] == 1  # second call uses cache
    assert ctx1["evidence"] == ctx2["evidence"]
    cache.invalidate()


def test_context_includes_evidence_text_and_meta():
    items = [
        {"text": "chunk one", "path": "p1", "chunk_id": 0},
        {"text": "chunk two", "path": "p2", "chunk_id": 1},
    ]

    def stub_retriever(query: str, k: int):
        return items[:k]

    ctx = build_context(
        project_id="proj",
        user_question="what",
        retriever=stub_retriever,
        top_k=2,
        pinned_rules=["rule"],
        project_state="state",
        recent_summary="summary",
    )
    assert len(ctx["evidence"]) == 2
    assert ctx["evidence_meta"][0]["path"] == "p1"
    assert "# Evidence" in ctx["prompt"]