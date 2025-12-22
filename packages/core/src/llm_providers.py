"""
LLM Provider Interface and Implementations

Unified interface for multiple LLM backends with reliability features.
Supports local inference (llama.cpp, vLLM) and hosted APIs (OpenAI, Anthropic, DeepSeek).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Literal, Iterator
from enum import Enum
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import os


class ProviderCapability(Enum):
    """Provider capability flags"""
    STREAMING = "streaming"
    TOOL_CALLS = "tool_calls"
    JSON_MODE = "json_mode"
    VISION = "vision"
    LOGPROBS = "logprobs"


@dataclass
class ProviderCapabilities:
    """Provider capability metadata"""
    streaming: bool = True
    tool_calls: bool = False
    json_mode: bool = False
    vision: bool = False
    logprobs: bool = False
    max_context_tokens: int = 4096
    supports_system_message: bool = True


@dataclass
class UsageMetrics:
    """Token usage and cost tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class LLMResponse:
    """Standardized LLM response object"""
    text: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: UsageMetrics = field(default_factory=UsageMetrics)
    latency_ms: float = 0.0
    provider: str = ""
    model_id: str = ""
    request_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    finish_reason: Optional[str] = None


@dataclass
class Message:
    """Chat message"""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class CircuitBreaker:
    """Circuit breaker pattern for provider failure handling"""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state: Literal["closed", "open", "half_open"] = "closed"
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.timeout_seconds:
                self.state = "half_open"
            else:
                raise Exception(f"Circuit breaker OPEN: provider unavailable")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise e


class RateLimiter:
    """Simple token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_update = time.time()
    
    def acquire(self):
        """Acquire a token, blocking if necessary"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.requests_per_minute, self.tokens + elapsed * (self.requests_per_minute / 60))
        self.last_update = now
        
        if self.tokens < 1:
            sleep_time = (1 - self.tokens) * (60 / self.requests_per_minute)
            time.sleep(sleep_time)
            self.tokens = 1
        
        self.tokens -= 1


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(
        self,
        model_id: str,
        api_key: Optional[str] = None,
        timeout_seconds: int = 60,
        max_retries: int = 3,
        rate_limit_rpm: int = 60
    ):
        self.model_id = model_id
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter(requests_per_minute=rate_limit_rpm)
        
        # Setup requests session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities"""
        pass
    
    @abstractmethod
    def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """Generate completion"""
        pass
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost in USD (override per provider)"""
        return 0.0


class OpenAIProvider(LLMProvider):
    """OpenAI and OpenAI-compatible providers"""
    
    def __init__(
        self,
        model_id: str = "gpt-4",
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        **kwargs
    ):
        super().__init__(model_id, api_key or os.getenv("OPENAI_API_KEY"), **kwargs)
        self.base_url = base_url.rstrip("/")
        
        # Cost per 1M tokens (update as needed)
        self.cost_per_million_input = 0.01  # $0.01/1M tokens
        self.cost_per_million_output = 0.03  # $0.03/1M tokens
    
    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            streaming=True,
            tool_calls=True,
            json_mode=True,
            vision=False,
            logprobs=False,
            max_context_tokens=8192,
            supports_system_message=True
        )
    
    def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """Generate completion via OpenAI API"""
        self.rate_limiter.acquire()
        
        start_time = time.time()
        
        def _make_request():
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_id,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            if tools:
                payload["tools"] = tools
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            return response.json()
        
        # Execute with circuit breaker
        result = self.circuit_breaker.call(_make_request)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Parse response
        choice = result["choices"][0]
        message = choice["message"]
        usage = result.get("usage", {})
        
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        return LLMResponse(
            text=message.get("content", ""),
            tool_calls=message.get("tool_calls", []),
            usage=UsageMetrics(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=self.estimate_cost(prompt_tokens, completion_tokens)
            ),
            latency_ms=latency_ms,
            provider="openai",
            model_id=self.model_id,
            request_id=result.get("id", ""),
            finish_reason=choice.get("finish_reason")
        )
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost in USD"""
        input_cost = (prompt_tokens / 1_000_000) * self.cost_per_million_input
        output_cost = (completion_tokens / 1_000_000) * self.cost_per_million_output
        return input_cost + output_cost


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(
        self,
        model_id: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_id, api_key or os.getenv("ANTHROPIC_API_KEY"), **kwargs)
        self.base_url = "https://api.anthropic.com/v1"
        
        # Cost per 1M tokens
        self.cost_per_million_input = 0.003
        self.cost_per_million_output = 0.015
    
    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            streaming=True,
            tool_calls=True,
            json_mode=False,
            vision=True,
            logprobs=False,
            max_context_tokens=200000,
            supports_system_message=True
        )
    
    def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """Generate completion via Anthropic API"""
        self.rate_limiter.acquire()
        
        start_time = time.time()
        
        def _make_request():
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            # Anthropic requires system message separate
            system_message = None
            user_messages = []
            for m in messages:
                if m.role == "system":
                    system_message = m.content
                else:
                    user_messages.append({"role": m.role, "content": m.content})
            
            payload = {
                "model": self.model_id,
                "messages": user_messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024
            }
            
            if system_message:
                payload["system"] = system_message
            if tools:
                payload["tools"] = tools
            
            response = self.session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            return response.json()
        
        result = self.circuit_breaker.call(_make_request)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Parse response
        content = result["content"][0]
        usage = result.get("usage", {})
        
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)
        
        return LLMResponse(
            text=content.get("text", ""),
            tool_calls=[],
            usage=UsageMetrics(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=self.estimate_cost(prompt_tokens, completion_tokens)
            ),
            latency_ms=latency_ms,
            provider="anthropic",
            model_id=self.model_id,
            request_id=result.get("id", ""),
            finish_reason=result.get("stop_reason")
        )
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        input_cost = (prompt_tokens / 1_000_000) * self.cost_per_million_input
        output_cost = (completion_tokens / 1_000_000) * self.cost_per_million_output
        return input_cost + output_cost


