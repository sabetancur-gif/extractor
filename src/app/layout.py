# src/app/layout.py
r"""Construcción del layout principal (Marcado y etiquetas ).

Define el layout principal de la app Dash (Navbar, Sidebar, Tabs, Stores, etc).
Expone la función layout() y get_tabs_layout().

IDs Dash usados (para trazabilidad callbacks/layout):
    - upload-store, doc-context, sidebar-state, download-md, download-html, download-visualization
    - btn-toggle-sidebar, page-content, sidebar, sidebar-tabs
    - tab-visualization-content, tab-pdf-analysis-content, tab-ocr-processing-content, tab-format-conversion-content, tab-translation-content, tab-toc-extraction-content, tab-clustering-content
    - visualization-pdf-selector, analysis-target, run-analysis, summary-output, pdf-preview, download-visualization-btn, overlay-prev-viz, overlay-next-viz, overlay-page-indicator-viz
    - analysis-search-keyword, analysis-search-field, analysis-search-btn, pdf-summary-output, pdf-analysis-output
    - ocr-language, ocr-dpi, ocr-preprocess, ocr-show-confidence, run-ocr, ocr-progress-store, ocr-progress-bar, ocr-output, overlay-prev-ocr, overlay-next-ocr, overlay-page-indicator-ocr
    - convert-md, convert-html, run-translation, target-language, translation-output, extract-toc, toc-output
    - clustering-reduction, clustering-method, clustering-param, run-clustering, clustering-output
    - global-data-store, pdf-files-store, upload-state-store, overlay-page-index
"""

# THIRDPARTY
from dash import dcc, html
import dash_bootstrap_components as dbc

from src.app.ui.pdf_analysis_panel import pdf_analysis_panel
from src.app.ui.llm_analysis_panel import llm_analysis_panel


