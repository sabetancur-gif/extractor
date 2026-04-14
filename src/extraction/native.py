"""Docstring for extraction.native.

Docstring.
"""

import fitz
from typing import List, Dict
from .base import BaseExtractor

from src.extraction.block_classifier import classify_block


class NativePDFExtractor(BaseExtractor):
    def __init__(self):
        pass

    def extract(self, file_path: str) -> List[Dict]:
        from .field_detection import extract_fields_from_block
        # import numpy as np  # No se usa
        doc = fitz.open(file_path)
        pages = []
        for pno, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")
            width, height = page.rect.width, page.rect.height
            blocks = []
            order = 0
            for b in page_dict.get("blocks", []):
                bbox = b.get("bbox", [0,0,0,0])
                # Normaliza bbox: corrige orden, redondea, asegura dentro de página
                x0, y0, x1, y1 = bbox if len(bbox) == 4 else (0,0,0,0)
                x0, x1 = sorted([x0, x1])
                y0, y1 = sorted([y0, y1])
                x0, x1 = max(0, x0), min(width, x1)
                y0, y1 = max(0, y0), min(height, y1)
                bbox = [round(float(x0)), round(float(y0)), round(float(x1)), round(float(y1))]
                text_parts = []
                font_sizes = []
                font_names = []
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        txt = span.get("text", "")
                        if txt.strip():
                            text_parts.append(txt)
                            font_sizes.append(span.get("size", None))
                            font_names.append(span.get("font", None))
                text = " ".join([p for p in text_parts]).strip()
                avg_font = sum([s for s in font_sizes if s])/len(font_sizes) if font_sizes else None
                block = {
                    "block_id": f"{pno}_b{order}",
                    "text": text,
                    "bbox": bbox,
                    "font_size": avg_font,
                    "font_name": font_names[0] if font_names else None,
                    "page": pno,
                    "source": "native",
                    "order": order
                }
                # Clasificación de campo clave y tipo de bloque
                context = text
                field_info = extract_fields_from_block(text, context)
                if field_info:
                    block["field_type"] = field_info["field"]
                    block["field_value"] = field_info["value"]
                    block["all_fields"] = field_info.get("all_fields", [])
                font_size = block.get("font_size", None)
                text_len = len(text)
                text_lower = text.lower()
                if font_size and font_size > 16 and text_len < 80:
                    block["block_type"] = "title"
                elif "table" in text_lower or "tabla" in text_lower:
                    block["block_type"] = "table"
                elif any(k in text_lower for k in ["total", "monto", "$", "importe"]):
                    block["block_type"] = "amount"
                elif any(k in text_lower for k in ["fecha", "date"]):
                    block["block_type"] = "date"
                elif text_len > 200:
                    block["block_type"] = "paragraph"
                elif text_len < 30 and font_size and font_size > 10:
                    block["block_type"] = "header"
                else:
                    block["block_type"] = "other"

                semantic = classify_block(
                    block,
                    page_width=width,
                    pafe_height=height
                )

                block.update(
                    {
                        "semantic_type": semantic["semantic_type"],
                        "semantic_confidence": semantic["confidence"],
                        "semantic_labels": semantic["labels"],
                        "is_table_like": semantic["is_table_like"],
                        "is_signature": semantic["is_signature"],
                        "is_logo": semantic["is_logo"],
                        "is_image": semantic["is_image"],
                        "is_address": semantic["is_addres"],
                        "is_date": semantic["is_date"],
                        "is_amount": semantic["is_amount"],
                        "is_phone": semantic["is_phone"],
                        "is_email": semantic["is_email"],
                        "is_url": semantic["is_url"],
                        "is_identifier": semantic["is_identifier"],
                    }
                )

                blocks.append(block)
                order += 1

            pages.append({"page_number": pno, "width": width, "height": height, "blocks": blocks})
        return pages
