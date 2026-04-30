# # src/llm/enricher.py
# from __future__ import annotations

# import json
# import re
# import unicodedata
# from copy import deepcopy
# from dataclasses import dataclass, asdict
# from typing import Any

# from src.llm.client import build_llm_client, BaseLLMClient
# from src.llm.prompts import SYSTEM_PROMPT, build_enrichment_prompt


# @dataclass
# class LLMEnrichmentResult:
#     mode: str
#     raw_response: str
#     parsed: dict[str, Any]
#     applied_changes: list[dict[str, Any]]
#     warnings: list[str]


# def _has_reliable_value(field: dict[str, Any]) -> bool:
#     val = field.get("value")
#     if val in (None, "", [], {}):
#         return False
#     try:
#         return float(field.get("confidence", 1.0) or 1.0) >= 0.4
#     except Exception:
#         return True


# def _normalize_name(value: Any) -> str:
#     """Normaliza un nombre de campo: minúsculas, sin acentos, sin caracteres especiales."""
#     text = _safe_text(value).strip().lower()
#     # Quitar acentos
#     text = unicodedata.normalize("NFD", text)
#     text = "".join(c for c in text if unicodedata.category(c) != "Mn")
#     return re.sub(r"[^a-z0-9]+", "", text)


# def _normalize_suggestion(suggestion: dict[str, Any]) -> dict[str, Any] | None:
#     if not isinstance(suggestion, dict):
#         return None

#     target_field = (
#         suggestion.get("field")
#         or suggestion.get("target_field")
#         or suggestion.get("name")
#         or suggestion.get("field_name")
#     )
#     suggested_value = suggestion.get("suggested_value")
#     if suggested_value is None:
#         suggested_value = suggestion.get("value")

#     if not target_field:
#         return None

#     try:
#         confidence = float(suggestion.get("confidence", 0.0) or 0.0)
#     except Exception:
#         confidence = 0.0

#     return {
#         "field": target_field,
#         "suggested_value": suggested_value,
#         "confidence": confidence,
#         "status": suggestion.get(
#             "status", "filled" if suggested_value not in (None, "", []) else "rejected"
#         ),
#         "reason": suggestion.get("reason", ""),
#         "evidence": suggestion.get("evidence", []),
#         "page_number": suggestion.get("page_number"),
#         "block_id": suggestion.get("block_id"),
#     }


# def _extract_json(text: Any) -> dict[str, Any]:
#     """
#     Intenta parsear JSON desde el texto.
#     Maneja: JSON puro, markdown con ```json```, JSON embebido en texto.
#     NUNCA recibe un dict (el cliente siempre retorna str ahora).
#     """
#     if isinstance(text, dict):
#         # Seguridad: si por alguna razón llega un dict, usarlo directamente
#         return text

#     text = (text or "").strip()
#     if not text:
#         return {}

#     # 1) JSON puro
#     try:
#         return json.loads(text)
#     except Exception:
#         pass

#     # 2) Bloque ```json ... ```
#     fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
#     for candidate in fenced:
#         try:
#             return json.loads(candidate.strip())
#         except Exception:
#             pass

#     # 3) Primer objeto JSON completo en el texto
#     start = text.find("{")
#     end = text.rfind("}")
#     if 0 <= start < end:
#         try:
#             return json.loads(text[start : end + 1])
#         except Exception:
#             pass

#     # 4) Fallback: intentar construir fill_suggestions desde texto markdown
#     #    El modelo devolvió markdown con sugerencias → extraer manualmente
#     suggestions = _parse_markdown_suggestions(text)
#     if suggestions:
#         return {
#             "document_summary": "Parsed from markdown response",
#             "fill_suggestions": suggestions,
#             "llm_raw_response": text,
#         }

#     return {}


# def _parse_markdown_suggestions(text: str) -> list[dict[str, Any]]:
#     """
#     Extrae sugerencias de fill desde una respuesta en markdown cuando el modelo
#     no siguió el formato JSON.
#     Busca patrones como:
#       - **Field Name:** `field_key`
#       - **Value Suggestion:** "valor"
#       - `field_key`: "valor"
#     """
#     suggestions = []

