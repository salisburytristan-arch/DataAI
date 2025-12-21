"""
Vault record types and data structures.
Core abstractions for the ArcticCodex Vault knowledge base.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import json


class RecordType(str, Enum):
    """Record types in the Vault."""
    DOC = "DOC"              # Document metadata
    CHUNK = "CHUNK"          # Content chunk
    FACT = "FACT"            # Knowledge triple (subject-predicate-object)
    SUMMARY = "SUMMARY"      # Conversation/thread summary
    PREF = "PREF"            # User preference (format, style, defaults)
    TRACE = "TRACE"          # Tool call / model call trace
    EMBEDDING = "EMBEDDING"  # Vector embedding
    TOMBSTONE = "TOMBSTONE"  # Deletion marker


@dataclass
class DocRecord:
    """Document metadata record."""
    doc_id: str               # Unique doc identifier
    title: str                # Document title
    source_path: str          # Original file path
    doc_type: str             # "text", "markdown", "json", etc.
    created_at: datetime      # Import timestamp
    updated_at: datetime      # Last update timestamp
    chunk_count: int          # Number of chunks
    total_bytes: int          # Total original bytes
    encoding: str = "utf-8"   # Text encoding
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra fields (tags, source, etc.)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "source_path": self.source_path,
            "doc_type": self.doc_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "chunk_count": self.chunk_count,
            "total_bytes": self.total_bytes,
            "encoding": self.encoding,
            "metadata": self.metadata,
        }
    
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "DocRecord":
        return DocRecord(
            doc_id=d["doc_id"],
            title=d["title"],
            source_path=d["source_path"],
            doc_type=d["doc_type"],
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
            chunk_count=d["chunk_count"],
            total_bytes=d["total_bytes"],
            encoding=d.get("encoding", "utf-8"),
            metadata=d.get("metadata", {}),
        )


@dataclass
class ChunkRecord:
    """Content chunk record."""
    chunk_id: str             # Unique chunk identifier (hash-based)
    doc_id: str               # Parent document ID
    sequence: int             # Order within document (0-indexed)
    content: str              # Chunk text content
    content_hash: str         # SHA256 of content (canonical)
    byte_offset: int          # Byte offset in original file
    byte_length: int          # Byte length of chunk in original
    created_at: datetime      # Creation timestamp
    object_hash: Optional[str] = None  # Hash of persisted chunk object in object store
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra fields
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "sequence": self.sequence,
            "content": self.content,
            "content_hash": self.content_hash,
            "byte_offset": self.byte_offset,
            "byte_length": self.byte_length,
            "created_at": self.created_at.isoformat(),
            "object_hash": self.object_hash,
            "metadata": self.metadata,
        }
    
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ChunkRecord":
        return ChunkRecord(
            chunk_id=d["chunk_id"],
            doc_id=d["doc_id"],
            sequence=d["sequence"],
            content=d["content"],
            content_hash=d["content_hash"],
            byte_offset=d["byte_offset"],
            byte_length=d["byte_length"],
            created_at=datetime.fromisoformat(d["created_at"]),
            object_hash=d.get("object_hash"),
            metadata=d.get("metadata", {}),
        )


@dataclass
class FactRecord:
    """Knowledge triple (semantic fact)."""
    fact_id: str              # Unique fact identifier
    subject: str              # Subject entity/token
    predicate: str            # Predicate/relation
    obj: str                  # Object entity/token
    confidence: float = 1.0   # Confidence 0.0-1.0
    source_chunk_id: Optional[str] = None  # Which chunk this came from
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "obj": self.obj,
            "confidence": self.confidence,
            "source_chunk_id": self.source_chunk_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SummaryRecord:
    """Conversation or thread summary."""
    summary_id: str           # Unique ID
    convo_id: str             # Conversation ID
    summary_text: str         # Summary content
    key_decisions: List[str] = field(default_factory=list)  # Important decisions
    open_tasks: List[str] = field(default_factory=list)    # Outstanding tasks
    definitions: Dict[str, str] = field(default_factory=dict)  # Term definitions
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "convo_id": self.convo_id,
            "summary_text": self.summary_text,
            "key_decisions": self.key_decisions,
            "open_tasks": self.open_tasks,
            "definitions": self.definitions,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class TombstoneRecord:
    """Deletion marker for "forget" operations."""
    tombstone_id: str         # Unique ID
    target_id: str            # ID of deleted record
    target_type: str          # Type of deleted record (DOC, CHUNK, FACT, etc.)
    reason: Optional[str] = None  # Reason for deletion
    deleted_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tombstone_id": self.tombstone_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "reason": self.reason,
            "deleted_at": self.deleted_at.isoformat(),
        }
