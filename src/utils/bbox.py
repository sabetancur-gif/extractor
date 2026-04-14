# src/utils/bbox.py
from __future__ import annotations

from typing import Any, Iterable

def normalize_page_number(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value).strip()))
        except Exception:
            return None

def normalize_bbox(bbox: Any) -> list[float] | None:
    if bbox is None:
        return None

    if isinstance(bbox, dict):
        x0 = bbox.get("x0", bbox.get("left", bbox.get("xmin")))
        y0 = bbox.get("y0", bbox.get("top", bbox.get("ymin")))
        x1 = bbox.get("x1", bbox.get("right", bbox.get("xmax")))
        y1 = bbox.get("y1", bbox.get("bottom", bbox.get("ymax")))
        if None in (x0, y0, x1, y1):
            return None
        try:
            return [float(x0), float(y0), float(x1), float(y1)]
        except Exception:
            return None

    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        try:
            return [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
        except Exception:
            return None

    return None

def row_bbox(row: dict[str, Any] | None) -> list[float] | None:
    if not isinstance(row, dict):
        return None

    for key in ("bbox", "bounding_box", "box", "rect", "bounds", "bbox_normalized"):
        value = row.get(key)
        if value:
            out = normalize_bbox(value)
            if out is not None:
                return out

    if all(k in row for k in ("x", "y", "w", "h")):
        try:
            x = float(row["x"])
            y = float(row["y"])
            w = float(row["w"])
            h = float(row["h"])
            return [x, y, x + w, y + h]
        except Exception:
            return None

    if all(k in row for k in ("left", "top", "right", "bottom")):
        try:
            return [
                float(row["left"]),
                float(row["top"]),
                float(row["right"]),
                float(row["bottom"]),
            ]
        except Exception:
            return None

    return None

def row_page_number(row: dict[str, Any] | None) -> int | None:
    if not isinstance(row, dict):
        return None

    for key in ("page_number", "page", "page_index"):
        value = normalize_page_number(row.get(key))
        if value is not None:
            return value

    return None

def bbox_area(bbox: Any) -> float:
    norm = normalize_bbox(bbox)
    if not norm:
        return 0.0
    x0, y0, x1, y1 = norm
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)

def find_overlay_for_page(
        overlays: Iterable[dict[str, Any]] | None,
        page_number: int | None,
) -> dict[str, Any] | None:
    if overlays is None or page_number is None:
        return None

    overlays_list = list(overlays)
    if not overlays_list:
        return None

    def _get_page(ov: dict[str, Any]) -> int | None:
        return normalize_page_number(
            ov.get("page_number", ov.get("page", ov.get("page_index")))
        )

    for ov in overlays_list:
        if _get_page(ov) == page_number:
            return ov

    for delta in (-1, 1):
        alt = page_number + delta
        for ov in overlays_list:
            if _get_page(ov) == alt:
                return ov

    return overlays_list[0]