#     # Patrón: **Field/Campo:** `nombre` seguido de valor
#     # También captura líneas tipo `field`: "value"
#     patterns = [
#         # `field_name`: "value" o `field_name`: value
#         re.compile(r"`([^`]+)`\s*:\s*[\"']([^\"'\n]+)[\"']"),
#         # **Field Name:** `field_key` + línea de valor
#         re.compile(r"\*\*([^*]+)\*\*\s*:\s*[\"']([^\"'\n]+)[\"']"),
#         # - field: value
#         re.compile(r"[-*]\s+`?([a-z_][a-z0-9_]*)`?\s*:\s*[\"']([^\"'\n]+)[\"']", re.IGNORECASE),
#     ]

#     seen = set()
#     for pat in patterns:
#         for m in pat.finditer(text):
#             field = m.group(1).strip()
#             value = m.group(2).strip()
#             key = f"{field}|{value}"
#             if key not in seen and field and value:
#                 seen.add(key)
#                 suggestions.append(
#                     {
#                         "field": field,
#                         "suggested_value": value,
#                         "confidence": 0.5,
#                         "status": "filled",
#                         "reason": "Extracted from markdown response",
#                         "evidence": [],
#                     }
#                 )

#     return suggestions


# def _safe_text(value: Any) -> str:
#     if value is None:
#         return ""
#     if isinstance(value, (dict, list)):
#         return json.dumps(value, ensure_ascii=False)
#     return str(value)


# class LLMEnricher:
#     def __init__(self, client: BaseLLMClient | None = None):
#         self.client = client or build_llm_client()

#     def enrich_document(
#         self,
#         doc_ctx: dict[str, Any],
#         mode: str = "auto_fill_missing",
#         confidence_threshold: float = 0.3,
#     ) -> dict[str, Any]:
#         base = deepcopy(doc_ctx or {})
#         prompt = build_enrichment_prompt(base, mode=mode)

#         # generate() SIEMPRE retorna str ahora
#         raw: str = self.client.generate(system=SYSTEM_PROMPT, user=prompt, temperature=0.0)

#         # Debug
#         print("\n===== LLM RAW RESPONSE =====\n")
#         print(raw[:2000] if isinstance(raw, str) else repr(raw))
#         print("\n============================\n")

#         with open("llm_response.txt", "w", encoding="utf-8") as f:
#             f.write(str(raw))

#         parsed = _extract_json(raw)

#         applied_changes: list[dict[str, Any]] = []

#         if isinstance(parsed, dict):
#             suggestions = (
#                 parsed.get("fill_suggestions")
#                 or parsed.get("llm_applied_changes")
#                 or []
#             )

#             if isinstance(suggestions, list):
#                 fields = base.get("fields", [])

#                 # Construir set de nombres existentes para detectar campos nuevos
#                 existing_field_names = {
#                     _normalize_name(
#                         f.get("field") or f.get("label") or f.get("name") or ""
#                     )
#                     for f in fields
#                 }

#                 for suggestion in suggestions:
#                     normalized = _normalize_suggestion(suggestion)
#                     if not normalized:
#                         continue

#                     target_name = _normalize_name(normalized["field"])
#                     suggested_value = normalized["suggested_value"]
#                     confidence = normalized["confidence"]

#                     if suggested_value in (None, "", []):
#                         continue
#                     if confidence < confidence_threshold:
#                         continue

#                     matched = False
#                     for field in fields:
#                         field_name = _normalize_name(
#                             field.get("field")
#                             or field.get("label")
#                             or field.get("name")
#                             or field.get("semantic_type")
#                             or ""
#                         )

#                         if field_name != target_name:
#                             continue

#                         is_correction = normalized.get("status") == "corrected" and confidence >= 0.7

#                         if _has_reliable_value(field) and not is_correction:
#                             matched = True  # existe pero no se sobrescribe
#                             continue

