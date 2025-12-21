import os
from typing import Optional

from .llm.llama_client import HttpLLM, LLMClient


def get_llm_client() -> Optional[LLMClient]:
    endpoint = os.environ.get("AC_LLM_ENDPOINT")
    if endpoint:
        try:
            return HttpLLM(endpoint)
        except Exception:
            return None
    return None
