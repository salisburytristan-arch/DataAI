from typing import Any, Dict, List
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class LLMClient:
    def generate(self, *, system: str, user: str, prompt: str, evidence: List[Dict[str, Any]]) -> str:
        raise NotImplementedError


class MockLLM(LLMClient):
    def generate(self, *, system: str, user: str, prompt: str, evidence: List[Dict[str, Any]]) -> str:
        # Deterministic synthetic generation: echo query and cite first evidence
        top = evidence[0] if evidence else {}
        doc_title = top.get("doc_title", "Unknown")
        chunk_id = top.get("chunk_id", "?")
        snippet = (top.get("content", "").strip().replace("\n", " ")[:160] + "…") if top.get("content") else ""
        return (
            f"You asked: '{user}'.\n"
            f"Answer synthesized from {len(evidence)} evidence chunks.\n"
            f"Top source: {doc_title} (chunk {chunk_id}).\n"
            f"Snippet: {snippet}"
        )


class HttpLLM(LLMClient):
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint.rstrip("/")

    def generate(self, *, system: str, user: str, prompt: str, evidence: List[Dict[str, Any]]) -> str:
        # OpenAI/llama.cpp compatible /v1/chat/completions payload
        payload = {
            "model": "local",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 256,
            "stream": False,
        }
        url = f"{self.endpoint}/v1/chat/completions"
        req = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Expect standard choices[0].message.content
                choices = data.get("choices") or []
                if choices:
                    msg = choices[0].get("message") or {}
                    content = msg.get("content")
                    if content:
                        return content
                # Fallback parse for llama.cpp variants
                return json.dumps(data)[:400]
        except (URLError, HTTPError, TimeoutError):
            # Bubble up to caller to decide fallback
            raise
