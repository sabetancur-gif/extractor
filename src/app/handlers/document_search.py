# src/app/handlers/document_search.py

r"""Creacíon y definición de callbacks.

Callbacks para búsqueda avanzada y análisis de texto en el documento.
"""

# STDLIB
import difflib
import json
import re
import os

# THIRDPARTY
from datetime import datetime
from dash import ctx
from dash import Input, Output, State, dash_table, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from src.search.universal_search import search_document
# from src.utils.crop import crop_page_region
# from src.utils.bbox import row_bbox, row_page_number
# from src.ingest.storage import StorageManager
# from src.utils.image import render_page_to_image

ANALYSIS_VIEW_ORDER = [
    "fields",
    "blocks",
    "tables",
    "signatures",
    "assets",
    "dates",
    "amounts",
    "addresses",
]

ANALYSIS_VIEW_META = {
    "fields": {"label": "Campos", "icon": "bi-card-text"},
    "blocks": {"label": "Bloques", "icon": "bi-layers"},
    "tables": {"label": "Tablas", "icon": "bi-table"},
    "signatures": {"label": "Firmas", "icon": "bi-pen"},
    "assets": {"label": "Imágenes y logos", "icon": "bi-image"},
    "dates": {"label": "Fechas", "icon": "bi-calendar3"},
    "amounts": {"label": "Valores", "icon": "bi-currency-dollar"},
    "addresses": {"label": "Direcciones", "icon": "bi-geo-alt"},
}

def _safe_cell_value(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False)
    return value

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

def _build_analysis_rows(doc_ctx: dict, matches: list[dict], view_key: str) -> list[dict]:
    blocks = doc_ctx.get("classified_blocks", []) or []
    fields = doc_ctx.get("fields", []) or []

    if view_key == "fields":
        rows = []
        for item in matches or []:
            if item.get("kind") != "field":
                continue
            rows.append(
                {
                    "field": item.get("field"),
                    "value": item.get("value"),
                    "page_number": item.get("page_number", item.get("page")),
                    "bbox": _safe_cell_value(item.get("bbox")),
                    "block_id": item.get("block_id"),
                    # "source": item.get("source"),
                    "source": (
                        json.dumps(item.get("source"), ensure_ascii=False)
                        if isinstance(item.get("source"), (dict, list))
                        else item.get("source")
                    ),
                    "confidence": item.get("confidence", item.get("score")),
                    "semantic_type": item.get("semantic_type"),
                    "text": item.get("text", item.get("value", "")),
                    "kind": "field",
                }
            )
        return rows

    if view_key == "blocks":
        rows = []
        for item in matches or []:
            if item.get("kind") != "block":
                continue
            rows.append(
                {
                    "semantic_type": item.get("semantic_type", item.get("block_type")),
                    "text": item.get("text", ""),
                    "page_number": item.get("page_number", item.get("page")),
                    "bbox": _safe_cell_value(item.get("bbox")),
                    "block_id": item.get("block_id"),
                    # "source": item.get("source"),
                    "source": (
                        json.dumps(item.get("source"), ensure_ascii=False)
                        if isinstance(item.get("source"), (dict, list))
                        else item.get("source")
                    ),
                    "confidence": item.get("confidence"),
                    "kind": "block",
                }
            )
        return rows

    def _by_semantic(predicate):
        rows = []
        for block in blocks:
            if predicate(block):
                rows.append(
                    {
                        "semantic_type": block.get("semantic_type", block.get("block_type")),
                        "text": block.get("text", ""),
                        "page_number": block.get("page_number", block.get("page")),
                        "bbox": _safe_cell_value(block.get("bbox")),
                        "block_id": block.get("block_id"),
                        # "source": item.get("source"),
                        "source": _safe_cell_value(block.get("source")),
                        "confidence": block.get("semantic_confidence", block.get("confidence")),
                        "kind": "block",
                    }
                )
            return rows

        if view_key == "tables":
            return _by_semantic(lambda b: b.get("semantic_type") == "table" or b.get("block_type") == "table" or b.get("is_table_like"))

        if view_key == "signatures":
            return _by_semantic(lambda b: b.get("semantic_type") == "signature" or b.get("is_signature"))

        if view_key == "assets":
            return _by_semantic(lambda b: b.get("semantic_type") in {"image", "logo", "figure", "stamp"} or b.get("is_image") or b.get("is_logo"))

        if view_key == "dates":
            return _by_semantic(lambda b: b.get("semantic_type") == "date" or b.get("is_date"))

        if view_key == "amounts":
            return _by_semantic(lambda b: b.get("semantic_type") == "amount" or b.get("is_amount"))

        if view_key == "addresses":
            return _by_semantic(lambda b: b.get("semantic_type") == "address" or b.get("is_address"))

        return []


