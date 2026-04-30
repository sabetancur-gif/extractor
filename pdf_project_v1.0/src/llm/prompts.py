# src/llm/prompts.py
from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """
You are a document-enrichment assistant for a PDF extraction system.

Given extracted document data, you must:
1. Analyze the full_document_text to understand the document content
2. Identify ALL extractable fields (names, dates, amounts, IDs, addresses, etc.)
3. Fill missing fields when you can infer them from the text
4. Correct low-confidence extractions
5. Suggest new fields not in the original extraction

IMPORTANT:
- Use the SAME field names as in all_extracted_fields when filling existing fields
- You CAN suggest new fields not previously detected
- Set confidence between 0 and 1 based on how certain you are
- Return STRICT JSON only. No markdown. No code fences.

The JSON MUST have this structure:
{
  "document_summary": string,
  "document_type": string,
  "fill_suggestions": [
    {
      "field": string,
      "suggested_value": string or null,
      "confidence": float,
      "status": "filled" | "corrected" | "new" | "rejected",
      "reason": string,
      "evidence": [string],
      "page_number": number | null,
      "block_id": string | null
    }
  ]
}
"""


def _is_missing_value(value: Any) -> bool:
    return value in (None, "", [], {})


def _is_low_confidence(field: dict[str, Any], threshold: float = 0.4) -> bool:
    try:
        return float(field.get("confidence", 1.0) or 1.0) < threshold
    except Exception:
        return True


def _candidate_fields(doc_ctx: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for field in doc_ctx.get("fields", []) or []:
        if not isinstance(field, dict):
            continue
        value = field.get("value")
        if _is_missing_value(value) or _is_low_confidence(field):
            candidates.append({
                "field": field.get("field") or field.get("label") or field.get("name"),
                "value": value,
                "confidence": field.get("confidence"),
                "page_number": field.get("page_number") or field.get("page"),
                "block_id": field.get("block_id"),
                "bbox": field.get("bbox"),
                "text": field.get("text"),
                "source": field.get("source"),
            })
    return candidates


def build_enrichment_prompt(doc_ctx: dict[str, Any], mode: str = "auto_fill_missing") -> str:
    # Incluir texto completo (truncado) para que el LLM pueda inferir valores
    full_text = doc_ctx.get("full_text", "")
    if not full_text:
        # Reconstruir desde páginas si no está precalculado
        pages = doc_ctx.get("pages", []) or []
        texts = []
        for p in pages:
            for b in p.get("blocks", []) or []:
                t = b.get("text", "")
                if t:
                    texts.append(t)
        full_text = "\n".join(texts)

    # Todos los campos (no solo los vacíos) para que el LLM entienda la estructura
    all_fields = []
    for f in (doc_ctx.get("fields", []) or [])[:120]:
        if isinstance(f, dict):
            all_fields.append({
                "field": f.get("field") or f.get("label") or f.get("name"),
                "value": f.get("value"),
                "confidence": f.get("confidence"),
                "page": f.get("page_number") or f.get("page"),
            })

    payload = {
        "mode": mode,
        "file_name": doc_ctx.get("file_name"),
        "pages_total": doc_ctx.get("pages_total"),
        "full_document_text": full_text[:8000],   # ← NUEVO: texto completo
        "all_extracted_fields": all_fields,        # ← NUEVO: todos los campos
        "missing_or_low_confidence_fields": _candidate_fields(doc_ctx)[:80],
        "classified_blocks": doc_ctx.get("classified_blocks", [])[:60],
        "notes": [
            "Analyze the full_document_text to understand the document.",
            "Fill missing fields AND suggest corrected values for low-confidence ones.",
            "Use field names from all_extracted_fields when possible.",
            "If the document has new fields not in all_extracted_fields, suggest them.",
            "Return fill_suggestions for EVERY field you can infer.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
