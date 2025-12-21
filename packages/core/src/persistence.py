from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

# Import Vault with robust path handling
try:
    from packages.vault.src.vault import Vault
    from .fact_extraction import extract_svo_facts
except Exception:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.vault.src.vault import Vault


def persist_response(vault: Vault, convo_id: Optional[str], query: str, response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist an agent response into the Vault as a summary.
    Optionally extracts trivial 'facts' from citations (placeholder).
    Returns a dict with written IDs.
    """
    convo = convo_id or str(uuid.uuid4())
    text = response.get("text", "")
    citations: List[Dict[str, Any]] = response.get("citations", [])

    summary_id = vault.put_summary(
        convo_id=convo,
        summary_text=text,
        key_decisions=[],
        open_tasks=[],
        definitions={},
        metadata={
            "query": query,
            "used_chunks": [c.get("chunk_id") for c in citations if c.get("chunk_id")],
            "created_at": datetime.now().isoformat(),
        },
    )

    # Basic fact extraction from response text
    fact_ids: List[str] = []
    svo = extract_svo_facts(text)
    source_chunk_id = citations[0].get("chunk_id") if citations else None
    for subj, pred, obj in svo:
        fid = vault.put_fact(
            subject=subj,
            predicate=pred,
            obj=obj,
            confidence=0.6,
            source_chunk_id=source_chunk_id,
            metadata={"convo_id": convo, "query": query}
        )
        fact_ids.append(fid)

    return {"summary_id": summary_id, "convo_id": convo, "fact_ids": fact_ids}
