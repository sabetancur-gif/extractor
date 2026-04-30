"""
src/llm/client.py
-----------------
Cliente para comunicarse con modelos LLM (Ollama por defecto).
El método generate() SIEMPRE retorna str (nunca un dict).
El parseo/validación del JSON se hace en el enriquecedor.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class LLMConfig:
    """Configuración del cliente LLM. Usa variables de entorno."""
    provider: str          = os.getenv("LLM_PROVIDER", "ollama")
    model:    str          = os.getenv("LLM_MODEL",    "qwen2.5:3b-instruct")
    base_url: str          = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    api_key:  Optional[str]= os.getenv("LLM_API_KEY")
    timeout:  int          = int(os.getenv("LLM_TIMEOUT", "300"))


class BaseLLMClient:
    """Interfaz base para clientes LLM."""
    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        raise NotImplementedError


class NullLLMClient(BaseLLMClient):
    """Cliente nulo: retorna un JSON vacío válido cuando no hay LLM configurado."""
    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        return json.dumps({
            "document_summary": "LLM no configurado.",
            "fill_suggestions": [],
            "warnings":         ["LLM client not configured."],
        }, ensure_ascii=False)


class OllamaClient(BaseLLMClient):
    """Cliente para Ollama (local). Siempre retorna str con la respuesta del modelo."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig()

    def generate(self, *, system: str, user: str, temperature: float = 0.0) -> str:
        """
        Llama a la API de Ollama y retorna el contenido como str.
        Si el modelo retorna JSON válido, retorna el string directamente.
        En caso de error, retorna un JSON de error serializado.
        """
        payload = {
            "model":   self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "stream":  False,
            "options": {"temperature": temperature},
        }

        # Activar formato JSON nativo si el prompt lo requiere
        if "STRICT JSON" in system or "Return STRICT JSON" in system:
            payload["format"] = "json"

        url = f"{self.config.base_url.rstrip('/')}/api/chat"

        try:
            print(f"[LLM] Model: {self.config.model} | Prompt: {len(user)} chars")
            resp = requests.post(url, json=payload, timeout=self.config.timeout)
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            # Siempre retornar str
            return content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)

        except requests.exceptions.ConnectionError:
            return json.dumps({
                "document_summary": "",
                "fill_suggestions": [],
                "warnings":         [f"No se pudo conectar a Ollama en {self.config.base_url}. ¿Está corriendo?"],
            }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "document_summary": "",
                "fill_suggestions": [],
                "warnings":         [f"Error LLM: {str(e)}"],
            }, ensure_ascii=False)


def build_llm_client() -> BaseLLMClient:
    """Factory: construye el cliente LLM según la variable de entorno LLM_PROVIDER."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()
    if provider == "ollama":
        return OllamaClient()
    return NullLLMClient()
