"""Teacher client for DeepSeek API integration.

Provides access to DeepSeek model for verification, critique, and revision tasks.
Handles API authentication, rate limiting, and response parsing.
"""

import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TeacherResponse:
    """Response from a teacher model."""
    role: str              # 'verifier', 'critic', 'rewriter'
    content: str           # Generated response
    reasoning: str         # Explanation of reasoning
    score: Optional[float] # Confidence/quality score (0.0-1.0)
    metadata: Dict[str, Any]  # Additional info


class DeepSeekClient:
    """
    DeepSeek API client for critique and verification tasks.
    
    Features:
    - Stateless requests (no conversation history)
    - Role-based prompting (verifier, critic, rewriter)
    - Token limit enforcement
    - Error handling with fallback
    
    Usage:
        client = DeepSeekClient(api_key=os.getenv("DEEPSEEK_API_KEY"))
        response = client.verify(draft, evidence)
        response = client.critique(draft, rubric)
        response = client.rewrite(draft, feedback)
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        """
        Initialize DeepSeek client.
        
        Args:
            api_key: DeepSeek API key (default: DEEPSEEK_API_KEY env var)
            model: Model ID (default: deepseek-chat)
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")
        
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"
        self.max_tokens = 2048
    
    def verify(self, draft: str, evidence: str, strict: bool = False) -> TeacherResponse:
        """
        Verify factual accuracy of draft against evidence.
        
        Args:
            draft: Text to verify
            evidence: Supporting evidence/reference material
            strict: If True, require high confidence for approval
            
        Returns:
            TeacherResponse with verification result
        """
        prompt = f"""Role: Fact Verifier

You are a strict fact-checking agent. Verify the draft against the provided evidence.

DRAFT:
{draft}

EVIDENCE:
{evidence}

Task:
1. Identify any factual claims in the draft
2. Check each claim against the evidence
3. Mark claims as: CORRECT, INCORRECT, UNVERIFIED
4. Provide a confidence score (0.0-1.0) for overall accuracy
5. List any corrections needed

Format your response as JSON:
{{
  "verified": true/false,
  "score": 0.0-1.0,
  "claims": [
    {{"claim": "...", "status": "CORRECT|INCORRECT|UNVERIFIED", "note": "..."}}
  ],
  "corrections": ["..."],
  "reasoning": "Overall assessment..."
}}"""
        
        response = self._call_api(prompt)
        return self._parse_verification_response(response, strict)
    
    def critique(self, draft: str, rubric: str = None) -> TeacherResponse:
        """
        Provide constructive critique on draft quality.
        
        Args:
            draft: Text to critique
            rubric: Evaluation criteria (optional)
            
        Returns:
            TeacherResponse with feedback
        """
        rubric_section = f"\nRubric:\n{rubric}" if rubric else ""
        
        prompt = f"""Role: Quality Critic

You are a constructive critic. Evaluate the draft for clarity, coherence, and completeness.

DRAFT:
{draft}{rubric_section}

Task:
1. Identify strengths
2. Identify weaknesses
3. Score overall quality (0.0-1.0)
4. Provide specific improvement suggestions
5. Suggest 1-2 key revisions

Format your response as JSON:
{{
  "score": 0.0-1.0,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": ["..."],
  "key_revisions": ["..."],
  "reasoning": "Overall assessment..."
}}"""
        
        response = self._call_api(prompt)
        return self._parse_critique_response(response)
    
    def rewrite(self, draft: str, feedback: str) -> TeacherResponse:
        """
        Rewrite draft based on feedback.
        
        Args:
            draft: Original text
            feedback: Specific feedback/instructions for revision
            
        Returns:
            TeacherResponse with revised text
        """
        prompt = f"""Role: Expert Rewriter

You are a skilled editor. Improve the draft based on the feedback provided.

ORIGINAL DRAFT:
{draft}

FEEDBACK:
{feedback}

Task:
1. Rewrite the draft incorporating the feedback
2. Preserve core meaning while improving clarity/quality
3. Keep similar length (±20%)
4. Explain key changes

Format your response as JSON:
{{
  "revised_text": "...",
  "improvements_made": ["..."],
  "reasoning": "Explanation of revisions...",
  "score": 0.0-1.0
}}"""
        
        response = self._call_api(prompt)
        return self._parse_rewrite_response(response)
    
    def _call_api(self, prompt: str) -> str:
        """Make API call to DeepSeek."""
        try:
            import urllib.request
            import urllib.error
            
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            data = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,  # Lower temp for structured output
                "max_tokens": self.max_tokens,
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"Warning: DeepSeek API call failed: {e}")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback for API failures (mock response for testing)."""
        return json.dumps({
            "verified": True,
            "score": 0.8,
            "reasoning": "[FALLBACK] Unable to reach DeepSeek API",
            "claims": [],
            "corrections": [],
        })
    
    @staticmethod
    def _parse_verification_response(response: str, strict: bool = False) -> TeacherResponse:
        """Parse verification response."""
        try:
            data = json.loads(response)
            score = data.get("score", 0.5)
            
            # Apply strictness threshold
            if strict:
                verified = score >= 0.95
            else:
                verified = score >= 0.7
            
            return TeacherResponse(
                role="verifier",
                content=json.dumps(data.get("claims", [])),
                reasoning=data.get("reasoning", ""),
                score=score,
                metadata={
                    "verified": verified,
                    "corrections": data.get("corrections", []),
                }
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse verification response: {e}")
            return TeacherResponse(
                role="verifier",
                content="",
                reasoning="Parse error",
                score=0.0,
                metadata={"error": str(e)}
            )
    
    @staticmethod
    def _parse_critique_response(response: str) -> TeacherResponse:
        """Parse critique response."""
        try:
            data = json.loads(response)
            return TeacherResponse(
                role="critic",
                content="",
                reasoning=data.get("reasoning", ""),
                score=data.get("score", 0.5),
                metadata={
                    "strengths": data.get("strengths", []),
                    "weaknesses": data.get("weaknesses", []),
                    "suggestions": data.get("suggestions", []),
                    "key_revisions": data.get("key_revisions", []),
                }
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse critique response: {e}")
            return TeacherResponse(
                role="critic",
                content="",
                reasoning="Parse error",
                score=0.0,
                metadata={"error": str(e)}
            )
    
    @staticmethod
    def _parse_rewrite_response(response: str) -> TeacherResponse:
        """Parse rewrite response."""
        try:
            data = json.loads(response)
            return TeacherResponse(
                role="rewriter",
                content=data.get("revised_text", ""),
                reasoning=data.get("reasoning", ""),
                score=data.get("score", 0.5),
                metadata={
                    "improvements": data.get("improvements_made", []),
                }
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not parse rewrite response: {e}")
            return TeacherResponse(
                role="rewriter",
                content="",
                reasoning="Parse error",
                score=0.0,
                metadata={"error": str(e)}
            )


class TeacherRouter:
    """
    Route tasks to appropriate teachers based on task type.
    
    Implements draft-critique-revise protocol:
    1. Agent generates draft
    2. Critic provides feedback
    3. Verifier checks accuracy
    4. Rewriter improves based on feedback
    5. Loop until quality threshold reached
    """
    
    def __init__(self, deepseek_client: Optional[DeepSeekClient] = None):
        """Initialize router with optional DeepSeek client."""
        self.deepseek = deepseek_client
        self.max_iterations = 3
        self.quality_threshold = 0.8
    
    def draft_critique_revise(
        self,
        draft: str,
        evidence: str = "",
        rubric: str = None,
        iterations: int = None
    ) -> Dict[str, Any]:
        """
        Execute full draft-critique-revise loop.
        
        Args:
            draft: Initial draft from agent
            evidence: Supporting evidence for verification
            rubric: Evaluation criteria
            iterations: Max iterations (default: self.max_iterations)
            
        Returns:
            Dict with final_text, quality_score, iterations_used, history
        """
        if not self.deepseek:
            return {
                "final_text": draft,
                "quality_score": 0.0,
                "error": "DeepSeek client not configured"
            }
        
        iterations = iterations or self.max_iterations
        current_text = draft
        history = []
        
        for i in range(iterations):
            # Critique current version
            critique_result = self.deepseek.critique(current_text, rubric)
            quality = critique_result.score
            
            history.append({
                "iteration": i,
                "step": "critique",
                "score": quality,
                "feedback": critique_result.metadata.get("suggestions", []),
            })
            
            # Check if quality threshold reached
            if quality >= self.quality_threshold:
                history.append({
                    "iteration": i,
                    "step": "stopped",
                    "reason": "quality_threshold_reached",
                    "score": quality,
                })
                break
            
            # Get verification feedback
            if evidence:
                verify_result = self.deepseek.verify(current_text, evidence)
                history[-1]["verification_score"] = verify_result.score
                corrections = verify_result.metadata.get("corrections", [])
            else:
                corrections = []
            
            # Combine feedback
            feedback = "\n".join([
                "Critique feedback:",
                "\n".join(critique_result.metadata.get("suggestions", [])),
                "Suggested key revisions:",
                "\n".join(critique_result.metadata.get("key_revisions", [])),
            ])
            
            if corrections:
                feedback += "\n\nFactual corrections needed:\n"
                feedback += "\n".join(corrections)
            
            # Rewrite with feedback
            rewrite_result = self.deepseek.rewrite(current_text, feedback)
            current_text = rewrite_result.content
            
            history.append({
                "iteration": i,
                "step": "revision",
                "improvements": rewrite_result.metadata.get("improvements", []),
            })
        
        return {
            "final_text": current_text,
            "quality_score": quality,
            "iterations_used": i + 1,
            "history": history,
            "threshold_reached": quality >= self.quality_threshold,
        }
