from typing import Dict, Any, List
from datetime import datetime

# Robust imports for ForgeNumerics modules
try:
    from src.frames import Frame, make_blob_t
    from src.canonicalize import canonicalize_string
except Exception:
    import sys
    from pathlib import Path
    import importlib
    # Add ForgeNumerics_Language folder to sys.path so 'src.*' resolves
    fn_root = Path(__file__).resolve().parents[4] / "ForgeNumerics_Language"
    if str(fn_root) not in sys.path:
        sys.path.insert(0, str(fn_root))
    # Alias ForgeNumerics_Language.src to top-level 'src' to satisfy internal imports
    fn_pkg = importlib.import_module('ForgeNumerics_Language.src')
    sys.modules['src'] = fn_pkg
    from src.frames import Frame, make_blob_t
    from src.canonicalize import canonicalize_string

# Robust import for Vault types
try:
    from packages.vault.src.types import SummaryRecord, FactRecord
except Exception:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from packages.vault.src.types import SummaryRecord, FactRecord


def to_fn_summary(summary: SummaryRecord) -> str:
    """Convert a Vault SummaryRecord to a canonical ForgeNumerics frame string."""
    header = [
        ("TYPE", "SUMMARY"),
        ("SUMMARY_ID", summary.summary_id),
        ("CONVO_ID", summary.convo_id),
        ("CREATED_AT", summary.created_at.isoformat()),
    ]
    # Use BLOB-T for arbitrary text payload
    payload_blob = make_blob_t(summary.summary_text.encode("utf-8"))
    frame = Frame(header=header, payload=[payload_blob])
    return canonicalize_string(frame.serialize())


def to_fn_fact(fact: FactRecord) -> str:
    """Convert a Vault FactRecord to a canonical ForgeNumerics frame string."""
    header = [
        ("TYPE", "FACT"),
        ("FACT_ID", fact.fact_id),
        ("CONFIDENCE", f"{fact.confidence:.3f}"),
    ]
    if fact.source_chunk_id:
        header.append(("SOURCE_CHUNK_ID", fact.source_chunk_id))
    # Payload as literal WORD tokens for S, P, O
    payload = [
        f"≛SUBJ⦙≛{fact.subject}",
        f"≛PRED⦙≛{fact.predicate}",
        f"≛OBJ⦙≛{fact.obj}",
    ]
    frame = Frame(header=header, payload=payload)
    return canonicalize_string(frame.serialize())


def from_fn_summary(frame_str: str) -> SummaryRecord:
    """Parse a canonical FN frame string back into a SummaryRecord."""
    from src.frames import Frame, trits_to_bytes, MODE_NUM, TRIT_TWO, TRIT_ZERO
    frame = Frame.parse(frame_str)
    header_dict = dict(frame.header)
    # Extract BLOB-T payload
    if not frame.payload or not frame.payload[0].startswith(MODE_NUM + TRIT_TWO + TRIT_ZERO):
        raise ValueError("Expected BLOB-T payload in SUMMARY frame")
    blob_token = frame.payload[0]
    blob_trits = blob_token[3:]  # skip MODE_NUM + profile
    text_bytes = trits_to_bytes(blob_trits)
    summary_text = text_bytes.decode("utf-8")
    return SummaryRecord(
        summary_id=header_dict["SUMMARY_ID"],
        convo_id=header_dict["CONVO_ID"],
        summary_text=summary_text,
        created_at=datetime.fromisoformat(header_dict["CREATED_AT"]),
    )


def from_fn_fact(frame_str: str) -> FactRecord:
    """Parse a canonical FN frame string back into a FactRecord."""
    frame = Frame.parse(frame_str)
    header_dict = dict(frame.header)
    # Parse payload word tokens (format: ≛SUBJ, ≛agent, ≛PRED, ≛knows, ≛OBJ, ≛python)
    subj = pred = obj = ""
    i = 0
    while i < len(frame.payload):
        token = frame.payload[i]
        if token == "≛SUBJ" and i + 1 < len(frame.payload):
            subj = frame.payload[i + 1].lstrip("≛")
            i += 2
        elif token == "≛PRED" and i + 1 < len(frame.payload):
            pred = frame.payload[i + 1].lstrip("≛")
            i += 2
        elif token == "≛OBJ" and i + 1 < len(frame.payload):
            obj = frame.payload[i + 1].lstrip("≛")
            i += 2
        else:
            i += 1
    return FactRecord(
        fact_id=header_dict["FACT_ID"],
        subject=subj,
        predicate=pred,
        obj=obj,
        confidence=float(header_dict.get("CONFIDENCE", "1.0")),
        source_chunk_id=header_dict.get("SOURCE_CHUNK_ID"),
    )


def to_fn_train_pair(instruction: str, completion: str, metadata: Dict[str, Any] = None) -> str:
    """Convert instruction/completion pair to a canonical TRAIN_PAIR FN frame."""
    header = [
        ("TYPE", "TRAIN_PAIR"),
        ("CREATED_AT", datetime.now().isoformat()),
    ]
    if metadata:
        for k, v in sorted(metadata.items()):
            header.append((k.upper(), str(v)))
    # Payload: two BLOB-T tokens (instruction, completion)
    instr_blob = make_blob_t(instruction.encode("utf-8"))
    comp_blob = make_blob_t(completion.encode("utf-8"))
    frame = Frame(header=header, payload=[instr_blob, comp_blob])
    return canonicalize_string(frame.serialize())


def export_conversation_fn(vault, convo_id: str) -> List[str]:
    """Export all summaries and facts for a conversation as canonical FN frames (strings)."""
    summaries = [s for s in vault.list_summaries() if s.convo_id == convo_id]
    facts = [f for f in vault.list_facts() if f.metadata.get("convo_id") == convo_id]
    frames: List[str] = []
    for s in summaries:
        frames.append(to_fn_summary(s))
    for f in facts:
        frames.append(to_fn_fact(f))
    return frames
