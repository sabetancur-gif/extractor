"""
src/app/ui/pdf_analysis_panel.py
---------------------------------
Panel de análisis de PDF: búsqueda avanzada, tabla de resultados,
crop de región y visualización de evidencia.
"""
from dash import dcc, html
import dash_bootstrap_components as dbc

# Tipos semánticos disponibles para filtro
SEMANTIC_TYPES = [
    {"label": "— Todos los tipos —",      "value": ""},
    {"label": "📅 Fecha",                 "value": "date"},
    {"label": "💰 Monto / Valor",         "value": "amount"},
    {"label": "📞 Teléfono",              "value": "phone"},
    {"label": "📧 Correo electrónico",    "value": "email"},
    {"label": "👤 Nombre",                "value": "name"},
    {"label": "✍️  Firma",                "value": "signature"},
    {"label": "📋 Título",                "value": "title"},
    {"label": "📝 Subtítulo",             "value": "subtitle"},
    {"label": "🖼️  Imagen / Figura",      "value": "figure"},
    {"label": "📊 Tabla",                 "value": "table"},
    {"label": "📄 Párrafo",               "value": "paragraph"},
    {"label": "🏠 Dirección",             "value": "address"},
    {"label": "🔢 Identificador",         "value": "identifier"},
    {"label": "🔗 URL",                   "value": "url"},
    {"label": "➗ Expresión matemática",  "value": "math_expression"},
    {"label": "💻 Código",                "value": "code"},
    {"label": "🏷️  Logo",                 "value": "logo"},
    {"label": "🔖 Encabezado",            "value": "header"},
    {"label": "📎 Pie de página",         "value": "footer"},
]


def pdf_analysis_panel() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Row(
                [
                    # ── Columna izquierda: controles ──────────────────────────
                    dbc.Col(
                        [
                            # Tarjeta de búsqueda
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.I(className="bi-search me-2", style={"color": "#E3530F"}),
                                                html.Span("PDF Analysis", className="fw-bold fs-5"),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                        style={"background": "#1e1e1e"},
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Label("Documento", className="form-label text-muted small"),
                                            dcc.Dropdown(
                                                id="analysis-target",
                                                options=[],
                                                placeholder="Selecciona el documento",
                                                clearable=False,
                                                multi=False,
                                                className="mb-3",
                                            ),
                                            html.Label("Buscar texto", className="form-label text-muted small"),
                                            dbc.InputGroup(
                                                [
                                                    dbc.InputGroupText(html.I(className="bi-search")),
                                                    dbc.Input(
                                                        id="analysis-search-keyword",
                                                        type="text",
                                                        placeholder="Palabra clave...",
                                                        debounce=False,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            html.Label("Filtrar por tipo semántico", className="form-label text-muted small"),
                                            dcc.Dropdown(
                                                id="analysis-search-field",
                                                options=SEMANTIC_TYPES,
                                                value="",
                                                clearable=True,
                                                placeholder="Filtrar por tipo...",
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                [html.I(className="bi-search me-2"), "Analizar documento"],
                                                id="analysis-search-btn",
                                                color="primary",
                                                className="w-100 fw-bold",
                                                style={"background": "#E3530F", "border": "none"},
                                            ),
                                        ],
                                        style={"background": "#1a1a1a"},
                                    ),
                                ],
                                className="border-0 shadow-sm mb-3",
                                style={"border": "1px solid #333 !important"},
                            ),

                            # Tarjeta de navegación de vistas
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.I(className="bi-layers me-2", style={"color": "#E3530F"}),
                                                html.Span("Vistas", className="fw-bold"),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                        style={"background": "#1e1e1e"},
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        html.I(className="bi-chevron-left"),
                                                        id="analysis-prev-view-btn",
                                                        color="secondary",
                                                        outline=True,
                                                        size="sm",
                                                    ),
                                                    dbc.Button(
                                                        id="analysis-view-label",
                                                        children="Campos",
                                                        color="secondary",
                                                        disabled=True,
                                                        className="px-3",
                                                        style={"minWidth": "100px"},
                                                    ),
                                                    dbc.Button(
                                                        html.I(className="bi-chevron-right"),
                                                        id="analysis-next-view-btn",
                                                        color="secondary",
                                                        outline=True,
                                                        size="sm",
                                                    ),
                                                ],
                                                className="w-100 mb-2",
                                            ),
                                            html.Small(
                                                "Navega entre: Campos · Bloques · Tablas · Firmas · "
                                                "Imágenes · Fechas · Montos · Direcciones",
                                                className="text-muted",
                                            ),
                                        ],
                                        style={"background": "#1a1a1a"},
                                    ),
                                ],
                                className="border-0 shadow-sm",
                                style={"border": "1px solid #333 !important"},
                            ),
                        ],
                        md=4,
                    ),

                    # ── Columna derecha: resultados ───────────────────────────
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.I(className="bi-file-earmark-text me-2", style={"color": "#E3530F"}),
                                                html.Span("Resultados del análisis", className="fw-bold fs-5"),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                        style={"background": "#1e1e1e"},
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Resumen automático
                                            html.Div(id="pdf-summary-output", className="mb-3"),

                                            # Tabla de resultados + crop
                                            html.Div(id="pdf-analysis-output"),

                                            # Preview del crop seleccionado
                                            html.Div(
                                                id="analysis-selection-preview",
                                                className="mt-3",
                                            ),
                                        ],
                                        style={"background": "#1a1a1a", "minHeight": "500px"},
                                    ),
                                ],
                                className="border-0 shadow-lg",
                                style={"border": "1px solid #333 !important"},
                            ),
                        ],
                        md=8,
                    ),
                ],
                className="align-items-start g-3",
            ),
        ],
        fluid=True,
        className="py-3",
    )