#                         field["llm_filled_value"] = suggested_value
#                         field["llm_confidence"] = confidence
#                         field["llm_reason"] = normalized["reason"]
#                         field["llm_evidence"] = normalized["evidence"]
#                         field["llm_status"] = normalized["status"]

#                         applied_changes.append(
#                             {
#                                 "field": normalized["field"],
#                                 "value": suggested_value,
#                                 "confidence": confidence,
#                                 "status": normalized["status"],
#                                 "reason": normalized["reason"],
#                             }
#                         )
#                         matched = True

#                     # Si no hay match y el LLM sugiere campo nuevo
#                     if not matched and target_name not in existing_field_names:
#                         new_field = {
#                             "field": normalized["field"],
#                             "value": None,
#                             "llm_filled_value": suggested_value,
#                             "llm_confidence": confidence,
#                             "llm_reason": normalized["reason"],
#                             "llm_status": "new",
#                             "source": "llm",
#                         }
#                         fields.append(new_field)
#                         existing_field_names.add(target_name)
#                         applied_changes.append(
#                             {
#                                 "field": normalized["field"],
#                                 "value": suggested_value,
#                                 "confidence": confidence,
#                                 "status": "new",
#                                 "reason": normalized["reason"],
#                             }
#                         )

#                 base["fields"] = fields

#         result = LLMEnrichmentResult(
#             mode=mode,
#             raw_response=raw if isinstance(raw, str) else json.dumps(raw),
#             parsed=parsed if isinstance(parsed, dict) else {"raw": str(raw)},
#             applied_changes=applied_changes,
#             warnings=[] if parsed else ["LLM response could not be parsed as JSON"],
#         )

#         base["llm"] = asdict(result)
#         base["llm_applied_changes"] = applied_changes
#         base["llm_raw_response"] = raw if isinstance(raw, str) else str(raw)
#         base["llm_parsed"] = parsed
#         return base

# src/llm/enricher.py
from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass, asdict
from typing import Any

from src.llm.client import build_llm_client, BaseLLMClient
from src.llm.prompts import SYSTEM_PROMPT, build_enrichment_prompt


_JSON_BLOCK_RE = re.compile(r"\{(?:.|\n)*\}", re.MULTILINE)


@dataclass
class LLMEnrichmentResult:
    mode: str
    raw_response: str
    parsed: dict[str, Any]
    applied_changes: list[dict[str, Any]]
    warnings: list[str]


def _has_reliable_value(field: dict[str, Any]) -> bool:
    val = field.get("value")
    if val in (None, "", [], {}):
        return False
    try:
        return float(field.get("confidence", 1.0) or 1.0) >= 0.4
    except Exception:
        return True


def _normalize_name(value: Any) -> str:
    text = _safe_text(value).strip().lower()
    # Normalizar acentos
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", text)


