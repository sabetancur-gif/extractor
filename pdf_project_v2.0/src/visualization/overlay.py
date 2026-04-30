"""
src/visualization/overlay.py
-----------------------------
Genera imágenes de página con rectángulos superpuestos por bloque clasificado.
Cada tipo semántico tiene su propio color para facilitar la visualización.
Los overlays se guardan en data/cache/<doc_id>/overlays/.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from src.logs.logger import LogManager

# ── Paleta de colores por tipo semántico ──────────────────────────────────────
# Formato: (R, G, B)
SEMANTIC_COLORS: dict[str, tuple[int, int, int]] = {
    "title":            (10,  120, 240),   # azul brillante
    "subtitle":         (30,  160, 255),   # azul claro
    "header":           (60,  180, 200),   # cian
    "footer":           (100, 140, 160),   # gris azulado
    "paragraph":        (80,  180, 80),    # verde
    "table":            (200, 100, 50),    # naranja
    "figure":           (180, 60,  200),   # morado
    "image":            (200, 80,  160),   # rosa
    "signature":        (240, 50,  50),    # rojo
    "date":             (240, 180, 20),    # amarillo
    "email":            (20,  200, 140),   # verde azulado
    "phone":            (60,  200, 120),   # verde claro
    "amount":           (240, 120, 30),    # naranja oscuro
    "address":          (160, 100, 60),    # café
    "url":              (0,   140, 220),   # azul URL
    "identifier":       (150, 100, 200),   # lavanda
    "name":             (220, 100, 100),   # rojo suave
    "math_expression":  (100, 200, 200),   # turquesa
    "code":             (80,  80,  160),   # índigo
    "logo":             (220, 160, 0),     # dorado
    "stamp":            (160, 80,  80),    # rojo oscuro
    "other":            (140, 140, 140),   # gris
    "empty":            (200, 200, 200),   # gris claro
}

DEFAULT_COLOR = (140, 140, 140)  # gris para tipos desconocidos


class OverlayGenerator:
    """
    Genera imágenes de overlay: toma una imagen de página y dibuja
    rectángulos de colores sobre cada bloque clasificado.
    """

    def __init__(self, cache_dir: str = "data/cache", log_mgr: LogManager | None = None):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.log_mgr = log_mgr or LogManager()

    def render_page_overlay(
        self,
        page_image_path: str,
        blocks: list[dict[str, Any]],
        doc_id: str,
        page_num: int,
        page_width: float,
        page_height: float,
        show_labels: bool = True,
    ) -> str:
        """
        Dibuja rectángulos de colores sobre la imagen de una página.

        Args:
            page_image_path: Ruta a la imagen base de la página.
            blocks:          Lista de bloques con bbox y semantic_type.
            doc_id:          ID del documento.
            page_num:        Número de página (1-indexed).
            page_width:      Ancho de la página en unidades PDF.
            page_height:     Alto de la página en unidades PDF.
            show_labels:     Si True, escribe el tipo semántico sobre el rectángulo.

        Returns:
            Ruta de la imagen generada.
        """
        # Cargar imagen base
        base_img = Image.open(page_image_path).convert("RGBA")
        img_w, img_h = base_img.size

        # Crear capa transparente para los overlays
        overlay_layer = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay_layer)

        # Cargar fuente
        font = _load_font(11)

        # Factores de escala PDF → imagen
        sx = img_w / page_width  if page_width  > 0 else 1.0
        sy = img_h / page_height if page_height > 0 else 1.0

        for block in blocks:
            bbox = block.get("bbox")
            if not bbox or len(bbox) < 4:
                continue

            sem_type = block.get("semantic_type", "other")
            color    = SEMANTIC_COLORS.get(sem_type, DEFAULT_COLOR)
            alpha_fill   = 30   # transparencia del relleno
            alpha_border = 200  # opacidad del borde

            x0, y0, x1, y1 = [float(v) for v in bbox[:4]]

            # Escalar a píxeles
            px0 = int(x0 * sx)
            py0 = int(y0 * sy)
            px1 = int(x1 * sx)
            py1 = int(y1 * sy)

            # Asegurar que las coordenadas estén ordenadas y dentro de la imagen
            px0, px1 = sorted([max(0, px0), min(img_w, px1)])
            py0, py1 = sorted([max(0, py0), min(img_h, py1)])

            if px1 - px0 < 2 or py1 - py0 < 2:
                continue

            # Relleno semi-transparente
            fill_color = color + (alpha_fill,)
            draw.rectangle([px0, py0, px1, py1], fill=fill_color)

            # Borde sólido
            border_color = color + (alpha_border,)
            draw.rectangle([px0, py0, px1, py1], outline=border_color, width=2)

            # Etiqueta del tipo semántico
            if show_labels and sem_type and sem_type not in ("other", "empty", "paragraph"):
                label_text = sem_type.replace("_", " ").upper()
                tx = px0 + 3
                ty = max(0, py0 - 14)
                # Fondo de la etiqueta
                draw.rectangle(
                    [tx - 2, ty, tx + len(label_text) * 6 + 2, ty + 12],
                    fill=color + (200,),
                )
                draw.text((tx, ty), label_text, fill=(255, 255, 255, 230), font=font)

        # Componer sobre la imagen base
        composite = Image.alpha_composite(base_img, overlay_layer).convert("RGB")

        # Guardar
        out_dir = os.path.join(self.cache_dir, doc_id, "overlays")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"overlay_p{page_num}.png")
        composite.save(out_path, format="PNG")

        self.log_mgr.log({
            "timestamp":       datetime.now().isoformat(),
            "file_id":         doc_id,
            "step":            "OVERLAY_GENERATED",
            "page_number":     page_num,
            "status":          "success",
            "context_snippet": f"blocks={len(blocks)}, size={img_w}x{img_h}",
        })

        return out_path


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Carga una fuente TrueType o retorna la fuente por defecto."""
    for font_name in ("DejaVuSans.ttf", "Arial.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()
