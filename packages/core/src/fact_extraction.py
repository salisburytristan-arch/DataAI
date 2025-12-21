import re
from typing import List, Tuple

# Very simple SVO extraction heuristics
# Patterns: "X is a Y", "X is an Y", "X is Y", "X are Y"
_PATTERNS = [
    re.compile(r"\b([A-Za-z][A-Za-z0-9_\- ]+)\s+is\s+an?\s+([A-Za-z][A-Za-z0-9_\- ]+)\b", re.IGNORECASE),
    re.compile(r"\b([A-Za-z][A-Za-z0-9_\- ]+)\s+is\s+([A-Za-z][A-Za-z0-9_\- ]+)\b", re.IGNORECASE),
    re.compile(r"\b([A-Za-z][A-Za-z0-9_\- ]+)\s+are\s+([A-Za-z][A-Za-z0-9_\- ]+)\b", re.IGNORECASE),
]


def extract_svo_facts(text: str) -> List[Tuple[str, str, str]]:
    facts: List[Tuple[str, str, str]] = []
    for pat in _PATTERNS:
        for m in pat.finditer(text):
            subj = m.group(1).strip()
            obj = m.group(2).strip()
            pred = "is_a" if "are" in pat.pattern or "is" in pat.pattern else "is"
            # Normalize simple casing
            facts.append((subj, pred, obj))
    return facts
