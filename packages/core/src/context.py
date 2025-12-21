from dataclasses import dataclass
from typing import Any, Dict, List

# Lazy import to tolerate test runner CWD
try:
    from packages.vault.src.vault import Vault
except Exception:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.vault.src.vault import Vault


@dataclass
class BuiltContext:
    system: str
    user: str
    prompt: str
    evidence: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]


class ContextBuilder:
    def __init__(self, system_rules: str | None = None) -> None:
        self.system_rules = system_rules or (
            "You are the ArcticCodex Agent. Use only provided evidence. "
            "Cite chunk_ids for claims. Be concise."
        )

    def build(self, query: str, vault: Vault, limit: int = 5) -> BuiltContext:
        pack = vault.retriever.get_evidence_pack(query, limit=limit)
        chunks = pack.get("chunks", [])
        citations = pack.get("citations", [])

        lines: List[str] = []
        lines.append("System Rules:\n" + self.system_rules)
        lines.append("\nUser Question:\n" + query)
        lines.append("\nEvidence:")
        for i, ch in enumerate(chunks, 1):
            snippet = ch.get("content", "").strip().replace("\n", " ")
            if len(snippet) > 240:
                snippet = snippet[:240] + "…"
            lines.append(
                f"- [{i}] chunk_id={ch.get('chunk_id','?')} doc={ch.get('doc_title','?')}: {snippet}"
            )
        prompt = "\n".join(lines)

        return BuiltContext(
            system=self.system_rules,
            user=query,
            prompt=prompt,
            evidence=chunks,
            citations=citations,
        )
