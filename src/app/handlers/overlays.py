# src/app/handlers/overlays.py
"""
Callbacks para overlays y preview de bloques en la visualización.
"""

# STDLIB
import os

# THIRDPARTY
import dash
from dash import Input, Output, State, html, ctx

from src.logs.logger import LogManager
from src.utils.crop import crop_page_region
from src.utils.bbox import row_bbox, row_page_number, find_overlay_for_page, normalize_page_number
import dash_bootstrap_components as dbc



def register_callbacks_13(app, controller, embedder=None):
    """
    Registra callbacks para overlays y preview de bloques en la visualización.
    Relacionado con IDs: pdf-overlay-img, pdf-overlay-layer, blocks-datatable, doc-context.
    """
    log_mgr = LogManager()

    # STDLIB
    from urllib.parse import quote

    # THIRDPARTY
    import flask

    # === Directorio base donde están las imágenes (ABSOLUTO) ===
    OVERLAY_DIR = os.path.abspath("data/cache")

    # === Ruta Flask para servir overlays ===
    # OJO: usar <path:filename> (no HTML escapado)
    @app.server.route("/overlays/<path:filename>")
    def serve_overlay(filename):
        # Seguridad mínima: solo sirve dentro de OVERLAY_DIR
        return flask.send_from_directory(OVERLAY_DIR, filename)

    @app.callback(
        Output("analysis-selection-preview", "children"),
        Input("analysis-datatable", "active_cell"),
        State("analysis-datatable", "derived_viewport_data"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def preview_selected_row(active_cell, view_data, doc_ctx):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        if not active_cell or not view_data:
            raise dash.exceptions.PreventUpdate

        row_idx = active_cell.get("row")
        if row_idx is None or row_idx >= len(view_data):
            raise dash.exceptions.PreventUpdate

        row = view_data[row_idx]
        bbox = row_bbox(row)
        page_number = row_page_number(row)

        def _recover_bbox_from_doc_context():
            block_id = row.get("block_id")
            text = (row.get("text") or row.get("value") or row.get("field_value") or "").strip()

            pages = doc_ctx.get("pages", []) or []
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

        overlays = doc_ctx.get("overlays", []) or []
        overlay = find_overlay_for_page(overlays, page_number)

        page_image = ""
        if overlay:
            page_image = overlay.get("path") or overlay.get("image") or ""

        crop_src = crop_page_region(page_image, bbox) if page_image and bbox else ""

        title = row.get("field") or row.get("semantic_type") or row.get("block_type") or "Selected item"

        details = dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.H5(title, className="mb-1"),
                            html.Div(f"Page: {page_number}", className="text-muted"),
                            html.Div(
                                row.get("text", "")[:500]
                                or row.get("value", "")[:500]
                                or row.get("field_value", "")[:500],
                                className="mt-2",
                            ),
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

        return details
    # @app.callback(
    #     Output("analysis-selection-preview", "children"),
    #     Input("analysis-fields-datatable", "active_cell"),
    #     Input("analysis-blocks-datatable", "active_cell"),
    #     State("analysis-fields-datatable", "derived_viewport_data"),
    #     State("analysis-blocks-datatable", "derived_viewport_data"),
    #     State("doc-context", "data"),
    #     prevent_initial_call=True,
    # )
    # def preview_selected_row(active_field, active_block, fields_view, blocks_view, doc_ctx):
    #     if not doc_ctx:
    #         raise dash.exceptions.PreventUpdate

    #     triggered = ctx.triggered_id
    #     if triggered == "analysis-fields-datatable":
    #         active_cell = active_field
    #         view_data = fields_view or []
    #     elif triggered == "analysis-blocks-datatable":
    #         active_cell = active_block
    #         view_data = blocks_view or []
    #     else:
    #         raise dash.exceptions.PreventUpdate

    #     if not active_cell or not view_data:
    #         raise dash.exceptions.PreventUpdate

    #     row_idx = active_cell.get("row")
    #     if row_idx is None or row_idx >= len(view_data):
    #         raise dash.exceptions.PreventUpdate

    #     row = view_data[row_idx]

    #     bbox = row.get("bbox")
    #     page_number = row.get("page_number")

    #     # Busca la página/overlay correspondiente
    #     overlays = doc_ctx.get("overlays", []) or []
    #     page_image = ""
    #     for ov in overlays:
    #         ov_page = ov.get("page_number", ov.get("page_index"))
    #         if str(ov_page) == str(page_number):
    #             page_image = ov.get("path") or ov.get("image") or ""
    #             break

    #     print("[DEBUG preview_selected_row]")
    #     print(f"  page_number: {page_number}")
    #     print(f"  bbox: {bbox}")
    #     print(f"  page_image: {page_image}")

    #     crop_src = crop_page_region(page_image, bbox) if page_image and bbox else ""

    #     return dbc.Card(
    #         dbc.CardBody(
    #             [
    #                 html.H6("Selected item preview"),
    #                 html.Div(f"Page: {page_number}"),
    #                 html.Div(f"Text: {row.get('text', '')[:300]}"),
    #                 html.Hr(),
    #                 html.Img(
    #                     src=crop_src,
    #                     style={"width": "100%", "height": "auto", "borderRadius": "8px"},
    #                 ) if crop_src else html.Div("No crop available.", className="text-muted"),
    #             ]
    #         ),
    #         className="shadow-sm",
    #     )

    # === Callback: dibujar rect y cambiar página según fila seleccionada ===
    @app.callback(
        Output("pdf-overlay-img", "src"),
        Output("pdf-overlay-layer", "children"),
        # Si quieres escuchar SOLO a la tabla principal de Bloques:
        Input("blocks-datatable", "active_cell"),
        State("blocks-datatable", "derived_viewport_data"),
        State("doc-context", "data"),
        prevent_initial_call=True
    )
    def show_block_preview(active_cell, viewport_data, doc_ctx):
        # log_mgr.log({
        #     "timestamp": __import__('datetime').datetime.now().iso8601(),
        #     "file_id": doc_ctx.get("doc_id") if doc_ctx else None,
        #     "filename": doc_ctx.get("file_name") if doc_ctx else None,
        #     "step": "BLOCK_PREVIEW",
        #     "page_number": None,
        #     "pages_total": doc_ctx.get("pages_total") if doc_ctx else None,
        #     "worker_id": __import__('threading').get_ident(),
        #     "status": "info",
        #     "duration_seconds": None,
        #     "avg_sec_per_page": None,
        #     "concurrency_count": None,
        #     "match_query": None,
        #     "context_snippet": f"active_cell={active_cell}",
        #     "error_message": None
        # })

        if not active_cell or not doc_ctx:
            raise dash.exceptions.PreventUpdate

        # Obtén la fila activa
        row_idx = active_cell.get("row")
        if row_idx is None or not isinstance(viewport_data, list) or row_idx >= len(viewport_data):
            raise dash.exceptions.PreventUpdate

        row = viewport_data[row_idx]

        # ========== Selección de página ==========
        overlays = doc_ctx.get("overlays") or []
        img_src = ""

        # 1) Normaliza el número de página que viene del bloque
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

        # 2) Helper para normalizar ints en overlays
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

        # 3) Intenta encontrar el overlay por página (soporta 0/1-based y tipos)
        def try_find_overlay(_overlays, target_page):
            if target_page is None:
                return None

            # a) Match directo
            for ov in _overlays:
                op = norm_page_val(ov.get("page"))
                opi = norm_page_val(ov.get("page_index"))  # <-- FIX: get, no "ger"
                if op == target_page or opi == target_page:
                    return ov

            # b) Prueba ±1 por desface 0/1-based
            for delta in (-1, 1):
                alt = target_page + delta
                for ov in _overlays:
                    op = norm_page_val(ov.get("page"))
                    opi = norm_page_val(ov.get("page_index"))
                    if op == alt or opi == alt:
                        return ov

            return None

        ov = try_find_overlay(overlays, page_num)
        if ov is None and overlays:
            # Último recurso: índice directo si parece válido, si no primera página
            if page_num is not None and 0 <= page_num < len(overlays):
                ov = overlays[page_num]
            else:
                ov = overlays[0]

        img_src_path = (ov.get("path") or ov.get("image") or "") if ov else ""

        # ========== Convertir path local a URL servida ==========
        def make_overlay_url(path: str) -> str:
            if not path:
                return ""

            # 0) Si ya es URL servida, úsala tal cual
            if isinstance(path, str) and (path.startswith("/overlays/") or path.startswith("/assets/") or path.startswith("http://") or path.startswith("https://")):
                return path

            # 1) Intenta resolver absoluto y verificar que esté bajo OVERLAY_DIR
            abs_path = os.path.abspath(path)
            base = os.path.abspath(OVERLAY_DIR)

            # 2) Si la ruta cae bajo OVERLAY_DIR, mapea a /overlays/<rel>
            #    (ej: base/UUID/overlay_p1.png -> /overlays/UUID/overlay_p1.png)
            try:
                if abs_path.startswith(base):
                    rel = os.path.relpath(abs_path, base).replace(os.sep, "/")
                    return f"/overlays/{quote(rel)}"
            except Exception:
                pass

            # 3) Como fallback: si el archivo existe dentro de base aunque venga con otra forma, intenta re-ubicarlo
            #    (útil si guardas solo el nombre relativo tipo "UUID/overlay_p1.png")
            rel_guess = path.replace("\\", "/")
            rel_guess = rel_guess.lstrip("./").lstrip("/")
            candidate = os.path.join(base, rel_guess)
            if os.path.exists(candidate):
                rel = os.path.relpath(candidate, base).replace(os.sep, "/")
                return f"/overlays/{quote(rel)}"

            # 4) Último recurso: devuelve el original (dejará la imagen igual si no es válido)
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

        # Si no hay bbox, actualiza imagen y limpia capas
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
        pages_info = doc_ctx.get("pages", [])
        if page_num is not None and isinstance(pages_info, list):
            p = next((p for p in pages_info if p.get("page_index") == page_num or p.get("page") == page_num), None)
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
            left_pct = to_pct(x0, page_w)
            top_pct = to_pct(y0, page_h)
            width_pct = to_pct(x1 - x0, page_w)
            height_pct = to_pct(y1 - y0, page_h)
        else:
            left_pct = x0 * 100.0 if x0 <= 1 else (x0 / 1000.0) * 100.0
            top_pct = y0 * 100.0 if y0 <= 1 else (y0 / 1000.0) * 100.0
            width_pct = (x1 - x0) * 100.0 if (x1 - x0) <= 1 else ((x1 - x0) / 1000.0) * 100.0
            height_pct = (y1 - y0) * 100.0 if (y1 - y0) <= 1 else ((y1 - y0) / 1000.0) * 100.0

        style_rect = {
            "left": f"{left_pct}%",
            "top": f"{top_pct}%",
            "width": f"{width_pct}%",
            "height": f"{height_pct}%",
        }

        typ = row.get("block_type") or row.get("type")
        label = html.Div(typ, className="pdf-rect-label") if typ else None

        rect_div = html.Div(children=[label] if label else [], className="pdf-rect-div", style=style_rect)

        return (img_src or dash.no_update), [rect_div]

# """
# src/app/handlers/overlays.py
# ----------------------------
# Callbacks para overlays y preview de bloques en la visualización.
# """

# # STDLIB
# import os

# # THIRDPARTY
# import dash
# from dash import Input, Output, State, html

# from src.logs.logger import LogManager


# def register_callbacks_13(app, controller, embedder=None):
#     """
#     Registra callbacks para overlays y preview de bloques en la visualización.
#     Relacionado con IDs: pdf-overlay-img, pdf-overlay-layer, blocks-datatable, doc-context.
#     """
#     log_mgr = LogManager()

#     # STDLIB
#     from urllib.parse import quote

#     # THIRDPARTY
#     import flask

#     # --- Ajusta esto a la carpeta real donde están las imágenes (ruta ABSOLUTA) ---
#     # Windows example:
#     # OVERLAY_DIR = r"C:\Users\USER\Downloads\pdf-main\data\cache"
#     # Linux example:
#     # OVERLAY_DIR = "/home/user/pdf-main/data/cache"
#     OVERLAY_DIR = os.path.abspath("data/cache")  # o pon la ruta absoluta aquí

#     # Flask route para servir overlays
#     @app.server.route("/overlays/<path:filename>")
#     def serve_overlay(filename):
#         # seguridad mínima: no permitir subir directorios fuera de OVERLAY_DIR
#         return flask.send_from_directory(OVERLAY_DIR, filename)

#     # Callback corregido
#     @app.callback(
#         Output("pdf-overlay-img", "src"),
#         Output("pdf-overlay-layer", "children"),
#         Input("blocks-datatable", "active_cell"),
#         State("blocks-datatable", "data"),
#         State("doc-context", "data"),
#         prevent_initial_call=True
#     )
#     def show_block_preview(active_cell, table_data, doc_ctx):
#         log_mgr.log({
#             "timestamp": __import__('datetime').datetime.now().isoformat(),
#             "file_id": doc_ctx.get("doc_id") if doc_ctx else None,
#             "filename": doc_ctx.get("file_name") if doc_ctx else None,
#             "step": "BLOCK_PREVIEW",
#             "page_number": None,
#             "pages_total": doc_ctx.get("pages_total") if doc_ctx else None,
#             "worker_id": __import__('threading').get_ident(),
#             "status": "info",
#             "duration_seconds": None,
#             "avg_sec_per_page": None,
#             "concurrency_count": None,
#             "match_query": None,
#             "context_snippet": f"active_cell={active_cell}",
#             "error_message": None
#         })
#         if not active_cell or not doc_ctx:
#             raise dash.exceptions.PreventUpdate

#         row_idx = active_cell["row"]

#         try:
#             row = table_data[row_idx]
#         except Exception:
#             raise dash.exceptions.PreventUpdate

#         # --- encontrar la imagen de la página en doc_ctx.overlays ---
#         img_src = ""
#         overlays = doc_ctx.get("overlays") or []
#         raw_page = row.get("page", row.get("page_index", None))
#         page_num = None

#         if raw_page is not None:
#             try:
#                 page_num = int(raw_page)
#             except (ValueError, TypeError):
#                 try:
#                     page_num = int(float(str(raw_page).strip()))
#                 except Exception:
#                     page_num = None

#         def norm_page_val(v):
#             if v is None:
#                 return None
#             try:
#                 return int(v)
#             except (ValueError, TypeError):
#                 try:
#                     return int(float(str(v).strip()))
#                 except Exception:
#                     return None

#         def try_find_overlay(overlays, target_page):
#             if target_page is None:
#                 return None
#             for ov in overlays:
#                 op = norm_page_val(ov.get("page"))
#                 opi = norm_page_val(ov.ger("page_index"))
#                 if op == target_page or opi == target_page:
#                     return ov

#             for delta in (-1, 1):
#                 alt = target_page + delta
#                 for ov in overlays:
#                     op = norm_page_val(ov.get("page"))
#                     opi = norm_page_val(ov.get("page_index"))
#                     if op == alt or opi == alt:
#                         return ov
#             return None
#         ov = try_find_overlay(overlays, page_num)
#         if ov is None and overlays:
#             if page_num is not None and 0 <= page_num < len(overlays):
#                 ov = overlays[page_num]
#             else:
#                 ov = overlays[0]

#         img_src = (ov.get("path") or ov.get("image") or "") if ov else ""

#         # Si img_src es una ruta local (ej. "data/cache/overlay_p1.png" o "C:\\...\\overlay.png"),
#         # convertir a URL servido por Flask: /overlays/<filename>
#         def make_overlay_url(path):
#             if not path:
#                 return ""

#             path = os.path.abspath(path)
#             base = os.path.abspath(OVERLAY_DIR)

#             if not path.startswith(base):
#                 return ""

#             rel = os.path.relpath(path, base)  # UUID/overlays/overlay_p1.png
#             rel = rel.replace(os.sep, "/")

#             return f"/overlays/{quote(rel)}"

#         img_src = make_overlay_url(img_src)

#         # --- extraer bbox (soportar formas comunes) ---
#         bbox = None
#         for key in ("bbox", "rect", "bounds", "bbox_normalized"):
#             if row.get(key):
#                 bbox = row.get(key)
#                 break
#         if not bbox:
#             if all(k in row for k in ("x", "y", "w", "h")):
#                 bbox = [row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"]]
#             elif all(k in row for k in ("left", "top", "right", "bottom")):
#                 bbox = [row["left"], row["top"], row["right"], row["bottom"]]

#         if not bbox:
#             # no bbox -> solo actualizar imagen (sin rects)
#             return img_src or dash.no_update, []

#         # --- normalizar bbox a x0,y0,x1,y1 floats ---
#         try:
#             if isinstance(bbox, dict):
#                 x0 = float(bbox.get("x0") or bbox.get("left") or bbox.get("x") or 0)
#                 y0 = float(bbox.get("y0") or bbox.get("top") or bbox.get("y") or 0)
#                 x1 = float(bbox.get("x1") or bbox.get("right") or (bbox.get("x", 0) + bbox.get("w", 0)))
#                 y1 = float(bbox.get("y1") or bbox.get("bottom") or (bbox.get("y", 0) + bbox.get("h", 0)))
#             else:
#                 coords = [float(v) for v in bbox]
#                 if len(coords) >= 4:
#                     x0, y0, x1, y1 = coords[:4]
#                 elif len(coords) == 2:
#                     x0, y0, x1, y1 = 0.0, 0.0, coords[0], coords[1]
#                 else:
#                     return img_src or dash.no_update, []
#         except Exception:
#             return img_src or dash.no_update, []

#         # --- intentar usar dimensiones de página (si existen) ---
#         page_w = None
#         page_h = None
#         pages_info = doc_ctx.get("pages", [])
#         if page_num is not None and isinstance(pages_info, list):
#             p = next((p for p in pages_info if p.get("page_index") == page_num or p.get("page") == page_num), None)
#             if p:
#                 page_w = p.get("width")
#                 page_h = p.get("height")

#         def to_pct(val, dim):
#             if dim and dim > 0:
#                 return (val / dim) * 100.0
#             if val <= 1.0:
#                 return val * 100.0
#             return max(0.0, min(100.0, (val / 1000.0) * 100.0))

#         if page_w and page_h:
#             left_pct = to_pct(x0, page_w)
#             top_pct = to_pct(y0, page_h)
#             width_pct = to_pct(x1 - x0, page_w)
#             height_pct = to_pct(y1 - y0, page_h)
#         else:
#             left_pct = x0 * 100.0 if x0 <= 1 else (x0 / 1000.0) * 100.0
#             top_pct = y0 * 100.0 if y0 <= 1 else (y0 / 1000.0) * 100.0
#             width_pct = (x1 - x0) * 100.0 if (x1 - x0) <= 1 else ((x1 - x0) / 1000.0) * 100.0
#             height_pct = (y1 - y0) * 100.0 if (y1 - y0) <= 1 else ((y1 - y0) / 1000.0) * 100.0

#         style_rect = {
#             "left": f"{left_pct}%",
#             "top": f"{top_pct}%",
#             "width": f"{width_pct}%",
#             "height": f"{height_pct}%",
#         }

#         typ = row.get("block_type") or row.get("type") or None
#         label = html.Div(typ, className="pdf-rect-label") if typ else None

#         rect_div = html.Div(children=[label] if label else [], className="pdf-rect-div", style={**style_rect})

#         return img_src or dash.no_update, [rect_div]