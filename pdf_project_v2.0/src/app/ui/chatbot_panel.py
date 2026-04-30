"""
src/app/ui/chatbot_panel.py
---------------------------
Panel de JuanBot — chatbot de análisis de documentos PDF.
Diseño profesional con área de mensajes scrollable, burbuja de mensajes y
acceso rápido a comandos frecuentes.
"""
from dash import dcc, html
import dash_bootstrap_components as dbc


def chatbot_panel() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # ── Tarjeta principal del chat ────────────────
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Div(
                                                            "🤖",
                                                            style={
                                                                "fontSize": "2rem",
                                                                "lineHeight": "1",
                                                                "marginRight": "12px",
                                                            },
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.H4(
                                                                    "JuanBot",
                                                                    className="mb-0 fw-bold",
                                                                    style={"color": "#E3530F"},
                                                                ),
                                                                html.Small(
                                                                    "Asistente de análisis de documentos PDF",
                                                                    className="text-muted",
                                                                ),
                                                            ]
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                                html.Div(
                                                    [
                                                        dbc.Badge(
                                                            "Online",
                                                            color="success",
                                                            className="me-2",
                                                            style={"fontSize": "0.75rem"},
                                                        ),
                                                        dbc.Button(
                                                            [html.I(className="bi-trash me-1"), "Limpiar"],
                                                            id="chatbot-clear-btn",
                                                            color="outline-secondary",
                                                            size="sm",
                                                            n_clicks=0,
                                                            style={"border": "1px solid #555"},
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="d-flex justify-content-between align-items-center w-100",
                                        ),
                                        style={"background": "#1e1e1e", "borderBottom": "2px solid #E3530F"},
                                    ),

                                    dbc.CardBody(
                                        [
                                            # ── Área de mensajes ──────────────────────
                                            html.Div(
                                                id="chatbot-messages",
                                                style={
                                                    "height":      "440px",
                                                    "overflowY":   "auto",
                                                    "padding":     "16px",
                                                    "background":  "#141414",
                                                    "borderRadius":"8px",
                                                    "marginBottom":"12px",
                                                    "border":      "1px solid #2a2a2a",
                                                },
                                                children=[
                                                    _welcome_message(),
                                                ],
                                            ),

                                            # ── Sugerencias rápidas ───────────────────
                                            html.Div(
                                                [
                                                    html.Small("Preguntas rápidas:", className="text-muted me-2"),
                                                    dbc.Button(
                                                        "📋 Resumen",
                                                        id="quick-summary-btn",
                                                        color="outline-secondary",
                                                        size="sm",
                                                        className="me-1 mb-1",
                                                        n_clicks=0,
                                                    ),
                                                    dbc.Button(
                                                        "📅 Fechas",
                                                        id="quick-dates-btn",
                                                        color="outline-secondary",
                                                        size="sm",
                                                        className="me-1 mb-1",
                                                        n_clicks=0,
                                                    ),
                                                    dbc.Button(
                                                        "💰 Montos",
                                                        id="quick-amounts-btn",
                                                        color="outline-secondary",
                                                        size="sm",
                                                        className="me-1 mb-1",
                                                        n_clicks=0,
                                                    ),
                                                    dbc.Button(
                                                        "👤 Nombres",
                                                        id="quick-names-btn",
                                                        color="outline-secondary",
                                                        size="sm",
                                                        className="me-1 mb-1",
                                                        n_clicks=0,
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),

                                            # ── Input + botón enviar ──────────────────
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="chatbot-input",
                                                        placeholder="Escribe tu pregunta sobre el documento...",
                                                        type="text",
                                                        n_submit=0,
                                                        debounce=False,
                                                        style={
                                                            "background": "#1e1e1e",
                                                            "border":     "1px solid #444",
                                                            "color":      "#fff",
                                                        },
                                                    ),
                                                    dbc.Button(
                                                        [html.I(className="bi-send me-1"), "Enviar"],
                                                        id="chatbot-send-btn",
                                                        color="primary",
                                                        n_clicks=0,
                                                        style={"background": "#E3530F", "border": "none"},
                                                    ),
                                                ]
                                            ),

                                            # Store para el estado del chat
                                            dcc.Store(id="chatbot-state", data={}),
                                        ],
                                        style={"background": "#1a1a1a"},
                                    ),
                                ],
                                className="border-0 shadow-lg",
                                style={"border": "1px solid #333 !important"},
                            ),
                        ],
                        md=8,
                        className="mx-auto",
                    ),

                    # ── Panel de info lateral ─────────────────────────────────
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("📄 Documentos cargados", className="mb-0"),
                                        style={"background": "#1e1e1e"},
                                    ),
                                    dbc.CardBody(
                                        html.Div(id="chatbot-docs-info", children=[
                                            html.P("Procesa un PDF para comenzar.", className="text-muted small"),
                                        ]),
                                        style={"background": "#141414", "minHeight": "200px"},
                                    ),
                                ],
                                className="border-0 shadow-sm mb-3",
                                style={"border": "1px solid #333 !important"},
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("💡 Tips", className="mb-0"),
                                        style={"background": "#1e1e1e"},
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Puedes preguntar sobre:", className="text-muted small mb-1"),
                                            html.Ul(
                                                [
                                                    html.Li("Fechas y montos del documento", className="small"),
                                                    html.Li("Nombres y firmas", className="small"),
                                                    html.Li("Contenido de tablas", className="small"),
                                                    html.Li("Comparar múltiples docs", className="small"),
                                                    html.Li("Resúmenes y hallazgos", className="small"),
                                                ],
                                                className="text-muted ps-3",
                                            ),
                                        ],
                                        style={"background": "#141414"},
                                    ),
                                ],
                                className="border-0 shadow-sm",
                                style={"border": "1px solid #333 !important"},
                            ),
                        ],
                        md=4,
                    ),
                ],
                className="align-items-start",
            )
        ],
        fluid=True,
        className="py-3",
    )


