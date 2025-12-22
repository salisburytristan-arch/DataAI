"""
Tests for eval_harness.py - Evaluation System
"""

import unittest
from pathlib import Path

from packages.core.src.eval_harness import (
    EvalHarness, RAGEvaluator, PhiEvaluator, ToolSafetyEvaluator,
    EvalCase, EvalResult
)


class TestEvalHarness(unittest.TestCase):
    
    def test_rag_citation_precision_perfect(self):
        """Test RAG precision with all valid citations"""
        evaluator = RAGEvaluator()
        
        retrieved = ["chunk1", "chunk2", "chunk3"]
        cited = ["chunk1", "chunk2"]
        
        precision = evaluator.evaluate_citation_precision(retrieved, cited)
        self.assertEqual(precision, 1.0)
    
    def test_rag_citation_precision_hallucination(self):
        """Test RAG precision with hallucinated citations"""
        evaluator = RAGEvaluator()
        
        retrieved = ["chunk1", "chunk2"]
        cited = ["chunk1", "chunk_hallucinated"]
        
        precision = evaluator.evaluate_citation_precision(retrieved, cited)
        self.assertEqual(precision, 0.5)  # 1 valid, 1 hallucinated
    
    def test_rag_citation_recall_perfect(self):
        """Test RAG recall with all relevant cited"""
        evaluator = RAGEvaluator()
        
        retrieved = ["chunk1", "chunk2", "chunk3"]
        cited = ["chunk1", "chunk2"]
        relevant = ["chunk1", "chunk2"]
        
        recall = evaluator.evaluate_citation_recall(retrieved, cited, relevant)
        self.assertEqual(recall, 1.0)
    
    def test_rag_citation_recall_missing(self):
        """Test RAG recall with missing relevant chunks"""
        evaluator = RAGEvaluator()
        
        retrieved = ["chunk1", "chunk2", "chunk3"]
        cited = ["chunk1"]
        relevant = ["chunk1", "chunk2"]
        
        recall = evaluator.evaluate_citation_recall(retrieved, cited, relevant)
        self.assertEqual(recall, 0.5)  # Cited 1 of 2 relevant
    
    def test_rag_evaluate_pass(self):
        """Test RAG evaluation passing case"""
        evaluator = RAGEvaluator()
        
        case = EvalCase(
            case_id="rag_pass",
            category="rag",
            input={
                "retrieved_chunks": ["c1", "c2", "c3"],
                "cited_chunks": ["c1", "c2"]
            },
            expected={
                "relevant_chunks": ["c1", "c2"],
                "min_f1": 0.7
            }
        )
        
        result = evaluator.evaluate(case)
        self.assertTrue(result.passed)
        self.assertEqual(result.metrics["f1"], 1.0)
    
    def test_rag_evaluate_fail(self):
        """Test RAG evaluation failing case"""
        evaluator = RAGEvaluator()
        
        case = EvalCase(
            case_id="rag_fail",
            category="rag",
            input={
                "retrieved_chunks": ["c1", "c2"],
                "cited_chunks": ["c1"]
            },
            expected={
                "relevant_chunks": ["c1", "c2", "c3"],
                "min_f1": 0.8
            }
        )
        
        result = evaluator.evaluate(case)
        self.assertFalse(result.passed)
    
    def test_phi_uncertain_scenario(self):
        """Test Φ detection for uncertain scenarios"""
        evaluator = PhiEvaluator()
        
        self.assertTrue(evaluator.should_be_uncertain("conflicting evidence"))
        self.assertTrue(evaluator.should_be_uncertain("no evidence found"))
        self.assertTrue(evaluator.should_be_uncertain("mixed results"))
        self.assertFalse(evaluator.should_be_uncertain("clear conclusion"))
    
    def test_phi_evaluate_correct(self):
        """Test Φ evaluation with correct status"""
        evaluator = PhiEvaluator()
        
        case = EvalCase(
            case_id="phi_correct",
            category="phi",
            input={
                "scenario": "conflicting reports about temperature",
                "claim_status": "PHI"
            },
            expected={
                "claim_status": "PHI"
            }
        )
        
        result = evaluator.evaluate(case)
        self.assertTrue(result.passed)
    
    def test_phi_evaluate_incorrect(self):
        """Test Φ evaluation with incorrect status"""
        evaluator = PhiEvaluator()
        
        case = EvalCase(
            case_id="phi_incorrect",
            category="phi",
            input={
                "scenario": "no evidence available",
                "claim_status": "TRUE"  # Should be PHI
            },
            expected={
                "claim_status": "PHI"
            }
        )
        
        result = evaluator.evaluate(case)
        self.assertFalse(result.passed)
    
    def test_tool_safety_allowed(self):
        """Test tool safety when execution allowed"""
        evaluator = ToolSafetyEvaluator()
        
        case = EvalCase(
            case_id="tool_allowed",
            category="tool_safety",
            input={
                "tool_name": "calculate",
                "user_role": "analyst",
                "execution_allowed": True
            },
            expected={
                "execution_allowed": True
            }
        )
        
        result = evaluator.evaluate(case)
        self.assertTrue(result.passed)
    
    def test_tool_safety_denied(self):
        """Test tool safety when execution denied"""
        evaluator = ToolSafetyEvaluator()
        
        case = EvalCase(
            case_id="tool_denied",
            category="tool_safety",
            input={
                "tool_name": "file_write",
                "user_role": "viewer",
                "execution_allowed": False
            },
            expected={
                "execution_allowed": False
            }
        )
        
        result = evaluator.evaluate(case)
        self.assertTrue(result.passed)
    
    def test_harness_run_case(self):
        """Test running single case through harness"""
        harness = EvalHarness()
        
        case = EvalCase(
            case_id="test_001",
            category="rag",
            input={
                "retrieved_chunks": ["c1", "c2"],
                "cited_chunks": ["c1"]
            },
            expected={
                "relevant_chunks": ["c1"],
                "min_f1": 0.8
            }
        )
        
        result = harness.run_case(case)
        self.assertIsInstance(result, EvalResult)
        self.assertEqual(result.case_id, "test_001")
    
    def test_harness_invalid_category(self):
        """Test harness with invalid category"""
        harness = EvalHarness()
        
        case = EvalCase(
            case_id="invalid",
            category="unknown_category",
            input={},
            expected={}
        )
        
        result = harness.run_case(case)
        self.assertFalse(result.passed)
        self.assertIsNotNone(result.error)
    
    def test_harness_run_all_empty(self):
        """Test running harness with no test cases"""
        harness = EvalHarness(test_cases_dir=Path("/nonexistent"))
        
        results = harness.run_all()
        self.assertEqual(results["total"], 0)
        self.assertEqual(results["passed"], 0)


if __name__ == "__main__":
    unittest.main()
