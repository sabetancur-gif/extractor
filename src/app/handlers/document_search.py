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
from dash import ctx
from dash import Input, Output, State, dash_table, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from src.search.universal_search import search_document
from src.utils.crop import crop_page_region
from src.utils.bbox import row_bbox, row_page_number

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
                    "bbox": item.get("bbox"),
                    "block_id": item.get("block_id"),
                    "source": item.get("source"),
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
                    "bbox": item.get("bbox"),
                    "block_id": item.get("block_id"),
                    "source": item.get("source"),
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
                    "semantic_type": item.get("semantic_type", item.get("block_type")),
                    "text": item.get("text", ""),
                    "page_number": item.get("page_number", item.get("page")),
                    "bbox": item.get("bbox"),
                    "block_id": item.get("block_id"),
                    "source": item.get("source"),
                    "confidence": item.get("semantic_confidence", block.get("confidence")),
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
                {"name": "block_id", "id": "block_id", "hidden": True},
                {"name": "bbox", "id": "bbox", "hidden": True},
            ]
        else:
            columns = [
                {"name": "Semántica", "id": "semantic_type"},
                {"name": "Texto", "id": "text"},
                {"name": "Página", "id": "page_number"},
                {"name": "Confianza", "id": "confidence"},
                {"name": "Fuente", "id": "source"},
                {"name": "block_id", "id": "block_id", "hidden": True},
                {"name": "bbox", "id": "bbox", "hidden": True},
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
            style_header={
                "fontWeight": "700",
            },
        )

        preview = html.Div(
            id="analysis-selection-preview",
            children=html.Div(
                "Selecciona una fila para ver el crop.",
                className="text-muted",
            ),
        )

        json_comp = dbc.Card(
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
            className="shadow-sm border-0 panel-card",
        )

        return dbc.Container(
            [
                table_card,
                html.Div(preview, className="mt-3"),
                json_comp,
            ],
            fluid=True,
            className="p-0",
        )

    # @app.callback(
    #     [
    #         Output("pdf-summary-output", "children"),
    #         Output("pdf-analysis-output", "children"),
    #     ],
    #     [
    #         Input("analysis-search-btn", "n_clicks"),
    #     ],
    #     [
    #         State("analysis-target", "value"),
    #         State("doc-context", "data"),
    #         State("analysis-search-keyword", "value"),
    #         State("analysis-search-field", "value"),
    #     ],
    #     prevent_initial_call=True,
    # )
    # def search_fields(_n_clicks, selected_ids, doc_ctx, keyword, field_type):
    #     if not selected_ids or not doc_ctx:
    #         raise PreventUpdate

    #     doc_id = selected_ids[0] if isinstance(selected_ids, list) else selected_ids
    #     doc_ctx = doc_ctx.get(doc_id) if isinstance(doc_ctx, dict) else doc_ctx
    #     if not doc_ctx:
    #         raise PreventUpdate

    #     query = (keyword or "").strip()
    #     # search_document debe estar importado o definido en el scope
    #     matches = search_document(doc_ctx, query=query, field_type=field_type)

    #     summary_content = html.Div(
    #         [
    #             html.H6("Document summary"),
    #             html.Div(f"File: {doc_ctx.get('file_name', doc_id)}"),
    #             html.Div(f"Pages: {doc_ctx.get('pages_total', len(doc_ctx.get('pages', [])))}"),
    #             html.Div(f"Fields: {len(doc_ctx.get('fields', []))}"),
    #             html.Div(f"Blocks: {len(doc_ctx.get('classified_blocks', []))}"),
    #         ]
    #     )

    #     field_rows = [m for m in matches if m["kind"] == "field"]
    #     block_rows = [m for m in matches if m["kind"] == "block"]

    #     def _table(rows, table_id, title):
    #         if not rows:
    #             return dbc.Card(
    #                 dbc.CardBody([html.H6(title), html.Div("No results.", className="text-muted")])
    #             )

    #         data = []
    #         for r in rows:
    #             src = r.get("source", {}) or {}
    #             data.append(
    #                 {
    #                     "kind": r.get("kind"),
    #                     "page_number": r.get("page_number"),
    #                     "text": r.get("text"),
    #                     "confidence": r.get("confidence"),
    #                     "bbox": r.get("bbox"),
    #                     "source": src.get("field") or src.get("label") or src.get("type") or "",
    #                 }
    #             )

    #         columns = [
    #             {"name": "kind", "id": "kind"},
    #             {"name": "page_number", "id": "page_number"},
    #             {"name": "source", "id": "source"},
    #             {"name": "text", "id": "text"},
    #             {"name": "confidence", "id": "confidence"},
    #             {"name": "bbox", "id": "bbox"},
    #         ]

    #         return dbc.Card(
    #             dbc.CardBody(
    #                 [
    #                     html.H6(title, className="mb-2"),
    #                     dash_table.DataTable(
    #                         id=table_id,
    #                         columns=columns,
    #                         data=data,
    #                         page_size=8,
    #                         row_selectable="single",
    #                         active_cell=None,
    #                         filter_action="native",
    #                         sort_action="native",
    #                         style_table={"overflowX": "auto"},
    #                         style_cell={
    #                             "whiteSpace": "normal",
    #                             "height": "auto",
    #                             "textAlign": "left",
    #                             "fontSize": "0.9rem",
    #                         },
    #                         style_header={"fontWeight": "600"},
    #                     ),
    #                 ]
    #             ),
    #             className="shadow-sm mb-3",
    #         )

    #     preview = html.Div(
    #         id="analysis-selection-preview",
    #         children=html.Div("Select a row to preview the page crop.", className="text-muted"),
    #     )

    #     # --- helpers y renderizado de overlay/json siguen igual ---
    #     overlays = doc_ctx.get("overlays") or []
    #     overlay_comp = html.Div()
    #     if overlays:
    #         page_overlay = overlays[0]
    #         image_src_local = page_overlay.get("path") or page_overlay.get("image") or ""
    #         image_src = _overlay_local_to_url(image_src_local) if image_src_local else ""
    #         print(f"Ruta a la imagen: {image_src}")
    #         if image_src:
    #             overlay_comp = html.Div([
    #                 # Espacio para mostrar el bbox en la page donde sale el selected block
    #                 html.H6(
    #                     "Preview de Páginas y Overlays"
    #                 ),
    #                 html.Div(
    #                     className="pdf-overlay-wrapper",
    #                     style={"position": "relative"},
    #                     children=[
    #                         html.Img(
    #                             src=image_src,
    #                             id="pdf-overlay-img",
    #                             style={"width": "100%", "height": "auto", "display": "block"},
    #                             alt="Preview"
    #                         ),
    #                         html.Div(
    #                             id="pdf-overlay-layer",
    #                             children=[],
    #                             style={
    #                                 "position": "absolute",
    #                                 "top": 0,
    #                                 "left": 0,
    #                                 "width": "100%",
    #                                 "height": "100%",
    #                                 "pointerEvents": "none"
    #                             }
    #                         )
    #                     ]
    #                 ),
    #                 html.Div("Click en una fila de 'Bloques' para mostrar bbox e información.", className="text-muted-small mt-2")
    #             ])

    #     raw_json_str = json.dumps(doc_ctx, indent=2, ensure_ascii=False)
    #     json_comp = html.Div([
    #         html.H6("JSON del documento"),
    #         dbc.Button("Copiar JSON", id="copy-json-btn", color="outline-secondary", size="sm", className="mb-2"),
    #         html.Pre(
    #             raw_json_str[:12000],
    #             style={
    #                 "maxHeight": "360px",
    #                 "overflow": "auto",
    #                 "background": "#f8f9fa",
    #                 "padding": "10px",
    #                 "borderRadius": "6px"
    #             }
    #         ),
    #         html.Div("JSON truncado en vista; disponible descarga completa.", className="small text-muted"),
    #         dbc.Button("Descargar JSON completo", id="download-json-btn", color="secondary", outline=True, size="sm")
    #     ])

    #     # --- Layout final ---
    #     children_01 = [summary_content]
    #     children = [
    #         html.Div([
    #             # Right row
    #             # Matched fields / Matched blocks 
    #             dbc.Row(
    #                 [
    #                     dbc.Col(_table(field_rows, "analysis-fields-datatable", "Matched fields"), md=6),
    #                     dbc.Col(_table(block_rows, "analysis-blocks-datatable", "Matched blocks"), md=6),
    #                 ],
    #                 className="g-3",
    #             ),
    #             html.Hr(),
    #             # Previsualización ssobre la fila seleccionada (Text information and bbox overlay)
    #             preview,
    #             html.Hr(),
    #             # Overlay sobre la pagina que contiene la fila seleccionada
    #             overlay_comp,
    #             html.Hr(),
    #             # json general sobre el documento que se esta visualizando
    #             json_comp,
    #         ])
    #     ]

    #     return children_01, children

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


    # def auto_update_pdf_analysis(doc_ctx):
    #     """Actualiza automáticamente el PDF Analysis cuando cambia doc-context (ej: OCR Processing)."""
    #     if not doc_ctx:
    #         raise PreventUpdate

    #     # Generar resumen
    #     meta = {
    #         "file_name": doc_ctx.get("file_name"),
    #         "pdf_type": doc_ctx.get("pdf_type"),
    #         "pages": len(doc_ctx.get("pages", [])),
    #         "num_fields": len(doc_ctx.get("fields", [])),
    #         "embedding": doc_ctx.get("embedding"),
    #         "ocr_language": doc_ctx.get("ocr_language"),
    #         "ocr_average_confidence": doc_ctx.get("ocr_average_confidence"),
    #     }

    #     summary_content = [
    #         html.H6("Información del Documento", className="mb-3"),
    #         dbc.Row([
    #             dbc.Col([
    #                 html.Small(html.B("Archivo:")), html.Br(),
    #                 html.Small(meta["file_name"] or "N/A")
    #             ], md=6),
    #             dbc.Col([
    #                 html.Small(html.B("Tipo:")), html.Br(),
    #                 html.Small(meta["pdf_type"] or "N/A")
    #             ], md=6),
    #         ]),
    #         dbc.Row([
    #             dbc.Col([
    #                 html.Small(html.B("Páginas:")), html.Br(),
    #                 html.Small(str(meta["pages"]))
    #             ], md=6),
    #             dbc.Col([
    #                 html.Small(html.B("Campos:")), html.Br(),
    #                 html.Small(str(meta["num_fields"]))
    #             ], md=6),
    #         ]),
    #     ]

    #     if meta.get("ocr_language"):
    #         summary_content.extend([
    #             dbc.Row([
    #                 dbc.Col([
    #                     html.Small(html.B("OCR Idioma:")), html.Br(),
    #                     html.Small(meta["ocr_language"])
    #                 ], md=6),
    #                 dbc.Col([
    #                     html.Small(html.B("OCR Confianza:")), html.Br(),
    #                     html.Small(f"{meta.get('ocr_average_confidence', 0):.1f}%" if meta.get('ocr_average_confidence') else "N/A")
    #                 ], md=6),
    #             ], className="mt-2"),
    #         ])

    #     # Resumen de campos y bloques
    #     fields = doc_ctx.get("fields", []) or []
    #     blocks = doc_ctx.get("classified_blocks", []) or []

    #     overview_content = []

    #     # SECCIÓN: Campos
    #     overview_content.append(html.H6("Primeros 10 Campos Detectados", className="mb-2"))

    #     if fields:
    #         # Generar tabla de campos
    #         keys = list({k for r in fields[:10] for k in r.keys()})
    #         columns = [{"name": k, "id": k} for k in keys]

    #         table = dash_table.DataTable(
    #             id="auto-overview-fields-datatable",
    #             columns=columns,
    #             data=fields[:10],
    #             page_size=8,
    #             style_table={"overflowX": "auto", "maxWidth": "100%"},
    #             style_header={
    #                 "backgroundColor": "#0e1620",
    #                 "fontWeight": "600",
    #                 "color": "#cfe6ff",
    #                 "border": "none"
    #             },
    #             style_cell={
    #                 "backgroundColor": "transparent",
    #                 "color": "#e6eef8",
    #                 "textAlign": "left",
    #                 "whiteSpace": "normal",
    #                 "height": "auto",
    #                 "padding": "8px",
    #                 "fontSize": "0.9rem"
    #             },
    #         )
    #         overview_content.append(table)
    #     else:
    #         overview_content.append(html.Small("No se detectaron campos", className="text-muted"))

    #     # SECCIÓN: Bloques (del OCR o extracción)
    #     overview_content.append(html.Hr(className="mt-4 mb-2"))
    #     overview_content.append(html.H6("Primeros 10 Bloques Extraídos", className="mb-2"))

    #     if blocks:
    #         # Generar tabla de bloques
    #         keys = list({k for r in blocks[:10] for k in r.keys()})
    #         columns = [{"name": k, "id": k} for k in keys]

    #         table_blocks = dash_table.DataTable(
    #             id="auto-overview-blocks-datatable",
    #             columns=columns,
    #             data=blocks[:10],
    #             page_size=8,
    #             style_table={"overflowX": "auto", "maxWidth": "100%"},
    #             style_header={
    #                 "backgroundColor": "#0e1620",
    #                 "fontWeight": "600",
    #                 "color": "#cfe6ff",
    #                 "border": "none"
    #             },
    #             style_cell={
    #                 "backgroundColor": "transparent",
    #                 "color": "#e6eef8",
    #                 "textAlign": "left",
    #                 "whiteSpace": "normal",
    #                 "height": "auto",
    #                 "padding": "8px",
    #                 "fontSize": "0.9rem"
    #             },
    #         )
    #         overview_content.append(table_blocks)
    #     else:
    #         overview_content.append(html.Small("No se detectaron bloques", className="text-muted"))

    #     return summary_content, overview_content