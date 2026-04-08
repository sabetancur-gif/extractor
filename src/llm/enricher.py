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


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}

    # 1) full parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) fenced or embedded JSON
    matches = _JSON_BLOCK_RE.findall(text)
    for candidate in matches:
        try:
            return json.loads(candidate)
        except Exception:
            continue

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
        confidence_threshold: float = 0.75,
    ) -> dict[str, Any]:
        base = deepcopy(doc_ctx or {})
        prompt = build_enrichment_prompt(base, mode=mode)
        raw = self.client.generate(system=SYSTEM_PROMPT, user=prompt, temperature=0.0)
        parsed = _extract_json(raw)

        applied_changes: list[dict[str, Any]] = []

        if isinstance(parsed, dict):
            suggestions = parsed.get("fill_suggestions", [])
            if isinstance(suggestions, list):
                # Apply only low-risk fills
                fields = base.get("fields", [])
                for suggestion in suggestions:
                    if not isinstance(suggestion, dict):
                        continue
                    target_field = suggestion.get("field")
                    suggested_value = suggestion.get("suggested_value")
                    confidence = float(suggestion.get("confidence", 0.0) or 0.0)
                    evidence = suggestion.get("evidence", [])
                    if not target_field or suggested_value in (None, "", []):
                        continue
                    if confidence < confidence_threshold:
                        continue

                    # fill only empty matching fields
                    for field in fields:
                        field_name = _safe_text(field.get("field") or field.get("label") or field.get("name")).lower()
                        current_value = field.get("value")
                        if field_name == _safe_text(target_field).lower() and current_value in (None, "", [], {}):
                            field["llm_filled_value"] = suggested_value
                            field["llm_confidence"] = confidence
                            field["llm_evidence"] = evidence
                            applied_changes.append(
                                {
                                    "field": target_field,
                                    "value": suggested_value,
                                    "confidence": confidence,
                                }
                            )

                base["fields"] = fields

        result = LLMEnrichmentResult(
            mode=mode,
            raw_response=raw,
            parsed=parsed if isinstance(parsed, dict) else {"raw": raw},
            applied_changes=applied_changes,
            warnings=[] if parsed else ["LLM response could not be parsed as JSON"],
        )

        base["llm"] = asdict(result)
        base["llm_applied_changes"] = applied_changes
        base["llm_raw_response"] = raw
        base["llm_parsed"] = parsed
        return base