def _overlay_local_to_url(local_path: str) -> str:
    r"""Transformación de paths locales.

    Convierte paths locales a URLs servidas por Flask en /overlays/<path>.
    """
    if not local_path:
        return ""

    # Normalizar
    abs_path = os.path.abspath(local_path)
    base = os.path.abspath("data/cache")

    # Confirmar que está dentro de data/cache
    if not abs_path.startswith(base):
        return ""

    # Convertir a ruta relativa dentro del directorio de overlays
    rel = os.path.relpath(abs_path, base).replace(os.sep, "/")

    # Retornar URL servida por Flask
    return f"/overlays/{rel}"


def register_callbacks_03(app, *_args, **_kwargs):
    r"""Registra callbacks para búsqueda avanzada y análisis de campos/bloques.

    Relacionado con IDs: pdf-summary-output, pdf-analysis-output, analysis-search-btn, analysis-search-keyword, analysis-search-field.
    """
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
        if not n_clicks:
            raise PreventUpdate

        if not doc_id or not isinstance(doc_ctx, dict):
            raise PreventUpdate

        selected_ctx = doc_ctx.get(doc_id)
        if not isinstance(selected_ctx, dict):
            raise PreventUpdate

        query = (keyword or "").strip()
        matches = search_document(selected_ctx, query=query, field_type=field_type)

        summary_content = dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.H5(selected_ctx.get("file_name", doc_id), className="mb-1"),
                            html.Div(
                                [
                                    dbc.Badge(f"Páginas: {selected_ctx.get('pages_total', len(selected_ctx.get('pages', [])))}", color="secondary", className="me-2"),
                                    dbc.Badge(f"Campos: {len(selected_ctx.get('fields', []))}", color="info", className="me-2"),
                                    dbc.Badge(f"Bloques: {len(selected_ctx.get('classified_blocks', []))}", color="warning", className="me-2"),
                                    dbc.Badge(f"Matches: {len(matches)}", color="success"),
                                ]
                            ),
                            html.Div(
                                f"Búsqueda: '{query}'" if query else "Búsqueda sin texto, filtrando solo por tipo",
                                className="text-muted mt-2",
                            ),
                        ]
                    )
                ]
            ),
            className="shadow-sm border-0 mb-3 panel-card",
        )

        result_store = {
            "doc_id": doc_id,
            "query": query,
            "field_type": field_type,
            "matches": matches,
            "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

        view_state = {"index": 0, "key": "fields"}

        return summary_content, result_store, view_state

    @app.callback(
        Output("analysis-view-state", "data", allow_duplicate=True),
        Output("analysis-view-label", "children"),
        Input("analysis-prev-view-btn", "n_clicks"),
        Input("analysis-next-view-btn", "n_clicks"),
        State("analysis-view-state", "data"),
        prevent_initial_call=True,
    )
    def cycle_analysis_view(prev_clicks, next_clicks, view_state):
        if not ctx.triggered_id:
            raise PreventUpdate

        current = _current_view_key(view_state)
        try:
            idx = ANALYSIS_VIEW_ORDER.index(current)
        except ValueError:
            idx = 0

        if ctx.triggered_id == "analysis-prev-view-btn":
            idx = (idx - 1) % len(ANALYSIS_VIEW_ORDER)
        elif ctx.triggered_id == "analysis-next-view-btn":
            idx = (idx + 1) % len(ANALYSIS_VIEW_ORDER)

        key = ANALYSIS_VIEW_ORDER[idx]
        return {"index": idx, "key": key}, ANALYSIS_VIEW_META[key]["label"]

    @app.callback(
        Output("pdf-analysis-output", "children"),
        Input("analysis-result-store", "data"),
        Input("analysis-view-state", "data"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def render_analysis_output(result_store, view_state, doc_ctx):
        if not isinstance(result_store, dict) or not isinstance(doc_ctx, dict):
            raise PreventUpdate

        doc_id = result_store.get("doc_id")
        selected_ctx = doc_ctx.get(doc_id)
        if not isinstance(selected_ctx, dict):
            raise PreventUpdate

        view_key = _current_view_key(view_state)
        view_label = ANALYSIS_VIEW_META[view_key]["label"]
        rows = _build_analysis_rows(selected_ctx, result_store.get("matches", []), view_key)

        if not rows:
            return dbc.Alert(
                f"No hay datos para la vista '{view_label}'.",
                color="secondary",
                className="shadow-sm",
            )

        if view_key == "fields":
            columns = [
                {"name": "Campo", "id": "field"},
                {"name": "Valor", "id": "value"},
                {"name": "Página", "id": "page_number"},
                {"name": "Confianza", "id": "confidence"},
                {"name": "Semántica", "id": "semantic_type"},
                {"name": "Fuente", "id": "source"},
                {"name": "block_id", "id": "block_id", "hideable": True},
                {"name": "bbox", "id": "bbox", "hideable": True},
            ]
        else:
            columns = [
                {"name": "Semántica", "id": "semantic_type"},
                {"name": "Texto", "id": "text"},
                {"name": "Página", "id": "page_number"},
                {"name": "Confianza", "id": "confidence"},
                {"name": "Fuente", "id": "source"},
                {"name": "block_id", "id": "block_id", "hideable": True},
                {"name": "bbox", "id": "bbox", "hideable": True},
            ]

        table = dash_table.DataTable(
            id="analysis-datatable",
            columns=columns,
            data=rows,
            row_selectable="single",
            cell_selectable=True,
            filter_action="none",
            sort_action="native",
            page_action="native",
            page_size=12,
            style_table={
                "overflowX": "auto",
                "overflowY": "auto",
                "maxHeight": "420px",
            },
            style_cell={
                "whiteSpace": "normal",
                "height": "auto",
                "textAlign": "left",
                "fontSize": "0.92rem",
                "padding": "10px",
            },
            style_header={"fontWeight": "700"},
        )

        table_card = dbc.Card(
            [
                dbc.CardHeader(
                    html.Div(
                        [
                            html.H5(f"Vista: {view_label}", className="mb-0"),
                            html.Small(
                                f"Filas visibles: {len(rows)}",
                                className="text-muted",
                            ),
                        ]
                    )
                ),
                dbc.CardBody(table),
            ],
            className="shadow-sm border-0 panel-card h-100",
        )

        preview_card = dbc.Card(
            [
                dbc.CardHeader(
                    html.Div(
                        [
                            html.H5("Crop seleccionado", className="mb-0"),
                            html.Small(
                                "Selecciona una fila para ver el recorte",
                                className="text-muted",
                            ),
                        ]
                    )
                ),
                dbc.CardBody(
                    html.Div(
                        id="analysis-selection-preview",
                        children=dbc.Alert(
                            "Selecciona una fila para ver el crop.",
                            color="secondary",
                            className="mb-0",
                        ),
                    )
                ),
            ],
            className="shadow-sm border-0 panel-card h-100",
        )

        json_card = dbc.Card(
            [
                dbc.CardHeader("JSON del documento"),
                dbc.CardBody(
                    html.Pre(
                        json.dumps(selected_ctx, indent=2, ensure_ascii=False)[:14000],
                        style={
                            "maxHeight": "420px",
                            "overflow": "auto",
                            "whiteSpace": "pre-wrap",
                        },
                    )
                ),
            ],
            className="shadow-sm border-0 panel-card mt-3",
        )

        return dbc.Row(
            [
                dbc.Col([table_card, preview_card, json_card], className="mb-3 mb-md-0"),
            ],
            className="g-3 align-items-start",
        )

    # ===== AUTO-UPDATE PDF ANALYSIS cuando cambia doc-context =====
    @app.callback(
        Output("pdf-auto-analysis-output", "children"),
        Input("doc-context", "data"),
        prevent_initial_call=True,
    )
    def auto_update_pdf_analysis(doc_ctx):
        if not doc_ctx:
            raise PreventUpdate

        # Si doc_ctx es un dict de documentos (por id), tomar el primero
        if isinstance(doc_ctx, dict) and not ("fields" in doc_ctx or "classified_blocks" in doc_ctx):
            # Tomar el primer documento disponible
            first_doc = next(iter(doc_ctx.values()), None)
            doc_ctx = first_doc if isinstance(first_doc, dict) else None
            if not doc_ctx:
                return [html.Small("No document selected", className="text-muted")]

        fields = doc_ctx.get("fields", []) or []
        blocks = doc_ctx.get("classified_blocks", []) or []

        content = []

        # --- METADATA --
        content.append(html.H6("Detected metadata", className="mb-2"))

        content.append(html.Small(f"File: {doc_ctx.get('file_name', 'N/A')}"))
        content.append(html.Br())
        content.append(html.Small(f"Pages: {len(doc_ctx.get('pages', []) or [])}"))
        content.append(html.Br())
        content.append(html.Small(f"Blocks: {len(blocks)}"))

        # --- FIELDS PREVIEW ---
        content.append(html.Hr())
        content.append(html.H6("First detected fields"))

        if fields:
            content.append(
                dash_table.DataTable(
                    columns=[
                        {"name": "label", "id": "label"},
                        {"name": "value", "id": "value"},
                    ],
                    data=[
                        {
                            "label": f.get("label", ""),
                            "value": f.get("text", ""),
                        }
                        for f in fields[:5]
                    ],
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "fontSize": "0.8rem",
                        "whiteSpace": "normal",
                        "textAlign": "left",
                    },
                )
            )
        else:
            content.append(html.Small("No fields detected", className="text-muted"))

        # --- BLOCKs PREVIEW ---
        content.append(html.Hr())
        content.append(html.H6("First text blocks"))

        if blocks:
            content.append(
                html.Ul([
                    html.Li(b.get("text", "")[:120])
                    for b in blocks[:5]
                ], style={"fontSize": "0.85rem"})
            )
        else:
            content.append(html.Small("No blocks detected", className="text-muted"))

        return content

    # @app.callback(
    #     Output("analysis-selection-preview", "children"),
    #     Input("analysis-datatable", "selected_rows"),
    #     State("analysis-datatable", "data"),
    #     State("analysis-result-store", "data"),
    #     State("doc-context", "data"),
    #     prevent_initial_call=True,
    # )
    # def render_analysis_selection_preview(selected_rows, rows, result_store, doc_ctx):
    #     if not selected_rows or not rows or not isinstance(result_store, dict) or not isinstance(doc_ctx, dict):
    #         raise PreventUpdate

    #     idx = selected_rows[0]
    #     if idx < 0 or idx >= len(rows):
    #         raise PreventUpdate

    #     row = rows[idx]
    #     doc_id = result_store.get("doc_id")
    #     selected_ctx = doc_ctx.get(doc_id)
    #     if not isinstance(selected_ctx, dict):
    #         raise PreventUpdate

    #     page_number = row_page_number(row)
    #     if page_number is None:
    #         return dbc.Alert("La fila seleccionada no tiene página asociada.", color="warning")

    #     bbox = row_bbox(row)
    #     if bbox is None:
    #         raw_bbox = row.get("bbox")
    #         if isinstance(raw_bbox, str):
    #             try:
    #                 raw_bbox = json.loads(raw_bbox)
    #             except Exception:
    #                 raw_bbox = None
    #         bbox = raw_bbox

    #     if bbox is None:
    #         return dbc.Alert("La fila seleccionada no tiene bbox utilizable.", color="warning")

    #     storage = StorageManager()
    #     page_path = storage.page_cache_path(doc_id, page_number)

    #     if not os.path.exists(page_path):
    #         file_path = selected_ctx.get("file_path")
    #         if file_path:
    #             render_page_to_image(file_path, page_number, page_path)

    #     crop_src = crop_page_region(page_path, bbox)
    #     if not crop_src:
    #         return dbc.Alert("No se pudo generar el crop.", color="warning")

    #     return html.Div(
    #         [
    #             html.Img(src=crop_src, className="img-fluid rounded border mb-3"),
    #             html.Hr(),
    #             html.Pre(
    #                 json.dumps(row, indent=2, ensure_ascii=False),
    #                 style={
    #                     "maxHeight": "260px",
    #                     "overflow": "auto",
    #                     "whiteSpace": "pre-wrap",
    #                     "marginBottom": 0,
    #                 },
    #             ),
    #         ]
    #     )