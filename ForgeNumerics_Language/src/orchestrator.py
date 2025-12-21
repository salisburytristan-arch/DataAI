from typing import Any, Callable, Dict, List, Optional
import json
import os

from src.determinism import now

from src.context_builder import build_context
from src.meta_frames import build_train_pair_frame, build_repair_pair_frame
from src.frames import Frame


TeacherFn = Callable[[str, List[str]], Dict[str, Any]]
StudentFn = Callable[[str], str]
RetrieverFn = Callable[[str, int], List[str]]


def run_turn(
    project_id: str,
    user_question: str,
    student_client: StudentFn,
    retriever: Optional[RetrieverFn] = None,
    teachers: Optional[List[TeacherFn]] = None,
    pinned_rules: Optional[List[str]] = None,
    project_state: Optional[str] = None,
    recent_summary: Optional[str] = None,
    response_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run a single deterministic agent turn with optional teacher critique.

    Returns structured result with trace, citations (evidence indices), and
    memory proposals placeholder.
    """
    ctx = build_context(
        project_id=project_id,
        user_question=user_question,
        pinned_rules=pinned_rules,
        project_state=project_state,
        recent_summary=recent_summary,
        retriever=retriever,
        response_schema=response_schema,
    )

    prompt = ctx["prompt"]
    draft = student_client(prompt)
    critiques: List[Dict[str, Any]] = []
    if teachers:
        for t in teachers:
            try:
                fb = t(draft, ctx["evidence"])  # pass draft + evidence
            except Exception as e:
                fb = {"error": str(e)}
            critiques.append(fb)

    # Simple revision plan: apply textual suggestions if provided
    revised = draft
    for c in critiques:
        suggestion = c.get("suggestion") or c.get("revision")
        if isinstance(suggestion, str) and suggestion.strip():
            revised = suggestion

    # Bind citations to evidence indices if teacher provided mapping
    citations = []
    for c in critiques:
        idxs = c.get("citations")
        if isinstance(idxs, list):
            citations.extend([int(i) for i in idxs if isinstance(i, (int, float))])
    citations = sorted(set(citations))

    # naive Layer-1 summary and Layer-2 facts placeholders
    layer1_summary = None
    if ctx["evidence"]:
        layer1_summary = (
            f"Answered question using {len(ctx['evidence'])} evidence chunks; "
            f"citations bound: {', '.join(str(i) for i in citations) or 'none'}."
        )
    layer2_facts: List[Dict[str, Any]] = []
    # simple heuristic: extract sentences containing keywords from user_question
    try:
        import re
        kws = [w for w in re.findall(r"[A-Za-z0-9_]+", user_question.lower()) if len(w) > 3]
        for kw in set(kws):
            layer2_facts.append({"predicate": kw, "value": True, "source_citations": citations})
    except Exception:
        pass

    # Build a simple Forge ANSWER frame to keep parity with meta-layer
    header = [("TYPE", "ANSWER")]
    if citations:
        header.append(("CITATIONS", ",".join(str(c) for c in citations)))
    payload = ["≛NATLANG", f"≛⟦{revised}⟧"]
    answer_frame = Frame(header, payload)

    result = {
        "prompt": prompt,
        "draft": draft,
        "final": revised,
        "citations": citations,
        "evidence_count": len(ctx["evidence"]),
        "evidence_meta": ctx.get("evidence_meta", []),
        "critiques": critiques,
        "memory_proposals": {
            "layer1_summary": layer1_summary,
            "layer2_facts": layer2_facts,
        },
        "answer_frame": answer_frame.serialize(),
        "ts": now(),
    }
    return result


def _write_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False))
        f.write("\n")


def _append_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")


def run_distillation_job(
    project_id: str,
    tasks: List[Dict[str, Any]],
    student_client: StudentFn,
    retriever: Optional[RetrieverFn],
    teachers: List[TeacherFn],
    out_dir: str,
    max_turns: Optional[int] = None,
) -> Dict[str, Any]:
    """Run a multi-turn distillation job and write TRAIN/REPAIR pairs to JSONL.

    `tasks` are dicts containing at least {"question": str} and optional fields.
    Outputs JSONL files under `out_dir`.
    """
    train_path = os.path.join(out_dir, "train_pairs.jsonl")
    repair_path = os.path.join(out_dir, "repair_pairs.jsonl")
    train_forge_path = os.path.join(out_dir, "train_pairs.forge.txt")
    repair_forge_path = os.path.join(out_dir, "repair_pairs.forge.txt")
    stats = {"total": 0, "written_train": 0, "written_repair": 0}

    turns = tasks[:]
    if max_turns is not None:
        turns = turns[:max_turns]

    for t in turns:
        q = t.get("question") or t.get("input") or ""
        res = run_turn(
            project_id=project_id,
            user_question=q,
            student_client=student_client,
            retriever=retriever,
            teachers=teachers,
            pinned_rules=t.get("rules"),
            project_state=t.get("project_state"),
            recent_summary=t.get("recent_summary"),
            response_schema=t.get("response_schema"),
        )

        stats["total"] += 1

        _write_jsonl(train_path, {
            "prompt": res["prompt"],
            "final": res["final"],
            "citations": res["citations"],
            "evidence_meta": res.get("evidence_meta"),
            "critiques": res["critiques"],
            "memory_proposals": res.get("memory_proposals"),
            "answer_frame": res.get("answer_frame"),
            "project_id": project_id,
        })
        stats["written_train"] += 1

        # Emit TRAIN_PAIR meta-frame (NL→Forge placeholder)
        forge_payload = res.get("answer_frame") or ""
        train_frame = build_train_pair_frame(natural_language=res["prompt"], forgenumerics_frame=forge_payload)
        _append_text(train_forge_path, train_frame.serialize())

        if res.get("critiques"):
            _write_jsonl(repair_path, {
                "draft": res["draft"],
                "final": res["final"],
                "critiques": res["critiques"],
                "prompt": res["prompt"],
                "evidence_meta": res.get("evidence_meta"),
                "memory_proposals": res.get("memory_proposals"),
                "answer_frame": res.get("answer_frame"),
                "project_id": project_id,
            })
            stats["written_repair"] += 1

            # Emit REPAIR_PAIR meta-frame
            critique_summary = json.dumps(res["critiques"], ensure_ascii=False)
            repair_frame = build_repair_pair_frame(
                draft_nl=res["draft"],
                critique_summary=critique_summary,
                revised_nl=res["final"],
            )
            _append_text(repair_forge_path, repair_frame.serialize())

    return {
        "paths": {"train": train_path, "repair": repair_path, "train_forge": train_forge_path, "repair_forge": repair_forge_path},
        "stats": stats,
    }
