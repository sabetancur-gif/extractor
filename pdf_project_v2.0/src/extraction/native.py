"""
src/extraction/native.py
------------------------
Extractor nativo de PDFs (con capa de texto seleccionable).
Usa PyMuPDF (fitz) para extraer texto, fuentes, bounding boxes y metadatos.
Cada bloque es clasificado semánticamente por block_classifier.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

import fitz  # PyMuPDF

from .base import BaseExtractor
from .block_classifier import classify_block
from .field_detection import extract_fields_from_block


class NativePDFExtractor(BaseExtractor):
    """Extractor para PDFs con texto nativo (no escaneados)."""

    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extrae todos los bloques de texto del PDF con metadatos de fuente y posición.

        Returns:
            Lista de páginas. Cada página tiene: page_number, width, height, blocks.
        """
        doc = fitz.open(file_path)
        pages = []

        for pno, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            width, height = page.rect.width, page.rect.height

            blocks = _extract_blocks(page_dict, pno, width, height)
            pages.append({
                "page_number": pno,
                "width":       width,
                "height":      height,
                "blocks":      blocks,
            })

        doc.close()
        return pages


# ── helpers ───────────────────────────────────────────────────────────────────

def _normalize_bbox(bbox_raw: Any, page_w: float, page_h: float) -> list[float] | None:
    """Normaliza y valida un bbox dentro de los límites de la página."""
    if not bbox_raw or len(bbox_raw) < 4:
        return None
    try:
        x0, y0, x1, y1 = [float(v) for v in bbox_raw[:4]]
        x0, x1 = sorted([max(0, x0), min(page_w, x1)])
        y0, y1 = sorted([max(0, y0), min(page_h, y1)])
        if x1 - x0 < 1 or y1 - y0 < 1:
            return None
        return [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)]
    except Exception:
        return None


def _extract_blocks(
    page_dict: Dict[str, Any],
    pno: int,
    width: float,
    height: float,
) -> List[Dict[str, Any]]:
    """Extrae y enriquece los bloques de una página."""
    blocks = []
    order  = 0

    for b in page_dict.get("blocks", []):
        block_type = b.get("type", 0)  # 0=text, 1=image

        # Bloque de imagen nativa
        if block_type == 1:
            bbox = _normalize_bbox(b.get("bbox"), width, height)
            if bbox:
                blocks.append({
                    "block_id":          f"{pno}_img_{order}",
                    "text":              "",
                    "bbox":              bbox,
                    "page":              pno,
                    "page_number":       pno,
                    "source":            "native_image",
                    "order":             order,
                    "semantic_type":     "figure",
                    "semantic_confidence": 0.90,
                    "semantic_labels":   ["figure", "image"],
                    "is_image":          True,
                    "is_table_like":     False,
                    "is_signature":      False,
                    "is_logo":           False,
                    "is_address":        False,
                    "is_date":           False,
                    "is_amount":         False,
                    "is_phone":          False,
                    "is_email":          False,
                    "is_url":            False,
                    "is_identifier":     False,
                    "is_name":           False,
                    "is_math":           False,
                })
                order += 1
            continue

        # Bloque de texto: extraer spans con metadatos de fuente
        text_parts: list[str] = []
        font_sizes: list[float] = []
        font_names: list[str]   = []
        is_bold = False

        for line in b.get("lines", []):
            for span in line.get("spans", []):
                txt = span.get("text", "").strip()
                if not txt:
                    continue
                text_parts.append(txt)
                fs = span.get("size")
                if fs:
                    font_sizes.append(float(fs))
                fn = span.get("font", "")
                font_names.append(fn)
                # Detectar negrita por nombre de fuente
                if "Bold" in fn or "bold" in fn or "Heavy" in fn:
                    is_bold = True

        text = " ".join(text_parts).strip()
        if not text:
            continue

        bbox = _normalize_bbox(b.get("bbox"), width, height)
        if not bbox:
            continue

        avg_font = (sum(font_sizes) / len(font_sizes)) if font_sizes else None
        font_name = font_names[0] if font_names else None

        # Clasificar semánticamente
        raw_block = {
            "text":      text,
            "bbox":      bbox,
            "font_size": avg_font,
            "font_name": font_name,
            "is_bold":   is_bold,
        }
        semantic = classify_block(raw_block, page_width=width, page_height=height)

        # Detectar campos específicos
        field_info = extract_fields_from_block(text, context=text)
        field_type  = field_info.get("field")  if field_info else None
        field_value = field_info.get("value")  if field_info else None

        block = {
            "block_id":            f"{pno}_b{order}",
            "text":                text,
            "bbox":                bbox,
            "font_size":           avg_font,
            "font_name":           font_name,
            "is_bold":             is_bold,
            "page":                pno,
            "page_number":         pno,
            "source":              "native",
            "order":               order,
            "field_type":          field_type,
            "field_value":         field_value,
            "semantic_type":       semantic["semantic_type"],
            "semantic_confidence": semantic["confidence"],
            "semantic_labels":     semantic["labels"],
            "is_table_like":       semantic["is_table_like"],
            "is_signature":        semantic["is_signature"],
            "is_logo":             semantic["is_logo"],
            "is_image":            semantic["is_image"],
            "is_address":          semantic["is_address"],
            "is_date":             semantic["is_date"],
            "is_amount":           semantic["is_amount"],
            "is_phone":            semantic["is_phone"],
            "is_email":            semantic["is_email"],
            "is_url":              semantic["is_url"],
            "is_identifier":       semantic["is_identifier"],
            "is_name":             semantic.get("is_name", False),
            "is_math":             semantic.get("is_math", False),
        }

        blocks.append(block)
        order += 1

    return blocks
