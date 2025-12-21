import os
from src import orchestrator as orch


def test_distillation_writes_outputs(tmp_path):
    os.environ["ACX_TEST_MODE"] = "1"
    os.environ["ACX_FAKE_TIME"] = "555.0"

    tasks = [{"question": "What?"}]

    def student(prompt: str) -> str:
        return "draft"

    def teacher(draft: str, evidence: list):
        return {"suggestion": draft + " revised", "citations": [1]}

    def retriever(query: str, k: int):
        return [
            {"text": "e1", "path": "p1", "chunk_id": 0, "score": 1.0},
            {"text": "e2", "path": "p2", "chunk_id": 1, "score": 0.9},
        ]

    out_dir = tmp_path / "out"
    stats = orch.run_distillation_job(
        project_id="proj",
        tasks=tasks,
        student_client=student,
        retriever=retriever,
        teachers=[teacher],
        out_dir=str(out_dir),
        max_turns=1,
    )

    paths = stats["paths"]
    for p in paths.values():
        assert os.path.exists(p)
    assert stats["stats"]["written_train"] == 1
    assert stats["stats"]["written_repair"] == 1