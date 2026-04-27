# # src/llm/client.py
# from __future__ import annotations

# import json
# import os
# from dataclasses import dataclass
# from typing import Optional

# import requests


# @dataclass
# class LLMConfig:
#     provider: str = os.getenv("LLM_PROVIDER", "ollama")
#     model: str = os.getenv("LLM_MODEL", "qwen2.5:3b-instruct")
#     base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
#     api_key: Optional[str] = os.getenv("LLM_API_KEY")
#     timeout: int = int(os.getenv("LLM_TIMEOUT", "3600"))


# class BaseLLMClient:
#     def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
#         raise NotImplementedError


# class NullLLMClient(BaseLLMClient):
#     def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
#         return json.dumps(
#             {
#                 "document_summary": "",
#                 "fill_suggestions": [],
#                 "warnings": ["LLM client not configured"],
#             },
#             ensure_ascii=False,
#         )


# class OllamaClient(BaseLLMClient):
#     def __init__(self, config: LLMConfig | None = None):
#         self.config = config or LLMConfig()

#     def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
#         """
#         Siempre retorna str.
#         - Si el modelo devuelve JSON válido, retorna ese string directamente.
#         - Si devuelve markdown u otro formato, retorna el contenido crudo como str.
#         - Si hay error de red, retorna un JSON de error serializado como str.
#         """
#         payload = {
#             "model": self.config.model,
#             "messages": [
#                 {"role": "system", "content": system},
#                 {"role": "user", "content": user},
#             ],
#             "stream": False,
#             "options": {
#                 "temperature": temperature,
#                 # Fuerza JSON en modelos que lo soportan (Ollama >=0.1.14)
#                 # Si el modelo no lo soporta, simplemente lo ignora
#             },
#         }

#         # Intentar activar formato JSON nativo de Ollama
#         # Solo lo añadimos si el system prompt pide JSON estrictamente
#         if "STRICT JSON" in system or "Return STRICT JSON" in system:
#             payload["format"] = "json"

#         url = f"{self.config.base_url.rstrip('/')}/api/chat"

#         try:
#             print("LLM MODEL:", self.config.model)
#             print("Prompt length (chars):", len(user))

#             response = requests.post(url, json=payload, timeout=self.config.timeout)
#             response.raise_for_status()

#             data = response.json()
#             content = data["message"]["content"]

#             # Retornar siempre el contenido crudo como str
#             # El enriquecedor (_extract_json) se encarga del parseo
#             return content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)

#         except Exception as e:
#             # Retornar un JSON de error serializado como str (nunca un dict)
#             return json.dumps(
#                 {
#                     "document_summary": "",
#                     "fill_suggestions": [],
#                     "warnings": [f"Ollama error: {str(e)}"],
#                     "llm_raw_response": "",
#                 },
#                 ensure_ascii=False,
#             )


# def build_llm_client() -> BaseLLMClient:
#     provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()
#     if provider == "ollama":
#         return OllamaClient()
#     return NullLLMClient()

# src/llm/client.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class LLMConfig:
    provider: str = os.getenv("LLM_PROVIDER", "ollama")
    model: str = os.getenv("LLM_MODEL", "qwen2.5:3b-instruct")
    base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    api_key: Optional[str] = os.getenv("LLM_API_KEY")
    timeout: int = int(os.getenv("LLM_TIMEOUT", "300"))


class BaseLLMClient:
    def generate(self, system: str, user: str, temperature: float = 0.0) -> str:
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

    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> dict:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }

        url = f"{self.config.base_url.rstrip('/')}/api/chat"

        try:
            print("LLM MODEL:", self.config.model)
            print("Prompt length (chars):", len(user))

            response = requests.post(url, json=payload, timeout=self.config.timeout)
            response.raise_for_status()

            data = response.json()
            content = data["message"]["content"]

            try:
                return json.loads(content)
            except Exception:
                return {
                    "llm_applied_changes": [],
                    "warnings": ["Invalid JSON returned by LLM"],
                    "llm_raw_response": content,
                }

        except Exception as e:
            return {
                "llm_applied_changes": [],
                "warnings": [f"Ollama error: {str(e)}"],
                "llm_raw_response": "",
            }


def build_llm_client() -> BaseLLMClient:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()
    if provider == "ollama":
        return OllamaClient()
    return NullLLMClient()
