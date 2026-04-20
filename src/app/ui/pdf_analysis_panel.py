# src/app/ui/pdf_analysis_panel.py
from __future__ import annotations

from dash import dcc, html
import dash_bootstrap_components as dbc


def pdf_analysis_panel() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.H4("PDF Analysis", className="mb-0"),
                                                html.Small(
                                                    "Explora campos, bloques y evidencias del documento",
                                                    className="text-muted",
                                                ),
                                            ]
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Label("Documento procesado", className="form-label"),
                                            dcc.Dropdown(
                                                id="analysis-target",
                                                options=[],
                                                placeholder="Selecciona el documento para análisis",
                                                clearable=False,
                                                multi=False,
                                                className="mb-3",
                                            ),
                                            html.Label("Buscar", className="form-label"),
                                            dcc.Input(
                                                id="analysis-search-keyword",
                                                type="text",
                                                placeholder="Palabra clave o texto",
                                                className="form-control mb-3",
                                            ),
                                            html.Label("Tipo de campo", className="form-label"),
                                            dcc.Dropdown(
                                                id="analysis-search-field",
                                                options=[
                                                    {"label": "Todos", "value": ""},
                                                    {"label": "Fecha", "value": "date"},
                                                    {"label": "Monto", "value": "amount"},
                                                    {"label": "Teléfono", "value": "phone"},
                                                    {"label": "Correo", "value": "email"},
                                                    {"label": "Identificador", "value": "identifier"},
                                                ],
                                                value="",
                                                clearable=True,
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                "Analizar documento",
                                                id="analysis-search-btn",
                                                color="primary",
                                                className="w-100",
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow-sm border-0 mb-3 panel-card",
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.H5("Vistas disponibles", className="mb-0"),
                                                html.Small(
                                                    "Usa las flechas para cambiar entre conjuntos de evidencia",
                                                    className="text-muted",
                                                ),
                                            ]
                                        )
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
                                                    ),
                                                    dbc.Button(
                                                        html.Span("Campos"),
                                                        id="analysis-view-label",
                                                        color="light",
                                                        disabled=True,
                                                        className="analysis-view-label-btn",
                                                    ),
                                                    dbc.Button(
                                                        html.I(className="bi-chevron-right"),
                                                        id="analysis-next-view-btn",
                                                        color="secondary",
                                                        outline=True,
                                                    ),
                                                ],
                                                className="w-100",
                                            ),
                                            html.Div(
                                                "El panel derecho cambia según la vista seleccionada.",
                                                className="text-muted small mt-3",
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow-sm border-0 panel-card",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Div(
                                            [
                                                html.H4("Documento seleccionado", className="mb-0"),
                                                html.Small(
                                                    "Resumen, tabla, crop y trazabilidad visual",
                                                    className="text-muted",
                                                ),
                                            ]
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="pdf-summary-output"),
                                            html.Hr(className="my-3"),
                                            html.Div(id="pdf-analysis-output"),
                                        ]
                                    ),
                                ],
                                className="shadow-lg border-0 panel-card analysis-shell",
                            )
                        ],
                        md=8,
                    ),
                ],
                className="align-items-start",
            )
        ],
        fluid=True,
        className="py-3 pdf-analysis-page",
    )
