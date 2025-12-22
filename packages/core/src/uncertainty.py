"""
State Φ Uncertainty Protocol

Operationalizes trinary logic: responses include claims with status (true/false/phi).
Handles epistemic uncertainty, contradiction detection, and escalation policies.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Set
from enum import Enum
import re


class ClaimStatus(Enum):
    """Trinary claim status"""
    TRUE = "true"      # ⊗ State 1: Verified/supported
    FALSE = "false"    # ⊙ State 0: Refuted
    PHI = "phi"        # Φ State Φ: Unknown/conflicting/needs verification


@dataclass
class Citation:
    """Evidence citation"""
    doc_id: str
    chunk_id: str
    text: str
    offset: int
    relevance_score: float = 0.0


@dataclass
class Claim:
    """Atomic knowledge claim with uncertainty metadata"""
    claim_id: str
    text: str
    status: ClaimStatus
    confidence: float  # 0.0-1.0
    support: List[Citation] = field(default_factory=list)
    contradiction_ids: List[str] = field(default_factory=list)
    requires_verification: bool = False
    impact_level: Literal["low", "medium", "high"] = "medium"
    
    def is_phi(self) -> bool:
        """Check if claim is in Φ state"""
        return self.status == ClaimStatus.PHI
    
    def has_contradictions(self) -> bool:
        """Check if claim has contradictions"""
        return len(self.contradiction_ids) > 0


@dataclass
class UncertaintyReport:
    """Summary of uncertainty in a response"""
    total_claims: int
    phi_count: int
    contradiction_count: int
    high_impact_phi: List[str]  # IDs of high-impact Φ claims
    requires_escalation: bool
    escalation_reason: Optional[str] = None


class ClaimExtractor:
    """Extract atomic claims from text"""
    
    def extract_claims(self, text: str) -> List[str]:
        """
        Extract declarative statements from text.
        Simple heuristic: sentences ending in periods.
        """
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            # Filter out questions
            if '?' in sentence:
                continue
            if len(sentence) > 10:  # Minimum length
                # Filter out commands
                if not sentence.startswith(('Please', 'Let', 'Do')):
                    claims.append(sentence)
        
        return claims


class ContradictionDetector:
    """Detect contradictions between claims"""
    
    def __init__(self):
        # Negation patterns
        self.negation_words = {'not', 'no', 'never', 'neither', "n't", 'none', 'nobody', 'nothing'}
        
    def are_contradictory(self, claim1: str, claim2: str) -> bool:
        """
        Simple contradiction detection (heuristic).
        Returns True if claims appear contradictory.
        """
        # Convert to lowercase for comparison
        c1 = claim1.lower()
        c2 = claim2.lower()
        
        # Extract key terms (nouns/verbs)
        terms1 = set(re.findall(r'\b\w+\b', c1)) - self.negation_words
        terms2 = set(re.findall(r'\b\w+\b', c2)) - self.negation_words
        
        # High overlap in terms?
        overlap = terms1 & terms2
        if len(overlap) < 3:  # Not enough overlap to be contradictory
            return False
        
        # Check negation patterns
        has_negation1 = any(neg in c1 for neg in self.negation_words)
        has_negation2 = any(neg in c2 for neg in self.negation_words)
        
        # If one has negation and other doesn't, likely contradictory
        return has_negation1 != has_negation2


class UncertaintyEngine:
    """Core engine for State Φ uncertainty handling"""
    
    def __init__(
        self,
        confidence_threshold: float = 0.7,
        phi_threshold: float = 0.5,
        high_impact_keywords: Optional[List[str]] = None
    ):
        self.confidence_threshold = confidence_threshold
        self.phi_threshold = phi_threshold
        self.high_impact_keywords = high_impact_keywords or [
            'diagnosis', 'treatment', 'medication', 'surgery',
            'legal', 'contract', 'liability', 'criminal',
            'financial', 'investment', 'loan', 'credit',
            'security', 'vulnerability', 'breach', 'hack'
        ]
        
        self.extractor = ClaimExtractor()
        self.detector = ContradictionDetector()
    
    def assess_claim(
        self,
        claim_text: str,
        evidence_chunks: List[Dict[str, any]],
        existing_claims: Optional[List[Claim]] = None
    ) -> Claim:
        """
        Assess a claim against evidence and existing knowledge.
        Returns Claim object with status and confidence.
        """
        claim_id = f"claim_{hash(claim_text) & 0xffffffff:08x}"
        
        # Convert evidence to citations
        citations = []
        for chunk in evidence_chunks:
            citations.append(Citation(
                doc_id=chunk.get('doc_id', 'unknown'),
                chunk_id=chunk.get('chunk_id', 'unknown'),
                text=chunk.get('text', ''),
                offset=chunk.get('offset', 0),
                relevance_score=chunk.get('score', 0.0)
            ))
        
        # Determine confidence based on evidence quality
        if not citations:
            confidence = 0.0
        else:
            avg_relevance = sum(c.relevance_score for c in citations) / len(citations)
            confidence = avg_relevance
        
        # Determine status based on confidence
        if confidence >= self.confidence_threshold:
            status = ClaimStatus.TRUE
        elif confidence <= self.phi_threshold:  # Below phi threshold = uncertain
            status = ClaimStatus.PHI
        else:
            status = ClaimStatus.FALSE
        
        # Check for contradictions with existing claims
        contradiction_ids = []
        if existing_claims:
            for existing in existing_claims:
                if self.detector.are_contradictory(claim_text, existing.text):
                    contradiction_ids.append(existing.claim_id)
                    status = ClaimStatus.PHI  # Contradictions force Φ state
        
        # Assess impact level
        impact_level = "low"
        claim_lower = claim_text.lower()
        if any(keyword in claim_lower for keyword in self.high_impact_keywords):
            impact_level = "high"
        elif len(claim_text) > 100:  # Long claims might be important
            impact_level = "medium"
        
        # Determine if verification required
        requires_verification = (
            status == ClaimStatus.PHI and impact_level in ["medium", "high"]
        )
        
        return Claim(
            claim_id=claim_id,
            text=claim_text,
            status=status,
            confidence=confidence,
            support=citations,
            contradiction_ids=contradiction_ids,
            requires_verification=requires_verification,
            impact_level=impact_level
        )
    
    def process_response(
        self,
        response_text: str,
        evidence_chunks: List[Dict[str, any]],
        existing_claims: Optional[List[Claim]] = None
    ) -> tuple[List[Claim], UncertaintyReport]:
        """
        Process a response, extract claims, assess uncertainty.
        Returns (claims, uncertainty_report).
        """
        # Extract claims from response
        claim_texts = self.extractor.extract_claims(response_text)
        
        # Assess each claim
        claims = []
        for claim_text in claim_texts:
            claim = self.assess_claim(claim_text, evidence_chunks, existing_claims)
            claims.append(claim)
        
        # Generate uncertainty report
        phi_claims = [c for c in claims if c.is_phi()]
        contradictory_claims = [c for c in claims if c.has_contradictions()]
        high_impact_phi = [c.claim_id for c in phi_claims if c.impact_level == "high"]
        
        requires_escalation = len(high_impact_phi) > 0
        escalation_reason = None
        if requires_escalation:
            escalation_reason = f"{len(high_impact_phi)} high-impact claims in Φ state require verification"
        
        report = UncertaintyReport(
            total_claims=len(claims),
            phi_count=len(phi_claims),
            contradiction_count=len(contradictory_claims),
            high_impact_phi=high_impact_phi,
            requires_escalation=requires_escalation,
            escalation_reason=escalation_reason
        )
        
        return claims, report


class DecisionPolicy:
    """Policy engine for handling Φ state in operations"""
    
    def __init__(self):
        self.escalation_enabled = True
        self.tool_gating_enabled = True
    
    def should_escalate_to_teacher(self, report: UncertaintyReport) -> bool:
        """Decide if response should be escalated to teacher verification"""
        if not self.escalation_enabled:
            return False
        
        return report.requires_escalation
    
    def should_gate_tool_execution(
        self,
        tool_name: str,
        tool_args: Dict[str, any],
        relevant_claims: List[Claim]
    ) -> tuple[bool, Optional[str]]:
        """
        Decide if tool execution should be gated due to Φ claims.
        Returns (should_gate, reason).
        """
        if not self.tool_gating_enabled:
            return False, None
        
        # Check if tool depends on any Φ claims
        phi_claims = [c for c in relevant_claims if c.is_phi()]
        high_impact_phi = [c for c in phi_claims if c.impact_level == "high"]
        
        if high_impact_phi:
            reason = f"Tool '{tool_name}' depends on {len(high_impact_phi)} unverified high-impact claims"
            return True, reason
        
        return False, None
    
    def generate_user_message(self, report: UncertaintyReport, claims: List[Claim]) -> str:
        """Generate user-facing uncertainty message"""
        if report.phi_count == 0:
            return ""
        
        phi_claims = [c for c in claims if c.is_phi()]
        contradictory = [c for c in phi_claims if c.has_contradictions()]
        
        messages = []
        
        if contradictory:
            messages.append(f"⚠️ I found conflicting information about {len(contradictory)} point(s).")
        
        if report.high_impact_phi:
            messages.append(f"⚠️ {len(report.high_impact_phi)} important claim(s) could not be verified with available evidence.")
        
        if report.requires_escalation:
            messages.append("🔍 These claims require additional verification before proceeding.")
        
        return " ".join(messages)


# Example usage and integration
if __name__ == "__main__":
    # Initialize engine
    engine = UncertaintyEngine()
    policy = DecisionPolicy()
    
    # Example response
    response = "Python is a programming language. It was created in 1991. Python is not suitable for real-time systems."
    
    # Evidence (simulated)
    evidence = [
        {"doc_id": "doc1", "chunk_id": "chunk1", "text": "Python was created by Guido van Rossum in 1991", "score": 0.9},
        {"doc_id": "doc2", "chunk_id": "chunk2", "text": "Python is a high-level language", "score": 0.8}
    ]
    
    # Process
    claims, report = engine.process_response(response, evidence)
    
    print(f"Total claims: {report.total_claims}")
    print(f"Φ claims: {report.phi_count}")
    print(f"Contradictions: {report.contradiction_count}")
    
    for claim in claims:
        print(f"\nClaim: {claim.text}")
        print(f"  Status: {claim.status.value}")
        print(f"  Confidence: {claim.confidence:.2f}")
        print(f"  Impact: {claim.impact_level}")
    
    # Check escalation
    if policy.should_escalate_to_teacher(report):
        print("\n🔍 Escalating to teacher verification")
    
    # Generate user message
    user_msg = policy.generate_user_message(report, claims)
    if user_msg:
        print(f"\nUser message: {user_msg}")
