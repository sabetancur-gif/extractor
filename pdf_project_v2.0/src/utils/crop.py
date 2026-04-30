# src/utils/crop.py
from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image


def _as_box(bbox: Any) -> tuple[float, float, float, float] | None:
    if bbox is None:
        return None
    if isinstance(bbox, dict):
        x0 = bbox.get("x0", bbox.get("left", bbox.get("xmin")))
        y0 = bbox.get("y0", bbox.get("top", bbox.get("ymin")))
        x1 = bbox.get("x1", bbox.get("right", bbox.get("xmax")))
        y1 = bbox.get("y1", bbox.get("bottom", bbox.get("ymax")))
        if None in (x0, y0, x1, y1):
            return None
        return float(x0), float(y0), float(x1), float(y1)
    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        return float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
    return None


def _scale_bbox(
    box: tuple[float, float, float, float],
    img_w: int,
    img_h: int,
    pdf_width: float | None = None,
    pdf_height: float | None = None,
) -> tuple[int, int, int, int]:
    """
    Convierte coordenadas de bbox a píxeles de imagen.

    Prioridades:
    1. Si se proveen pdf_width / pdf_height, escala usando el factor
       img / pdf (coordenadas PDF → píxeles de imagen).
    2. Si las coordenadas parecen normalizadas [0..1], escala por img_w/img_h.
    3. De lo contrario se usan directamente como píxeles.
    """
    x0, y0, x1, y1 = box

    if pdf_width and pdf_height and pdf_width > 0 and pdf_height > 0:
        sx = img_w / pdf_width
        sy = img_h / pdf_height
        x0, x1 = x0 * sx, x1 * sx
        y0, y1 = y0 * sy, y1 * sy
    elif max(abs(x0), abs(y0), abs(x1), abs(y1)) <= 1.5:
        # Coordenadas normalizadas [0..1]
        x0, x1 = x0 * img_w, x1 * img_w
        y0, y1 = y0 * img_h, y1 * img_h

    left   = max(0, min(img_w, int(min(x0, x1))))
    top    = max(0, min(img_h, int(min(y0, y1))))
    right  = max(0, min(img_w, int(max(x0, x1))))
    bottom = max(0, min(img_h, int(max(y0, y1))))
    return left, top, right, bottom


def crop_page_region(
    image_path: str,
    bbox: Any,
    padding: int = 16,
    pdf_width: float | None = None,
    pdf_height: float | None = None,
) -> str:
    """
    Recorta la región de una imagen de página definida por bbox y la devuelve
    como data-URI PNG en base64.

    Args:
        image_path: Ruta a la imagen de la página (PNG/JPEG).
        bbox:       Bounding box en coordenadas PDF o de imagen.
                    Puede ser lista [x0,y0,x1,y1] o dict con claves x0/y0/x1/y1.
        padding:    Píxeles extra alrededor del recorte.
        pdf_width:  Ancho de la página PDF en puntos. Si se provee junto con
                    pdf_height, se usa para escalar bbox de espacio PDF a píxeles.
        pdf_height: Alto de la página PDF en puntos.

    Returns:
        Data-URI "data:image/png;base64,..." o "" si no se puede procesar.
    """
    box = _as_box(bbox)
    if not image_path or box is None:
        return ""

    try:
        with Image.open(image_path) as img:
            img_w, img_h = img.size
            left, top, right, bottom = _scale_bbox(
                box, img_w, img_h, pdf_width, pdf_height
            )

            left   = max(0, left   - padding)
            top    = max(0, top    - padding)
            right  = min(img_w, right  + padding)
            bottom = min(img_h, bottom + padding)

            if right <= left or bottom <= top:
                return ""

            crop = img.crop((left, top, right, bottom))
            buf  = io.BytesIO()
            crop.save(buf, format="PNG")
            encoded = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""