def _welcome_message() -> html.Div:
    """Mensaje de bienvenida inicial de JuanBot."""
    return html.Div(
        [
            html.Div(
                [
                    html.Span("🤖", style={"fontSize": "1.5rem", "marginRight": "8px"}),
                    html.Span("JuanBot", className="fw-bold", style={"color": "#E3530F"}),
                ],
                className="mb-2",
            ),
            html.P(
                "¡Hola! Soy JuanBot, tu asistente de análisis de documentos PDF. "
                "Procesa uno o más PDFs primero y luego pregúntame lo que necesites.",
                className="mb-1",
                style={"color": "#ccc"},
            ),
            html.P(
                "Puedo ayudarte a encontrar fechas, montos, nombres, firmas, "
                "resumir el contenido y comparar múltiples documentos.",
                className="mb-0 small",
                style={"color": "#888"},
            ),
        ],
        className="p-3 rounded",
        style={
            "background": "#1e2d3d",
            "border":     "1px solid #1a4a7a",
            "borderRadius": "8px",
        },
    )


def render_user_message(text: str) -> html.Div:
    """Renderiza un mensaje del usuario (burbuja derecha)."""
    return html.Div(
        html.Div(
            [
                html.Span("Tú", className="fw-bold me-2", style={"color": "#E3530F"}),
                html.Span(text, style={"color": "#eee"}),
            ],
            className="p-3 rounded",
            style={
                "background":    "#1e2d1e",
                "border":        "1px solid #2a5a2a",
                "maxWidth":      "85%",
                "display":       "inline-block",
            },
        ),
        className="mb-2 text-end",
    )


def render_bot_message(text: str) -> html.Div:
    """Renderiza un mensaje de JuanBot (burbuja izquierda)."""
    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        html.Span("🤖", style={"marginRight": "6px"}),
                        html.Span("JuanBot", className="fw-bold", style={"color": "#E3530F"}),
                    ],
                    className="mb-1",
                ),
                html.Span(text, style={"color": "#ddd", "whiteSpace": "pre-wrap"}),
            ],
            className="p-3 rounded",
            style={
                "background":  "#1e1e2e",
                "border":      "1px solid #2a2a5a",
                "maxWidth":    "85%",
                "display":     "inline-block",
            },
        ),
        className="mb-2",
    )
