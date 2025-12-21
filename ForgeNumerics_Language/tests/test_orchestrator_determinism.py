import os
from src import orchestrator as orch


def test_run_turn_deterministic_with_fake_time():
    os.environ["ACX_TEST_MODE"] = "1"
    os.environ["ACX_FAKE_TIME"] = "777.0"

    def student(prompt: str) -> str:
        return "draft"

    def teacher(draft: str, evidence: list):
        return {"suggestion": draft + " revised", "citations": [1]}

    def retriever(query: str, k: int):
        return [
            {"text": "e1", "path": "p1", "chunk_id": 0, "score": 1.0},
            {"text": "e2", "path": "p2", "chunk_id": 1, "score": 0.9},
        ]

    res1 = orch.run_turn(
        project_id="proj",
        user_question="q?",
        student_client=student,
        retriever=retriever,
        teachers=[teacher],
        pinned_rules=["rule"],
        project_state="state",
        recent_summary="summary",
    )
    res2 = orch.run_turn(
        project_id="proj",
        user_question="q?",
        student_client=student,
        retriever=retriever,
        teachers=[teacher],
        pinned_rules=["rule"],
        project_state="state",
        recent_summary="summary",
    )

    assert res1["final"] == res2["final"]
    assert res1["citations"] == [1]
    assert res1["ts"] == 777.0
    assert res2["ts"] == 777.0
