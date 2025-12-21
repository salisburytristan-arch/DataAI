# ArcticCodex Core → ForgeNumerics Bridge

Complete bidirectional bridge between Vault records and ForgeNumerics canonical frames.

## Status: ✅ Complete

### What Works

**Export (Python → FN Frames)**
- `to_fn_summary(SummaryRecord)` → canonical SUMMARY frame
- `to_fn_fact(FactRecord)` → canonical FACT frame  
- `to_fn_train_pair(instruction, completion, metadata)` → canonical TRAIN_PAIR frame
- `export_conversation_fn(vault, convo_id)` → list of FN frame strings

**Import (FN Frames → Python)**
- `from_fn_summary(frame_str)` → SummaryRecord
- `from_fn_fact(frame_str)` → FactRecord
- `Vault.import_fn_frame(frame_str)` → writes to storage and index

**CLI Commands**
```powershell
# Export conversation as FN frames
python -m packages.core.src.cli export-fn --vault ./vault --convo "session-1" --out ./out/session-1.fn.jsonl

# Import FN frames into Vault
python -m packages.core.src.cli import-fn --vault ./vault --file ./out/session-1.fn.jsonl
```

### Frame Formats

**SUMMARY Frame**
```
⧆≛TYPE⦙≛SUMMARY∴≛SUMMARY_ID⦙≛<uuid>∴≛CONVO_ID⦙≛<id>∴≛CREATED_AT⦙≛<iso>∷≗Φ⊙<blob_trits>⧈
```
- Headers: TYPE, SUMMARY_ID, CONVO_ID, CREATED_AT (lexicographically sorted)
- Payload: Single BLOB-T token encoding summary_text as UTF-8

**FACT Frame**
```
⧆≛TYPE⦙≛FACT∴≛CONFIDENCE⦙≛0.600∴≛FACT_ID⦙≛<uuid>∴≛SOURCE_CHUNK_ID⦙≛<hash>∷≛SUBJ⦙≛<s>⦙≛PRED⦙≛<p>⦙≛OBJ⦙≛<o>⧈
```
- Headers: TYPE, FACT_ID, CONFIDENCE, SOURCE_CHUNK_ID (sorted)
- Payload: Word tokens for SUBJ, PRED, OBJ

**TRAIN_PAIR Frame**
```
⧆≛TYPE⦙≛TRAIN_PAIR∴≛CREATED_AT⦙≛<iso>∴≛SOURCE⦙≛<src>∷≗Φ⊙<instruction_blob>⦙≗Φ⊙<completion_blob>⧈
```
- Headers: TYPE, CREATED_AT, custom metadata (sorted)
- Payload: Two BLOB-T tokens (instruction, completion)

### Guarantees

1. **Canonical**: All frames use `canonicalize_string()` before export
2. **Parsable**: All exported frames pass `Frame.parse()` verification  
3. **Idempotent**: `canonicalize(canonicalize(x)) == canonicalize(x)`
4. **Roundtrip**: `from_fn_*(to_fn_*(record))` preserves data
5. **Verifiable**: Frames can be hashed, signed, and validated

### Test Coverage

- `test_fn_bridge.py`: Export + canonicalization + parsing
- `test_fn_roundtrip.py`: Import/export roundtrip + TRAIN_PAIR generation
- Total: 8/8 core tests passing

### Use Cases

**Training Data Export**
```python
from packages.core.src.fn_bridge import to_fn_train_pair

pairs = []
for interaction in curated_interactions:
    frame = to_fn_train_pair(
        instruction=interaction.user_query,
        completion=interaction.agent_response,
        metadata={"quality": "high", "source": "review_queue"}
    )
    pairs.append(frame)

with open("train.fn.jsonl", "w") as f:
    for p in pairs:
        f.write(p + "\n")
```

**Knowledge Transfer**
```python
# Export from vault1
frames = export_conversation_fn(vault1, "session-42")

# Import into vault2  
for frame in frames:
    vault2.import_fn_frame(frame)
```

**Audit Trail**
```python
# All summaries/facts are verifiable canonical frames
frame_str = to_fn_summary(summary)
frame_hash = hashlib.sha256(frame_str.encode()).hexdigest()
# Store frame_hash in audit log
```

### Next Steps

- Add encryption wrapper for frames (encrypt BLOB-T payloads)
- Add signature support (sign canonical frame strings)
- Extend to DOC/CHUNK frames for full Vault export
- Add streaming frame parser for large .fn.jsonl files
