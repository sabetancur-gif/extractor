"""
src/llm/prompts.py
------------------
Prompts para el LLM Enricher y el Chatbot.
Se usa una representación compacta (TOON: Text-Only Object Notation)
para reducir el tamaño del payload y mantener solo la información relevante.
"""
from __future__ import annotations

import json
from typing import Any


# ── System prompt del enriquecedor ───────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a document-enrichment assistant for a PDF extraction pipeline.

Given the document text and extracted fields, you MUST:
1. Analyze the full document text to understand its content.
2. Identify ALL detectable fields: names, dates, amounts, IDs, emails, phones, addresses, etc.
3. Fill or correct missing/low-confidence fields using evidence from the text.
4. Suggest new fields not previously detected.
5. Return STRICT JSON ONLY — no markdown, no code fences, no preamble.

The JSON MUST have EXACTLY this structure:
{
  "document_summary": "<1-3 sentence summary in the document's language>",
  "document_type": "<invoice | contract | letter | report | form | id_card | other>",
  "fill_suggestions": [
    {
      "field": "<field_name>",
      "suggested_value": "<value or null>",
      "confidence": <0.0 to 1.0>,
      "status": "<filled | corrected | new | rejected>",
      "reason": "<brief explanation>",
      "evidence": ["<text excerpt supporting this>"],
      "page_number": <int or null>
    }
  ]
}

Rules:
- status "filled"    = field was missing, you found a value.
- status "corrected" = field had a low-confidence value, you improved it.
- status "new"       = field was not in the original extraction at all.
- status "rejected"  = you could NOT find a reliable value.
- confidence must be between 0.0 and 1.0 (float, not string).
- Always respond in the SAME language as the document.
- NEVER invent data not supported by the document text.
"""


# ── Helpers de construcción del payload ─────────────────────────────────────

def _is_missing(value: Any) -> bool:
    return value in (None, "", [], {})


def _is_low_confidence(field: dict[str, Any], threshold: float = 0.45) -> bool:
    try:
        return float(field.get("confidence", 1.0) or 1.0) < threshold
    except Exception:
        return True


def _toon_field(f: dict[str, Any]) -> str:
    """Serializa un campo en formato TOON compacto: 'name|value|conf|page'."""
    name  = f.get("field") or f.get("label") or f.get("name") or ""
    value = f.get("value") or ""
    conf  = f.get("confidence") or ""
    page  = f.get("page_number") or f.get("page") or ""
    return f"{name}|{value}|{conf}|{page}"


def _toon_block(b: dict[str, Any]) -> str:
    """Serializa un bloque en formato TOON compacto: 'type|page|text[:80]'."""
    btype = b.get("semantic_type") or b.get("block_type") or "other"
    page  = b.get("page_number")  or b.get("page") or ""
    text  = (b.get("text") or "")[:80].replace("\n", " ")
    return f"{btype}|{page}|{text}"


def build_enrichment_prompt(doc_ctx: dict[str, Any], mode: str = "auto_fill_missing") -> str:
    """
    Construye el prompt de enriquecimiento en formato TOON (compacto).
    Reduce el payload significativamente vs JSON completo, manteniendo la información clave.

    Args:
        doc_ctx: Contexto del documento (pages, fields, classified_blocks, etc.)
        mode:    Modo de enriquecimiento.

    Returns:
        String del prompt listo para enviar al LLM.
    """
    # Texto completo del documento (truncado)
    full_text = doc_ctx.get("full_text", "")
    if not full_text:
        pages = doc_ctx.get("pages", []) or []
        parts = []
        for p in pages:
            for b in p.get("blocks", []) or []:
                t = (b.get("text") or "").strip()
                if t:
                    parts.append(f"[p{p.get('page_number','')}] {t}")
        full_text = "\n".join(parts)

    # Campos: todos (para dar contexto) + los faltantes/bajos (para priorizar)
    all_fields      = []
    missing_fields  = []

    for f in (doc_ctx.get("fields", []) or [])[:100]:
        if not isinstance(f, dict):
            continue
        toon = _toon_field(f)
        all_fields.append(toon)
        if _is_missing(f.get("value")) or _is_low_confidence(f):
            missing_fields.append(toon)

    # Bloques clasificados (solo los más relevantes, excluir párrafos genéricos)
    relevant_types = {"title", "date", "amount", "email", "phone", "signature",
                      "table", "address", "name", "identifier", "subtitle", "header"}
    top_blocks = [
        _toon_block(b)
        for b in (doc_ctx.get("classified_blocks", []) or [])
        if b.get("semantic_type") in relevant_types
    ][:60]

    # Construir el payload TOON
    lines = [
        f"MODE: {mode}",
        f"FILE: {doc_ctx.get('file_name', 'unknown')}",
        f"PAGES: {doc_ctx.get('pages_total', '?')}",
        "",
        "# DOCUMENT TEXT (truncated to 6000 chars):",
        full_text[:6000],
        "",
        "# ALL EXTRACTED FIELDS (name|value|confidence|page):",
        *all_fields[:80],
        "",
        "# MISSING OR LOW-CONFIDENCE FIELDS (prioritize these):",
        *missing_fields[:40],
        "",
        "# RELEVANT CLASSIFIED BLOCKS (type|page|text):",
        *top_blocks,
        "",
        "# INSTRUCTIONS:",
        f"- Mode: {mode}",
        "- Fill ALL missing_fields if you can find evidence in the document text.",
        "- Also suggest new fields you detect in the text.",
        "- Return STRICT JSON ONLY as specified in the system prompt.",
    ]

    return "\n".join(lines)
