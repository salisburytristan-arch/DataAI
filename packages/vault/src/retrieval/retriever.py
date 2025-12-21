"""
Retrieval pipeline for Vault.
Keyword search, ranking, and citation building.
"""
from typing import List, Dict, Any, Optional
from ..types import ChunkRecord


class Retriever:
    """Retrieval interface for Vault."""
    
    def __init__(self, vault):
        """Initialize retriever with vault reference."""
        self.vault = vault
    
    def search_keyword(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Simple keyword search across all chunks.
        Returns ranked list of matching chunks with scores.
        """
        query_terms = set(query.lower().split())
        
        results = []
        for doc in self.vault.list_docs():
            for chunk in self.vault.get_chunks_for_doc(doc.doc_id):
                # Score based on term frequency
                chunk_text_lower = chunk.content.lower()
                score = sum(chunk_text_lower.count(term) for term in query_terms)
                
                if score > 0:
                    results.append({
                        "chunk_id": chunk.chunk_id,
                        "doc_id": chunk.doc_id,
                        "doc_title": doc.title,
                        "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                        "score": score,
                        "sequence": chunk.sequence,
                    })
        
        # Sort by score descending, then by document/sequence
        results.sort(key=lambda r: (-r["score"], r["doc_id"], r["sequence"]))
        
        return results[:limit]
    
    def get_evidence_pack(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get a pack of evidence for a query (for RAG).
        Returns chunks + citations + summaries.
        """
        search_results = self.search_keyword(query, limit=limit)
        
        chunks = []
        citations = []
        
        for result in search_results:
            chunk = self.vault.get_chunk(result["chunk_id"])
            doc = self.vault.get_doc(result["doc_id"])
            
            if chunk and doc:
                verified = False
                obj_hash = chunk.object_hash
                if obj_hash:
                    verified = self.vault.objects.verify_integrity(obj_hash)
                chunks.append({
                    "chunk_id": chunk.chunk_id,
                    "doc_id": doc.doc_id,
                    "doc_title": doc.title,
                    "doc_source": doc.source_path,
                    "sequence": chunk.sequence,
                    "content": chunk.content,
                    "object_hash": obj_hash,
                    "object_verified": verified,
                })
                
                citations.append({
                    "chunk_id": chunk.chunk_id,
                    "doc_id": doc.doc_id,
                    "doc_title": doc.title,
                    "doc_source": doc.source_path,
                    "offset": chunk.byte_offset,
                    "byte_length": chunk.byte_length,
                    "content_hash": chunk.content_hash,
                    "object_hash": obj_hash,
                    "object_verified": verified,
                    "relevance_score": result["score"],
                })
        
        return {
            "query": query,
            "chunks": chunks,
            "citations": citations,
            "chunk_count": len(chunks),
        }

    def search_hybrid(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid search combining keyword scoring and vector similarity.
        Prefers sentence-transformer embeddings when available; otherwise falls back to TF-IDF vectors.
        Merges candidate lists and reranks by normalized scores.
        """
        kw = self.search_keyword(query, limit=limit * 2)
        # Prefer embedding-based search if available and ready
        vec_pairs: List[tuple[str, float]] = []
        try:
            if hasattr(self.vault, "embeddings") and self.vault.embeddings.is_ready():
                vec_pairs = self.vault.embeddings.search(query, limit=limit * 2)
            else:
                vec_pairs = self.vault.vector.search(query, limit=limit * 2)
        except Exception:
            vec_pairs = self.vault.vector.search(query, limit=limit * 2)
        vec_scores = dict(vec_pairs)

        # Normalize keyword scores
        max_kw = max((r["score"] for r in kw), default=1)
        merged: Dict[str, Dict[str, Any]] = {}
        for r in kw:
            cid = r["chunk_id"]
            merged[cid] = r.copy()
            merged[cid]["kw_score_norm"] = r["score"] / max_kw
            merged[cid]["vec_score"] = vec_scores.get(cid, 0.0)

        # Add pure vector results not present yet
        for cid, vs in vec_scores.items():
            if cid not in merged:
                chunk = self.vault.get_chunk(cid)
                if not chunk:
                    continue
                doc = self.vault.get_doc(chunk.doc_id)
                if not doc:
                    continue
                merged[cid] = {
                    "chunk_id": cid,
                    "doc_id": doc.doc_id,
                    "doc_title": doc.title,
                    "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "score": 0,
                    "sequence": chunk.sequence,
                    "kw_score_norm": 0.0,
                    "vec_score": vs,
                }

        # Final score is weighted sum
        results = list(merged.values())
        for r in results:
            r["hybrid_score"] = 0.6 * r.get("kw_score_norm", 0.0) + 0.4 * r.get("vec_score", 0.0)

        results.sort(key=lambda r: (-r["hybrid_score"], r["doc_id"], r["sequence"]))
        return results[:limit]
