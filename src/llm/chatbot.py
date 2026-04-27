# src/llm/chatbot.py
from __future__ import annotations

import json
from typing import Any

from src.llm.client import build_llm_client


CHATBOT_SYSTEM = """
Eres un asistente experto en análisis de documentos. El usuario ha procesado un PDF.
Responde SIEMPRE basándote en el contenido del documento proporcionado.
Cuando cites información, menciona la página de origen si está disponible.
Si la información no está en el documento, dilo claramente — no inventes datos.
Sé conciso y preciso. Responde en el mismo idioma que el usuario.
"""


def _safe_str(value: Any) -> str:
    """Convierte cualquier valor a str de forma segura — nunca retorna un dict/list."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        # El cliente retornó un dict de error → extraer mensaje legible
        if isinstance(value, dict):
            # Intentar sacar el contenido útil
            raw = value.get("llm_raw_response") or value.get("content") or ""
            if raw:
                return str(raw)
            warnings = value.get("warnings", [])
            if warnings:
                return f"Error del LLM: {'; '.join(str(w) for w in warnings)}"
        return json.dumps(value, ensure_ascii=False)
    return str(value)


class PDFChatbot:
    def __init__(self):
        self.client = build_llm_client()
        self.history: list[dict] = []
        self._doc_context: str = ""
        self._doc_hash: str = ""

    def set_document(self, doc_ctx: dict[str, Any]) -> None:
        """Inicializa el chatbot con el contexto del documento procesado."""
        parts = []

        file_name = doc_ctx.get("file_name", "Documento")
        pages_total = doc_ctx.get("pages_total", "?")
        processing_mode = doc_ctx.get("processing_mode", "")
        parts.append(f"DOCUMENTO: {file_name} ({pages_total} páginas, modo: {processing_mode})\n")

        # ── Texto completo ──────────────────────────────────────────────────
        full_text = doc_ctx.get("full_text", "")
        if not full_text:
            pages = doc_ctx.get("pages", []) or []
            texts = []
            for p in pages:
                pn = p.get("page_number", "?")
                for b in p.get("blocks", []) or []:
                    t = (b.get("text") or "").strip()
                    if t:
                        texts.append(f"[Pág {pn}] {t}")
            full_text = "\n".join(texts)

        if full_text:
            parts.append(f"CONTENIDO DEL DOCUMENTO:\n{full_text[:14000]}")
        else:
            parts.append("CONTENIDO DEL DOCUMENTO: (no disponible)")

        # ── Campos extraídos ────────────────────────────────────────────────
        fields = doc_ctx.get("fields", []) or []
        if fields:
            parts.append("\nCAMPOS EXTRAÍDOS:")
            for f in fields[:60]:
                if not isinstance(f, dict):
                    continue
                name = f.get("field") or f.get("label") or ""
                val = f.get("llm_filled_value") or f.get("value") or ""
                page = f.get("page_number") or f.get("page") or ""
                conf = f.get("llm_confidence") or f.get("confidence") or ""
                if name and val:
                    parts.append(f"  • {name}: {val}  (pág {page}, conf {conf})")

        self._doc_context = "\n".join(parts)
        self._doc_hash = str(id(doc_ctx))
        self.history = []

    def chat(self, user_message: str) -> str:
        """
        Envía un mensaje y retorna la respuesta como str.
        NUNCA retorna un dict — siempre es texto legible.
        """
        if not self._doc_context:
            return "Primero debes procesar un PDF antes de hacer preguntas sobre él."

        system = f"{CHATBOT_SYSTEM}\n\n---INICIO DOCUMENTO---\n{self._doc_context}\n---FIN DOCUMENTO---"

        self.history.append({"role": "user", "content": user_message})

        # Construir los últimos N turnos como prompt de usuario
        conversation_turns = self.history[-12:]  # máx 6 turnos (12 mensajes)
        conversation_text = "\n".join(
            f"{'Usuario' if m['role'] == 'user' else 'Asistente'}: {m['content']}"
            for m in conversation_turns[:-1]  # todo menos el último (ya está como user)
        )
        if conversation_text:
            full_user_prompt = f"Historial previo:\n{conversation_text}\n\nPregunta actual: {user_message}"
        else:
            full_user_prompt = user_message

        try:
            raw_response = self.client.generate(
                system=system,
                user=full_user_prompt,
                temperature=0.3,
            )
            # _safe_str garantiza que siempre sea str, nunca dict
            response = _safe_str(raw_response)
        except Exception as e:
            response = f"Error al consultar el modelo: {e}"

        self.history.append({"role": "assistant", "content": response})
        return response

    def clear(self) -> None:
        """Limpia el historial de conversación."""
        self.history = []

# # src/llm/chatbot.py
# from __future__ import annotations
# from typing import Any
# from src.llm.client import build_llm_client


# CHATBOT_SYSTEM = """
# Eres un asistente experto en análisis de documentos. El usuario ha procesado un PDF.
# Responde SIEMPRE basándote en el contenido del documento.
# Cuando cites información, menciona la página de origen si está disponible.
# Si la información no está en el documento, dilo claramente.
# Sé conciso y preciso.
# """


# class PDFChatbot:
#     def __init__(self):
#         self.client = build_llm_client()
#         self.history: list[dict] = []
#         self._doc_context: str = ""

#     def set_document(self, doc_ctx: dict[str, Any]) -> None:
#         """Inicializa el chatbot con el contexto del documento."""
#         parts = []

#         file_name = doc_ctx.get("file_name", "Documento")
#         pages_total = doc_ctx.get("pages_total", "?")
#         parts.append(f"DOCUMENTO: {file_name} ({pages_total} páginas)\n")

#         # Texto completo
#         full_text = doc_ctx.get("full_text", "")
#         if not full_text:
#             pages = doc_ctx.get("pages", []) or []
#             texts = []
#             for p in pages:
#                 pn = p.get("page_number", "?")
#                 for b in p.get("blocks", []) or []:
#                     t = b.get("text", "").strip()
#                     if t:
#                         texts.append(f"[Pág {pn}] {t}")
#             full_text = "\n".join(texts)

#         parts.append(f"CONTENIDO:\n{full_text[:12000]}")

#         # Campos extraídos
#         fields = doc_ctx.get("fields", []) or []
#         if fields:
#             parts.append("\nCAMPOS EXTRAÍDOS:")
#             for f in fields[:40]:
#                 name = f.get("field") or f.get("label", "")
#                 val = f.get("llm_filled_value") or f.get("value", "")
#                 page = f.get("page_number") or f.get("page", "")
#                 parts.append(f"  - {name}: {val} (pág {page})")

#         self._doc_context = "\n".join(parts)
#         self.history = []

#     def chat(self, user_message: str) -> str:
#         """Envía un mensaje y retorna la respuesta del asistente."""
#         system = f"{CHATBOT_SYSTEM}\n\n---DOCUMENTO---\n{self._doc_context}\n---FIN DOCUMENTO---"

#         self.history.append({"role": "user", "content": user_message})

#         try:
#             response = self.client.generate(
#                 system=system,
#                 user="\n".join(
#                     f"{m['role'].upper()}: {m['content']}"
#                     for m in self.history[-10:]  # ultimos 10 turnos
#                 ),
#                 temperature=0.3,
#             )
#         except Exception as e:
#             response = f"Error al consultar el LLM: {e}"

#         self.history.append({"role": "assistant", "content": response})
#         return response

#     def clear(self) -> None:
#         self.history = []
