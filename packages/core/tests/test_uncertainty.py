"""
Tests for State Φ Uncertainty Protocol
"""

import unittest
from packages.core.src.uncertainty import (
    Claim,
    ClaimStatus,
    Citation,
    ClaimExtractor,
    ContradictionDetector,
    UncertaintyEngine,
    UncertaintyReport,
    DecisionPolicy
)


class TestClaimExtractor(unittest.TestCase):
    """Test claim extraction from text"""
    
    def setUp(self):
        self.extractor = ClaimExtractor()
    
    def test_extract_simple_claims(self):
        """Should extract declarative sentences"""
        text = "Python is a programming language. It was created in 1991. Python is popular."
        claims = self.extractor.extract_claims(text)
        
        self.assertEqual(len(claims), 3)
        self.assertIn("Python is a programming language", claims)
        self.assertIn("It was created in 1991", claims)
    
    def test_filter_questions(self):
        """Should not extract questions"""
        text = "What is Python? Python is a language. It is popular."
        claims = self.extractor.extract_claims(text)
        
        # Should get two declarative statements, not the question
        self.assertGreaterEqual(len(claims), 2)
        self.assertIn("Python is a language", claims)
        self.assertIn("It is popular", claims)
    
    def test_minimum_length(self):
        """Should filter out very short sentences"""
        text = "Python. It is great. Hi. This is a proper sentence."
        claims = self.extractor.extract_claims(text)
        
        # Short ones should be filtered
        self.assertNotIn("Python", claims)
        self.assertNotIn("Hi", claims)
        self.assertIn("This is a proper sentence", claims)


class TestContradictionDetector(unittest.TestCase):
    """Test contradiction detection"""
    
    def setUp(self):
        self.detector = ContradictionDetector()
    
    def test_detects_negation_contradiction(self):
        """Should detect contradictions with negation"""
        claim1 = "Python is suitable for real-time systems"
        claim2 = "Python is not suitable for real-time systems"
        
        is_contradictory = self.detector.are_contradictory(claim1, claim2)
        self.assertTrue(is_contradictory)
    
    def test_no_contradiction_different_topics(self):
        """Should not flag different topics as contradictory"""
        claim1 = "Python was created in 1991"
        claim2 = "JavaScript was created in 1995"
        
        is_contradictory = self.detector.are_contradictory(claim1, claim2)
        self.assertFalse(is_contradictory)
    
    def test_requires_term_overlap(self):
        """Should require sufficient term overlap"""
        claim1 = "The sky is blue"
        claim2 = "The grass is not green"
        
        # Different subjects, should not be contradictory
        is_contradictory = self.detector.are_contradictory(claim1, claim2)
        self.assertFalse(is_contradictory)


class TestUncertaintyEngine(unittest.TestCase):
    """Test uncertainty engine"""
    
    def setUp(self):
        self.engine = UncertaintyEngine(confidence_threshold=0.7)
    
    def test_high_confidence_claim_is_true(self):
        """High evidence should result in TRUE status"""
        claim_text = "Python was created in 1991"
        evidence = [
            {"doc_id": "doc1", "chunk_id": "c1", "text": "Python created 1991", "score": 0.9},
            {"doc_id": "doc2", "chunk_id": "c2", "text": "Guido van Rossum 1991", "score": 0.85}
        ]
        
        claim = self.engine.assess_claim(claim_text, evidence)
        
        self.assertEqual(claim.status, ClaimStatus.TRUE)
        self.assertGreater(claim.confidence, 0.7)
        self.assertEqual(len(claim.support), 2)
    
    def test_low_confidence_claim_is_phi(self):
        """Low evidence should result in Φ status"""
        claim_text = "Python is the best language"
        evidence = [
            {"doc_id": "doc1", "chunk_id": "c1", "text": "Some languages", "score": 0.3}
        ]
        
        claim = self.engine.assess_claim(claim_text, evidence)
        
        self.assertEqual(claim.status, ClaimStatus.PHI)
        self.assertLess(claim.confidence, 0.7)
    
    def test_no_evidence_is_phi(self):
        """No evidence should result in Φ status"""
        claim_text = "Something unknown"
        evidence = []
        
        claim = self.engine.assess_claim(claim_text, evidence)
        
        self.assertEqual(claim.status, ClaimStatus.PHI)
        self.assertEqual(claim.confidence, 0.0)
    
    def test_contradiction_forces_phi(self):
        """Contradictions should force Φ status"""
        existing_claims = [
            Claim(
                claim_id="c1",
                text="Python is suitable for real-time systems",
                status=ClaimStatus.TRUE,
                confidence=0.8
            )
        ]
        
        claim_text = "Python is not suitable for real-time systems"
        evidence = [{"doc_id": "doc1", "chunk_id": "c1", "text": "Python not real-time", "score": 0.9}]
        
        claim = self.engine.assess_claim(claim_text, evidence, existing_claims)
        
        # Even with high evidence, contradiction should force Φ
        self.assertEqual(claim.status, ClaimStatus.PHI)
        self.assertTrue(len(claim.contradiction_ids) > 0)
    
    def test_high_impact_detection(self):
        """Should detect high-impact claims"""
        claim_text = "This diagnosis indicates severe condition"
        evidence = [{"doc_id": "doc1", "chunk_id": "c1", "text": "medical info", "score": 0.5}]
        
        claim = self.engine.assess_claim(claim_text, evidence)
        
        self.assertEqual(claim.impact_level, "high")
    
    def test_process_response_extracts_claims(self):
        """Should process full response and extract claims"""
        response = "Python is a language. It was created in 1991. Python is not suitable for embedded systems."
        evidence = [
            {"doc_id": "doc1", "chunk_id": "c1", "text": "Python language", "score": 0.8},
            {"doc_id": "doc2", "chunk_id": "c2", "text": "Created 1991", "score": 0.9}
        ]
        
        claims, report = self.engine.process_response(response, evidence)
        
        self.assertGreater(len(claims), 0)
        self.assertIsInstance(report, UncertaintyReport)
        self.assertEqual(report.total_claims, len(claims))


