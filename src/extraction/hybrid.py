# src/extraction/hybrid.py

from .base import BaseExtractor
from .native import NativePDFExtractor
from .ocr import OCRExtractor
from src.utils.geometry import iou_bbox

from src.extraction.block_classifier import classify_block

class HybridExtractor(BaseExtractor):
    """
    Extractor híbrido:
    - Usa extracción nativa para texto embebido en PDFs digitales
    - Usa OCR para capturar texto dentro de imágenes
    - Fusiona ambos resultados evitando duplicados

    La deduplicación se hace por:
    1. Solapamiento geométrico (IoU)
    2. Igualdad de texto (para PDFs mixtos rasterizados)
    """

    def __init__(self, native=None, ocr=None, iou_thresh=0.45):
        # Extractor de texto nativo (PDF digital)
        self.native = native or NativePDFExtractor()

        # Extractor OCR (PDF escaneado / imágenes)
        self.ocr = ocr or OCRExtractor()

        # Umbral de solapamiento geométrico
        self.iou_thresh = iou_thresh

    def _is_duplicate(self, ocr_block, native_blocks):
        """
        Determina si un bloque OCR es duplicado de algún bloque nativo.

        Criterios:
        - IoU mayor al umbral
        - Texto exactamente igual (case-insensitive)
        """
        ocr_text = ocr_block.get("text", "").strip().lower()

        for nb in native_blocks:
            nb_text = nb.get("text", "").strip().lower()

            # 1. Duplicado geométrico
            if iou_bbox(ocr_block["bbox"], nb["bbox"]) > self.iou_thresh:
                return True

            # 2. Duplicado semántico exacto
            if ocr_text and ocr_text == nb_text:
                return True

        return False

    def extract(self, file_path: str):
        """
        Extracción híbrida inteligente: si la extracción nativa es vacía o pobre, usa OCR automáticamente.
        Mejora la precisión de los bbox y la robustez de la fusión.
        """
        from .field_detection import extract_fields_from_block
        native_pages = self.native.extract(file_path)
        # Si la extracción nativa es vacía o tiene muy poco texto, forzar OCR
        def total_text(pages):
            return sum(len(b.get("text", "").strip()) for p in pages for b in p.get("blocks", []))
        if not native_pages or total_text(native_pages) < 30:
            ocr_pages = self.ocr.extract(file_path)
            pages_to_use = ocr_pages
        else:
            ocr_pages = self.ocr.extract(file_path)
            pages_to_use = []
            for n_page, o_page in zip(native_pages, ocr_pages):
                def fix_bbox(b, page_w=None, page_h=None):
                    bbox = b.get("bbox", [0,0,0,0])
                    if len(bbox) == 4:
                        x0, y0, x1, y1 = bbox
                        x0, x1 = sorted([x0, x1])
                        y0, y1 = sorted([y0, y1])
                        # No sobrescribo page_w/page_h, solo uso los argumentos
                        x0, x1 = max(0, x0), min(page_w, x1) if page_w else x1
                        y0, y1 = max(0, y0), min(page_h, y1) if page_h else y1
                        return [round(float(x0)), round(float(y0)), round(float(x1)), round(float(y1))]
                    return [0,0,0,0]
                out_blocks = []
                native_texts = set()
                page_w = n_page.get("width")
                page_h = n_page.get("height")
                for nb in n_page["blocks"]:
                    nb["bbox"] = fix_bbox(nb, page_w, page_h)
                    native_texts.add(nb.get("text", "").strip().lower())
                    out_blocks.append(nb)
                for ob in o_page["blocks"]:
                    ob["bbox"] = fix_bbox(ob, page_w, page_h)
                    if not self._is_duplicate(ob, n_page["blocks"]) and ob.get("text", "").strip().lower() not in native_texts:
                        ob["source"] = "ocr"
                        out_blocks.append(ob)
                out_blocks = sorted(
                    out_blocks,
                    key=lambda b: (b["bbox"][1], b["bbox"][0])
                )
                for i, b in enumerate(out_blocks):
                    b["order"] = i + 1
                    context = b.get("text", "")
                    field_info = extract_fields_from_block(b.get("text", ""), context)
                    if field_info:
                        b["field_type"] = field_info["field"]
                        b["field_value"] = field_info["value"]
                        b["all_fields"] = field_info.get("all_fields", [])
                    font_size = b.get("font_size", None)
                    text_len = len(b.get("text", ""))
                    text_lower = b.get("text", "").lower()
                    if font_size and font_size > 16 and text_len < 80:
                        b["block_type"] = "title"
                    elif "table" in text_lower or "tabla" in text_lower:
                        b["block_type"] = "table"
                    elif any(k in text_lower for k in ["total", "monto", "$", "importe"]):
                        b["block_type"] = "amount"
                    elif any(k in text_lower for k in ["fecha", "date"]):
                        b["block_type"] = "date"
                    elif text_len > 200:
                        b["block_type"] = "paragraph"
                    elif text_len < 30 and font_size and font_size > 10:
                        b["block_type"] = "header"
                    else:
                        b["block_type"] = "other"

                    semantic = classify_block(
                        b,
                        page_width=page_w,
                        page_height=page_h
                    )

                    b.update(
                        {
                            "semantic_type": semantic["semantic_type"],
                            "semantic_confidence": semantic["confidence"],
                            "semantic_labels": semantic["labels"],
                            "is_table_like": semantic["is_table_like"],
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

                pages_to_use.append({
                    "page_number": n_page["page_number"],
                    "width": n_page["width"],
                    "height": n_page["height"],
                    "blocks": out_blocks,
                })
        return pages_to_use
