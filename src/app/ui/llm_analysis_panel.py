# src/app/ui/llm_analysis_panel.py
from __future__ import annotations

from dash import dcc, html
import dash_bootstrap_components as dbc


def llm_analysis_panel() -> dbc.Container:
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
                                                html.H4("LLM Enrichment", className="mb-0"),
                                                html.Small(
                                                    "Comparación entre extracción y sugerencia del modelo",
                                                    className="text-muted",
                                                ),
                                            ]
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Label("Documento", className="form-label"),
                                            dcc.Dropdown(
                                                id="llm-doc-selector",
                                                options=[],
                                                placeholder="Selecciona el documento",
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            html.Label("Modo", className="form-label"),
                                            dcc.Dropdown(
                                                id="llm-mode",
                                                options=[
                                                    {"label": "Completar faltantes", "value": "auto_fill_missing"},
                                                    {"label": "Resumir", "value": "summarize"},
                                                    {"label": "Describir imágenes y tablas", "value": "describe_assets"},
                                                ],
                                                value="auto_fill_missing",
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                "Ejecutar LLM",
                                                id="run-llm-btn",
                                                color="primary",
                                                className="w-100",
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow-sm border-0 panel-card",
                            )
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
                                                html.H4("Comparación", className="mb-0"),
                                                html.Small(
                                                    "Extracción base vs documento enriquecido",
                                                    className="text-muted",
                                                ),
                                            ]
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="llm-summary-output"),
                                            html.Hr(className="my-3"),
                                            html.Div(id="llm-results-output"),
                                        ]
                                    ),
                                ],
                                className="shadow-lg border-0 panel-card analysis-shell",
                            )
                        ],
                        md=8,
                    ),
                ],
                className="g-4 align-items-start",
            )
        ],
        fluid=True,
        className="py-3 llm-analysis-page",
    )