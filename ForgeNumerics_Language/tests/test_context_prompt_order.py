from src import context_builder as cb


def test_prompt_section_order():
    ctx = cb.build_context(
        project_id="p",
        user_question="Q?",
        pinned_rules=["R"],
        project_state="STATE",
        recent_summary="SUMMARY",
        retriever=lambda q, k: [{"text": "E"}],
    )
    prompt = ctx["prompt"].splitlines()
    # Ensure order: Rules -> Project State -> Evidence -> Recent Summary -> User Question
    idx_rules = prompt.index("# Rules")
    idx_state = prompt.index("# Project State")
    idx_ev = prompt.index("# Evidence (Top-K)")
    idx_sum = prompt.index("# Recent Summary")
    idx_q = prompt.index("# User Question")
    assert idx_rules < idx_state < idx_ev < idx_sum < idx_q