from typing import Callable, Dict, List, Optional, Any

from src.conversation_cache import cacheKeyFrom, get_block, set_block


def build_context(
    project_id: str,
    user_question: str,
    pinned_rules: Optional[List[str]] = None,
    project_state: Optional[str] = None,
    recent_summary: Optional[str] = None,
    retriever: Optional[Callable[[str, int], List[Any]]] = None,
    top_k: int = 6,
    response_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble a deterministic prompt context from standard blocks.

    Returns a dict containing individual blocks and a combined `prompt` string.
    Caches expensive blocks (project_state, recent_summary, evidence pack).
    """
    pinned_rules = pinned_rules or []
    # Cache keys
    state_key = cacheKeyFrom("state", project_id)
    summary_key = cacheKeyFrom("summary", project_id)
    query_key = cacheKeyFrom("evidence", project_id, user_question, top_k)

    # Fetch/calc blocks, with caching for expensive ones
    state_block = project_state
    if state_block is None:
        state_block = get_block(project_id, "project_state", state_key)
    else:
        set_block(project_id, "project_state", state_key, state_block)

    summary_block = recent_summary
    if summary_block is None:
        summary_block = get_block(project_id, "recent_summary", summary_key)
    else:
        set_block(project_id, "recent_summary", summary_key, summary_block)

    evidence_items: List[Any] = []
    cached_evidence = get_block(project_id, "evidence_pack", query_key)
    if cached_evidence is not None:
        evidence_items = list(cached_evidence)
    elif retriever:
        try:
            evidence_items = retriever(user_question, top_k) or []
        except Exception:
            evidence_items = []
        set_block(project_id, "evidence_pack", query_key, evidence_items)

    # Normalize evidence to texts and keep metadata
    evidence_texts: List[str] = []
    evidence_meta: List[Dict[str, Any]] = []
    for item in evidence_items:
        if isinstance(item, dict):
            evidence_meta.append(item)
            evidence_texts.append(item.get("text", ""))
        else:
            evidence_texts.append(str(item))

    # Compose prompt deterministically
    lines: List[str] = []
    if pinned_rules:
        lines.append("# Rules")
        for r in pinned_rules:
            lines.append(f"- {r}")
        lines.append("")
    if state_block:
        lines.append("# Project State")
        lines.append(state_block)
        lines.append("")
    if evidence_texts:
        lines.append("# Evidence (Top-K)")
        for i, chunk in enumerate(evidence_texts, 1):
            lines.append(f"[{i}] {chunk}")
        lines.append("")
    if summary_block:
        lines.append("# Recent Summary")
        lines.append(summary_block)
        lines.append("")
    lines.append("# User Question")
    lines.append(user_question)
    lines.append("")
    if response_schema:
        lines.append("# Response Schema (JSON)")
        # compact schema printing
        try:
            import json
            lines.append(json.dumps(response_schema, ensure_ascii=False))
        except Exception:
            lines.append(str(response_schema))

    prompt = "\n".join(lines)

    return {
        "pinned_rules": pinned_rules,
        "project_state": state_block,
        "evidence": evidence_texts,
        "evidence_meta": evidence_meta,
        "recent_summary": summary_block,
        "user_question": user_question,
        "response_schema": response_schema,
        "prompt": prompt,
    }