def layout():
    r"""Layout principal de la app Dash.

    Construye la estructura principal de la UI (Navbar, Sidebar, Tabs, Stores).
    """
    return dbc.Container([

        # === STORES / DOWNLOADS ===
        dcc.Store(id="upload-store"),
        dcc.Store(id="doc-context"),

        dcc.Store(id="sidebar-state", data=True),

        dcc.Store(id="llm-context", data={}),
        dcc.Store(id="analysis-view-state", data={"index": 0, "key": "fields"}),

        dcc.Download(id="download-md"),
        dcc.Download(id="download-html"),
        dcc.Download(id="download-visualization"),

        dcc.Store(id="analysis-result-store", data={}),

        # === NAVBAR ===
        dbc.Navbar(
            dbc.Container(
                [
                    html.Button(
                        html.I(className="bi-list"),
                        id="btn-toggle-sidebar",
                        className="btn text-white me-3",
                        style={"textDecoration": "none"}
                    ),

                    # Grid of 4 columns: [space][space][space][title]
                    html.Div(
                        [
                            # Col 1: space (empty)
                            html.Div(),

                            # Col 2: space (empty)
                            html.Div(),

                            # Col 3: space (empty)
                            html.Div(),

                            # Col 4: title (75%)
                            html.Div(
                                dbc.NavbarBrand(
                                    "PDF Analyzer",
                                    className="fw-bold text-white mb-0"
                                ),
                                className="title-cell"
                            ),
                        ],
                        className="navbar-grid w-100"
                    )
                ],
                fluid=True,
                className="px-3"
            ),
            color="dark",
            dark=True,
            className="shadow-sm fixed-top",
            style={"height": "90px"}
        ),

        # === CONTENEDOR - TODOS LOS TABS SE RENDERIZAN AQUÍ ===
        html.Div(
            id="page-content",
            style={
                "marginLeft": "260px",
                "padding": "2rem",
                "marginTop": "100px",
                "transition": "margin-left 0.3s ease"
            },
            children=[get_tabs_layout()]  # Renderiza todos los tabs (visibilidad controlada por callbacks)
        ),

        # === SIDEBAR ===
        html.Div(
            id="sidebar",
            children=[
                dbc.Tabs(
                    id="sidebar-tabs",
                    active_tab="tab-visualization",
                    children=[
                        dbc.Tab(
                            label="Visualization",
                            tab_id="tab-visualization",
                            tabClassName="sidebar-tab",
                            labelClassName="tab-icon tab-icon-eye"
                        ),
                        dbc.Tab(
                            label="OCR Processing",
                            tab_id="tab-ocr-processing",
                            tabClassName="sidebar-tab",
                            labelClassName="tab-icon tab-icon-ocr"
                        ),
                        dbc.Tab(
                            label="PDF Analysis",
                            tab_id="tab-pdf-analysis",
                            tabClassName="sidebar-tab",
                            labelClassName="tab-icon tab-icon-pdf"
                        ),
                        dbc.Tab(
                            label="LLM Enrichment",
                            tab_id="tab-llm-analysis",
                            tabClassName="sidebar-tab",
                            labelClassName="tab-icon tab-icon-ai",
                        ),
                        dbc.Tab(
                            label="Format Conversion",
                            tab_id="tab-format-conversion",
                            tabClassName="sidebar-tab",
                            labelClassName="tab-icon tab-icon-convert"
                        ),
                        dbc.Tab(
                            label="Translation",
                            tab_id="tab-translation",
                            tabClassName="sidebar-tab",
                            labelClassName="tab-icon tab-icon-translate"
                        ),
                        dbc.Tab(
                            label="TOC Extraction",
                            tab_id="tab-toc-extraction",
                            tabClassName="sidebar-tab",
                            labelClassName="tab-icon tab-icon-toc"
                        ),
                        dbc.Tab(
                            label="Clustering",
                            tab_id="tab-clustering",
                            tabClassName="sidebar-tab",
                            labelClassName="tab-icon tab-icon-cluster"
                        ),
                    ],
                    className="flex-column nav-pills"
                )
            ],
            style={
                "position": "fixed",
                "top": "100px",
                "left": 0,
                "bottom": 0,
                "width": "280px",
                "padding": "1rem",
                "backgroundColor": "#2f2f2f",  # más claro que el dark theme
                "borderRight": "3px solid #E3530F",
                "overflowY": "auto",
                "transition": "transform 0.3s ease",
            }
        ),
    ], fluid=True)


