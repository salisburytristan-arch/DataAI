"""
Metadata index for fast lookups.
Maintains in-memory index of all docs, chunks, facts for quick retrieval.
Can be persisted to JSON for recovery.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..types import DocRecord, ChunkRecord, FactRecord, TombstoneRecord, SummaryRecord


class MetadataIndex:
    """In-memory index with JSON persistence."""
    
    def __init__(self, root_path: str):
        """Initialize index, optionally loading from persisted state."""
        self.root = Path(root_path)
        self.index_dir = self.root / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory tables
        self.docs: Dict[str, dict] = {}      # doc_id -> DocRecord (as dict)
        self.chunks: Dict[str, dict] = {}    # chunk_id -> ChunkRecord (as dict)
        self.doc_chunks: Dict[str, List[str]] = {}  # doc_id -> [chunk_ids]
        self.facts: Dict[str, dict] = {}    # fact_id -> FactRecord (as dict)
        self.summaries: Dict[str, dict] = {}  # summary_id -> SummaryRecord (as dict)
        self.tombstones: Dict[str, dict] = {}  # tombstone_id -> TombstoneRecord (as dict)
        self.deleted_ids: set = set()       # Set of deleted record IDs
        
        self._load()
    
    def _persist_path(self, table_name: str) -> Path:
        """Get persistence file path for a table."""
        return self.index_dir / f"{table_name}.json"
    
    def _load(self):
        """Load index from disk if it exists."""
        try:
            if (self.index_dir / "docs.json").exists():
                with open(self.index_dir / "docs.json", 'r', encoding='utf-8') as f:
                    self.docs = json.load(f)
            if (self.index_dir / "chunks.json").exists():
                with open(self.index_dir / "chunks.json", 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
            if (self.index_dir / "doc_chunks.json").exists():
                with open(self.index_dir / "doc_chunks.json", 'r', encoding='utf-8') as f:
                    self.doc_chunks = json.load(f)
            if (self.index_dir / "facts.json").exists():
                with open(self.index_dir / "facts.json", 'r', encoding='utf-8') as f:
                    self.facts = json.load(f)
            if (self.index_dir / "summaries.json").exists():
                with open(self.index_dir / "summaries.json", 'r', encoding='utf-8') as f:
                    self.summaries = json.load(f)
            if (self.index_dir / "tombstones.json").exists():
                with open(self.index_dir / "tombstones.json", 'r', encoding='utf-8') as f:
                    self.tombstones = json.load(f)
                    # Rebuild deleted_ids set
                    for t in self.tombstones.values():
                        self.deleted_ids.add(t["target_id"])
        except Exception as e:
            print(f"Warning: Could not load index: {e}")
    
    def _persist(self):
        """Persist index to disk."""
        with open(self.index_dir / "docs.json", 'w', encoding='utf-8') as f:
            json.dump(self.docs, f, indent=2, ensure_ascii=False)
        with open(self.index_dir / "chunks.json", 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)
        with open(self.index_dir / "doc_chunks.json", 'w', encoding='utf-8') as f:
            json.dump(self.doc_chunks, f, indent=2, ensure_ascii=False)
        with open(self.index_dir / "facts.json", 'w', encoding='utf-8') as f:
            json.dump(self.facts, f, indent=2, ensure_ascii=False)
        with open(self.index_dir / "summaries.json", 'w', encoding='utf-8') as f:
            json.dump(self.summaries, f, indent=2, ensure_ascii=False)
        with open(self.index_dir / "tombstones.json", 'w', encoding='utf-8') as f:
            json.dump(self.tombstones, f, indent=2, ensure_ascii=False)
    
    # Document operations
    
    def put_doc(self, doc: DocRecord) -> None:
        """Store document record."""
        self.docs[doc.doc_id] = doc.to_dict()
        self.doc_chunks[doc.doc_id] = []
        self._persist()
    
    def get_doc(self, doc_id: str) -> Optional[DocRecord]:
        """Get document by ID."""
        if doc_id in self.deleted_ids:
            return None
        if doc_id not in self.docs:
            return None
        return DocRecord.from_dict(self.docs[doc_id])
    
    def list_docs(self) -> List[DocRecord]:
        """List all non-deleted documents."""
        return [
            DocRecord.from_dict(d)
            for doc_id, d in self.docs.items()
            if doc_id not in self.deleted_ids
        ]
    
    # Chunk operations
    
    def put_chunk(self, chunk: ChunkRecord) -> None:
        """Store chunk record."""
        self.chunks[chunk.chunk_id] = chunk.to_dict()
        if chunk.doc_id not in self.doc_chunks:
            self.doc_chunks[chunk.doc_id] = []
        if chunk.chunk_id not in self.doc_chunks[chunk.doc_id]:
            self.doc_chunks[chunk.doc_id].append(chunk.chunk_id)
        self._persist()
    
    def get_chunk(self, chunk_id: str) -> Optional[ChunkRecord]:
        """Get chunk by ID."""
        if chunk_id in self.deleted_ids:
            return None
        if chunk_id not in self.chunks:
            return None
        return ChunkRecord.from_dict(self.chunks[chunk_id])
    
    def get_doc_chunks(self, doc_id: str) -> List[ChunkRecord]:
        """Get all chunks for a document."""
        if doc_id in self.deleted_ids:
            return []
        chunk_ids = self.doc_chunks.get(doc_id, [])
        return [
            ChunkRecord.from_dict(self.chunks[cid])
            for cid in chunk_ids
            if cid not in self.deleted_ids and cid in self.chunks
        ]
    
    # Fact operations
    
    def put_fact(self, fact: FactRecord) -> None:
        """Store fact record."""
        self.facts[fact.fact_id] = fact.to_dict()
        self._persist()
    
    def get_fact(self, fact_id: str) -> Optional[FactRecord]:
        """Get fact by ID."""
        if fact_id in self.deleted_ids:
            return None
        if fact_id not in self.facts:
            return None
        from ..types import FactRecord
        d = self.facts[fact_id]
        return FactRecord(
            fact_id=d["fact_id"],
            subject=d["subject"],
            predicate=d["predicate"],
            obj=d["obj"],
            confidence=d.get("confidence", 1.0),
            source_chunk_id=d.get("source_chunk_id"),
            created_at=datetime.fromisoformat(d["created_at"]),
            metadata=d.get("metadata", {}),
        )
    
    def list_facts(self) -> List[FactRecord]:
        """List all non-deleted facts."""
        from ..types import FactRecord
        result = []
        for fact_id, d in self.facts.items():
            if fact_id in self.deleted_ids:
                continue
            result.append(FactRecord(
                fact_id=d["fact_id"],
                subject=d["subject"],
                predicate=d["predicate"],
                obj=d["obj"],
                confidence=d.get("confidence", 1.0),
                source_chunk_id=d.get("source_chunk_id"),
                created_at=datetime.fromisoformat(d["created_at"]),
                metadata=d.get("metadata", {}),
            ))
        return result

    # Summary operations

    def put_summary(self, summary: SummaryRecord) -> None:
        """Store a summary record."""
        self.summaries[summary.summary_id] = summary.to_dict()
        self._persist()

    def get_summary(self, summary_id: str) -> Optional[SummaryRecord]:
        """Get summary by ID."""
        if summary_id in self.deleted_ids:
            return None
        if summary_id not in self.summaries:
            return None
        d = self.summaries[summary_id]
        return SummaryRecord(
            summary_id=d["summary_id"],
            convo_id=d["convo_id"],
            summary_text=d["summary_text"],
            key_decisions=d.get("key_decisions", []),
            open_tasks=d.get("open_tasks", []),
            definitions=d.get("definitions", {}),
            created_at=datetime.fromisoformat(d["created_at"]),
            metadata=d.get("metadata", {}),
        )

    def list_summaries(self) -> List[SummaryRecord]:
        """List all non-deleted summaries."""
        result: List[SummaryRecord] = []
        for sid, d in self.summaries.items():
            if sid in self.deleted_ids:
                continue
            result.append(SummaryRecord(
                summary_id=d["summary_id"],
                convo_id=d["convo_id"],
                summary_text=d["summary_text"],
                key_decisions=d.get("key_decisions", []),
                open_tasks=d.get("open_tasks", []),
                definitions=d.get("definitions", {}),
                created_at=datetime.fromisoformat(d["created_at"]),
                metadata=d.get("metadata", {}),
            ))
        return result
    
    # Deletion / Tombstones
    
    def put_tombstone(self, tombstone: TombstoneRecord) -> None:
        """Record a deletion."""
        self.tombstones[tombstone.tombstone_id] = tombstone.to_dict()
        self.deleted_ids.add(tombstone.target_id)
        self._persist()
    
    def is_deleted(self, record_id: str) -> bool:
        """Check if a record has been deleted."""
        return record_id in self.deleted_ids
