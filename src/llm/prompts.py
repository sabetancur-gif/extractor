# src/llm/prompts.py
from __future__ import annotations

import json 
from typing import Any


SYSTEM_PROMPT = """
You are a document-enrichment assistant.

Your job is to fill missing or low-confidence extraction values only when strong evidence exists in the provided context.
Never hallucinate. If the value is not supported, return null.
Do not overwrite reliable extracted values.
Return STRICT JSON only. No markdown. No code fences.

The JSON MUST have this structure:
{
  "document_summary": string,
  "fill_suggestions": [
    {
      "field": string,
      "suggested_value": string or null,
      "confidence": float between 0 and 1,
      "status": string,
      "reason": string,
      "evidence": [string],
      "page_number": number | null,
      "block_id": string | null
    }
  ],
  "llm_raw_response": string
}

You must return ONLY valid JSON. 
Do not include explanations, markdown, code fences, or text outside the JSON object.
If you cannot infer values, return an empty array for llm_applied_changes.
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
    payload = {
        "mode": mode,
        "file_name": doc_ctx.get("file_name"),
        "doc_id": doc_ctx.get("doc_id"),
        "pages_total": doc_ctx.get("pages_total"),
        "ocr_average_confidence": doc_ctx.get("ocr_average_confidence"),
        "missing_or_low_confidence_fields": _candidate_fields(doc_ctx)[:80],
        "classified_blocks": doc_ctx.get("classified_blocks", [])[:120],
        "toc": doc_ctx.get("toc", []),
        "notes": [
            "Fill only missing or low-confidence fields.",
            "Do not overwrite reliable values.",
            "Use evidence from nearby blocks only when clear.",
            "Return an empty fill_suggestions list if no safe enrichment is possible.",
        ],
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)
