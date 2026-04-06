
"""Docstring for layout.reading_order.
Docstring."""
from PIL import Image, ImageDraw, ImageFont
import os
import threading
from datetime import datetime
from src.logs.logger import LogManager

COLORS = {
    "title": (10, 120, 240),
    "paragraph": (120, 200, 80),
    "table": (200, 100, 50),
    "figure": (180, 60, 200),
    "ocr": (240, 180, 20)
}


# 📁 Resultado típico: data/cache/<doc_id>/overlays/overlay_p1.png
class OverlayGenerator:
    """Docstring for OverlayGenerator.

    Docstring.
    """
    def __init__(self, cache_dir="data/cache", log_mgr: LogManager = None):
        self.cache_dir = cache_dir  # Define un directorio de caché
        os.makedirs(cache_dir, exist_ok=True)
        self.log_mgr = log_mgr or LogManager()

    def render_page_overlay(
            self,
            page_image_path: str,
            blocks: list,
            doc_id: str,
            page_num: int,
            page_width: int,
            page_height: int,
            show_labels=True,
    ) -> str:
        # Abrir imagen base
        img = Image.open(page_image_path).convert("RGBA")

        # Crear capa de pverlay transparente
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Cargar fuente
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 12)
        except Exception:
            font = ImageFont.load_default()

        # === Escalado de bounding boxes ===
        img_width, img_height = img.size
        pdf_width, pdf_height = page_width, page_height

        self.log_mgr.log({
            "timestamp": datetime.now().isoformat(),
            "file_id": doc_id,
            "filename": page_image_path.split(os.sep)[-1],
            "step": "OVERLAY_DIM",
            "page_number": page_num,
            "pages_total": None,
            "worker_id": threading.get_ident(),
            "status": "info",
            "duration_seconds": None,
            "avg_sec_per_page": None,
            "concurrency_count": None,
            "match_query": None,
            "context_snippet": f"width={pdf_width}, height={pdf_height}",
            "error_message": None
        })
        # for b in blocks:
        #     if "page_width" in b and "page_height" in b:
        #         pdf_width = b["page_width"]
        #         pdf_height = b["page_height"]
        #         break
        if pdf_width is None or pdf_height is None:
            max_bbox = [0, 0, 0, 0]
            for b in blocks:
                x0, y0, x1, y1 = b["bbox"]
                if (x1-x0)*(y1-y0) > (max_bbox[2]-max_bbox[0])*(max_bbox[3] - max_bbox[1]):
                    max_bbox = [x0, y0, x1, y1]
            pdf_width = max_bbox[2]
            pdf_height = max_bbox[3]

        scale_x = img_width / pdf_width if pdf_width else 1.0
        scale_y = img_height / pdf_height if pdf_height else 1.0
        for b in blocks:
            bbox = b.get("bbox", [])
            if not bbox or len(bbox) < 4:
                continue
            
            x0, y0, x1, y1 = bbox
            x0 = int(x0 * scale_x)
            y0 = int(y0 * scale_y)
            x1 = int(x1 * scale_x)
            y1 = int(y1 * scale_y)
            
            # Validar y corregir coordenadas si es necesario
            if x0 > x1:
                x0, x1 = x1, x0
            if y0 > y1:
                y0, y1 = y1, y0
            
            # Asegurar que las coordenadas están dentro de los límites de la imagen
            x0 = max(0, min(x0, img_width))
            y0 = max(0, min(y0, img_height))
            x1 = max(0, min(x1, img_width))
            y1 = max(0, min(y1, img_height))
            
            # Saltar si el rectángulo es demasiado pequeño o inválido
            if x0 >= x1 or y0 >= y1:
                continue
            
            color = COLORS.get(
                b.get("type") or b.get("source"), (255, 255, 255)
            )
            draw.rectangle([x0, y0, x1, y1], outline=color+(200,), width=2)
            if show_labels:
                draw.text(
                    (x0+3, y0+3),
                    f"{b['block_id']} {b.get('type', '')}",
                    fill=color+(220,),
                    font=font
                )

        # Guardar imagen combinadaa
        out_dir = os.path.join(self.cache_dir, doc_id, "overlays")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"overlay_p{page_num}.png")
        combined = Image.alpha_composite(img, overlay)
        combined.save(out_path)
        return out_path
