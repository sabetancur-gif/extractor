"""
src/app/ui/llm_analysis_panel.py
---------------------------------
Panel del LLM Enricher: configuración, ejecución y visualización
clara de resultados del enriquecimiento con Ollama.
"""
from dash import dcc, html
import dash_bootstrap_components as dbc


def llm_analysis_panel() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Row(
                [
                    # ── Columna izquierda: controles ──────────────────────────
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.I(className="bi-robot me-2", style={"color": "#E3530F"}),
                                                html.Span("LLM Enricher", className="fw-bold fs-5"),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                        style={"background": "#1e1e1e"},
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Label("Documento", className="form-label text-muted small"),
                                            dcc.Dropdown(
                                                id="llm-doc-selector",
                                                options=[],
                                                placeholder="Selecciona el documento",
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            html.Label("Modo de enriquecimiento", className="form-label text-muted small"),
                                            dcc.Dropdown(
                                                id="llm-mode",
                                                options=[
                                                    {
                                                        "label": "🔍 Completar campos faltantes",
                                                        "value": "auto_fill_missing",
                                                    },
                                                    {
                                                        "label": "📋 Resumir documento",
                                                        "value": "summarize",
                                                    },
                                                    {
                                                        "label": "🖼️ Describir imágenes y tablas",
                                                        "value": "describe_assets",
                                                    },
                                                ],
                                                value="auto_fill_missing",
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            html.Hr(style={"borderColor": "#333"}),
                                            html.P(
                                                "El modelo analiza el texto del documento y sugiere "
                                                "valores para campos faltantes o de baja confianza.",
                                                className="text-muted small mb-3",
                                            ),
                                            dbc.Button(
                                                [
                                                    html.I(className="bi-lightning-charge me-2"),
                                                    "Ejecutar LLM",
                                                ],
                                                id="run-llm-btn",
                                                color="primary",
                                                className="w-100 fw-bold",
                                                style={"background": "#E3530F", "border": "none"},
                                            ),
                                            html.Div(id="llm-spinner-container", className="mt-2"),
                                        ],
                                        style={"background": "#1a1a1a"},
                                    ),
                                ],
                                className="border-0 shadow-sm mb-3",
                                style={"border": "1px solid #333 !important"},
                            ),

                            # Card de información del modelo
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.I(className="bi-info-circle me-2"),
                                                html.Span("Configuración LLM", className="fw-bold small"),
                                            ],
                                            className="d-flex align-items-center text-muted",
                                        ),
                                        style={"background": "#1e1e1e"},
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Small("Proveedor: Ollama (local)", className="text-muted d-block"),
                                            html.Small("Modelo: qwen2.5:3b-instruct", className="text-muted d-block"),
                                            html.Small("URL: http://localhost:11434", className="text-muted d-block"),
                                            html.Hr(style={"borderColor": "#333"}),
                                            html.Small(
                                                "Configura mediante variables de entorno: "
                                                "LLM_MODEL, LLM_BASE_URL, LLM_PROVIDER",
                                                className="text-muted",
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

                    # ── Columna derecha: resultados ───────────────────────────
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.I(className="bi-bar-chart-line me-2", style={"color": "#E3530F"}),
                                                html.Span("Resultados del enriquecimiento", className="fw-bold fs-5"),
                                            ],
                                            className="d-flex align-items-center",
                                        ),
                                        style={"background": "#1e1e1e"},
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Resumen del proceso
                                            html.Div(id="llm-summary-output", className="mb-3"),

                                            # Resultados detallados (tabla + raw opcional)
                                            html.Div(id="llm-results-output"),
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
