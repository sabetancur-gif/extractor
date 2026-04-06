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
from dash import Input, Output, State, dash_table, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc


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
        [
            Output("pdf-summary-output", "children"),
            Output("pdf-analysis-output", "children"),
        ],
        [
            Input("analysis-search-btn", "n_clicks"),
        ],
        [
            State("analysis-target", "value"),
            State("doc-context", "data"),
            State("analysis-search-keyword", "value"),
            State("analysis-search-field", "value"),
        ],
        prevent_initial_call=True,
    )
    def search_fields(_n_clicks, selected_ids, doc_ctx, keyword, field_type):
        # print(f"[Temporal] analysis-target: {selected_ids}")
        # print(f"[Temporal] doc-context: {doc_ctx}")
        # print(f"[Temporal] analysis-search-keyword: {keyword}")
        # print(f"[Temporal] analysis-search-field: {field_type}")

        # Solo permite analizar los documentos seleccionados en analysis-target
        if not selected_ids or not doc_ctx:
            raise PreventUpdate
        # Si hay varios, toma el primero (podemos adaptar para multi-análisis si lo deseas)
        doc_id = selected_ids[0] if isinstance(selected_ids, list) else selected_ids
        doc_ctx = doc_ctx.get(doc_id) if isinstance(doc_ctx, dict) else doc_ctx

        if not doc_ctx:
            raise PreventUpdate

        # -------- Intern helpers --------
        def fuzzy_match(a, b, cutoff=0.6):
            if not a or not b:
                return False
            return difflib.SequenceMatcher(None, a, b).ratio() >= cutoff

        def is_regex_query(q):
            return isinstance(q, str) and q.startswith("/re:") and q.endswith("/")
        # --------------------------------

        # Parse keyword modes
        use_regex = False
        regex = None
        if keyword:
            kw = keyword.strip()
            if is_regex_query(kw):
                use_regex = True
                try:
                    regex = re.compile(kw[4:-1], re.IGNORECASE)
                except re.error:
                    regex = None

        # Gather top-level info
        meta = {
            "file_name": doc_ctx.get("file_name"),
            "pdf_type": doc_ctx.get("pdf_type"),
            "pages": len(doc_ctx.get("pages", [])),
            "num_fields": len(doc_ctx.get("fields", [])),
        }

        # Build fields and blocks lists
        fields = doc_ctx.get("fields", []) or []
        blocks = doc_ctx.get("classified_blocks", []) or []

        # Filter by dropdown selection (field:NAME or block:TYPE)
        filtered_fields = fields.copy()
        filtered_blocks = blocks.copy()

        if field_type:
            if field_type.startswith("field:"):
                fname = field_type.split(":", 1)[1]
                filtered_fields = [
                    f for f in fields if f.get("field") == fname
                ]
            elif field_type.startswith("block:"):
                btype = field_type.split(":", 1)[1]
                filtered_blocks = [
                    b for b in blocks if b.get("block_type") == btype
                ]

        # Apply keyword filtering
        if keyword:
            q = keyword.strip()

            # fields
            new_fields = []
            for f in filtered_fields:
                text = f.get("value", "") + " " + f.get("context", "")
                if use_regex and regex:
                    if regex.search(text):
                        new_fields.append(f)
                elif ":" in q and q.split(":", 1)[0].lower() in ["field", "f"]:
                    # e.g. "field:amount 54"
                    parts = q.split(":", 1)
                    rest = parts[1].strip()
                    if rest:
                        if rest in f.get("field", "") or rest in f.get("value", "") or rest in f.get("context", ""):
                            new_fields.append(f)
                else:
                    # Plain substring OR fuzzy
                    if q.lower() in text.lower() or fuzzy_match(q.lower(), text.lower()):
                        new_fields.append(f)
            filtered_fields = new_fields

            # blocks
            new_blocks = []
            for b in filtered_blocks:
                text = b.get("text", "") + " " + b.get("context", "")
                if use_regex and regex:
                    if regex.search(text):
                        new_blocks.append(b)
                else:
                    if q.lower() in text.lower() or fuzzy_match(q.lower(), text.lower()):
                        new_blocks.append(b)
            filtered_blocks = new_blocks

        # === BUSCAR EN BLOQUES CLASIFICADOS Y CAMPOS EXTRACTADOS ===
        # Buscar en todo el texto de bloques si el keyword no coincide con campos
        if keyword and not filtered_fields:
            q = keyword.strip().lower()
            for b in blocks:
                text = (b.get("text", "") + " " + b.get("context", "")).lower()
                if q in text or fuzzy_match(q, text):
                    # Crear campo virtual desde el bloque
                    filtered_fields.append({
                        "field": "text_match",
                        "value": b.get("text", "")[:100],
                        "page": b.get("page"),
                        "context": b.get("context", ""),
                        "confidence": b.get("confidence")
                    })

        # --- Rendering helpers: DataTable for fields & blocks ---
        def dt_from_records(records, id_prefix):
            if not records:
                return html.Div("No hay registros.", className="text-muted fst-italic")
            # columns desde todas las keys
            keys = list({k for r in records for k in r.keys()})
            columns = [{"name": k, "id": k} for k in keys]

            table = dash_table.DataTable(
                id=f"{id_prefix}-datatable",
                columns=columns,
                data=records,
                page_size=8,
                style_table={"overflowX": "auto", "maxWidth": "100%"},
                style_header={
                    "backgroundColor": "#0e1620",
                    "fontWeight": "600",
                    "color": "#cfe6ff",
                    "border": "none"
                },
                style_cell={
                    "backgroundColor": "transparent",
                    "color": "#e6eef8",
                    "textAlign": "left",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "padding": "8px",
                    "fontSize": "0.9rem"
                },
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "rgba(255,255,255,0.01)"
                    },
                    {
                        "if": {"state": "active"},
                        "backgroundColor": "linear-gradient(90deg, rgba(63,144,255,0.12), rgba(32,96,160,0.08))"
                    },
                ],
                style_as_list_view=True,
                row_selectable="single",
                selected_rows=[],
                tooltip_delay=500,
                tooltip_duration=None,
            )
            return table

        overlays = doc_ctx.get("overlays") or []
        overlay_comp = html.Div()
        if overlays:
            page_overlay = overlays[0]
            image_src_local = page_overlay.get("path") or page_overlay.get("image") or ""
            image_src = _overlay_local_to_url(image_src_local) if image_src_local else ""
            print(f"Ruta a la imagen: {image_src}")
            if image_src:
                overlay_comp = html.Div([
                    html.H6(
                        "Preview de Páginas y Overlays"
                    ),
                    html.Div(
                        className="pdf-overlay-wrapper",
                        style={"position": "relative"},
                        children=[
                            html.Img(
                                src=image_src,
                                id="pdf-overlay-img",
                                style={"width": "100%", "height": "auto", "display": "block"},
                                alt="Preview"
                            ),
                            html.Div(
                                id="pdf-overlay-layer",
                                children=[],
                                style={
                                    "position": "absolute",
                                    "top": 0,
                                    "left": 0,
                                    "width": "100%",
                                    "height": "100%",
                                    "pointerEvents": "none"
                                }
                            )
                        ]
                    ),
                    html.Div("Click en una fila de 'Bloques' para mostrar bbox e información.", className="text-muted-small mt-2")
                ])

        # --- JSON crudo + descarga ---
        raw_json_str = json.dumps(doc_ctx, indent=2, ensure_ascii=False)
        json_comp = html.Div([
            html.H6("JSON del documento"),
            dbc.Button("Copiar JSON", id="copy-json-btn", color="outline-secondary", size="sm", className="mb-2"),
            html.Pre(
                raw_json_str[:12000],
                style={
                    "maxHeight": "360px",
                    "overflow": "auto",
                    "background": "#f8f9fa",
                    "padding": "10px",
                    "borderRadius": "6px"
                }
            ),
            html.Div("JSON truncado en vista; disponible descarga completa.", className="small text-muted"),
            # si quieres permitir descarga, crea un endpoint /download/<doc_id> que sirva file
            dbc.Button("Descargar JSON completo", id="download-json-btn", color="secondary", outline=True, size="sm")
        ])

        # --- Embeddings: mostrar info y top-k si se pide (sin ejecutar búsqueda aquí) ---
        # emb_info = html.Div()
        # emb = doc_ctx.get("embedding")
        # if isinstance(emb, dict) and emb.get("saved"):
        #     shape = emb.get("shape")
        #     emb_info = html.Div([
        #         html.H6("Info de embeddings"),
        #         html.Ul([
        #             html.Li(f"Archivo: {emb.get('saved')}"),
        #             html.Li(f"Dimensiones: {shape}"),
        #         ], className="small")
        #     ])

        # --- Componer layout final con pestañas internas (el contenedor principal que devuelve el callback) ---
        children_01 = [
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Ul([
                            html.Li([
                                html.B("File: "),
                                meta['file_name']
                            ]),
                            html.Li([
                                html.B("Type: "),
                                meta['pdf_type']
                            ]),
                            html.Li([
                                html.B("Pages: "),
                                meta['pages']
                            ]),
                            html.Li([
                                html.B("Fields: "),
                                meta['num_fields']
                            ]),
                        ])
                    ], md=10),
                    dbc.Col([
                        # emb_info
                    ], md=2)
                ]),
            ])
        ]

        children = [
            html.Div([
                html.Small(
                    f"Saved JSON: {doc_ctx.get('logs', {}).get('saved_path') or 'not saved'}",
                    className="text-secondary"
                ),
                html.Hr(),
                # === REPORTE DE PROCESAMIENTO ===
                *(
                    [
                        dbc.Card([
                            dbc.CardHeader(
                                [html.H4("📊 Reporte de Procesamiento", className="center-color")],
                                className="bg-primary"
                            ),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Small(html.B("Processing Time:")),
                                        html.Br(),
                                        html.Small(f"{doc_ctx.get('report', {}).get('ocr_time', 0):.2f}s")
                                    ], md=3),
                                    dbc.Col([
                                        html.Small(html.B("Campos Extraídos:")),
                                        html.Br(),
                                        html.Small(f"{doc_ctx.get('report', {}).get('extracted_fields', 0)}")
                                    ], md=3),
                                    dbc.Col([
                                        html.Small(html.B("Bloques Clasificados:")),
                                        html.Br(),
                                        html.Small(f"{doc_ctx.get('report', {}).get('classified_blocks', 0)} / {doc_ctx.get('report', {}).get('total_blocks', 0)}")
                                    ], md=3),
                                    dbc.Col([
                                        html.Small(html.B("Tasa de Clasificación: ")),
                                        html.Br(),
                                        html.Small(f"{doc_ctx.get('report', {}).get('classification_rate', '0%')}")
                                    ], md=3),
                                ]),
                                html.Hr(className="my-2"),
                                html.Ul([
                                    html.Li([
                                        html.B("Confianza OCR: "),
                                        doc_ctx.get('report', {}).get('ocr_confidence', 'N/A')
                                    ]),
                                    html.Li([
                                        html.B("Lenguaje OCR: "),
                                        doc_ctx.get('report', {}).get('ocr_language', 'eng')
                                    ]),
                                    html.Li([
                                        html.B("DPI: "),
                                        doc_ctx.get('report', {}).get('ocr_dpi', 300)
                                    ])
                                ])
                            ])
                        ], color="info", outline=True, className="mb-3")
                    ] if doc_ctx.get("report") else []
                ),
                # TABS: Overview | Fields | Blocks | Pages | JSON | Embeddings
                dbc.Tabs([
                    dbc.Tab(label="Overview", tab_id="overview_tab", children=[
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H4("Vista rápida", className="center-color")],
                                    className="bg-primary"
                                ),
                                dbc.CardBody([
                                    dt_from_records(fields[:10], "overview-fields"),
                                    html.Hr(),
                                    overlay_comp
                                ]),
                            ]),
                        ], className="p-2")
                    ]),
                    dbc.Tab(label=f"Campos ({len(filtered_fields)})", tab_id="fields_tab", children=[
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H4("Campos detectados", className="center-color")],
                                    className="bg-primary"
                                ),
                                dbc.CardBody([
                                    dt_from_records(filtered_fields, "fields"),
                                    html.Div(
                                        "Selecciona una fila para ver contexto y copiar valor.",
                                        className="small text-muted"
                                    )
                                ])
                            ]),
                        ], className="p-2")
                    ]),
                    dbc.Tab(label=f"Bloques ({len(filtered_blocks)})", tab_id="blocks_tab", children=[
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H4("Bloques (texto, tipo, página)", className="center-color")],
                                    className="bg-primary"
                                ),
                                dbc.CardBody([
                                    dt_from_records(filtered_blocks, "blocks"),
                                    html.Div("Selecciona un bloque para ver bbox en el preview.", className="small text-muted")
                                ]),
                            ]),
                        ], className="p-2")
                    ]),
                    dbc.Tab(label="Páginas", tab_id="pages_tab", children=[
                        html.Div([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H4("Páginas y Overlays", className="center-color")],
                                    className="bg-primary"
                                ),
                                dbc.CardBody([
                                    overlay_comp
                                ])
                            ]),
                        ], className="p-2")
                    ]),
                    dbc.Tab(label="JSON", tab_id="json_tab", children=[
                        dbc.Card([
                            dbc.CardBody([json_comp])
                        ]),
                    ]),
                ], active_tab="overview_tab")
            ], className="container-fluid")
        ]

        return children_01, children

    # ===== AUTO-UPDATE PDF ANALYSIS cuando cambia doc-context =====
    @app.callback(
        [
            Output("pdf-summary-output", "children", allow_duplicate=True),
            Output("pdf-analysis-output", "children", allow_duplicate=True),
        ],
        Input("doc-context", "data"),
        prevent_initial_call=True,
    )
    def auto_update_pdf_analysis(doc_ctx):
        """Actualiza automáticamente el PDF Analysis cuando cambia doc-context (ej: OCR Processing)."""
        if not doc_ctx:
            raise PreventUpdate

        # Generar resumen
        meta = {
            "file_name": doc_ctx.get("file_name"),
            "pdf_type": doc_ctx.get("pdf_type"),
            "pages": len(doc_ctx.get("pages", [])),
            "num_fields": len(doc_ctx.get("fields", [])),
            "embedding": doc_ctx.get("embedding"),
            "ocr_language": doc_ctx.get("ocr_language"),
            "ocr_average_confidence": doc_ctx.get("ocr_average_confidence"),
        }

        summary_content = [
            html.H6("Información del Documento", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Small(html.B("Archivo:")), html.Br(),
                    html.Small(meta["file_name"] or "N/A")
                ], md=6),
                dbc.Col([
                    html.Small(html.B("Tipo:")), html.Br(),
                    html.Small(meta["pdf_type"] or "N/A")
                ], md=6),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Small(html.B("Páginas:")), html.Br(),
                    html.Small(str(meta["pages"]))
                ], md=6),
                dbc.Col([
                    html.Small(html.B("Campos:")), html.Br(),
                    html.Small(str(meta["num_fields"]))
                ], md=6),
            ]),
        ]

        if meta.get("ocr_language"):
            summary_content.extend([
                dbc.Row([
                    dbc.Col([
                        html.Small(html.B("OCR Idioma:")), html.Br(),
                        html.Small(meta["ocr_language"])
                    ], md=6),
                    dbc.Col([
                        html.Small(html.B("OCR Confianza:")), html.Br(),
                        html.Small(f"{meta.get('ocr_average_confidence', 0):.1f}%" if meta.get('ocr_average_confidence') else "N/A")
                    ], md=6),
                ], className="mt-2"),
            ])

        # Resumen de campos y bloques
        fields = doc_ctx.get("fields", []) or []
        blocks = doc_ctx.get("classified_blocks", []) or []

        overview_content = []

        # SECCIÓN: Campos
        overview_content.append(html.H6("Primeros 10 Campos Detectados", className="mb-2"))

        if fields:
            # Generar tabla de campos
            keys = list({k for r in fields[:10] for k in r.keys()})
            columns = [{"name": k, "id": k} for k in keys]

            table = dash_table.DataTable(
                id="auto-overview-fields-datatable",
                columns=columns,
                data=fields[:10],
                page_size=8,
                style_table={"overflowX": "auto", "maxWidth": "100%"},
                style_header={
                    "backgroundColor": "#0e1620",
                    "fontWeight": "600",
                    "color": "#cfe6ff",
                    "border": "none"
                },
                style_cell={
                    "backgroundColor": "transparent",
                    "color": "#e6eef8",
                    "textAlign": "left",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "padding": "8px",
                    "fontSize": "0.9rem"
                },
            )
            overview_content.append(table)
        else:
            overview_content.append(html.Small("No se detectaron campos", className="text-muted"))

        # SECCIÓN: Bloques (del OCR o extracción)
        overview_content.append(html.Hr(className="mt-4 mb-2"))
        overview_content.append(html.H6("Primeros 10 Bloques Extraídos", className="mb-2"))

        if blocks:
            # Generar tabla de bloques
            keys = list({k for r in blocks[:10] for k in r.keys()})
            columns = [{"name": k, "id": k} for k in keys]

            table_blocks = dash_table.DataTable(
                id="auto-overview-blocks-datatable",
                columns=columns,
                data=blocks[:10],
                page_size=8,
                style_table={"overflowX": "auto", "maxWidth": "100%"},
                style_header={
                    "backgroundColor": "#0e1620",
                    "fontWeight": "600",
                    "color": "#cfe6ff",
                    "border": "none"
                },
                style_cell={
                    "backgroundColor": "transparent",
                    "color": "#e6eef8",
                    "textAlign": "left",
                    "whiteSpace": "normal",
                    "height": "auto",
                    "padding": "8px",
                    "fontSize": "0.9rem"
                },
            )
            overview_content.append(table_blocks)
        else:
            overview_content.append(html.Small("No se detectaron bloques", className="text-muted"))

        return summary_content, overview_content
