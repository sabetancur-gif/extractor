"""
src/llm/chatbot.py
------------------
JuanBot — Chatbot de análisis de documentos PDF.
Características:
  - Conoce TODOS los documentos cargados (no solo el seleccionado).
  - Mantiene historial de conversación multi-turno.
  - Responde en el mismo idioma del usuario.
  - Cita la página de origen cuando es posible.
"""
from __future__ import annotations

import json
from typing import Any

from src.llm.client import build_llm_client


JUANBOT_SYSTEM = """\
Eres JuanBot, un asistente experto en análisis y extracción de documentos PDF.
El usuario ha procesado uno o más documentos PDF y puedes responder preguntas sobre ellos.

Reglas:
- Responde SIEMPRE basándote en el contenido de los documentos proporcionados.
- Si la información proviene de un documento específico, menciona el nombre del archivo y la página.
- Si la información NO está en los documentos, dilo claramente — NUNCA inventes datos.
- Sé conciso, preciso y profesional.
- Responde en el mismo idioma que el usuario.
- Cuando el usuario pregunte por fechas, montos, nombres, etc., busca en los campos extraídos primero.
- Si hay múltiples documentos, distingue la información por documento.
"""


def _safe_str(value: Any) -> str:
    """Convierte cualquier valor a str de forma segura."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        raw = value.get("llm_raw_response") or value.get("content") or ""
        if raw:
            return str(raw)
        warnings = value.get("warnings", [])
        if warnings:
            return f"Error del LLM: {'; '.join(str(w) for w in warnings)}"
    return json.dumps(value, ensure_ascii=False)


def _build_doc_summary(doc_ctx: dict[str, Any], max_text: int = 5000) -> str:
    """Construye un resumen compacto del documento para el contexto del chatbot."""
    parts: list[str] = []

    file_name   = doc_ctx.get("file_name", "Documento")
    pages_total = doc_ctx.get("pages_total", "?")
    mode        = doc_ctx.get("processing_mode", "")
    doc_type    = doc_ctx.get("llm_document_type", "")
    summary     = doc_ctx.get("llm_document_summary", "")

    parts.append(f"── DOCUMENTO: {file_name} ({pages_total} págs, modo: {mode}) ──")
    if doc_type:
        parts.append(f"   Tipo: {doc_type}")
    if summary:
        parts.append(f"   Resumen: {summary}")

    # Campos extraídos (compactos)
    fields = doc_ctx.get("fields", []) or []
    if fields:
        parts.append("   Campos:")
        for f in fields[:50]:
            if not isinstance(f, dict):
                continue
            name = f.get("field") or f.get("label") or ""
            val  = f.get("llm_filled_value") or f.get("value") or ""
            page = f.get("page_number") or f.get("page") or ""
            if name and val:
                parts.append(f"     • {name}: {val}  (pág {page})")

    # Texto completo (truncado por documento)
    full_text = doc_ctx.get("full_text", "")
    if not full_text:
        page_parts = []
        for p in (doc_ctx.get("pages", []) or []):
            pn = p.get("page_number", "?")
            for b in (p.get("blocks", []) or []):
                t = (b.get("text") or "").strip()
                if t:
                    page_parts.append(f"[Pág {pn}] {t}")
        full_text = "\n".join(page_parts)

    if full_text:
        parts.append(f"   Contenido:\n{full_text[:max_text]}")

    return "\n".join(parts)


class JuanBot:
    """
    JuanBot: asistente conversacional para análisis de documentos PDF.
    Soporta múltiples documentos simultáneamente.
    """

    def __init__(self):
        self.client  = build_llm_client()
        self.history: list[dict[str, str]] = []
        self._docs_context: str = ""
        self._docs_hash:    str = ""

    def set_documents(self, doc_ctx_map: dict[str, dict[str, Any]]) -> None:
        """
        Carga el contexto de TODOS los documentos procesados.

        Args:
            doc_ctx_map: dict {doc_id: doc_ctx} con todos los documentos cargados.
        """
        if not isinstance(doc_ctx_map, dict) or not doc_ctx_map:
            self._docs_context = ""
            self._docs_hash    = ""
            self.history       = []
            return

        parts = [f"Hay {len(doc_ctx_map)} documento(s) cargado(s):\n"]

        # Repartir el contexto máximo equitativamente entre documentos
        max_per_doc = max(2000, 12000 // len(doc_ctx_map))

        for doc_ctx in doc_ctx_map.values():
            if isinstance(doc_ctx, dict):
                parts.append(_build_doc_summary(doc_ctx, max_text=max_per_doc))
                parts.append("")  # separador

        self._docs_context = "\n".join(parts)
        self._docs_hash    = str(sorted(doc_ctx_map.keys()))
        self.history       = []  # limpiar historial al cargar nuevos documentos

    def chat(self, user_message: str) -> str:
        """
        Procesa un mensaje del usuario y retorna la respuesta de JuanBot.

        Returns:
            Respuesta como str (nunca un dict).
        """
        if not self._docs_context:
            return (
                "Hola, soy JuanBot 👋. Para poder ayudarte, primero debes procesar al menos "
                "un PDF usando el botón 'Create Visualization' en el tab de Visualization."
            )

        system = (
            f"{JUANBOT_SYSTEM}\n\n"
            f"=== DOCUMENTOS DISPONIBLES ===\n{self._docs_context}\n"
            f"=== FIN DOCUMENTOS ==="
        )

        # Construir historial de conversación (últimos 10 turnos)
        self.history.append({"role": "user", "content": user_message})
        conversation = self.history[-10:]

        # Formatear conversación para el LLM
        conv_text = "\n".join(
            f"{'Usuario' if m['role'] == 'user' else 'JuanBot'}: {m['content']}"
            for m in conversation[:-1]  # todos menos el último (que es el mensaje actual)
        )

        if conv_text:
            full_prompt = f"Historial:\n{conv_text}\n\nPregunta actual: {user_message}"
        else:
            full_prompt = user_message

        try:
            raw = self.client.generate(system=system, user=full_prompt, temperature=0.3)
            response = _safe_str(raw)
        except Exception as e:
            response = f"Error al consultar el modelo: {e}"

        self.history.append({"role": "assistant", "content": response})
        return response

    def clear(self) -> None:
        """Limpia el historial de conversación."""
        self.history = []


# Alias para compatibilidad con código anterior
PDFChatbot = JuanBot
