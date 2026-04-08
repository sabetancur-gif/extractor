# src/llm/prompts.py
from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """
You are a document-enrichment assistant.
Your job is to improve PDF extraction by inferring missing values only when evidence exists in the provided context.
Never hallucinate. If the value is not supported, return null.
Return STRICT JSON only. No markdown. No code fences.
"""


def build_enrichment_prompt(doc_ctx: dict[str, Any], mode: str = "auto_fill_missing") -> str:
    payload = {
        "mode": mode,
        "file_name": doc_ctx.get("file_name"),
        "doc_id": doc_ctx.get("doc_id"),
        "pages_total": doc_ctx.get("pages_total"),
        "ocr_average_confidence": doc_ctx.get("ocr_average_confidence"),
        "fields": doc_ctx.get("fields", [])[:80],
        "classified_blocks": doc_ctx.get("classified_blocks", [])[:120],
        "toc": doc_ctx.get("toc", []),
        "notes": [
            "Fill missing values only when the evidence is strong.",
            "Prefer low-risk corrections.",
            "Preserve original extracted data.",
            "Return confidence in [0, 1].",
        ],
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)