"""
src/llm/enricher.py
-------------------
Enriquecedor de documentos con LLM (Ollama).
Recibe el contexto del documento, construye el prompt TOON,
llama al modelo y parsea la respuesta JSON de forma robusta.

Correcciones clave vs. versión anterior:
- El cliente SIEMPRE retorna str → se parsea aquí.
- _extract_json() maneja: JSON puro, markdown fenced, JSON embebido.
- Se normaliza la respuesta del modelo para evitar "cambios: 0" falso-positivos.
- Se permite flexibilidad en los nombres de campo de la respuesta.
"""
from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from typing import Any

from src.llm.client import BaseLLMClient, build_llm_client
from src.llm.prompts import SYSTEM_PROMPT, build_enrichment_prompt


# ── Parseo de JSON robusto ────────────────────────────────────────────────────

def _extract_json(raw: Any) -> dict[str, Any]:
    """
    Intenta extraer un objeto JSON de la respuesta del LLM.
    Maneja: JSON puro, markdown ```json...```, JSON embebido en texto, texto libre.
    """
    if isinstance(raw, dict):
        return raw

    text = (raw or "").strip()
    if not text:
        return {}

    # 1. JSON puro
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Bloque markdown ```json ... ```
    for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE):
        try:
            return json.loads(m.group(1).strip())
        except Exception:
            continue

    # 3. Primer objeto JSON completo en el texto
    start = text.find("{")
    end   = text.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass

    # 4. Fallback: intentar extraer sugerencias de texto markdown
    suggestions = _parse_markdown_suggestions(text)
    if suggestions:
        return {
            "document_summary": "Respuesta en formato texto (no JSON).",
            "fill_suggestions": suggestions,
        }

    return {}


def _parse_markdown_suggestions(text: str) -> list[dict[str, Any]]:
    """
    Extrae sugerencias de una respuesta en markdown cuando el modelo no siguió el formato JSON.
    Busca patrones como: `field`: "value" o **Field:** value.
    """
    suggestions = []
    seen: set[str] = set()

    patterns = [
        re.compile(r"`([^`]+)`\s*:\s*[\"']([^\"'\n]+)[\"']"),
        re.compile(r"\*\*([^*]+)\*\*\s*:\s*[\"']([^\"'\n]+)[\"']"),
        re.compile(r"[-*]\s+`?([a-z_][a-z0-9_]*)`?\s*:\s*[\"']([^\"'\n]+)[\"']", re.I),
    ]

    for pat in patterns:
        for m in pat.finditer(text):
            f_name = m.group(1).strip()
            f_val  = m.group(2).strip()
            key    = f"{f_name}|{f_val}"
            if key not in seen and f_name and f_val:
                seen.add(key)
                suggestions.append({
                    "field":           f_name,
                    "suggested_value": f_val,
                    "confidence":      0.5,
                    "status":          "filled",
                    "reason":          "Extracted from markdown response",
                    "evidence":        [],
                    "page_number":     None,
                })

    return suggestions


# ── Normalización de sugerencias ─────────────────────────────────────────────

def _normalize_suggestion(s: Any) -> dict[str, Any] | None:
    """
    Normaliza una sugerencia del LLM a formato estándar.
    Acepta múltiples nombres de keys para mayor flexibilidad.
    """
    if not isinstance(s, dict):
        return None

    field = (
        s.get("field") or s.get("target_field") or
        s.get("name")  or s.get("field_name")
    )
    value = s.get("suggested_value")
    if value is None:
        value = s.get("value") or s.get("filled_value")

    if not field:
        return None

    try:
        confidence = float(s.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0

    status = s.get("status") or ("filled" if value not in (None, "", []) else "rejected")

    return {
        "field":           str(field),
        "value":           value,
        "confidence":      round(min(max(confidence, 0.0), 1.0), 3),
        "status":          status,
        "reason":          str(s.get("reason") or ""),
        "evidence":        s.get("evidence") or [],
        "page_number":     s.get("page_number"),
        "block_id":        s.get("block_id"),
    }


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


# ── LLMEnricher ──────────────────────────────────────────────────────────────

class LLMEnricher:
    """Enriquece el contexto de un documento usando un LLM."""

    def __init__(self, client: BaseLLMClient | None = None):
        self.client = client or build_llm_client()

    def enrich_document(
        self,
        doc_ctx: dict[str, Any],
        mode: str = "auto_fill_missing",
        confidence_threshold: float = 0.3,
    ) -> dict[str, Any]:
        """
        Enriquece el documento llamando al LLM.

        Args:
            doc_ctx:               Contexto del documento.
            mode:                  Modo de enriquecimiento.
            confidence_threshold:  Confianza mínima para aplicar una sugerencia.

        Returns:
            Copia enriquecida del doc_ctx con llm_applied_changes, llm_raw_response.
        """
        enriched = deepcopy(doc_ctx or {})
        prompt   = build_enrichment_prompt(enriched, mode=mode)

        # Llamar al LLM (siempre retorna str)
        raw_str: str = self.client.generate(system=SYSTEM_PROMPT, user=prompt, temperature=0.0)

        # Log para debug
        print("\n===== LLM RAW RESPONSE =====")
        print(raw_str[:2000])
        print("============================\n")

        # Parsear JSON
        parsed = _extract_json(raw_str)
        warnings: list[str] = parsed.get("warnings", [])

        # Extraer sugerencias normalizando keys
        raw_suggestions = (
            parsed.get("fill_suggestions")
            or parsed.get("suggestions")
            or parsed.get("fields")
            or []
        )

        applied_changes: list[dict[str, Any]] = []
        fields_map: dict[str, dict] = {
            _safe_text(f.get("field") or "").lower(): f
            for f in (enriched.get("fields") or [])
            if isinstance(f, dict)
        }

        for raw_s in raw_suggestions:
            norm = _normalize_suggestion(raw_s)
            if not norm:
                continue

            # Solo aplicar si la confianza supera el umbral o el campo estaba vacío
            field_key    = norm["field"].lower()
            existing     = fields_map.get(field_key)
            existing_val = existing.get("value") if existing else None
            is_missing   = existing_val in (None, "", [], {})

            if norm["confidence"] >= confidence_threshold or is_missing:
                change_entry = {
                    "field":      norm["field"],
                    "value":      norm["value"],
                    "confidence": norm["confidence"],
                    "status":     norm["status"],
                    "reason":     norm["reason"],
                    "page_number":norm["page_number"],
                }
                applied_changes.append(change_entry)

                # Actualizar el campo en el contexto enriquecido
                if existing:
                    existing["llm_filled_value"]  = norm["value"]
                    existing["llm_confidence"]     = norm["confidence"]
                    existing["llm_status"]         = norm["status"]
                else:
                    # Campo nuevo detectado por el LLM
                    enriched.setdefault("fields", []).append({
                        "field":      norm["field"],
                        "value":      norm["value"],
                        "confidence": norm["confidence"],
                        "source":     "llm",
                        "status":     "new",
                    })

        enriched.update({
            "llm_applied_changes": applied_changes,
            "llm_raw_response":    raw_str[:8000],
            "llm_document_summary": parsed.get("document_summary", ""),
            "llm_document_type":    parsed.get("document_type", ""),
            "llm_warnings":         warnings,
            "llm_mode":             mode,
        })

        return enriched
