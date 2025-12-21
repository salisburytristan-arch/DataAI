"""Tests for teacher client and router."""

import unittest
import json
from unittest.mock import patch, MagicMock
from packages.core.src.teacher_client import (
    DeepSeekClient,
    TeacherResponse,
    TeacherRouter,
)


class TestTeacherResponse(unittest.TestCase):
    """Test TeacherResponse dataclass."""
    
    def test_response_creation(self):
        """Test creating a teacher response."""
        response = TeacherResponse(
            role="verifier",
            content="verified",
            reasoning="accurate",
            score=0.95,
            metadata={"verified": True}
        )
        self.assertEqual(response.role, "verifier")
        self.assertEqual(response.score, 0.95)
        self.assertTrue(response.metadata["verified"])


class TestDeepSeekClient(unittest.TestCase):
    """Test DeepSeek API client."""
    
    def setUp(self):
        """Initialize test fixtures."""
        self.api_key = "test-key-12345"
        self.client = DeepSeekClient(api_key=self.api_key, model="deepseek-chat")
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.model, "deepseek-chat")
        self.assertTrue(self.client.base_url.startswith("https://api.deepseek.com"))
    
    def test_client_missing_api_key(self):
        """Test that missing API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                DeepSeekClient()
            self.assertIn("DEEPSEEK_API_KEY", str(ctx.exception))
    
    def test_parse_verification_response(self):
        """Test parsing verification response."""
        json_response = json.dumps({
            "score": 0.85,
            "claims": [
                {"claim": "Test fact", "status": "CORRECT"}
            ],
            "corrections": [],
            "reasoning": "Accurate summary"
        })
        
        response = self.client._parse_verification_response(json_response)
        self.assertEqual(response.role, "verifier")
        self.assertEqual(response.score, 0.85)
        self.assertEqual(response.reasoning, "Accurate summary")
        self.assertTrue(response.metadata["verified"])
    
    def test_parse_verification_response_strict_mode(self):
        """Test strict verification (requires high confidence)."""
        json_response = json.dumps({
            "score": 0.80,  # Below strict threshold
            "claims": [],
            "corrections": [],
            "reasoning": "Mostly accurate"
        })
        
        response = self.client._parse_verification_response(json_response, strict=True)
        self.assertFalse(response.metadata["verified"])
    
    def test_parse_verification_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        response = self.client._parse_verification_response("not valid json")
        self.assertEqual(response.score, 0.0)
        self.assertIn("error", response.metadata)
    
    def test_parse_critique_response(self):
        """Test parsing critique response."""
        json_response = json.dumps({
            "score": 0.75,
            "strengths": ["Clear writing"],
            "weaknesses": ["Missing examples"],
            "suggestions": ["Add specific examples"],
            "key_revisions": ["Expand section 2"],
            "reasoning": "Good structure but needs depth"
        })
        
        response = self.client._parse_critique_response(json_response)
        self.assertEqual(response.role, "critic")
        self.assertEqual(response.score, 0.75)
        self.assertIn("Clear writing", response.metadata["strengths"])
        self.assertIn("Missing examples", response.metadata["weaknesses"])
    
    def test_parse_critique_response_invalid_json(self):
        """Test parsing invalid critique response."""
        response = self.client._parse_critique_response("invalid")
        self.assertEqual(response.score, 0.0)
    
    def test_parse_rewrite_response(self):
        """Test parsing rewrite response."""
        revised_text = "This is the improved version..."
        json_response = json.dumps({
            "revised_text": revised_text,
            "improvements_made": ["Better clarity", "More concise"],
            "reasoning": "Simplified language",
            "score": 0.88
        })
        
        response = self.client._parse_rewrite_response(json_response)
        self.assertEqual(response.role, "rewriter")
        self.assertEqual(response.content, revised_text)
        self.assertEqual(response.score, 0.88)
        self.assertIn("Better clarity", response.metadata["improvements"])
    
    def test_fallback_response(self):
        """Test fallback response when API fails."""
        fallback = self.client._fallback_response("test prompt")
        parsed = json.loads(fallback)
        self.assertIn("reasoning", parsed)
        self.assertIn("FALLBACK", parsed["reasoning"])
    
    @patch("urllib.request.urlopen")
    def test_verify_success(self, mock_urlopen):
        """Test successful verification."""
        # API returns nested structure with choices array
        inner_content = json.dumps({
            "score": 0.92,
            "claims": [{"claim": "Test", "status": "CORRECT"}],
            "corrections": [],
            "reasoning": "Verified"
        })
        api_response = json.dumps({
            "choices": [{"message": {"content": inner_content}}]
        })
        mock_urlopen.return_value.__enter__.return_value.read.return_value = api_response.encode()
        
        response = self.client.verify("Test draft", "Test evidence")
        self.assertEqual(response.role, "verifier")
        self.assertEqual(response.score, 0.92)
    
    @patch("urllib.request.urlopen")
    def test_critique_success(self, mock_urlopen):
        """Test successful critique."""
        inner_content = json.dumps({
            "score": 0.80,
            "strengths": ["Well organized"],
            "weaknesses": ["Needs examples"],
            "suggestions": ["Add concrete examples"],
            "key_revisions": ["Expand introduction"],
            "reasoning": "Good structure"
        })
        api_response = json.dumps({
            "choices": [{"message": {"content": inner_content}}]
        })
        mock_urlopen.return_value.__enter__.return_value.read.return_value = api_response.encode()
        
        response = self.client.critique("Test draft", "Test rubric")
        self.assertEqual(response.role, "critic")
        self.assertEqual(response.score, 0.80)
        self.assertIn("Well organized", response.metadata["strengths"])
    
    @patch("urllib.request.urlopen")
    def test_rewrite_success(self, mock_urlopen):
        """Test successful rewrite."""
        revised = "This is the improved version of the text."
        inner_content = json.dumps({
            "revised_text": revised,
            "improvements_made": ["Clearer language", "Better flow"],
            "reasoning": "Improved clarity",
            "score": 0.85
        })
        api_response = json.dumps({
            "choices": [{"message": {"content": inner_content}}]
        })
        mock_urlopen.return_value.__enter__.return_value.read.return_value = api_response.encode()
        
        response = self.client.rewrite("Original text", "Make it clearer")
        self.assertEqual(response.role, "rewriter")
        self.assertEqual(response.content, revised)
        self.assertEqual(response.score, 0.85)


class TestTeacherRouter(unittest.TestCase):
    """Test teacher router for draft-critique-revise."""
    
    def setUp(self):
        """Initialize test fixtures."""
        self.router = TeacherRouter()
    
    def test_router_initialization(self):
        """Test router initialization."""
        self.assertEqual(self.router.max_iterations, 3)
        self.assertEqual(self.router.quality_threshold, 0.8)
    
    def test_draft_critique_revise_no_client(self):
        """Test DCR with no client configured."""
        result = self.router.draft_critique_revise("draft text")
        self.assertIn("error", result)
        self.assertEqual(result["final_text"], "draft text")
    
    def test_draft_critique_revise_with_mock_client(self):
        """Test DCR with mocked client."""
        mock_client = MagicMock()
        router = TeacherRouter(deepseek_client=mock_client)
        
        # Mock responses that reach quality threshold immediately
        mock_client.critique.return_value = TeacherResponse(
            role="critic",
            content="",
            reasoning="Good quality",
            score=0.85,  # Above threshold
            metadata={
                "strengths": ["Clear"],
                "weaknesses": [],
                "suggestions": [],
                "key_revisions": []
            }
        )
        
        result = router.draft_critique_revise("draft text", evidence="evidence")
        
        self.assertEqual(result["final_text"], "draft text")
        self.assertEqual(result["quality_score"], 0.85)
        self.assertTrue(result["threshold_reached"])
        self.assertGreaterEqual(result["iterations_used"], 1)
    
    def test_draft_critique_revise_multiple_iterations(self):
        """Test DCR with multiple iterations."""
        mock_client = MagicMock()
        router = TeacherRouter(deepseek_client=mock_client)
        
        # First call: low score, needs revision
        # Second call: high score, reaches threshold
        mock_client.critique.side_effect = [
            TeacherResponse(
                role="critic",
                content="",
                reasoning="Needs work",
                score=0.6,  # Below threshold
                metadata={
                    "strengths": [],
                    "weaknesses": ["Too brief"],
                    "suggestions": ["Add details"],
                    "key_revisions": ["Expand"]
                }
            ),
            TeacherResponse(
                role="critic",
                content="",
                reasoning="Much better",
                score=0.85,  # Above threshold
                metadata={
                    "strengths": ["Good"],
                    "weaknesses": [],
                    "suggestions": [],
                    "key_revisions": []
                }
            ),
        ]
        
        mock_client.verify.return_value = TeacherResponse(
            role="verifier",
            content="",
            reasoning="Verified",
            score=0.9,
            metadata={"verified": True, "corrections": []}
        )
        
        mock_client.rewrite.return_value = TeacherResponse(
            role="rewriter",
            content="Revised draft with more details.",
            reasoning="Added content",
            score=0.8,
            metadata={"improvements": ["Added details"]}
        )
        
        result = router.draft_critique_revise(
            "Original draft",
            evidence="Supporting evidence",
            rubric="Clear and detailed"
        )
        
        self.assertIn("Revised", result["final_text"])
        self.assertTrue(result["threshold_reached"])
        self.assertEqual(result["iterations_used"], 2)
        self.assertGreater(len(result["history"]), 0)


class TestDCRIntegration(unittest.TestCase):
    """Integration tests for draft-critique-revise loop."""
    
    def test_dcr_workflow_structure(self):
        """Test complete DCR workflow structure."""
        # Create mock client that simulates real behavior
        mock_client = MagicMock()
        router = TeacherRouter(deepseek_client=mock_client)
        
        # Setup realistic response sequence
        mock_client.critique.return_value = TeacherResponse(
            role="critic",
            content="",
            reasoning="Needs improvement",
            score=0.95,  # High enough to trigger end
            metadata={
                "strengths": ["Good start"],
                "weaknesses": ["Minor improvements"],
                "suggestions": ["Be more specific"],
                "key_revisions": ["Clarify intent"]
            }
        )
        
        result = router.draft_critique_revise(
            "Initial summary of the conversation.",
            evidence="Key facts from discussion",
            rubric="Clarity, completeness, accuracy"
        )
        
        # Verify structure
        self.assertIn("final_text", result)
        self.assertIn("quality_score", result)
        self.assertIn("iterations_used", result)
        self.assertIn("history", result)
        self.assertIn("threshold_reached", result)
        
        # Verify history is populated
        self.assertGreater(len(result["history"]), 0)
        
        # Verify each history entry has required fields
        for entry in result["history"]:
            self.assertIn("iteration", entry)
            self.assertIn("step", entry)


if __name__ == "__main__":
    unittest.main()