def _normalize_suggestion(suggestion: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(suggestion, dict):
        return None

    target_field = suggestion.get("field") or suggestion.get("target_field") or suggestion.get("name")
    suggested_value = suggestion.get("suggested_value")
    if suggested_value is None:
        suggested_value = suggestion.get("value")

    if not target_field:
        return None

    try:
        confidence = float(suggestion.get("confidence", 0.0) or 0.0)
    except Exception:
        confidence = 0.0

    return {
        "field": target_field,
        "suggested_value": suggested_value,
        "confidence": confidence,
        "status": suggestion.get("status", "filled" if suggested_value not in (None, "", []) else "rejected"),
        "reason": suggestion.get("reason", ""),
        "evidence": suggestion.get("evidence", []),
        "page_number": suggestion.get("page_number"),
        "block_id": suggestion.get("block_id"),
    }


def _extract_json(text: Any) -> dict[str, Any]:
    if isinstance(text, dict):
        return text  # ya está parseado

    text = (text or "").strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except Exception:
        pass

    fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    for candidate in fenced:
        try:
            return json.loads(candidate.strip())
        except Exception:
            pass

    start = text.find("{")
    end = text.rfind("}")

    if 0 <= start < end:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass

    return {}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _get_text_signature(item: dict[str, Any]) -> str:
    parts = []
    for key in ("field", "label", "type", "text", "value", "context", "caption", "title", "name"):
        if key in item:
            parts.append(_safe_text(item.get(key)))
    return " | ".join(p for p in parts if p).strip()


class LLMEnricher:
    def __init__(self, client: BaseLLMClient | None = None):
        self.client = client or build_llm_client()

    def enrich_document(
        self,
        doc_ctx: dict[str, Any],
        mode: str = "auto_fill_missing",
        confidence_threshold: float = 0.3,
    ) -> dict[str, Any]:
        base = deepcopy(doc_ctx or {})
        prompt = build_enrichment_prompt(base, mode=mode)
        raw = self.client.generate(system=SYSTEM_PROMPT, user=prompt, temperature=0.0)
        # --- DEBUG: imprimir en terminal ---
        print("\n===== LLM RAW RESPONSE =====\n")
        print(raw)
        print("\n============================\n")

        # --- DEBUG: guardar en archivo ---
        with open("llm_response.txt", "w", encoding="utf-8") as f:
            f.write(str(raw))

        parsed = _extract_json(raw)

        applied_changes: list[dict[str, Any]] = []

        if isinstance(parsed, dict):
            # suggestions = parsed.get("fill_suggestions", [])
            suggestions = parsed.get("fill_suggestions") or parsed.get("llm_applied_changes") or []
            if isinstance(suggestions, list):
                # Apply only low-risk fills
                fields = base.get("fields", [])
                for suggestion in suggestions:
                    normalized = _normalize_suggestion(suggestion)
                    if not normalized:
                        continue

                    target_name = _normalize_name(normalized["field"])
                    suggested_value = normalized["suggested_value"]
                    confidence = normalized["confidence"]

                    if suggested_value in (None, "", []):
                        continue
                    if confidence < confidence_threshold:
                        continue

                    for field in fields:
                        field_name = _normalize_name(
                            field.get("field") or field.get("label") or field.get("name") or field.get("semantic_type")
                        )

                        if field_name != target_name:
                            continue

                        is_new_field = normalized.get("status") == "new"
                        is_correction = normalized.get("status") == "corrected" and confidence >= 0.7

                        if _has_reliable_value(field) and not is_correction:
                            continue

                        field["llm_filled_value"] = suggested_value
                        field["llm_confidence"] = confidence
                        field["llm_reason"] = normalized["reason"]
                        field["llm_evidence"] = normalized["evidence"]
                        field["llm_status"] = normalized["status"]

                        applied_changes.append(
                            {
                                "field": normalized["field"],
                                "value": suggested_value,
                                "confidence": confidence,
                                "status": normalized["status"],
                                "reason": normalized["reason"],
                            }
                        )

                    existing_field_names = {
                        _normalize_name(f.get("field") or f.get("label") or f.get("name") or "")
                        for f in fields
                    }

                    if normalized.get("status") == "new" and target_name not in existing_field_names:
                        new_field = {
                            "field": normalized["field"],
                            "value": None,
                            "llm_filled_value": suggested_value,
                            "llm_confidence": confidence,
                            "llm_reason": normalized["reason"],
                            "llm_status": "new",
                            "source": "llm",
                        }
                        fields.append(new_field)
                        applied_changes.append({
                            "field": normalized["field"],
                            "value": suggested_value,
                            "confidence": confidence,
                            "status": "new",
                            "reason": normalized["reason"],
                        })

                base["fields"] = fields

        result = LLMEnrichmentResult(
            mode=mode,
            raw_response=raw,
            parsed=parsed if isinstance(parsed, dict) else {"raw": raw},
            applied_changes=applied_changes,
            warnings=[] if parsed else ["LLM response could not be parsed as JSON"],
        )

        base["llm"] = asdict(result)
        base["llm_applied_changes"] = applied_changes or parsed.get("llm_applied_changes", [])
        # base["llm_applied_changes"] = applied_changes
        base["llm_raw_response"] = raw
        base["llm_parsed"] = parsed
        return base