class LocalLLMProvider(LLMProvider):
    """Local inference via llama.cpp or vLLM (OpenAI-compatible)"""
    
    def __init__(
        self,
        model_id: str = "local-model",
        base_url: str = "http://localhost:8000",
        **kwargs
    ):
        super().__init__(model_id, api_key=None, **kwargs)
        self.base_url = base_url.rstrip("/")
    
    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            streaming=True,
            tool_calls=False,
            json_mode=False,
            vision=False,
            logprobs=False,
            max_context_tokens=4096,
            supports_system_message=True
        )
    
    def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """Generate completion via local server"""
        self.rate_limiter.acquire()
        
        start_time = time.time()
        
        def _make_request():
            payload = {
                "model": self.model_id,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            return response.json()
        
        result = self.circuit_breaker.call(_make_request)
        
        latency_ms = (time.time() - start_time) * 1000
        
        choice = result["choices"][0]
        message = choice["message"]
        usage = result.get("usage", {})
        
        return LLMResponse(
            text=message.get("content", ""),
            tool_calls=[],
            usage=UsageMetrics(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                estimated_cost_usd=0.0  # Local inference is free
            ),
            latency_ms=latency_ms,
            provider="local",
            model_id=self.model_id,
            request_id=result.get("id", "")
        )
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.0  # Local is free


class ProviderFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create(
        provider_name: str,
        model_id: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """Create provider by name"""
        if provider_name == "openai":
            return OpenAIProvider(model_id=model_id or "gpt-4", **kwargs)
        elif provider_name == "anthropic":
            return AnthropicProvider(model_id=model_id or "claude-3-5-sonnet-20241022", **kwargs)
        elif provider_name == "local":
            return LocalLLMProvider(model_id=model_id or "local-model", **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider_name}")
