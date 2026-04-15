from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Iterable, Tuple

from src.extraction.block_classifier import classify_block
from src.extraction.field_detection import extract_fields_from_block
from src.utils.bbox import normalize_bbox, normalize_page_number

def _pick_primary_field(field_info: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(field_info, dict):
        return None

    if field_info.get("field") and field_info.get("value"):
        return {
            "field": field_info.get("field"),
            "value": field_info.get("value"),
            "score": field_info.get("score", 1),
        }

    all_fields = field_info.get("all_fields") or []
    if not all_fields:
        return None

    best = max(all_fields, key=lambda item: item.get("score", 0))
    return {
        "field": field_info.get("field"),
        "value": field_info.get("value"),
        "score": field_info.get("score", 0),
    }

def enrich_pages(
        pages: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:

    enriched_pages: list[dict[str, Any]] = []
    classified_blocks: list[dict[str, Any]] = []
    fields: list[dict[str, Any]] = []

    seen_fields: set[tuple[Any, ...]] = set()

    for page in pages or []:
        page_number = normalize_page_number(page.get("page_number")) or 0
        width = int(page.get("width") or 0)
        height = int(page.get("height") or 0)

        page_blocks: list[dict[str, Any]] = []
        for order, block in enumerate(page.get("block", []) or []):
            text = (block.get("text") or "").strip()
            bbox = normalize_bbox(block.get("bbox"))

            semantic = classify_block(
                {**block, "bbox": bbox, "text": text},
                page_width=width,
                page_height=height,
            )

            context = " ".join(
                part for part in [
                    text,
                    str(block.get("field_type") or ""),
                    str(block.get("field_value") or ""),
                ] if part
            )

            field_info = extract_fields_from_block(text, context=context or text)
            primary_field = _pick_primary_field(field_info)

            enriched_block = deepcopy(block)
            enriched_block.update(
                {
                    "page_number": page_number,
                    "page": page_number,
                    "bbox": bbox,
                    "order": block.get("order", order),
                    "semantic_type": semantic["semantic_type"],
                    "semantic_confidence": semantic["confidence"],
                    "semantic_labels": semantic["labels"],
                    "is_table_like": semantic["is_tabla_like"],
                    "is_signature": semantic["is_signature"],
                    "is_logo": semantic["is_logo"],
                    "is_image": semantic["is_image"],
                    "is_address": semantic["is_address"],
                    "is_date": semantic["is_date"],
                    "is_amount": semantic["is_amount"],
                    "is_phone": semantic["is_phone"],
                    "is_email": semantic["is_email"],
                    "is_url": semantic["is_url"],
                    "is_identifier": semantic["is_identifier"],
                }
            )

            if primary_field:
                enriched_block["field_type"] = primary_field["field"]
                enriched_block["field_value"] = primary_field["value"]
                enriched_block["field_score"] = primary_field.get("score", 0)

                field_key = (
                    page_number,
                    enriched_block.get("block_id"),
                    primary_field.get("field"),
                    primary_field.get("value"),
                )

                if field_key not in seen_fields:
                    seen_fields.add(field_key)
                    fields.append(
                        {
                            "field": primary_field.get("field"),
                            "value": primary_field.get("value"),
                            "score": primary_field.get("score", 0),
                            "page_number": page_number,
                            "page": page_number,
                            "block_id": enriched_block.get("block_id"),
                            "bbox": bbox,
                            "source": enriched_block.get("source"),
                            "semantic_type": semantic["semantic_type"],
                            "semantic_confidence": semantic["confidence"],
                            "text": text,
                        }
                    )
            page_blocks.append(enriched_block)
            classified_blocks.append(enriched_block)

        enriched_pages.append(
            {
                "page_number": page_number,
                "width": width,
                "height": height,
                "blocks": page_blocks,
            }
        )

    return enriched_pages, classified_blocks, fields


def build_doc_context(
        *,
        doc_id: str,
        file_name: str,
        file_path: str,
        pages: list[dict[str, Any]],
        overlays: list[dict[str, Any]] | None = None,
        pdf_type: str | None = None,
        processing_mode: str | None = None,
        extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    enriched_pages, classified_blocks, fields = enrich_pages(pages)

    ctx: dict[str, Any] = {
        "doc_id": doc_id,
        "file_name": file_name,
        "file_path": file_path,
        "pdf_type": pdf_type or "unknown",
        "processing_mode": processing_mode or "unknown",
        "pages_total": len(enriched_pages),
        "pages": enriched_pages,
        "classified_blocks": classified_blocks,
        "fields": fields,
        "overlays": overlays or [],
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    if extra_meta:
        ctx.update(extra_meta)

    ctx["stats"] = {
        "pages": len(enriched_pages),
        "blocks": len(classified_blocks),
        "fields": len(fields),
        "has_overlays": bool(overlays),
    }

    return ctx