class TestDecisionPolicy(unittest.TestCase):
    """Test decision policy engine"""
    
    def setUp(self):
        self.policy = DecisionPolicy()
    
    def test_escalates_high_impact_phi(self):
        """Should escalate when high-impact claims are Φ"""
        report = UncertaintyReport(
            total_claims=5,
            phi_count=2,
            contradiction_count=0,
            high_impact_phi=["claim_1"],
            requires_escalation=True,
            escalation_reason="High impact Φ"
        )
        
        should_escalate = self.policy.should_escalate_to_teacher(report)
        self.assertTrue(should_escalate)
    
    def test_no_escalation_for_low_impact(self):
        """Should not escalate for low-impact Φ"""
        report = UncertaintyReport(
            total_claims=5,
            phi_count=2,
            contradiction_count=0,
            high_impact_phi=[],
            requires_escalation=False
        )
        
        should_escalate = self.policy.should_escalate_to_teacher(report)
        self.assertFalse(should_escalate)
    
    def test_gates_tool_on_phi_dependency(self):
        """Should gate tool execution if depends on Φ claims"""
        relevant_claims = [
            Claim(
                claim_id="c1",
                text="User account balance is $1000",
                status=ClaimStatus.PHI,
                confidence=0.5,
                impact_level="high"
            )
        ]
        
        should_gate, reason = self.policy.should_gate_tool_execution(
            tool_name="transfer_money",
            tool_args={"amount": 500},
            relevant_claims=relevant_claims
        )
        
        self.assertTrue(should_gate)
        self.assertIn("unverified", reason)
    
    def test_no_gating_for_verified_claims(self):
        """Should not gate if all claims are verified"""
        relevant_claims = [
            Claim(
                claim_id="c1",
                text="User account exists",
                status=ClaimStatus.TRUE,
                confidence=0.9,
                impact_level="medium"
            )
        ]
        
        should_gate, reason = self.policy.should_gate_tool_execution(
            tool_name="check_balance",
            tool_args={},
            relevant_claims=relevant_claims
        )
        
        self.assertFalse(should_gate)
    
    def test_generates_user_message(self):
        """Should generate user-facing uncertainty message"""
        claims = [
            Claim("c1", "Some claim", ClaimStatus.PHI, 0.5, impact_level="high"),
            Claim("c2", "Another claim", ClaimStatus.TRUE, 0.9, impact_level="low")
        ]
        
        report = UncertaintyReport(
            total_claims=2,
            phi_count=1,
            contradiction_count=0,
            high_impact_phi=["c1"],
            requires_escalation=True
        )
        
        message = self.policy.generate_user_message(report, claims)
        
        self.assertIn("⚠️", message)
        self.assertTrue(len(message) > 0)


if __name__ == '__main__':
    unittest.main()
