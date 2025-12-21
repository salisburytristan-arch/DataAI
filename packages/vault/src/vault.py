"""
ArcticCodex Vault: local-first knowledge base.
Main API for ingestion, retrieval, memory, and backup operations.
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib
import uuid

from .storage.objectStore import ObjectStore
from .storage.metadataIndex import MetadataIndex
from .index.vectorIndex import VectorIndex
from .index.embeddingIndex import EmbeddingIndex
from .types import DocRecord, ChunkRecord, FactRecord, SummaryRecord, TombstoneRecord, RecordType
from .ingest.chunker import chunk_by_size
from .retrieval.retriever import Retriever


class Vault:
    """Main Vault interface."""
    
    def __init__(self, vault_path: str):
        """Initialize or open a Vault at the given path."""
        self.path = Path(vault_path)
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage layers
        self.objects = ObjectStore(str(self.path))
        self.index = MetadataIndex(str(self.path))
        self.vector = VectorIndex(str(self.path))
        self.embeddings = EmbeddingIndex(str(self.path))
        self.retriever = Retriever(self)
    
    # Document operations
    
    def import_text(self, text: str, title: str, source_path: str = "", doc_type: str = "text") -> str:
        """
        Import a text document.
        Returns doc_id.
        """
        doc_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Chunk the text
        chunks_data = chunk_by_size(text, chunk_size=1024, overlap=256)
        
        # Create document record
        doc = DocRecord(
            doc_id=doc_id,
            title=title,
            source_path=source_path,
            doc_type=doc_type,
            created_at=now,
            updated_at=now,
            chunk_count=len(chunks_data),
            total_bytes=len(text.encode('utf-8')),
        )
        self.index.put_doc(doc)
        
        # Create chunk records
        for seq, (chunk_text, byte_offset, byte_length) in enumerate(chunks_data):
            chunk_id = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()
            chunk = ChunkRecord(
                chunk_id=chunk_id,
                doc_id=doc_id,
                sequence=seq,
                content=chunk_text,
                content_hash=chunk_id,
                byte_offset=byte_offset,
                byte_length=byte_length,
                created_at=now,
            )
            # Store chunk content in object store and capture hash for provenance
            obj_hash = self.objects.put(chunk.to_dict())
            chunk.object_hash = obj_hash
            self.index.put_chunk(chunk)
            # Index chunk for vector search
            self.vector.index_chunk(chunk_id, chunk_text)
            # Index chunk for embedding search (no-op if unavailable)
            try:
                self.embeddings.index_chunk(chunk_id, chunk_text)
            except Exception:
                # Do not fail ingest due to optional embeddings
                pass
        
        return doc_id
    
    def get_doc(self, doc_id: str) -> Optional[DocRecord]:
        """Get document metadata."""
        return self.index.get_doc(doc_id)
    
    def list_docs(self) -> List[DocRecord]:
        """List all documents."""
        return self.index.list_docs()
    
    # Chunk operations
    
    def get_chunks_for_doc(self, doc_id: str) -> List[ChunkRecord]:
        """Get all chunks for a document."""
        return self.index.get_doc_chunks(doc_id)
    
    def get_chunk(self, chunk_id: str) -> Optional[ChunkRecord]:
        """Get a specific chunk."""
        return self.index.get_chunk(chunk_id)
    
    # Retrieval
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for chunks matching query.
        Returns list of dicts with chunk info and relevance metadata.
        """
        return self.retriever.search_keyword(query, limit=limit)
    
    # Memory / Facts
    
    def put_fact(self, subject: str, predicate: str, obj: str, 
                 confidence: float = 1.0, source_chunk_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a semantic fact.
        Returns fact_id.
        """
        fact_id = str(uuid.uuid4())
        fact = FactRecord(
            fact_id=fact_id,
            subject=subject,
            predicate=predicate,
            obj=obj,
            confidence=confidence,
            source_chunk_id=source_chunk_id,
            metadata=metadata or {},
        )
        self.index.put_fact(fact)
        self.objects.put(fact.to_dict())
        return fact_id
    
    def list_facts(self) -> List[FactRecord]:
        """List all facts."""
        return self.index.list_facts()

    # Summaries
    def put_summary(self, convo_id: str, summary_text: str,
                    key_decisions: List[str] | None = None,
                    open_tasks: List[str] | None = None,
                    definitions: Dict[str, str] | None = None,
                    metadata: Dict[str, Any] | None = None) -> str:
        """
        Store a conversation/thread summary.
        Returns summary_id.
        """
        summary_id = str(uuid.uuid4())
        summary = SummaryRecord(
            summary_id=summary_id,
            convo_id=convo_id,
            summary_text=summary_text,
            key_decisions=key_decisions or [],
            open_tasks=open_tasks or [],
            definitions=definitions or {},
            metadata=metadata or {},
        )
        self.index.put_summary(summary)
        self.objects.put(summary.to_dict())
        return summary_id

    def list_summaries(self) -> List[SummaryRecord]:
        """List all summaries."""
        return self.index.list_summaries()

    def import_fn_frame(self, frame_str: str, verify: bool = False, public_key: Optional[bytes] = None) -> tuple[str, Optional[dict]]:
        """Import a canonical ForgeNumerics frame and store as a Vault record.
        
        Args:
            frame_str: The FN frame string (may include signature)
            verify: Whether to verify signature before importing
            public_key: Public key for signature verification (if verify=True)
            
        Returns:
            Tuple of (record_id, verification_result) where verification_result is None if not verified
        """
        # Lazy import to avoid circular dependency
        import sys
        from pathlib import Path
        core_root = Path(self.path).parent.parent / "packages" / "core" / "src"
        if str(core_root.parent.parent.parent) not in sys.path:
            sys.path.insert(0, str(core_root.parent.parent.parent))
        from packages.core.src.fn_bridge import from_fn_summary, from_fn_fact
        from packages.core.src.frame_verifier import FrameVerifier
        
        # Verify signature if requested
        verify_result = None
        frame_to_parse = frame_str
        if verify and public_key:
            verifier = FrameVerifier()
            verify_result = verifier.verify_frame(frame_str, public_key)
            if not verify_result.verified:
                raise ValueError(f"Frame verification failed for signer {verify_result.signer_id}")
            # Strip signature before parsing
            frame_to_parse = FrameVerifier._strip_signature(frame_str)
        
        # Parse frame to determine type
        try:
            from src.frames import Frame
        except:
            fn_root = Path(self.path).parent.parent / "ForgeNumerics_Language"
            if str(fn_root) not in sys.path:
                sys.path.insert(0, str(fn_root))
            from src.frames import Frame
        
        frame = Frame.parse(frame_to_parse)
        header_dict = dict(frame.header)
        frame_type = header_dict.get("TYPE")
        
        if frame_type == "SUMMARY":
            summary = from_fn_summary(frame_to_parse)
            self.index.put_summary(summary)
            self.objects.put(summary.to_dict())
            return summary.summary_id, verify_result
        elif frame_type == "FACT":
            fact = from_fn_fact(frame_to_parse)
            self.index.put_fact(fact)
            self.objects.put(fact.to_dict())
            return fact.fact_id, verify_result
        else:
            raise ValueError(f"Unsupported frame type: {frame_type}")

    
    def import_fn_frames_batch(self, frames: list[str], verify: bool = False, public_key: Optional[bytes] = None) -> list[tuple[str, Optional[dict]]]:
        """
        Import multiple FN frames in batch.
        
        Args:
            frames: List of FN frame strings
            verify: Whether to verify signatures
            public_key: Public key for verification
            
        Returns:
            List of (record_id, verification_result) tuples
        """
        results = []
        for frame_str in frames:
            try:
                record_id, verify_result = self.import_fn_frame(frame_str, verify, public_key)
                results.append((record_id, verify_result))
            except Exception as e:
                # Log error but continue
                print(f"Warning: Failed to import frame: {e}")
                results.append((None, {"error": str(e), "verified": False}))
        return results

    
    # Deletion / Tombstones
    
    def forget(self, record_id: str, reason: Optional[str] = None) -> Optional[str]:
        """
        Soft-delete a record by writing tombstones.

        For documents, cascades tombstones to all associated chunks. Returns the
        primary tombstone ID for the record, or None if the record is unknown.
        """
        primary_tombstone: Optional[str] = None

        # Handle document deletion and cascade to chunks
        doc = self.index.get_doc(record_id)
        if doc:
            # Get chunks BEFORE tombstoning the doc
            chunks_to_delete = self.index.get_doc_chunks(record_id)
            
            primary_tombstone = str(uuid.uuid4())
            ts_doc = TombstoneRecord(
                tombstone_id=primary_tombstone,
                target_id=record_id,
                target_type=RecordType.DOC,
                reason=reason,
            )
            self.index.put_tombstone(ts_doc)
            self.objects.put(ts_doc.to_dict())

            for chunk in chunks_to_delete:
                ts_chunk_id = str(uuid.uuid4())
                ts_chunk = TombstoneRecord(
                    tombstone_id=ts_chunk_id,
                    target_id=chunk.chunk_id,
                    target_type=RecordType.CHUNK,
                    reason=reason,
                )
                self.index.put_tombstone(ts_chunk)
                self.objects.put(ts_chunk.to_dict())
                self.objects.put(ts_chunk.to_dict())
            return primary_tombstone

        # Handle standalone chunk deletion
        chunk = self.index.get_chunk(record_id)
        if chunk:
            primary_tombstone = str(uuid.uuid4())
            ts_chunk = TombstoneRecord(
                tombstone_id=primary_tombstone,
                target_id=record_id,
                target_type=RecordType.CHUNK,
                reason=reason,
            )
            self.index.put_tombstone(ts_chunk)
            self.objects.put(ts_chunk.to_dict())
            return primary_tombstone

        # Handle fact deletion
        fact = self.index.get_fact(record_id)
        if fact:
            primary_tombstone = str(uuid.uuid4())
            ts_fact = TombstoneRecord(
                tombstone_id=primary_tombstone,
                target_id=record_id,
                target_type=RecordType.FACT,
                reason=reason,
            )
            self.index.put_tombstone(ts_fact)
            self.objects.put(ts_fact.to_dict())
            return primary_tombstone

        # Unknown record
        return None
    
    # Diagnostics
    
    def stats(self) -> Dict[str, Any]:
        """Get Vault statistics."""
        obj_stats = self.objects.stats()
        return {
            "doc_count": len(self.list_docs()),
            "chunk_count": len([c for d in self.list_docs() for c in self.get_chunks_for_doc(d.doc_id)]),
            "fact_count": len(self.list_facts()),
            "facts_count": len(self.list_facts()),
            "summary_count": len(self.list_summaries()),
            "object_store": obj_stats,
        }
    
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify vault integrity."""
        results = {
            "objects_verified": 0,
            "objects_failed": 0,
            "errors": [],
        }
        
        for obj_hash in self.objects.list_objects():
            if self.objects.verify_integrity(obj_hash):
                results["objects_verified"] += 1
            else:
                results["objects_failed"] += 1
                results["errors"].append(f"Object {obj_hash} integrity check failed")
        
        return results
