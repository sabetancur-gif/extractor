# src/search/universal_search.py
from __future__ import annotations

import difflib
import json
from typing import Any


def _norm(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (dict, list)):
        return json.dumps(x, ensure_ascii=False)
    return str(x)


def _score(query: str, text: str) -> float:
    q = (query or "").strip().lower()
    t = (text or "").strip().lower()
    if not q:
        return 1.0
    if q in t:
        return 1.0
    return difflib.SequenceMatcher(None, q, t).ratio()


def _item_text(item: dict[str, Any]) -> str:
    keys = [
        "field", "label", "type", "text", "value", "context",
        "caption", "title", "name", "content", "ocr_text",
    ]
    return " | ".join(_norm(item.get(k)) for k in keys if item.get(k) not in (None, "", [], {}))


def _build_rows(items: list[dict[str, Any]], kind: str, query: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, item in enumerate(items or []):
        text = _item_text(item)
        if not text:
            continue
        score = _score(query, text)
        if query and score < 0.25:
            continue
        rows.append(
            {
                "kind": kind,
                "row_id": f"{kind}-{i}",
                "page_number": item.get("page_number", item.get("page", item.get("page_index"))),
                "text": text[:500],
                "bbox": item.get("bbox") or item.get("bounding_box") or item.get("box"),
                "confidence": item.get("confidence"),
                "source": item,
                "score": round(score, 3),
            }
        )
    return rows


def search_document(doc_ctx: dict[str, Any], query: str = "", field_type: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    if not isinstance(doc_ctx, dict):
        return []

    rows: list[dict[str, Any]] = []
    fields = doc_ctx.get("fields", []) or []
    blocks = doc_ctx.get("classified_blocks", []) or []
    pages = doc_ctx.get("pages", []) or []

    rows.extend(_build_rows(fields, "field", query))
    rows.extend(_build_rows(blocks, "block", query))
    rows.extend(_build_rows(pages, "page", query))

    if field_type:
        ft = str(field_type).strip().lower()
        rows = [
            r for r in rows
            if ft in _norm(r.get("kind")).lower() or ft in _norm(r.get("text")).lower()
            or ft in _norm(r.get("source", {})).lower()
        ]

    rows.sort(key=lambda r: (r["score"], _norm(r.get("page_number"))), reverse=True)
    return rows[:limit]