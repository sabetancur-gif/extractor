# src/llm/client.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

import requests


@dataclass
class LLMConfig:
    provider: str = os.getenv("LLM_PROVIDER", "ollama")
    model: str = os.getenv("LLM_MODEL", "qwen2.5:14b-instruct")
    base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    api_key: Optional[str] = os.getenv("LLM_API_KEY")
    timeout: int = int(os.getenv("LLM_TIMEOUT", "120"))


class BaseLLMClient:
    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        raise NotImplementedError


class NullLLMClient(BaseLLMClient):
    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        return json.dumps(
            {
                "document_summary": "",
                "fill_suggestions": [],
                "warnings": ["LLM client not configured"],
            },
            ensure_ascii=False,
        )


class OllamaClient(BaseLLMClient):
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()

    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        url = f"{self.config.base_url.rstrip('/')}/api/chat"
        response = requests.post(url, json=payload, timeout=self.config.timeout)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


def build_llm_client() -> BaseLLMClient:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()
    if provider == "ollama":
        return OllamaClient()
    return NullLLMClient()