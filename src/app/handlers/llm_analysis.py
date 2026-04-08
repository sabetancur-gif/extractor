from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table, dcc, html
from dash.exceptions import PreventUpdate

from src.llm.enricher import LLMEnricher


llm_service = LLMEnricher()


def _options_from_doc_ctx(doc_ctx: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(doc_ctx, dict):
        return []
    options = []
    for doc_id, ctx in doc_ctx.items():
        label = ctx.get("file_name", doc_id) if isinstance(ctx, dict) else str(doc_id)
        options.append({"label": label, "value": doc_id})
    return options


def _render_changes_table(rows: list[dict[str, Any]]):
    if not rows:
        return html.Div("No hay sugerencias LLM aplicables.", className="text-muted fst-italic")

    columns = [
        {"name": "field", "id": "field"},
        {"name": "value", "id": "value"},
        {"name": "confidence", "id": "confidence"},
    ]
    return dash_table.DataTable(
        id="llm-changes-datatable",
        columns=columns,
        data=rows,
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"whiteSpace": "normal", "height": "auto", "textAlign": "left"},
        style_header={"fontWeight": "600"},
    )


def register_callbacks_15(app, controller, embedder=None):
    @app.callback(
        Output("llm-doc-selector", "options"),
        Output("llm-doc-selector", "value"),
        Input("doc-context", "data"),
        prevent_initial_call=True,
    )
    def update_llm_doc_selector(doc_ctx):
        options = _options_from_doc_ctx(doc_ctx)
        value = options[0]["value"] if options else None
        return options, value

    @app.callback(
        Output("llm-context", "data"),
        Output("llm-summary-output", "children"),
        Output("llm-results-output", "children"),
        Input("run-llm-btn", "n_clicks"),
        State("llm-doc-selector", "value"),
        State("llm-mode", "value"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def run_llm_enrichment(n_clicks, doc_id, mode, doc_ctx):
        if not n_clicks:
            raise PreventUpdate
        if not doc_id or not isinstance(doc_ctx, dict):
            raise PreventUpdate

        selected_ctx = doc_ctx.get(doc_id)
        if not isinstance(selected_ctx, dict):
            raise PreventUpdate

        enriched = llm_service.enrich_document(selected_ctx, mode=mode or "auto_fill_missing")
        changes = enriched.get("llm_applied_changes", [])

        summary = dbc.Alert(
            [
                html.H5("LLM enrichment complete", className="mb-1"),
                html.Div(f"Documento: {selected_ctx.get('file_name', doc_id)}"),
                html.Div(f"Cambios aplicados: {len(changes)}"),
            ],
            color="success",
            className="shadow-sm",
        )

        results = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H6("Cambios aplicados"),
                                        _render_changes_table(changes),
                                    ]
                                )
                            ),
                            md=7,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H6("Raw JSON"),
                                        html.Pre(
                                            enriched.get("llm_raw_response", "")[:12000],
                                            style={
                                                "maxHeight": "420px",
                                                "overflow": "auto",
                                                "whiteSpace": "pre-wrap",
                                            },
                                        ),
                                    ]
                                )
                            ),
                            md=5,
                        ),
                    ],
                    className="g-3",
                ),
            ],
            fluid=True,
        )

        return enriched, summary, results