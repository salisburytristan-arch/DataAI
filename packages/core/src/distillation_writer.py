"""Distillation dataset generation from agent interactions.

Collects high-quality training pairs from agent responses that have been
verified and refined by teachers. Writes TRAIN_PAIR ForgeNumerics frames
with signatures for provenance tracking.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from packages.vault.src.vault import Vault
from packages.vault.src.types import FactRecord
from packages.core.src.fn_bridge import to_fn_train_pair
from packages.core.src.frame_verifier import FrameVerifier


@dataclass
class TrainingPair:
    """A verified training pair ready for export."""
    pair_id: str
    instruction: str         # User query/instruction
    completion: str          # Agent response
    evidence_chunks: List[str]  # Supporting context
    teacher_feedback: str    # Critical feedback received
    quality_score: float     # Verifier score (0.0-1.0)
    signer_id: str           # Which teacher/agent verified this
    source_convo_id: str     # Original conversation
    created_at: str
    verified: bool
    frame_str: Optional[str] = None
    signature_hex: Optional[str] = None


class DistillationDatasetWriter:
    """
    Generates training datasets from verified agent interactions.
    
    Workflow:
    1. Collect agent responses + evidence + teacher feedback
    2. Filter by quality threshold
    3. Generate ForgeNumerics TRAIN_PAIR frames
    4. Sign frames with teacher/verifier signature
    5. Write to JSONL dataset file
    
    Usage:
        writer = DistillationDatasetWriter(vault)
        writer.add_training_pair(
            instruction="What is Python?",
            completion="Python is a programming language...",
            evidence=["chunk1", "chunk2"],
            feedback="Good explanation, needs more examples",
            quality_score=0.92,
            signer_id="verifier-01"
        )
        writer.export_dataset("training_dataset.jsonl")
    """
    
    def __init__(self, vault: Vault, verifier: Optional[FrameVerifier] = None):
        """
        Initialize dataset writer.
        
        Args:
            vault: Vault instance for storing metadata
            verifier: Optional FrameVerifier for signing exported frames
        """
        self.vault = vault
        self.verifier = verifier
        self.pairs: List[TrainingPair] = []
        self.quality_threshold = 0.75
    
    def add_training_pair(
        self,
        instruction: str,
        completion: str,
        evidence: List[str] = None,
        feedback: str = "",
        quality_score: float = 1.0,
        signer_id: str = "system",
        source_convo_id: str = "unknown"
    ) -> TrainingPair:
        """
        Add a training pair to the dataset.
        
        Args:
            instruction: User query/instruction
            completion: Model response
            evidence: Supporting chunks (optional)
            feedback: Teacher feedback on response
            quality_score: Verification score (0.0-1.0)
            signer_id: Who verified this pair
            source_convo_id: Conversation this came from
            
        Returns:
            TrainingPair object
        """
        pair_id = f"train-{datetime.now().timestamp()}"
        pair = TrainingPair(
            pair_id=pair_id,
            instruction=instruction,
            completion=completion,
            evidence_chunks=evidence or [],
            teacher_feedback=feedback,
            quality_score=quality_score,
            signer_id=signer_id,
            source_convo_id=source_convo_id,
            created_at=datetime.now().isoformat(),
            verified=quality_score >= self.quality_threshold
        )
        
        self.pairs.append(pair)
        return pair
    
    def filter_by_quality(self, threshold: float) -> List[TrainingPair]:
        """Filter pairs by quality score threshold."""
        return [p for p in self.pairs if p.quality_score >= threshold]
    
    def generate_frames(self) -> None:
        """Generate ForgeNumerics TRAIN_PAIR frames for all pairs."""
        for pair in self.pairs:
            # Create metadata dict with provenance
            metadata = {
                "pair_id": pair.pair_id,
                "source_convo_id": pair.source_convo_id,
                "quality_score": pair.quality_score,
                "teacher_feedback": pair.teacher_feedback,
                "evidence": pair.evidence_chunks,
                "created_at": pair.created_at,
            }
            
            # Generate frame string
            frame_str = to_fn_train_pair(
                instruction=pair.instruction,
                completion=pair.completion,
                metadata=metadata
            )
            
            pair.frame_str = frame_str
            
            # Sign if verifier available
            if self.verifier:
                signed_frame = self.verifier.sign_frame(
                    frame_str,
                    timestamp=datetime.now().isoformat()
                )
                pair.signature_hex = signed_frame
    
    def export_dataset(
        self,
        filepath: str,
        quality_threshold: Optional[float] = None,
        sign: bool = False
    ) -> Dict[str, Any]:
        """
        Export dataset to JSONL file.
        
        Args:
            filepath: Output file path
            quality_threshold: Filter to pairs above threshold
            sign: Whether to sign exported frames
            
        Returns:
            Export statistics
        """
        # Filter by quality if specified
        pairs_to_export = self.pairs
        if quality_threshold is not None:
            pairs_to_export = self.filter_by_quality(quality_threshold)
        
        # Generate frames if needed
        if not any(p.frame_str for p in pairs_to_export):
            self.generate_frames()
        
        # Write to JSONL
        with open(filepath, 'w') as f:
            for pair in pairs_to_export:
                export_dict = {
                    "pair_id": pair.pair_id,
                    "instruction": pair.instruction,
                    "completion": pair.completion,
                    "quality_score": pair.quality_score,
                    "verified": pair.verified,
                    "signer_id": pair.signer_id,
                    "source_convo_id": pair.source_convo_id,
                    "created_at": pair.created_at,
                    "frame": pair.frame_str,
                }
                
                if pair.signature_hex:
                    export_dict["signature"] = pair.signature_hex
                
                if pair.teacher_feedback:
                    export_dict["feedback"] = pair.teacher_feedback
                
                f.write(json.dumps(export_dict) + "\n")
        
        return {
            "output_file": filepath,
            "total_pairs": len(pairs_to_export),
            "verified_pairs": sum(1 for p in pairs_to_export if p.verified),
            "average_quality": sum(p.quality_score for p in pairs_to_export) / len(pairs_to_export) if pairs_to_export else 0.0,
            "signed": sign and bool(self.verifier),
        }
    
    def import_from_conversation(
        self,
        convo_id: str,
        verifier: Optional[FrameVerifier] = None
    ) -> int:
        """
        Import training pairs from conversation history.
        
        Collects summaries + facts + evidence from stored conversation
        and converts to training pairs.
        
        Args:
            convo_id: Conversation ID to import from
            verifier: Optional verifier for filtering
            
        Returns:
            Number of pairs imported
        """
        count = 0
        
        # Get summaries for this conversation
        summaries = self.vault.list_summaries(metadata_filter={"convo_id": convo_id})
        
        for summary in summaries:
            # Use summary as completion, extract instruction from context
            completion = summary.get("summary_text", "")
            if not completion:
                continue
            
            # Try to extract instruction from facts
            facts = self.vault.list_facts(metadata_filter={"convo_id": convo_id})
            
            # Use first fact as synthetic instruction
            instruction = "Summarize the conversation"
            if facts:
                first_fact = facts[0]
                # Build instruction from SVO triple
                subject = first_fact.get("subject", "")
                predicate = first_fact.get("predicate", "")
                instruction = f"What is the relationship between {subject} and {predicate}?"
            
            # Get evidence from stored chunks
            evidence = []
            # (In a real implementation, would retrieve chunks from vault storage)
            
            # Add as training pair
            self.add_training_pair(
                instruction=instruction,
                completion=completion,
                evidence=evidence,
                quality_score=0.85,  # Default score for auto-imported
                signer_id="auto-import",
                source_convo_id=convo_id
            )
            count += 1
        
        return count
    
    def statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if not self.pairs:
            return {
                "total_pairs": 0,
                "verified_pairs": 0,
                "average_quality": 0.0,
                "quality_distribution": {}
            }
        
        verified = [p for p in self.pairs if p.verified]
        quality_scores = [p.quality_score for p in self.pairs]
        
        # Bucket quality scores
        buckets = {
            "excellent (0.95+)": sum(1 for s in quality_scores if s >= 0.95),
            "good (0.85-0.95)": sum(1 for s in quality_scores if 0.85 <= s < 0.95),
            "acceptable (0.75-0.85)": sum(1 for s in quality_scores if 0.75 <= s < 0.85),
            "poor (<0.75)": sum(1 for s in quality_scores if s < 0.75),
        }
        
        return {
            "total_pairs": len(self.pairs),
            "verified_pairs": len(verified),
            "unverified_pairs": len(self.pairs) - len(verified),
            "average_quality": sum(quality_scores) / len(quality_scores),
            "min_quality": min(quality_scores),
            "max_quality": max(quality_scores),
            "quality_distribution": buckets,
            "signers": list(set(p.signer_id for p in self.pairs)),
        }
