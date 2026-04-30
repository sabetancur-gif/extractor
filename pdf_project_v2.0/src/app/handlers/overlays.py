"""
src/app/handlers/overlays.py
------------------------------
Callbacks para overlays y crop de región en el tab de visualización.
El crop se hace sobre la imagen de la página (NO la imagen de overlay)
usando las coordenadas PDF escaladas correctamente a píxeles de imagen.
"""
from __future__ import annotations

import json
import os
from urllib.parse import quote

import dash
import dash_bootstrap_components as dbc
import flask
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from src.logs.logger import LogManager
from src.utils.bbox import find_overlay_for_page, normalize_bbox, normalize_page_number, row_bbox, row_page_number
from src.utils.crop import crop_page_region

OVERLAY_DIR = os.path.abspath("data/cache")
_log = LogManager()


def _to_int_page(v) -> int | None:
    try:
        return int(v) if v is not None else None
    except Exception:
        return None


def _path_to_url(path: str) -> str:
    if not path:
        return ""
    abs_p = os.path.abspath(path)
    if abs_p.startswith(OVERLAY_DIR):
        rel = os.path.relpath(abs_p, OVERLAY_DIR).replace(os.sep, "/")
        return f"/overlays/{quote(rel)}"
    return path


def register_callbacks_13(app, controller, embedder=None):

    # ── Ruta Flask para servir overlays ──────────────────────────────────────
    @app.server.route("/overlays/<path:filename>")
    def serve_overlay(filename):
        return flask.send_from_directory(OVERLAY_DIR, filename)

    # ── Crop al seleccionar fila en la tabla de análisis ─────────────────────
    @app.callback(
        Output("analysis-selection-preview", "children", allow_duplicate=True),
        Input("analysis-datatable", "active_cell"),
        Input("analysis-datatable", "selected_rows"),
        State("analysis-datatable", "derived_viewport_data"),
        State("analysis-datatable", "derived_virtual_data"),
        State("doc-context",        "data"),
        State("analysis-result-store", "data"),
        prevent_initial_call=True,
    )
    def preview_selected_row(
        active_cell, selected_rows,
        viewport_data, virtual_data,
        doc_ctx, result_store
    ):
        if not doc_ctx:
            raise PreventUpdate

        data = viewport_data or virtual_data or []
        if not data:
            raise PreventUpdate

        # Determinar índice de fila
        row_idx = None
        if active_cell and isinstance(active_cell, dict):
            row_idx = active_cell.get("row")
        elif selected_rows:
            row_idx = selected_rows[0]
        if row_idx is None or row_idx >= len(data):
            raise PreventUpdate

        row = data[row_idx]

        # Documento activo
        doc_id = (result_store or {}).get("doc_id")
        if not doc_id or not isinstance(doc_ctx, dict):
            raise PreventUpdate
        sel_ctx = doc_ctx.get(doc_id)
        if not isinstance(sel_ctx, dict):
            # Fallback al primer documento
            sel_ctx = next(iter(doc_ctx.values()), {})

        pages    = sel_ctx.get("pages", []) or []
        overlays = sel_ctx.get("overlays", []) or []

        # ── bbox ─────────────────────────────────────────────────────────────
        bbox = None
        raw  = row.get("bbox_raw")
        if raw:
            try:
                bbox = normalize_bbox(json.loads(raw))
            except Exception:
                pass
        if bbox is None:
            bbox = row_bbox(row)

        # ── page_number ───────────────────────────────────────────────────────
        page_number = _to_int_page(row_page_number(row))
        if page_number is None:
            try:
                page_number = int(row.get("page_number") or row.get("page") or 1)
            except Exception:
                page_number = 1

        # ── recuperar bbox desde doc_ctx si no está en la fila ───────────────
        if bbox is None:
            block_id = row.get("block_id") or ""
            text_val = (row.get("text") or row.get("value") or "").strip()[:60]
            for p in pages:
                pn = normalize_page_number(p.get("page_number"))
                if page_number and pn != page_number:
                    continue
                for b in (p.get("blocks") or []):
                    if block_id and b.get("block_id") == block_id:
                        bbox = normalize_bbox(b.get("bbox"))
                        page_number = pn
                        break
                    if text_val and (b.get("text") or "").strip()[:60] == text_val:
                        bbox = normalize_bbox(b.get("bbox"))
                        page_number = pn
                        break
                if bbox:
                    break

        # ── dimensiones de la página ──────────────────────────────────────────
        pdf_w, pdf_h = None, None
        for p in pages:
            if normalize_page_number(p.get("page_number")) == page_number:
                pdf_w = p.get("width")
                pdf_h = p.get("height")
                break

        # ── imagen base de la página (no el overlay, sino la imagen original) ─
        page_img_path = _find_page_image(sel_ctx, doc_id, page_number)

        # ── generar crop ──────────────────────────────────────────────────────
        crop_src = ""
        if page_img_path and bbox:
            crop_src = crop_page_region(
                page_img_path, bbox,
                pdf_width=pdf_w,
                pdf_height=pdf_h,
                padding=18,
            )

        # ── UI del preview ────────────────────────────────────────────────────
        title   = row.get("field") or row.get("semantic_type") or "Elemento"
        snippet = (row.get("value") or row.get("text") or "")[:300]

        crop_element = (
            html.Img(
                src=crop_src,
                style={
                    "maxWidth": "100%",
                    "maxHeight": "280px",
                    "borderRadius": "8px",
                    "border": "2px solid #E3530F",
                    "boxShadow": "0 4px 16px rgba(0,0,0,0.5)",
                },
            )
            if crop_src
            else dbc.Alert(
                [html.I(className="bi-crop me-2"),
                 "Crop no disponible. "
                 "El bloque puede ser una imagen o no tiene bbox válido."],
                color="secondary",
                className="small",
            )
        )

        return dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6(title, className="fw-bold", style={"color": "#E3530F"}),
                        html.Small(f"Página {page_number}", className="text-muted d-block mb-2"),
                        html.P(snippet, className="small mb-2", style={"color": "#ccc", "whiteSpace": "pre-wrap"}),
                        html.Hr(style={"borderColor": "#333"}),
                        html.Small("BBox (coords. PDF):", className="text-muted"),
                        html.Code(
                            str(bbox) if bbox else "sin bbox",
                            style={"fontSize": "0.72rem", "display": "block", "color": "#9cdcfe"},
                        ),
                    ], md=5),
                    dbc.Col(
                        html.Div(crop_element, style={"textAlign": "center"}),
                        md=7,
                    ),
                ]),
            ], style={"background": "#1a1a1a"}),
            className="border-0 shadow-sm mt-2",
            style={"border": "1px solid #333 !important"},
        )

    # ── Overlay en Visualization (sin cambios de lógica, solo usa URL) ────────
    @app.callback(
        [
            Output("pdf-overlay-img",   "src",      allow_duplicate=True),
            Output("pdf-overlay-layer", "children", allow_duplicate=True),
        ],
        Input("blocks-datatable", "active_cell"),
        State("blocks-datatable", "derived_viewport_data"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def show_block_preview(active_cell, viewport_data, doc_ctx):
        if not active_cell or not doc_ctx:
            raise PreventUpdate
        row_idx = active_cell.get("row")
        if row_idx is None or not isinstance(viewport_data, list) or row_idx >= len(viewport_data):
            raise PreventUpdate

        row      = viewport_data[row_idx]
        first_ctx = next(iter(doc_ctx.values()), {}) if isinstance(doc_ctx, dict) else {}
        overlays  = first_ctx.get("overlays") or []
        pages     = first_ctx.get("pages", []) or []

        page_num  = _to_int_page(row.get("page") or row.get("page_index"))

        # Buscar overlay para la página
        ov = find_overlay_for_page(overlays, page_num)
        img_src = _path_to_url((ov.get("path") or "") if ov else "")

        # bbox
        bbox = None
        for k in ("bbox", "rect", "bounds"):
            if row.get(k):
                bbox = normalize_bbox(row[k])
                break

        if not bbox:
            return (img_src or dash.no_update), []

        # Dimensiones de página
        pdf_w = pdf_h = None
        for p in pages:
            pn = normalize_page_number(p.get("page_number"))
            if pn == page_num:
                pdf_w, pdf_h = p.get("width"), p.get("height")
                break

        # Convertir bbox PDF a porcentajes
        x0, y0, x1, y1 = bbox
        def pct(v, dim): return (v / dim * 100) if dim else (v * 100 if v <= 1 else v / 10)

        rect_div = html.Div(
            className="pdf-rect-div",
            style={
                "left":   f"{pct(x0, pdf_w):.2f}%",
                "top":    f"{pct(y0, pdf_h):.2f}%",
                "width":  f"{pct(x1-x0, pdf_w):.2f}%",
                "height": f"{pct(y1-y0, pdf_h):.2f}%",
            },
        )
        return (img_src or dash.no_update), [rect_div]


def _find_page_image(ctx: dict, doc_id: str, page_number: int) -> str | None:
    """
    Busca la imagen base de la página (no el overlay).
    Prioriza: cache de imagen renderizada → fallback a la imagen del overlay.
    """
    from src.ingest.storage import StorageManager
    storage = StorageManager()

    # 1. Cache de imagen renderizada
    cache_path = storage.page_cache_path(doc_id, page_number)
    if os.path.exists(cache_path):
        return cache_path

    # 2. Imagen de la página desde los overlays (el overlay ya tiene la imagen base)
    for ov in (ctx.get("overlays") or []):
        if normalize_page_number(ov.get("page")) == page_number:
            p = ov.get("path") or ""
            if p and os.path.exists(p):
                return p

    # 3. Intentar renderizar desde el PDF
    file_path = ctx.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            from src.utils.image import render_page_to_image
            render_page_to_image(file_path, page_number, cache_path)
            if os.path.exists(cache_path):
                return cache_path
        except Exception:
            pass

    return None
