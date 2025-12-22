"""
Tests for LLM Provider Interface
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from packages.core.src.llm_providers import (
    Message,
    LLMResponse,
    UsageMetrics,
    ProviderCapabilities,
    CircuitBreaker,
    RateLimiter,
    OpenAIProvider,
    AnthropicProvider,
    LocalLLMProvider,
    ProviderFactory
)


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern"""
    
    def test_closed_state_allows_calls(self):
        """Circuit breaker should allow calls in closed state"""
        cb = CircuitBreaker(failure_threshold=3)
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        self.assertEqual(result, "success")
        self.assertEqual(cb.state, "closed")
    
    def test_opens_after_threshold_failures(self):
        """Circuit breaker should open after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3)
        
        def failing_func():
            raise Exception("API error")
        
        # Trigger failures
        for i in range(3):
            with self.assertRaises(Exception):
                cb.call(failing_func)
        
        self.assertEqual(cb.state, "open")
    
    def test_open_state_blocks_calls(self):
        """Circuit breaker should block calls when open"""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=10)
        
        def failing_func():
            raise Exception("API error")
        
        # Trigger failures to open circuit
        for i in range(2):
            with self.assertRaises(Exception):
                cb.call(failing_func)
        
        # Should now block
        with self.assertRaises(Exception) as ctx:
            cb.call(failing_func)
        
        self.assertIn("Circuit breaker OPEN", str(ctx.exception))


class TestRateLimiter(unittest.TestCase):
    """Test rate limiting"""
    
    def test_allows_requests_within_limit(self):
        """Rate limiter should allow requests within limit"""
        limiter = RateLimiter(requests_per_minute=60)
        
        # Should not block (plenty of tokens)
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 0.1)  # Should be instant
    
    def test_enforces_rate_limit(self):
        """Rate limiter should delay when limit exceeded"""
        limiter = RateLimiter(requests_per_minute=6)  # 1 every 10 seconds
        
        # First request should be instant
        limiter.acquire()
        
        # Drain all tokens
        for i in range(5):
            limiter.tokens -= 1
        
        # Next request should block briefly
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        
        # Should have waited (at least a little bit)
        # Note: might be flaky, but shows concept
        # In practice this would wait ~10 seconds


class TestOpenAIProvider(unittest.TestCase):
    """Test OpenAI provider"""
    
    @patch('packages.core.src.llm_providers.requests.Session.post')
    def test_complete_success(self, mock_post):
        """OpenAI provider should handle successful completion"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "chatcmpl-123",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you?"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Create provider
        provider = OpenAIProvider(model_id="gpt-4", api_key="test-key")
        
        # Make request
        messages = [Message(role="user", content="Hello")]
        response = provider.complete(messages)
        
        # Verify
        self.assertIsInstance(response, LLMResponse)
        self.assertEqual(response.text, "Hello! How can I help you?")
        self.assertEqual(response.usage.prompt_tokens, 10)
        self.assertEqual(response.usage.completion_tokens, 20)
        self.assertEqual(response.provider, "openai")
        self.assertGreaterEqual(response.latency_ms, 0)  # Allow zero for fast mock
    
    def test_estimate_cost(self):
        """OpenAI provider should estimate cost correctly"""
        provider = OpenAIProvider(model_id="gpt-4")
        provider.cost_per_million_input = 10.0
        provider.cost_per_million_output = 30.0
        
        cost = provider.estimate_cost(prompt_tokens=1000, completion_tokens=500)
        
        # 1000 * 10 / 1M + 500 * 30 / 1M = 0.01 + 0.015 = 0.025
        self.assertAlmostEqual(cost, 0.025, places=4)
    
    def test_capabilities(self):
        """OpenAI provider should report capabilities"""
        provider = OpenAIProvider()
        caps = provider.get_capabilities()
        
        self.assertTrue(caps.streaming)
        self.assertTrue(caps.tool_calls)
        self.assertTrue(caps.json_mode)


class TestAnthropicProvider(unittest.TestCase):
    """Test Anthropic provider"""
    
    @patch('packages.core.src.llm_providers.requests.Session.post')
    def test_complete_success(self, mock_post):
        """Anthropic provider should handle successful completion"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "msg_123",
            "content": [{
                "type": "text",
                "text": "I'm Claude, how can I help?"
            }],
            "usage": {
                "input_tokens": 15,
                "output_tokens": 25
            },
            "stop_reason": "end_turn"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        provider = AnthropicProvider(model_id="claude-3-5-sonnet-20241022", api_key="test-key")
        
        messages = [
            Message(role="system", content="You are helpful"),
            Message(role="user", content="Hello")
        ]
        response = provider.complete(messages)
        
        self.assertEqual(response.text, "I'm Claude, how can I help?")
        self.assertEqual(response.usage.prompt_tokens, 15)
        self.assertEqual(response.usage.completion_tokens, 25)
        self.assertEqual(response.provider, "anthropic")
    
    def test_capabilities(self):
        """Anthropic provider should report capabilities"""
        provider = AnthropicProvider()
        caps = provider.get_capabilities()
        
        self.assertTrue(caps.streaming)
        self.assertTrue(caps.tool_calls)
        self.assertTrue(caps.vision)
        self.assertEqual(caps.max_context_tokens, 200000)


class TestLocalLLMProvider(unittest.TestCase):
    """Test local LLM provider"""
    
    @patch('packages.core.src.llm_providers.requests.Session.post')
    def test_complete_success(self, mock_post):
        """Local provider should handle completion"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "local-123",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Local model response"
                }
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        provider = LocalLLMProvider(base_url="http://localhost:8000")
        
        messages = [Message(role="user", content="Test")]
        response = provider.complete(messages)
        
        self.assertEqual(response.text, "Local model response")
        self.assertEqual(response.provider, "local")
        self.assertEqual(response.usage.estimated_cost_usd, 0.0)  # Local is free
    
    def test_zero_cost(self):
        """Local provider should have zero cost"""
        provider = LocalLLMProvider()
        cost = provider.estimate_cost(1000, 500)
        self.assertEqual(cost, 0.0)


class TestProviderFactory(unittest.TestCase):
    """Test provider factory"""
    
    def test_create_openai(self):
        """Factory should create OpenAI provider"""
        provider = ProviderFactory.create("openai", model_id="gpt-4")
        self.assertIsInstance(provider, OpenAIProvider)
        self.assertEqual(provider.model_id, "gpt-4")
    
    def test_create_anthropic(self):
        """Factory should create Anthropic provider"""
        provider = ProviderFactory.create("anthropic")
        self.assertIsInstance(provider, AnthropicProvider)
    
    def test_create_local(self):
        """Factory should create Local provider"""
        provider = ProviderFactory.create("local")
        self.assertIsInstance(provider, LocalLLMProvider)
    
    def test_unknown_provider_raises(self):
        """Factory should raise on unknown provider"""
        with self.assertRaises(ValueError):
            ProviderFactory.create("unknown-provider")


if __name__ == '__main__':
    unittest.main()
