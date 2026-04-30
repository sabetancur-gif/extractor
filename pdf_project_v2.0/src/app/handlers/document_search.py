"""
src/app/handlers/document_search.py
-------------------------------------
Callbacks para PDF Analysis:
- Búsqueda por palabra clave + filtro por tipo semántico.
- Tabla de resultados limpia (sin JSON crudo).
- Crop correcto de la región seleccionada en el PDF.
- Vistas: Campos, Bloques, Tablas, Firmas, Imágenes, Fechas, Montos, Direcciones.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, ctx, dash_table, html
from dash.exceptions import PreventUpdate

from src.search.universal_search import search_document
from src.utils.bbox import normalize_bbox, row_bbox, row_page_number
from src.utils.crop import crop_page_region
from src.ingest.storage import StorageManager
from src.utils.image import render_page_to_image

# ── Orden y metadatos de vistas ───────────────────────────────────────────────

ANALYSIS_VIEW_ORDER = [
    "fields", "blocks", "tables", "signatures",
    "assets", "dates", "amounts", "addresses",
]

ANALYSIS_VIEW_META = {
    "fields":     {"label": "📋 Campos",          "icon": "bi-card-text"},
    "blocks":     {"label": "📄 Bloques",          "icon": "bi-layers"},
    "tables":     {"label": "📊 Tablas",           "icon": "bi-table"},
    "signatures": {"label": "✍️  Firmas",          "icon": "bi-pen"},
    "assets":     {"label": "🖼️  Imágenes & Logos", "icon": "bi-image"},
    "dates":      {"label": "📅 Fechas",           "icon": "bi-calendar3"},
    "amounts":    {"label": "💰 Montos",           "icon": "bi-currency-dollar"},
    "addresses":  {"label": "🏠 Direcciones",      "icon": "bi-geo-alt"},
}


def _current_view_key(view_state: dict | None) -> str:
    if not isinstance(view_state, dict):
        return "fields"
    key = view_state.get("key")
    if key in ANALYSIS_VIEW_META:
        return key
    idx = view_state.get("index", 0)
    try:
        return ANALYSIS_VIEW_ORDER[int(idx) % len(ANALYSIS_VIEW_ORDER)]
    except Exception:
        return "fields"


def _safe_val(v):
    """Serializa valores no-string para mostrar en la tabla sin exponer JSON crudo."""
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)[:120]
    return str(v)


def _build_rows(doc_ctx: dict, matches: list, view_key: str) -> list[dict]:
    """Construye las filas de la tabla según la vista activa."""
    blocks = doc_ctx.get("classified_blocks", []) or []

    def _clean(block: dict) -> dict:
        """Fila limpia para la tabla, sin JSON interno."""
        bbox = block.get("bbox")
        return {
            "text":          (block.get("text") or "")[:200],
            "semantic_type": block.get("semantic_type") or block.get("block_type") or "",
            "page_number":   block.get("page_number") or block.get("page") or "",
            "confidence":    _fmt_conf(block.get("semantic_confidence") or block.get("confidence")),
            "source":        block.get("source") or "",
            "block_id":      block.get("block_id") or "",
            "bbox_raw":      json.dumps(bbox) if bbox else "",
        }

    def _by(predicate):
        return [_clean(b) for b in blocks if predicate(b)]

    if view_key == "fields":
        rows = []
        for item in matches:
            if item.get("kind") != "field":
                continue
            bbox = item.get("bbox")
            rows.append({
                "field":         item.get("field") or "",
                "value":         _safe_val(item.get("value")),
                "page_number":   item.get("page_number") or item.get("page") or "",
                "confidence":    _fmt_conf(item.get("confidence") or item.get("score")),
                "semantic_type": item.get("semantic_type") or "",
                "source":        item.get("source") if isinstance(item.get("source"), str) else "extracted",
                "block_id":      item.get("block_id") or "",
                "bbox_raw":      json.dumps(bbox) if bbox else "",
            })
        return rows

    if view_key == "blocks":
        rows = []
        for item in matches:
            if item.get("kind") != "block":
                continue
            rows.append(_clean({**item, "source": item.get("source") if isinstance(item.get("source"), str) else ""}))
        return rows

    # Vistas semánticas filtradas
    predicates = {
        "tables":     lambda b: b.get("semantic_type") in ("table",) or b.get("is_table_like"),
        "signatures": lambda b: b.get("semantic_type") == "signature" or b.get("is_signature"),
        "assets":     lambda b: b.get("semantic_type") in ("figure", "image", "logo", "stamp") or b.get("is_image") or b.get("is_logo"),
        "dates":      lambda b: b.get("semantic_type") == "date" or b.get("is_date"),
        "amounts":    lambda b: b.get("semantic_type") == "amount" or b.get("is_amount"),
        "addresses":  lambda b: b.get("semantic_type") == "address" or b.get("is_address"),
    }
    pred = predicates.get(view_key)
    return _by(pred) if pred else []


def _fmt_conf(v) -> str:
    if v is None:
        return ""
    try:
        f = float(v)
        if f <= 1.0:
            return f"{f * 100:.0f}%"
        return f"{f:.0f}%"
    except Exception:
        return str(v)


def _cols_for_view(view_key: str) -> list[dict]:
    if view_key == "fields":
        return [
            {"name": "Campo",     "id": "field"},
            {"name": "Valor",     "id": "value"},
            {"name": "Página",    "id": "page_number"},
            {"name": "Confianza", "id": "confidence"},
            {"name": "Tipo",      "id": "semantic_type"},
        ]
    return [
        {"name": "Tipo",      "id": "semantic_type"},
        {"name": "Texto",     "id": "text"},
        {"name": "Página",    "id": "page_number"},
        {"name": "Confianza", "id": "confidence"},
    ]


def _hidden_cols() -> list[dict]:
    return [
        {"name": "block_id", "id": "block_id"},
        {"name": "bbox_raw", "id": "bbox_raw"},
        {"name": "source",   "id": "source"},
    ]


# ── Storage helper ────────────────────────────────────────────────────────────

_storage = StorageManager()

OVERLAY_DIR = os.path.abspath("data/cache")


def _overlay_url(path: str) -> str:
    from urllib.parse import quote
    if not path:
        return ""
    abs_p = os.path.abspath(path)
    if abs_p.startswith(OVERLAY_DIR):
        rel = os.path.relpath(abs_p, OVERLAY_DIR).replace(os.sep, "/")
        return f"/overlays/{quote(rel)}"
    return path


# ── Callbacks ─────────────────────────────────────────────────────────────────

def register_callbacks_03(app, *_args, **_kwargs):

    # ── poblar dropdown de documentos en PDF Analysis ─────────────────────────
    @app.callback(
        [Output("analysis-target", "options", allow_duplicate=True),
         Output("analysis-target", "value", allow_duplicate=True)],
        Input("doc-context", "data"),
        prevent_initial_call=True,
    )
    def _populate_analysis_target(doc_ctx):
        if not isinstance(doc_ctx, dict):
            return [], None
        opts = [
            {"label": ctx.get("file_name", did), "value": did}
            for did, ctx in doc_ctx.items()
            if isinstance(ctx, dict)
        ]
        return opts, (opts[0]["value"] if opts else None)

    # ── búsqueda principal ────────────────────────────────────────────────────
    @app.callback(
        Output("pdf-summary-output", "children"),
        Output("analysis-result-store", "data"),
        Output("analysis-view-state", "data"),
        Input("analysis-search-btn", "n_clicks"),
        State("analysis-target", "value"),
        State("doc-context", "data"),
        State("analysis-search-keyword", "value"),
        State("analysis-search-field", "value"),
        prevent_initial_call=True,
    )
    def search_fields(n_clicks, doc_id, doc_ctx, keyword, field_type):
        if not n_clicks or not doc_id or not isinstance(doc_ctx, dict):
            raise PreventUpdate
        selected = doc_ctx.get(doc_id)
        if not isinstance(selected, dict):
            raise PreventUpdate

        query   = (keyword or "").strip()
        matches = search_document(selected, query=query, field_type=field_type or None)

        # Métricas
        n_fields = len(selected.get("fields", []) or [])
        n_blocks = len(selected.get("classified_blocks", []) or [])
        n_pages  = selected.get("pages_total") or len(selected.get("pages", []) or [])

        # Distribución de tipos semánticos
        sem_counts: dict[str, int] = {}
        for b in (selected.get("classified_blocks") or []):
            t = b.get("semantic_type") or "other"
            sem_counts[t] = sem_counts.get(t, 0) + 1
        top_types = sorted(sem_counts.items(), key=lambda x: -x[1])[:6]

        summary = dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5(selected.get("file_name", doc_id), className="mb-2 fw-bold"),
                        html.Div([
                            dbc.Badge(f"📄 {n_pages} págs",   color="secondary", className="me-2"),
                            dbc.Badge(f"🔖 {n_fields} campos", color="info",      className="me-2"),
                            dbc.Badge(f"📦 {n_blocks} bloques",color="warning",   className="me-2"),
                            dbc.Badge(f"🔍 {len(matches)} resultados", color="success"),
                        ], className="mb-2"),
                        html.Small(
                            f'Búsqueda: "{query}"' if query else "Sin filtro de texto",
                            className="text-muted",
                        ),
                    ], md=8),
                    dbc.Col([
                        html.Small("Tipos detectados:", className="text-muted d-block mb-1"),
                        html.Div([
                            dbc.Badge(f"{t}: {c}", color="dark", className="me-1 mb-1")
                            for t, c in top_types
                        ]),
                    ], md=4),
                ]),
            ]),
            className="shadow-sm border-0 mb-3",
            style={"border": "1px solid #333 !important"},
        )

        result_store = {
            "doc_id":     doc_id,
            "query":      query,
            "field_type": field_type,
            "matches":    matches,
            "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        return summary, result_store, {"index": 0, "key": "fields"}

    # ── navegación de vistas ──────────────────────────────────────────────────
    @app.callback(
        Output("analysis-view-state", "data", allow_duplicate=True),
        Output("analysis-view-label", "children"),
        Input("analysis-prev-view-btn", "n_clicks"),
        Input("analysis-next-view-btn", "n_clicks"),
        State("analysis-view-state", "data"),
        prevent_initial_call=True,
    )
    def cycle_view(prev_clicks, next_clicks, view_state):
        if not ctx.triggered_id:
            raise PreventUpdate
        key = _current_view_key(view_state)
        idx = ANALYSIS_VIEW_ORDER.index(key) if key in ANALYSIS_VIEW_ORDER else 0
        if ctx.triggered_id == "analysis-prev-view-btn":
            idx = (idx - 1) % len(ANALYSIS_VIEW_ORDER)
        else:
            idx = (idx + 1) % len(ANALYSIS_VIEW_ORDER)
        new_key = ANALYSIS_VIEW_ORDER[idx]
        return {"index": idx, "key": new_key}, ANALYSIS_VIEW_META[new_key]["label"]

    # ── renderizar tabla ──────────────────────────────────────────────────────
    @app.callback(
        Output("pdf-analysis-output", "children"),
        Input("analysis-result-store", "data"),
        Input("analysis-view-state", "data"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def render_table(result_store, view_state, doc_ctx):
        if not isinstance(result_store, dict) or not isinstance(doc_ctx, dict):
            raise PreventUpdate
        doc_id   = result_store.get("doc_id")
        selected = doc_ctx.get(doc_id)
        if not isinstance(selected, dict):
            raise PreventUpdate

        view_key   = _current_view_key(view_state)
        view_label = ANALYSIS_VIEW_META[view_key]["label"]
        rows       = _build_rows(selected, result_store.get("matches", []), view_key)

        if not rows:
            return dbc.Alert(
                [
                    html.I(className="bi-info-circle me-2"),
                    f"No hay datos para la vista '{view_label}'.",
                ],
                color="secondary",
            )

        all_cols = _cols_for_view(view_key) + _hidden_cols()
        visible  = [c["id"] for c in _cols_for_view(view_key)]

        table = dash_table.DataTable(
            id="analysis-datatable",
            columns=all_cols,
            data=rows,
            hidden_columns=[c["id"] for c in _hidden_cols()],
            row_selectable="single",
            cell_selectable=True,
            sort_action="native",
            page_action="native",
            page_size=12,
            style_table={"overflowX": "auto", "overflowY": "auto", "maxHeight": "400px"},
            style_cell={
                "textAlign": "left",
                "fontSize": "0.88rem",
                "padding": "8px 12px",
                "maxWidth": "300px",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "whiteSpace": "nowrap",
            },
            style_cell_conditional=[
                {"if": {"column_id": "text"}, "maxWidth": "260px"},
                {"if": {"column_id": "value"}, "maxWidth": "220px"},
            ],
            style_header={
                "fontWeight": "700",
                "fontSize": "0.82rem",
                "backgroundColor": "#1e1e1e",
                "color": "#E3530F",
                "textTransform": "uppercase",
                "letterSpacing": "0.05em",
            },
            style_data={
                "backgroundColor": "#1a1a1a",
                "color": "#ddd",
                "borderBottom": "1px solid #2a2a2a",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#141414"},
                {"if": {"state": "selected"}, "backgroundColor": "#1e2d3d",
                 "border": "1px solid #E3530F"},
            ],
            tooltip_data=[
                {c["id"]: {"value": str(row.get(c["id"], "")), "type": "markdown"}
                 for c in _cols_for_view(view_key)}
                for row in rows
            ],
            tooltip_delay=0,
            tooltip_duration=None,
        )

        return dbc.Card(
            [
                dbc.CardHeader(
                    html.Div([
                        html.Span(view_label, className="fw-bold"),
                        html.Small(f"  {len(rows)} elementos", className="text-muted ms-2"),
                    ]),
                    style={"background": "#1e1e1e"},
                ),
                dbc.CardBody(table, style={"background": "#1a1a1a", "padding": "0"}),
            ],
            className="border-0 shadow-sm",
            style={"border": "1px solid #333 !important"},
        )

    # ── crop: preview al seleccionar una fila ─────────────────────────────────
    @app.callback(
        Output("analysis-selection-preview", "children"),
        Input("analysis-datatable", "selected_rows"),
        State("analysis-datatable", "derived_viewport_data"),
        State("analysis-result-store", "data"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def show_crop(selected_rows, viewport_data, result_store, doc_ctx):
        if not selected_rows or not viewport_data:
            raise PreventUpdate
        idx = selected_rows[0]
        if idx >= len(viewport_data):
            raise PreventUpdate

        row = viewport_data[idx]
        if not isinstance(result_store, dict) or not isinstance(doc_ctx, dict):
            raise PreventUpdate

        doc_id   = result_store.get("doc_id")
        selected = doc_ctx.get(doc_id)
        if not isinstance(selected, dict):
            raise PreventUpdate

        # ── extraer page_number y bbox ────────────────────────────────────────
        page_number = row_page_number(row)
        if page_number is None:
            try:
                page_number = int(row.get("page_number") or row.get("page") or 1)
            except Exception:
                page_number = 1

        # bbox desde la fila (campo bbox_raw es JSON serializado)
        bbox = None
        raw = row.get("bbox_raw")
        if raw:
            try:
                bbox = normalize_bbox(json.loads(raw))
            except Exception:
                pass
        if bbox is None:
            bbox = row_bbox(row)

        # Si aún no tenemos bbox, buscar en los bloques del documento
        if bbox is None:
            block_id = row.get("block_id") or ""
            text_val = (row.get("text") or row.get("value") or "").strip()
            for p in (selected.get("pages") or []):
                pn = p.get("page_number")
                for b in (p.get("blocks") or []):
                    if block_id and b.get("block_id") == block_id:
                        bbox = normalize_bbox(b.get("bbox"))
                        page_number = pn
                        break
                    if text_val and (b.get("text") or "").strip()[:60] == text_val[:60]:
                        bbox = normalize_bbox(b.get("bbox"))
                        page_number = pn
                        break
                if bbox:
                    break

        # ── obtener imagen de la página ───────────────────────────────────────
        page_image_path = _storage.page_cache_path(doc_id, page_number)
        if not os.path.exists(page_image_path):
            file_path = selected.get("file_path")
            if file_path:
                try:
                    render_page_to_image(file_path, page_number, page_image_path)
                except Exception:
                    page_image_path = None
            else:
                # Intentar desde overlays
                for ov in (selected.get("overlays") or []):
                    if ov.get("page") == page_number:
                        page_image_path = ov.get("path")
                        break
                else:
                    page_image_path = None

        # ── dimensiones de la página ──────────────────────────────────────────
        pdf_width, pdf_height = None, None
        for p in (selected.get("pages") or []):
            if p.get("page_number") == page_number:
                pdf_width  = p.get("width")
                pdf_height = p.get("height")
                break

        # ── generar crop ──────────────────────────────────────────────────────
        crop_src = ""
        if page_image_path and bbox:
            crop_src = crop_page_region(
                page_image_path, bbox,
                pdf_width=pdf_width,
                pdf_height=pdf_height,
                padding=16,
            )

        # ── metadatos de la fila ──────────────────────────────────────────────
        title   = row.get("field") or row.get("semantic_type") or "Elemento seleccionado"
        snippet = (row.get("value") or row.get("text") or "")[:300]

        return dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6(title, className="fw-bold mb-1", style={"color": "#E3530F"}),
                        html.Small(f"Página {page_number}", className="text-muted d-block"),
                        html.P(snippet, className="mt-2 small", style={"color": "#ccc"}),
                        html.Hr(style={"borderColor": "#333"}),
                        html.Small("BBox:", className="text-muted"),
                        html.Code(str(bbox) if bbox else "sin bbox",
                                  style={"fontSize": "0.75rem", "display": "block"}),
                    ], md=5),
                    dbc.Col([
                        html.Div(
                            html.Img(
                                src=crop_src,
                                style={
                                    "maxWidth": "100%",
                                    "maxHeight": "260px",
                                    "borderRadius": "8px",
                                    "border": "2px solid #E3530F",
                                    "boxShadow": "0 4px 12px rgba(0,0,0,0.4)",
                                },
                            ) if crop_src else dbc.Alert(
                                [
                                    html.I(className="bi-crop me-2"),
                                    "No se pudo generar el crop. "
                                    "Verifica que el documento fue procesado y tiene bbox válido.",
                                ],
                                color="warning",
                                className="small",
                            ),
                            style={"textAlign": "center"},
                        )
                    ], md=7),
                ]),
            ], style={"background": "#1a1a1a"}),
            className="border-0 shadow-sm mt-3",
            style={"border": "1px solid #333 !important"},
        )
