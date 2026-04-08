# src/utils/crop.py
from __future__ import annotations

import base64
import io
from typing import Any, Iterable

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


def _maybe_scale_bbox(box: tuple[float, float, float, float], w: int, h: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    # If coordinates look normalized [0..1], scale them up
    if max(abs(x0), abs(y0), abs(x1), abs(y1)) <= 1.5:
        x0, x1 = x0 * w, x1 * w
        y0, y1 = y0 * h, y1 * h

    left = max(0, min(w, int(min(x0, x1))))
    top = max(0, min(h, int(min(y0, y1))))
    right = max(0, min(w, int(max(x0, x1))))
    bottom = max(0, min(h, int(max(y0, y1))))
    return left, top, right, bottom


def crop_page_region(image_path: str, bbox: Any, padding: int = 16) -> str:
    box = _as_box(bbox)
    if not image_path or box is None:
        return ""

    with Image.open(image_path) as img:
        w, h = img.size
        left, top, right, bottom = _maybe_scale_bbox(box, w, h)
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(w, right + padding)
        bottom = min(h, bottom + padding)

        crop = img.crop((left, top, right, bottom))
        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"