def get_tabs_layout():
    r"""Layouts secundarios: define el contenido de cada tab.

    Cada tab tiene su propio contenedor y componentes.
    """
    return html.Div([
        # Store global para datos compartidos entre tabs
        dcc.Store(id="global-data-store", data={}),
        dcc.Store(id="pdf-files-store", data={}),
        dcc.Store(id="upload-state-store", data={"uploaded": False}),
        dcc.Store(id="overlay-page-index", data={"viz": 0, "ocr": 0}),  # Índice de overlay actual para cada tab

        # ==================== TAB 1: VISUALIZATION ====================
        html.Div(
            id="tab-visualization-content",
            style={"display": "block"},  # Mostrado por defecto
            children=[
                dbc.Row([
                    # First column: Upload card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(
                                [html.H4("Upload your PDF", className="center-color")],
                                className="bg-primary"
                            ),
                            dbc.CardBody([
                                html.Div([
                                    dcc.Upload(
                                        id="upload-pdf",
                                        children=html.Div(
                                            [
                                                html.I(className="bi-cloud-upload"),
                                                html.Span("Drag here or click to upload")
                                            ],
                                            className="upload-content"
                                        ),
                                        className="upload-area mb-3",
                                        multiple=True,
                                    ),
                                    dbc.Tooltip(
                                        "You can upload one or more PDF files to analyze.",
                                        target="upload-pdf",
                                        placement="top"
                                    ),
                                ]),
                                dbc.Checkbox(
                                    id="fast-mode",
                                    label="Fast Mode",
                                    className="mb-2"
                                ),
                                dbc.Button(
                                    "Create Visualization",
                                    id="run-analysis",
                                    color="primary",
                                    className="w-100 mb-2 fw-bold shadow-sm"
                                ),
                                dbc.Tooltip(
                                    "Process the PDF and generate the display of blocks and fields.",
                                    target="run-analysis",
                                    placement="top",
                                    style={"fontSize": "1rem"}
                                ),
                                dcc.Dropdown(
                                    id="analysis-target",
                                    placeholder="Select File(s) to Analyze",
                                    className="mb-2 dropdown-gradient",
                                    clearable=True,
                                    multi=True
                                ),
                                dcc.Dropdown(
                                    id="visualization-pdf-selector",
                                    placeholder="Select PDF to Preview",
                                    className="mb-2 dropdown-gradient",
                                    clearable=True,
                                    multi=False
                                ),
                            ]),
                        ], className="shadow-lg border-0"),
                    ], md=4),

                    # Second column: Summary and preview card
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(
                                [html.H4("Summary and Preview", className="center-color")],
                                className="bg-primary"
                            ),
                            dbc.CardBody([
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        [
                                                            html.I(className="bi-clipboard-data me-2"),
                                                            html.Span("Summary", className="fw-bold")
                                                        ],
                                                        className="bg-primary text-white"
                                                    ),
                                                    dbc.CardBody(
                                                        html.Div(
                                                            id="summary-output",
                                                            className="summary-output",
                                                            style={"minHeight": "120px"}
                                                        )
                                                    ),
                                                ],
                                                className="shadow-lg border-0 mb-3"
                                            ),
                                            md=9, xs=12, className="mb-3"
                                        ),
                                        dbc.Col(
                                            html.Div(
                                                html.I(className="bi-clipboard-data"),
                                                className="summary-logo-wrapper"
                                            ),
                                            md=3, xs=12,
                                            className="mb-3"
                                        ),
                                    ],
                                    className="g-3"
                                ),
                                dbc.Button(
                                    "Download Visualization",
                                    id="download-visualization-btn",
                                    color="primary",
                                    className="w-100 mb-2 fw-bold shadow-sm",
                                    disabled=True
                                ),
                                dbc.Tooltip(
                                    "Download the generated visualization image.",
                                    target="download-visualization-btn",
                                    placement="top",
                                    style={"fontSize": "1rem"}
                                ),
                                html.Div([
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Button(
                                                html.I(className="bi-chevron-left"),
                                                id="overlay-prev-viz",
                                                size="lg",
                                                color="secondary",
                                                className="w-100",
                                                n_clicks=0
                                            )
                                        ], width=1),
                                        dbc.Col([
                                            html.Div(
                                                html.Img(
                                                    id="pdf-preview",
                                                    className="w-100 rounded border shadow-sm",
                                                    style={"marginTop": "10px"}
                                                ),
                                                style={"textAlign": "center"}
                                            )
                                        ], width=10),
                                        dbc.Col([
                                            dbc.Button(
                                                html.I(className="bi-chevron-right"),
                                                id="overlay-next-viz",
                                                size="lg",
                                                color="secondary",
                                                className="w-100",
                                                n_clicks=0
                                            )
                                        ], width=1),
                                    ], className="align-items-center"),
                                    html.Div(
                                        id="overlay-page-indicator-viz",
                                        style={"textAlign": "center", "marginTop": "5px", "fontSize": "0.9rem"},
                                        children="Page 0/0"
                                    )
                                ]),
                            ]),
                        ], className="shadow-lg border-0"),
                    ])
                ])
            ]
        ),

        # ==================== TAB 2: PDF ANALYSIS ====================
        html.Div(
            id="tab-ocr-processing-content",
            style={"display": "none"},
            children=[
                dbc.Container([
                    dbc.Card([
                        dbc.CardHeader("OCR", className="center-color"),

                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Row([
                                        dbc.Col([
                                            # Dropdown de documentos procesados
                                            dcc.Dropdown(
                                                id="ocr-doc-selector",
                                                # Se llenará dinámicamente con la lista de documentos procesados
                                                options=[],
                                                placeholder="Selecciona el documento para OCR",
                                                className="mb-2 dropdown-gradient",
                                                clearable=False,
                                                multi=False
                                            ),
                                            dbc.Tooltip(
                                                "Documento a procesar",
                                                target="ocr-doc-selector",
                                                placement="top",
                                                style={"fontSize": "1rem"}
                                            ),
                                        ], md=6),
                                        dbc.Col([
                                            dbc.Select(
                                                id="ocr-language",
                                                options=[{"label": "English", "value": "eng"}, {"label": "Spanish", "value": "spa"}],
                                                value="eng",
                                                className="mb-2 shadow-sm"
                                            ),
                                            dbc.Tooltip(
                                                "Idioma OCR",
                                                target="ocr-language",
                                                placement="top",
                                                style={"fontSize": "1rem"}
                                            ),
                                        ], md=3),
                                        dbc.Col([
                                            dbc.Input(
                                                id="ocr-dpi",
                                                type="number",
                                                min=100,
                                                max=600,
                                                step=50,
                                                value=300,
                                                className="mb-2 shadow-sm"
                                            ),
                                            dbc.Tooltip(
                                                "DPI (Resolución)",
                                                target="ocr-dpi",
                                                placement="top",
                                                style={"fontSize": "1rem"}
                                            ),
                                        ], md=3),
                                    ]),
                                    dbc.Row(
                                        dbc.Col([
                                            dbc.Checkbox(id="ocr-show-confidence", value=True, className="me-2"),
                                            dbc.Label("Mostrar confianza OCR", html_for="ocr-show-confidence"),
                                        ], md=4)
                                    ),
                                    html.Br(),
                                    dbc.Row(
                                        dbc.Col([
                                            dbc.Button(
                                                "Ejecutar OCR",
                                                id="run-ocr",
                                                color="warning",
                                                className="mb-2 w-100 fw-bold shadow-sm"
                                            ),
                                        ], md=12)
                                    ),
                                ], md=8),
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardHeader("Preprocesado", className="center-color"),
                                        dbc.CardBody([
                                            dbc.Checklist(
                                                options=[
                                                    {"label": html.Span("Denoise", id="tooltip-denoise"), "value": "denoise"},
                                                    {"label": html.Span("Threshold", id="tooltip-threshold"), "value": "threshold"},
                                                    {"label": html.Span("Deskew", id="tooltip-deskew"), "value": "deskew"},
                                                ],
                                                value=["denoise", "threshold", "deskew"],
                                                id="ocr-preprocess",
                                                inline=True,
                                                switch=True,
                                                className="mb-2"
                                            ),
                                        ], className="shadow-lg border-0 mb-3"),
                                    ]),
                                ], md=4),
                                dbc.Tooltip(
                                    "Reduce ruido visual para mejorar la legibilidad del texto.",
                                    target="tooltip-denoise",
                                    placement="top",
                                    style={"fontSize": "1rem"},
                                ),
                                dbc.Tooltip(
                                    "Convierte la imagen a blanco y negro para resaltar el texto.",
                                    target="tooltip-threshold",
                                    placement="top",
                                    style={"fontSize": "1rem"},
                                ),
                                dbc.Tooltip(
                                    "Corrige la inclinación del documento escaneado.",
                                    target="tooltip-deskew",
                                    placement="top",
                                    style={"fontSize": "1rem"},
                                ),
                            ]),
                        ]),
                    ], className="shadow-lg border-0 mb-3"),

                    html.Hr(),

                    # Store para progreso y overlays
                    dcc.Store(
                        id="ocr-progress-store",
                        data={"progress": 0, "status": "", "page": 1, "total_pages": 1, "overlays": []}
                    ),

                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H5("Visualización OCR", className="center-color")),
                                dbc.CardBody([
                                    # Barra superior de navegación
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Button(
                                                html.I(className="bi-chevron-left"),
                                                id="overlay-prev-ocr",
                                                size="sm",
                                                color="secondary",
                                                n_clicks=0,
                                                className="mb-2"
                                            )
                                        ], width="auto"),
                                        dbc.Col([
                                            # Barra de progreso visual
                                            dbc.Progress(
                                                id="ocr-progress-bar",
                                                value=0,
                                                max=100,
                                                striped=True,
                                                animated=True,
                                                className="mb-2 ocr-progress-custom",
                                                style={"height": "22px"}
                                            ),
                                        ], style={"flexGrow": 1}, width=True),
                                        dbc.Col([
                                            dbc.Button(
                                                html.I(className="bi-chevron-right"),
                                                id="overlay-next-ocr",
                                                size="sm",
                                                color="secondary",
                                                n_clicks=0,
                                                className="mb-2"
                                            )
                                        ], width="auto"),
                                    ], className="align-items-center", style={"gap": "10px"}),

                                    html.Div(
                                        id="ocr-output",
                                        className="mt-2",
                                        style={
                                            "height": "65vh",
                                            "overflowY": "auto",
                                            "width": "100%",
                                        }
                                    ),

                                    html.Div(
                                        id="overlay-page-indicator-ocr",
                                        style={"textAlign": "center", "marginTop": "10px", "fontSize": "0.85rem"},
                                        children="Página 0/0"
                                    ),
                                ])
                            ], className="shadow-lg border-0 mb-3"),
                        ], md=6, xs=12),

                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H5("Información OCR", className="center-color")),
                                dbc.CardBody(
                                    html.Div(id="ocr-messages")
                                )
                            ], className="shadow-lg border-0 mb-3"),
                        ], md=6, xs=12),
                    ], className="g-3 align-items-start"),
                ], fluid=True)
            ]
        ),

        # ==================== TAB 3: PDF Analysis ====================
        html.Div(
            id="tab-pdf-analysis-content",
            style={"display": "none"},
            children=[pdf_analysis_panel()],
        ),
        # html.Div(
        #     id="tab-pdf-analysis-content",
        #     style={"display": "none"},
        #     children=[

        #         dbc.Row([

        #             # First column: Advanced Search, Document Selector y Summary doc
        #             dbc.Col([

        #                 # Nuevo Dropdown para seleccionar documento procesado
        #                 dbc.Card([
        #                     dbc.CardHeader(
        #                         [html.H4("Selecciona documento procesado", className="center-color")],
        #                         className="bg-primary"
        #                     ),
        #                     dbc.CardBody([
        #                         dcc.Dropdown(
        #                             id="analysis-doc-selector",
        #                             options=[],  # Se llenará dinámicamente con la lista de documentos procesados
        #                             placeholder="Selecciona el documento para análisis",
        #                             className="mb-2 dropdown-gradient",
        #                             clearable=False,
        #                             multi=False
        #                         ),
        #                         dbc.Tooltip(
        #                             "Documento a consultar",
        #                             target="analysis-doc-selector",
        #                             placement="top",
        #                             style={"fontSize": "1rem"}
        #                         )
        #                     ]),
        #                 ], className="shadow-lg border-0 mb-3"),

        #                 dbc.Card([
        #                     dbc.CardHeader(
        #                         [html.H4("Advanced analysis and search", className="center-color")],
        #                         className="bg-primary"
        #                     ),
        #                     dbc.CardBody([
        #                         html.Div([
        #                             html.P("Explore metadata, structure and extracted text.", className="text-info-center"),
        #                         ]),
        #                         dbc.Input(id="analysis-search-keyword", placeholder="Search for keywords...", type="text", className="mb-2 shadow-sm"),
        #                         dbc.Tooltip(
        #                             "Search for any word or keyword extracted from the document.",
        #                             target="analysis-search-keyword",
        #                             placement="top",
        #                             style={"fontSize": "1rem"}
        #                         ),
        #                         dbc.Select(
        #                             id="analysis-search-field",
        #                             options=[],
        #                             placeholder="Filter by field type",
        #                             className="mb-2 shadow-sm"
        #                         ),
        #                         dbc.Tooltip(
        #                             "Filter results by field or block type.",
        #                             target="analysis-search-field",
        #                             placement="top",
        #                             style={"fontSize": "1rem"}
        #                         ),
        #                         dbc.Button("Search", id="analysis-search-btn", color="primary", className="mb-2 w-100 fw-bold shadow-sm"),
        #                         dbc.Tooltip(
        #                             "Run an advanced search in the document.",
        #                             target="analysis-search-btn",
        #                             placement="top",
        #                             style={"fontSize": "1rem"}
        #                         ),
        #                     ]),
        #                 ], className="shadow-lg border-0 mb-3"),

        #                 dbc.Card([
        #                     dbc.CardHeader(
        #                         [html.H4("Summary of the document", className="center-color")],
        #                         className="bg-primary"
        #                     ),
        #                     dbc.CardBody([
        #                         html.Div(id="pdf-summary-output", className="mt-2"),
        #                     ]),
        #                 ], className="shadow-lg border-0 mb-3"),

        #                 dbc.Card([
        #                     dbc.CardHeader(
        #                         [html.H4("Automatic document overview", className="center-color")],
        #                         className="bg-primary"
        #                     ),
        #                     dbc.CardBody([
        #                         html.Div(id="pdf-auto-analysis-output", className="mt-2"),
        #                     ]),
        #                 ], className="shadow-lg border-0 mb-3"),

        #             ], md=4),

        #             dbc.Col([
        #                 html.Div(id="pdf-analysis-output", className="mt-2"),
        #             ], md=8)
        #         ]),
        #     ]
        # ),

        # ==================== TAB 4: LLM ANALYSIS ====================
        html.Div(
            id="tab-llm-analysis-content",
            style={"display": "none"},
            children=[llm_analysis_panel()],
        ),
        # html.Div(
        #     id="tab-llm-analysis-content",
        #     style={"display": "none"},
        #     children=[
        #         dbc.Container(
        #             [
        #                 dbc.Row(
        #                     [
        #                         dbc.Col(
        #                             dbc.Card(
        #                                 [
        #                                     dbc.CardHeader(html.H4("LLM Enrichment", className="center-color")),
        #                                     dbc.CardBody(
        #                                         [
        #                                             dcc.Dropdown(
        #                                                 id="llm-doc-selector",
        #                                                 options=[],
        #                                                 placeholder="Selecciona el documento",
        #                                                 clearable=False,
        #                                                 className="mb-2 dropdown-gradient",
        #                                             ),
        #                                             dcc.Dropdown(
        #                                                 id="llm-mode",
        #                                                 options=[
        #                                                     {"label": "Auto fill missing", "value": "auto_fill_missing"},
        #                                                     {"label": "Summarize", "value": "summarize"},
        #                                                     {"label": "Describe images/tables", "value": "describe_assets"},
        #                                                 ],
        #                                                 value="auto_fill_missing",
        #                                                 clearable=False,
        #                                                 className="mb-2 dropdown-gradient",
        #                                             ),
        #                                             dbc.Button(
        #                                                 "Run LLM enrichment",
        #                                                 id="run-llm-btn",
        #                                                 color="primary",
        #                                                 className="w-100 fw-bold shadow-sm",
        #                                             ),
        #                                         ]
        #                                     ),
        #                                 ],
        #                                 className="shadow-lg border-0 mb-3",
        #                             ),
        #                             md=4,
        #                         ),
        #                         dbc.Col(
        #                             [
        #                                 dbc.Card(
        #                                     [
        #                                         dbc.CardHeader(html.H5("LLM summary", className="center-color")),
        #                                         dbc.CardBody(html.Div(id="llm-summary-output")),
        #                                     ],
        #                                     className="shadow-lg border-0 mb-3",
        #                                 ),
        #                                 dbc.Card(
        #                                     [
        #                                         dbc.CardHeader(html.H5("LLM results", className="center-color")),
        #                                         dbc.CardBody(html.Div(id="llm-results-output")),
        #                                     ],
        #                                     className="shadow-lg border-0 mb-3",
        #                                 ),
        #                             ],
        #                             md=8,
        #                         ),
        #                     ],
        #                     className="g-3",
        #                 )
        #             ],
        #             fluid=True,
        #         )
        #     ],
        # ),


        # html.Div(
        #     id="tab-ocr-processing-content",
        #     style={"display": "none"},
        #     children=[
        #         dbc.Container([
        #             html.H4("Procesamiento OCR", className="mb-2 mt-3 text-gradient-5"),
        #             dbc.Row([
        #                 dbc.Col([
        #                     dbc.Label("Documento a procesar"),
        #                     # Dropdown de documentos procesados (igual que visualization-pdf-selector)
        #                     dcc.Dropdown(
        #                         id="ocr-doc-selector",
        #                         options=[],  # Se llenará dinámicamente con la lista de documentos procesados
        #                         placeholder="Selecciona el documento para OCR",
        #                         className="mb-2 dropdown-gradient",
        #                         clearable=False,
        #                         multi=False
        #                     ),
        #                 ], md=4),
        #                 dbc.Col([
        #                     dbc.Label("Idioma OCR"),
        #                     dbc.Select(id="ocr-language", options=[{"label": "English", "value": "eng"}, {"label": "Spanish", "value": "spa"}], value="eng", className="mb-2 shadow-sm"),
        #                 ], md=2),
        #                 dbc.Col([
        #                     dbc.Label("DPI (Resolución)"),
        #                     dbc.Input(id="ocr-dpi", type="number", min=100, max=600, step=50, value=300, className="mb-2 shadow-sm"),
        #                 ], md=2),
        #                 dbc.Col([
        #                     dbc.Label("Preprocesado"),
        #                     dbc.Checklist(
        #                         options=[
        #                             {"label": "Denoise", "value": "denoise"},
        #                             {"label": "Threshold", "value": "threshold"},
        #                             {"label": "Deskew", "value": "deskew"},
        #                         ],
        #                         value=["denoise", "threshold"],
        #                         id="ocr-preprocess",
        #                         inline=True,
        #                         switch=True,
        #                         className="mb-2"
        #                     ),
        #                 ], md=4),
        #             ]),
        #             dbc.Row([
        #                 dbc.Col([
        #                     dbc.Checkbox(id="ocr-show-confidence", value=True, className="me-2"),
        #                     dbc.Label("Mostrar confianza OCR", html_for="ocr-show-confidence"),
        #                 ], md=4),
        #                 dbc.Col([
        #                     dbc.Button("Ejecutar OCR", id="run-ocr", color="warning", className="mb-2 w-100 fw-bold shadow-sm"),
        #                 ], md=8),
        #             ]),
        #             html.Hr(),
        #             # Store para progreso y overlays
        #             dcc.Store(id="ocr-progress-store", data={"progress": 0, "status": "", "page": 1, "total_pages": 1, "overlays": []}),
        #             dbc.Row([
        #                 dbc.Col([
        #                     dbc.Button(
        #                         html.I(className="bi-chevron-left"),
        #                         id="overlay-prev-ocr",
        #                         size="sm",
        #                         color="secondary",
        #                         n_clicks=0,
        #                         className="mb-2"
        #                     )
        #                 ], width="auto"),
        #                 dbc.Col([
        #                     # Barra de progreso visual
        #                     dbc.Progress(id="ocr-progress-bar", value=0, max=100, striped=True, animated=True, className="mb-2", style={"height": "22px"}),
        #                     html.Div(
        #                         id="ocr-output",
        #                         className="mt-2",
        #                         style={"maxHeight": "400px", "overflowY": "auto", "maxWidth": "600px"}
        #                     )
        #                 ], width="auto", style={"flexGrow": 1}),
        #                 dbc.Col([
        #                     dbc.Button(
        #                         html.I(className="bi-chevron-right"),
        #                         id="overlay-next-ocr",
        #                         size="sm",
        #                         color="secondary",
        #                         n_clicks=0,
        #                         className="mb-2"
        #                     )
        #                 ], width="auto"),
        #             ], className="align-items-start", style={"justifyContent": "center", "gap": "10px"}),
        #             html.Div(
        #                 id="overlay-page-indicator-ocr",
        #                 style={"textAlign": "center", "marginTop": "10px", "fontSize": "0.85rem"},
        #                 children="Page 0/0"
        #             ),
        #         ], fluid=True)
        #     ]
        # ),

        # ==================== TAB 4: FORMAT CONVERSION ====================
        html.Div(
            id="tab-format-conversion-content",
            style={"display": "none"},
            children=[
                dbc.Container([
                    html.H4("Conversión de Formato", className="mb-2 mt-3 text-gradient-6"),
                    dbc.Button("Convertir a Markdown", id="convert-md", color="secondary", className="me-2 fw-bold shadow-sm"),
                    dbc.Button("Convertir a HTML", id="convert-html", color="secondary", className="fw-bold shadow-sm"),
                ], fluid=True)
            ]
        ),

        # ==================== TAB 5: TRANSLATION ====================
        html.Div(
            id="tab-translation-content",
            style={"display": "none"},
            children=[
                dbc.Container([
                    html.H4("Traducción de Documento", className="mb-2 mt-3 text-gradient-2"),
                    dbc.Select(id="target-language", options=[{"label": "English", "value": "en"}, {"label": "Spanish", "value": "es"}, {"label": "French", "value": "fr"}], placeholder="Idioma destino", className="mb-2 shadow-sm"),
                    dbc.Button("Traducir", id="run-translation", color="success", className="mb-2 w-100 fw-bold shadow-sm"),
                    html.Hr(),
                    html.Div(id="translation-output", className="mt-2"),
                ], fluid=True)
            ]
        ),

        # ==================== TAB 6: TOC EXTRACTION ====================
        html.Div(
            id="tab-toc-extraction-content",
            style={"display": "none"},
            children=[
                dbc.Container([
                    html.H4("Extracción de Tabla de Contenidos", className="mb-2 mt-3 text-gradient-3"),
                    dbc.Button("Extraer TOC", id="extract-toc", color="info", className="mb-2 fw-bold shadow-sm"),
                    html.Div(id="toc-output", className="mt-3"),
                ], fluid=True)
            ]
        ),

        # ==================== TAB 7: CLUSTERING ====================
        html.Div(
            id="tab-clustering-content",
            style={"display": "none"},
            children=[
                dbc.Container([
                    html.H4("Clustering & Embeddings", className="mb-2 mt-3 text-gradient"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Reducción dimensional"),
                            dbc.Select(id="clustering-reduction", options=[{"label": "UMAP", "value": "umap"}, {"label": "PCA", "value": "pca"}], value="umap", className="mb-2 shadow-sm"),
                        ], md=4),
                        dbc.Col([
                            dbc.Label("Algoritmo de clustering"),
                            dbc.Select(id="clustering-method", options=[{"label": "HDBSCAN", "value": "hdbscan"}, {"label": "KMeans", "value": "kmeans"}], value="hdbscan", className="mb-2 shadow-sm"),
                        ], md=4),
                        dbc.Col([
                            dbc.Label("# Clusters (KMeans) / Min Cluster Size (HDBSCAN)"),
                            dbc.Input(id="clustering-param", type="number", min=2, max=20, step=1, value=3, className="mb-2 shadow-sm"),
                        ], md=4),
                    ]),
                    dbc.Button("Visualizar Clusters", id="run-clustering", color="primary", className="mb-2 fw-bold shadow-sm"),
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="clustering-output", className="mt-2"),
                        ], md=12),
                    ]),
                ], fluid=True)
            ]
        ),
    ])
