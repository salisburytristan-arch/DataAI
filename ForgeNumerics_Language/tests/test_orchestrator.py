from src.orchestrator import run_turn


def test_run_turn_emits_answer_frame_and_memory():
    def student(prompt: str) -> str:
        return "draft answer"

    def teacher(draft: str, evidence):
        return {"role": "reasoning", "suggestion": draft + " revised", "citations": [1]}

    res = run_turn(
        project_id="proj",
        user_question="What is alpha?",
        student_client=student,
        retriever=lambda q, k: ["alpha info"],
        teachers=[teacher],
        pinned_rules=["rule"],
        project_state="state",
        recent_summary="summary",
    )
    assert "answer_frame" in res
    assert res["memory_proposals"]["layer1_summary"]