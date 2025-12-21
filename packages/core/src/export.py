from typing import Dict, Any, List
import json
from pathlib import Path

# Robust import of Vault
try:
    from packages.vault.src.vault import Vault
except Exception:
    import sys
    from pathlib import Path as P
    root = P(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.vault.src.vault import Vault


def export_conversation(vault: Vault, convo_id: str, out_path: str) -> Dict[str, Any]:
    """
    Export summaries and facts for a conversation ID to JSONL.
    Returns basic stats.
    """
    summaries = [s for s in vault.list_summaries() if s.convo_id == convo_id]
    facts = [f for f in vault.list_facts() if f.metadata.get("convo_id") == convo_id]

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for s in summaries:
            f.write(json.dumps({
                "type": "summary",
                "summary_id": s.summary_id,
                "convo_id": s.convo_id,
                "summary_text": s.summary_text,
                "key_decisions": s.key_decisions,
                "open_tasks": s.open_tasks,
                "definitions": s.definitions,
                "created_at": s.created_at.isoformat(),
                "metadata": s.metadata,
            }, ensure_ascii=False) + "\n")
        for x in facts:
            f.write(json.dumps({
                "type": "fact",
                "fact_id": x.fact_id,
                "subject": x.subject,
                "predicate": x.predicate,
                "obj": x.obj,
                "confidence": x.confidence,
                "source_chunk_id": x.source_chunk_id,
                "created_at": x.created_at.isoformat(),
                "metadata": x.metadata,
            }, ensure_ascii=False) + "\n")
    return {"summaries": len(summaries), "facts": len(facts), "path": str(out)}
