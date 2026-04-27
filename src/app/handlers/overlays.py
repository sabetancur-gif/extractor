# src/app/handlers/overlays.py
"""
Callbacks para overlays y preview de bloques en la visualización.
"""
# STDLIB
import os
# THIRDPARTY
import dash
from dash import Input, Output, State, html
import json
from src.logs.logger import LogManager
from src.utils.crop import crop_page_region
from src.utils.bbox import row_bbox, row_page_number, find_overlay_for_page, normalize_page_number
import dash_bootstrap_components as dbc


def _overlay_image_path(overlay):
    if not overlay:
        return ""
    for key in ("path", "image", "img", "file", "src", "url"):
        value = overlay.get(key)
        if value:
            return value
    return ""


def _to_init_page(value):
    try:
        return int(value) if value is not None else None
    except Exception:
        return None


def register_callbacks_13(app, controller, embedder=None):
    """Registra callbacks para overlays y preview de bloques en la visualización.
    Relacionado con IDs: pdf-overlay-img, pdf-overlay-layer, blocks-datatable, doc-context.
    """
    log_mgr = LogManager()  # noqa: F841
    # STDLIB
    from urllib.parse import quote
    # THIRDPARTY
    import flask

    # === Directorio base donde están las imágenes (ABSOLUTO) ===
    OVERLAY_DIR = os.path.abspath("data/cache")

    # === Ruta Flask para servir overlays ===
    @app.server.route("/overlays/<path:filename>")
    def serve_overlay(filename):
        return flask.send_from_directory(OVERLAY_DIR, filename)

    @app.callback(
        Output("analysis-selection-preview", "children"),
        Input("analysis-datatable", "active_cell"),
        Input("analysis-datatable", "selected_rows"),
        State("analysis-datatable", "derived_viewport_data"),
        State("analysis-datatable", "derived_virtual_data"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def preview_selected_row(active_cell, selected_rows, viewport_data, virtual_data, doc_ctx):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        view_data = viewport_data or virtual_data or []
        if not view_data:
            raise dash.exceptions.PreventUpdate

        row_idx = None
        if active_cell and isinstance(active_cell, dict):
            row_idx = active_cell.get("row")
        elif selected_rows:
            row_idx = selected_rows[0]
        if row_idx is None:
            raise dash.exceptions.PreventUpdate

        if row_idx < 0 or row_idx >= len(view_data):
            if selected_rows and virtual_data and 0 <= row_idx < len(virtual_data):
                view_data = virtual_data
            else:
                raise dash.exceptions.PreventUpdate

        row = view_data[row_idx]

        # ✅ Extraer el ctx del documento activo (multi-doc)
        first_ctx = next(iter(doc_ctx.values()), {}) if isinstance(doc_ctx, dict) else {}
        # Si hay un active_doc_id disponible (pasarlo como State), usarlo:
        # active_ctx = doc_ctx.get(active_doc_id, first_ctx)
        active_ctx = first_ctx
        overlays = active_ctx.get("overlays", []) or []
        pages    = active_ctx.get("pages", []) or []

        # --- bbox ---
        bbox_raw = row.get("bbox_raw")
        if isinstance(bbox_raw, str):
            try:
                bbox = json.loads(bbox_raw)
            except Exception:
                bbox = None
        else:
            bbox = bbox_raw
        bbox = bbox or row_bbox(row)

        page_number = _to_init_page(row_page_number(row))

        def _recover_bbox_from_doc_context():
            block_id = row.get("block_id") or row.get("id")
            text = (row.get("text") or row.get("value") or row.get("field_value") or "").strip()
            for page in pages:
                current_page_number = normalize_page_number(page.get("page_number"))
                if page_number is not None and current_page_number != page_number:
                    continue
                for block in page.get("blocks", []) or []:
                    if block_id and block.get("block_id") == block_id:
                        return row_bbox(block), current_page_number
                    if text and (block.get("text") or "").strip() == text:
                        return row_bbox(block), current_page_number
            return None, page_number

        if bbox is None:
            bbox, page_number = _recover_bbox_from_doc_context()
            page_number = _to_init_page(page_number)

        overlay = find_overlay_for_page(overlays, page_number)
        if not overlay and page_number is not None:
            candidates = {page_number, page_number - 1, page_number + 1}
            for ov in overlays:
                ov_page = _to_init_page(
                    ov.get("page_number") or ov.get("page") or ov.get("page_index")
                )
                if ov_page in candidates:
                    overlay = ov
                    break

        page_image = _overlay_image_path(overlay)
        crop_src = crop_page_region(page_image, bbox) if page_image and bbox else ""

        title = (
            row.get("field") or
            row.get("semantic_type") or
            row.get("block_type") or
            row.get("kind") or
            "Selected item"
        )
        snippet = (
            row.get("text", "") or
            row.get("value", "") or
            row.get("field_value", "") or
            ""
        )

        details = dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.H5(title, className="mb-1"),
                            html.Div(f"Page: {page_number}", className="text-muted"),
                            html.Div(snippet[:500], className="mt-2"),
                        ]
                    ),
                    html.Hr(),
                    html.Div(
                        [
                            html.Small("BBox", className="text-muted d-block"),
                            html.Code(str(bbox) if bbox else "bbox unavailable"),
                        ]
                    ),
                    html.Div(
                        [
                            html.Small("Source", className="text-muted d-block mt-2"),
                            html.Code(str(row.get("source", "unknown"))),
                        ]
                    ),
                    html.Hr(),
                    html.Div(
                        html.Img(
                            src=crop_src,
                            style={"width": "100%", "height": "auto", "borderRadius": "12px"},
                        )
                        if crop_src
                        else html.Div(
                            [
                                html.Div("No crop available.", className="fw-semibold"),
                                html.Div(
                                    "The row did not include a usable bbox or the page image was not found.",
                                    className="text-muted small",
                                ),
                            ],
                            className="text-center py-4",
                        )
                    ),
                ]
            ),
            className="shadow-sm border-0 analysis-preview-card",
        )

        print("ROW PAGE:", page_number)
        print("BBOX:", bbox)
        print("OVERLAY FOUND:", bool(overlay))
        print("PAGE IMAGE:", page_image)
        print("OVERLAY KEYS:", list(overlay.keys()) if overlay else [])

        return details

    # === Callback: dibujar rect y cambiar página según fila seleccionada ===
    @app.callback(
        Output("pdf-overlay-img", "src"),
        Output("pdf-overlay-layer", "children"),
        Input("blocks-datatable", "active_cell"),
        State("blocks-datatable", "derived_viewport_data"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def show_block_preview(active_cell, viewport_data, doc_ctx):
        if not active_cell or not doc_ctx:
            raise dash.exceptions.PreventUpdate

        row_idx = active_cell.get("row")
        if row_idx is None or not isinstance(viewport_data, list) or row_idx >= len(viewport_data):
            raise dash.exceptions.PreventUpdate

        row = viewport_data[row_idx]

        # ✅ Extraer el ctx del documento activo (multi-doc)
        first_ctx  = next(iter(doc_ctx.values()), {}) if isinstance(doc_ctx, dict) else {}
        overlays   = first_ctx.get("overlays") or []
        pages_info = first_ctx.get("pages", [])

        # ========== Selección de página ==========
        raw_page = row.get("page", row.get("page_index"))
        page_num = None
        if raw_page is not None:
            try:
                page_num = int(raw_page)
            except (ValueError, TypeError):
                try:
                    page_num = int(float(str(raw_page).strip()))
                except Exception:
                    page_num = None

        def norm_page_val(v):
            if v is None:
                return None
            try:
                return int(v)
            except (ValueError, TypeError):
                try:
                    return int(float(str(v).strip()))
                except Exception:
                    return None

        def try_find_overlay(_overlays, target_page):
            if target_page is None:
                return None
            for ov in _overlays:
                op  = norm_page_val(ov.get("page"))
                opi = norm_page_val(ov.get("page_index"))
                if op == target_page or opi == target_page:
                    return ov
            for delta in (-1, 1):
                alt = target_page + delta
                for ov in _overlays:
                    op  = norm_page_val(ov.get("page"))
                    opi = norm_page_val(ov.get("page_index"))
                    if op == alt or opi == alt:
                        return ov
            return None

        ov = try_find_overlay(overlays, page_num)
        if ov is None and overlays:
            if page_num is not None and 0 <= page_num < len(overlays):
                ov = overlays[page_num]
            else:
                ov = overlays[0]

        img_src_path = (ov.get("path") or ov.get("image") or "") if ov else ""

        # ========== Convertir path local a URL servida ==========
        def make_overlay_url(path: str) -> str:
            if not path:
                return ""
            if isinstance(path, str) and (
                path.startswith("/overlays/")
                or path.startswith("/assets/")
                or path.startswith("http://")
                or path.startswith("https://")
            ):
                return path
            abs_path = os.path.abspath(path)
            base = os.path.abspath(OVERLAY_DIR)
            try:
                if abs_path.startswith(base):
                    rel = os.path.relpath(abs_path, base).replace(os.sep, "/")
                    return f"/overlays/{quote(rel)}"
            except Exception:
                pass
            rel_guess = path.replace("\\", "/").lstrip("./").lstrip("/")
            candidate = os.path.join(base, rel_guess)
            if os.path.exists(candidate):
                rel = os.path.relpath(candidate, base).replace(os.sep, "/")
                return f"/overlays/{quote(rel)}"
            return path

        img_src = make_overlay_url(img_src_path)

        # ========== Extraer bbox ==========
        bbox = None
        for key in ("bbox", "rect", "bounds", "bbox_normalized"):
            if row.get(key):
                bbox = row.get(key)
                break
        if not bbox:
            if all(k in row for k in ("x", "y", "w", "h")):
                bbox = [row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"]]
            elif all(k in row for k in ("left", "top", "right", "bottom")):
                bbox = [row["left"], row["top"], row["right"], row["bottom"]]

        if not bbox:
            return (img_src or dash.no_update), []

        # ========== Normalizar bbox ==========
        try:
            if isinstance(bbox, dict):
                x0 = float(bbox.get("x0") or bbox.get("left") or bbox.get("x") or 0)
                y0 = float(bbox.get("y0") or bbox.get("top") or bbox.get("y") or 0)
                x1 = float(bbox.get("x1") or bbox.get("right") or (bbox.get("x", 0) + bbox.get("w", 0)))
                y1 = float(bbox.get("y1") or bbox.get("bottom") or (bbox.get("y", 0) + bbox.get("h", 0)))
            else:
                coords = [float(v) for v in bbox]
                if len(coords) >= 4:
                    x0, y0, x1, y1 = coords[:4]
                elif len(coords) == 2:
                    x0, y0, x1, y1 = 0.0, 0.0, coords[0], coords[1]
                else:
                    return (img_src or dash.no_update), []
        except Exception:
            return (img_src or dash.no_update), []

        # ========== Dimensiones de página ==========
        page_w = None
        page_h = None
        if page_num is not None and isinstance(pages_info, list):
            p = next(
                (p for p in pages_info if p.get("page_index") == page_num or p.get("page") == page_num),
                None,
            )
            if p:
                page_w = p.get("width")
                page_h = p.get("height")

        def to_pct(val, dim):
            if dim and dim > 0:
                return (val / dim) * 100.0
            if val <= 1.0:
                return val * 100.0
            return max(0.0, min(100.0, (val / 1000.0) * 100.0))

        if page_w and page_h:
            left_pct   = to_pct(x0,       page_w)
            top_pct    = to_pct(y0,       page_h)
            width_pct  = to_pct(x1 - x0, page_w)
            height_pct = to_pct(y1 - y0, page_h)
        else:
            left_pct   = x0       * 100.0 if x0       <= 1 else (x0       / 1000.0) * 100.0
            top_pct    = y0       * 100.0 if y0       <= 1 else (y0       / 1000.0) * 100.0
            width_pct  = (x1-x0) * 100.0 if (x1-x0) <= 1 else ((x1-x0) / 1000.0) * 100.0
            height_pct = (y1-y0) * 100.0 if (y1-y0) <= 1 else ((y1-y0) / 1000.0) * 100.0

        style_rect = {
            "left":   f"{left_pct}%",
            "top":    f"{top_pct}%",
            "width":  f"{width_pct}%",
            "height": f"{height_pct}%",
        }

        typ = row.get("block_type") or row.get("type")
        label = html.Div(typ, className="pdf-rect-label") if typ else None
        rect_div = html.Div(children=[label] if label else [], className="pdf-rect-div", style=style_rect)

        return (img_src or dash.no_update), [rect_div]