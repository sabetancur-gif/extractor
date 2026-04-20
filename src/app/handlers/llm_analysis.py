from __future__ import annotations

from typing import Any
import json

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


def _snapshot_card(title: str, ctx: dict[str, Any]):
    pages = ctx.get("pages", [])
    if not isinstance(pages, list):
        pages = []

    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="mb-2"),
                html.Div(f"Archivo: {ctx.get('file_name', 'N/A')}", className="mb-1"),
                html.Div(
                    f"Páginas: {ctx.get('pages_total', len(pages))}",
                    className="mb-1",
                ),
                html.Div(f"Campos: {len(ctx.get('fields', []))}", className="mb-1"),
                html.Div(
                    f"Bloques: {len(ctx.get('classified_blocks', []))}",
                    className="mb-1",
                ),
                html.Div(
                    f"Modo: {ctx.get('processing_mode', 'N/A')}",
                    className="text-muted small",
                ),
            ]
        ),
        className="shadow-sm border-0 panel-card h-100",
    )


def _comparison_badges(changes: list[dict[str, Any]]):
    return html.Div(
        [
            dbc.Badge(f"Cambios: {len(changes)}", color="primary", className="me-2"),
            dbc.Badge("Base vs LLm", color="info", className="me-2"),
            dbc.Badge("Evidencia trazable", color="success"),
        ]
    )


def _render_changes_table(rows: list[dict[str, Any]]):
    if not rows:
        return html.Div("No hay sugerencias en  LLM aplocables.", className="text-muted fst-italic")

    columns = [
        {"name": "Campo", "id": "field"},
        {"name": "Valor", "id": "value"},
        {"name": "Confianza", "id": "confidence"},
        {"name": "Estado", "id": "status"},
        {"name": "Razón", "id": "reason"},
    ]

    return dash_table.DataTable(
        id="llm-changes-datatable",
        columns=columns,
        data=rows,
        page_size=10,
        sort_action="native",
        filter_action="none",
        style_table={"overflowX": "auto", "maxHeight": "380px", "overflowY": "auto"},
        style_cell={
            "whiteSpace": "normal",
            "height": "auto",
            "textAlign": "left",
            "padding": "10px",
            "fontSize": "0.92rem",
        },
        style_header={"fontWeight": "700"},
    )


def register_callbacks_15(app, controller, embedder=None):
    @app.callback(
        Output("llm-doc-selector", "options"),
        Output("llm-doc-selector", "value"),
        Input("doc-context", "data"),
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

        try:
            enriched = llm_service.enrich_document(selected_ctx, mode=mode or "auto_fill_missing")
            changes = enriched.get("llm_applied_changes", [])
        except Exception as e:
            error = dbc.Alert(
                [
                    html.H5("LLM enrichment failed", className="mb-1"),
                    html.Div(str(e)),
                ],
                color="danger",
                className="shadow-sm border-0",
            )
            return {}, error, error

        llm_store = {
            "doc_id": doc_id,
            "mode": mode or "auto_fill_missing",
            "base_document": selected_ctx,
            "enriched_document": enriched,
            "changes": changes,
            "raw_response": enriched.get("llm_raw_response", ""),
        }

        summary = dbc.Alert(
            [
                html.H5("LLM enrichment complete", className="mb-1"),
                html.Div(f"Documento: {selected_ctx.get('file_name', doc_id)}"),
                html.Div(f"Cambios aplicados: {len(changes)}"),
                _comparison_badges(changes),
            ],
            color="success",
            className="shadow-sm border-0",
        )

        results = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(_snapshot_card("Extracción base", selected_ctx), md=4),
                        dbc.Col(_snapshot_card("Documento enriquecido", enriched), md=4),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5("Cambios resumidos", className="mb-2"),
                                        html.Div(f"Modo: {mode or 'auto_fill_missing'}", className="mb-2"),
                                        _comparison_badges(changes),
                                        html.Hr(),
                                        html.Div(
                                            [
                                                html.Div(f"{c.get('field')}: {c.get('value')}", className="mb-1")
                                                for c in changes[:8]
                                            ]
                                            or [html.Div("Sin cambios aplicables.", className="text-muted")]
                                        ),
                                    ]
                                ),
                                className="shadow-sm border-0 panel-card h-100",
                            ),
                            md=4,
                        ),
                    ],
                    className="g-3 mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader("Cambios aplicados"),
                                    dbc.CardBody(_render_changes_table(changes)),
                                ],
                                className="shadow-sm border-0 panel-card",
                            ),
                            md=7,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader("Raw JSON"),
                                    dbc.CardBody(
                                        html.Pre(
                                            json.dumps(enriched, indent=2, ensure_ascii=False)[:14000],
                                            style={
                                                "maxHeight": "420px",
                                                "overflow": "auto",
                                                "whiteSpace": "pre-wrap",
                                            },
                                        )
                                    ),
                                ],
                                className="shadow-sm border-0 panel-card",
                            ),
                            md=5,
                        ),
                    ],
                    className="g-3",
                ),
            ],
            fluid=True,
        )

        return llm_store, summary, results
    # @app.callback(
    #     Output("llm-context", "data"),
    #     Output("llm-summary-output", "children"),
    #     Output("llm-results-output", "children"),
    #     Input("run-llm-btn", "n_clicks"),
    #     State("llm-doc-selector", "value"),
    #     State("llm-mode", "value"),
    #     State("doc-context", "data"),
    #     prevent_initial_call=True,
    # )
    # def run_llm_enrichment(n_clicks, doc_id, mode, doc_ctx):
    #     if not n_clicks:
    #         raise PreventUpdate

    #     if not doc_id or not isinstance(doc_ctx, dict):
    #         raise PreventUpdate

    #     selected_ctx = doc_ctx.get(doc_id)
    #     if not isinstance(selected_ctx, dict):
    #         raise PreventUpdate

    #     enriched = llm_service.enrich_document(selected_ctx, mode=mode or "auto_fill_missing")
    #     changes = enriched.get("llm_applied_changes", [])

    #     llm_store = {
    #         "doc_id": doc_id,
    #         "mode": mode or "auto_fill_missing",
    #         "base_document": selected_ctx,
    #         "enriched_document": enriched,
    #         "changes": changes,
    #         "raw_response": enriched.get("llm_raw_response", ""),
    #     }

    #     summary = dbc.Alert(
    #         [
    #             html.H5("LLM enrichment complete", className="mb-1"),
    #             html.Div(f"Documento: {selected_ctx.get('file_name', doc_id)}"),
    #             html.Div(f"Cambios aplicados: {len(changes)}"),
    #             _comparison_badges(changes),
    #         ],
    #         color="success",
    #         className="shadow-sm border-0",
    #     )

    #     results = dbc.Container(
    #         [
    #             dbc.Row(
    #                 [
    #                     dbc.Col(_snapshot_card("Extracción base", selected_ctx), md=4),
    #                     dbc.Col(_snapshot_card("Documento enriquecido", enriched), md=4),
    #                     dbc.Col(
    #                         dbc.Card(
    #                             dbc.CardBody(
    #                                 [
    #                                     html.H5("Cambios resumidos", className="mb-2"),
    #                                     html.Div(f"Modo: {mode or 'auto_fill_missing'}", className="mb-2"),
    #                                     _comparison_badges(changes),
    #                                     html.Hr(),
    #                                     html.Div(
    #                                         [
    #                                             html.Div(f"{c.get('field')}: {c.get('value')}", className="mb-1")
    #                                             for c in changes[:8]
    #                                         ]
    #                                         or [html.Div("Sin cambios aplicables.", className="text-muted")]
    #                                     ),
    #                                 ]
    #                             ),
    #                             className="shadow-sm border-0 panel-card h-100",
    #                         ),
    #                         md=4,
    #                     ),
    #                 ],
    #                 className="g-3 mb-3",
    #             ),
    #             dbc.Row(
    #                 [
    #                     dbc.Col(
    #                         dbc.Card(
    #                             [
    #                                 dbc.CardHeader("Cambios aplicados"),
    #                                 dbc.CardBody(_render_changes_table(changes)),
    #                             ],
    #                             className="shadow-sm border-0 panel-card",
    #                         ),
    #                         md=7,
    #                     ),
    #                     dbc.Col(
    #                         dbc.Card(
    #                             [
    #                                 dbc.CardHeader("Raw JSON"),
    #                                 dbc.CardBody(
    #                                     html.Pre(
    #                                         json.dumps(enriched, indent=2, ensure_ascii=False)[:14000],
    #                                         style={
    #                                             "maxHeight": "420px",
    #                                             "overflow": "auto",
    #                                             "whiteSpace": "pre-wrap",
    #                                         },
    #                                     )
    #                                 ),
    #                             ],
    #                             className="shadow-sm border-0 panel-card",
    #                         ),
    #                         md=5,
    #                     ),
    #                 ],
    #                 className="g-3",
    #             ),
    #         ],
    #         fluid=True,
    #     )

    #     return llm_store, summary, results
# def _render_changes_table(rows: list[dict[str, Any]]):
#     if not rows:
#         return html.Div("No hay sugerencias LLM aplicables.", className="text-muted fst-italic")

#     columns = [
#         {"name": "field", "id": "field"},
#         {"name": "value", "id": "value"},
#         {"name": "confidence", "id": "confidence"},
#     ]
#     return dash_table.DataTable(
#         id="llm-changes-datatable",
#         columns=columns,
#         data=rows,
#         page_size=10,
#         style_table={"overflowX": "auto"},
#         style_cell={"whiteSpace": "normal", "height": "auto", "textAlign": "left"},
#         style_header={"fontWeight": "600"},
#     )

    # @app.callback(
    #     Output("llm-context", "data"),
    #     Output("llm-summary-output", "children"),
    #     Output("llm-results-output", "children"),
    #     Input("run-llm-btn", "n_clicks"),
    #     State("llm-doc-selector", "value"),
    #     State("llm-mode", "value"),
    #     State("doc-context", "data"),
    #     prevent_initial_call=True,
    # )
    # def run_llm_enrichment(n_clicks, doc_id, mode, doc_ctx):
    #     if not n_clicks:
    #         raise PreventUpdate
    #     if not doc_id or not isinstance(doc_ctx, dict):
    #         raise PreventUpdate

    #     selected_ctx = doc_ctx.get(doc_id)
    #     if not isinstance(selected_ctx, dict):
    #         raise PreventUpdate

    #     enriched = llm_service.enrich_document(selected_ctx, mode=mode or "auto_fill_missing")
    #     changes = enriched.get("llm_applied_changes", [])

    #     summary = dbc.Alert(
    #         [
    #             html.H5("LLM enrichment complete", className="mb-1"),
    #             html.Div(f"Documento: {selected_ctx.get('file_name', doc_id)}"),
    #             html.Div(f"Cambios aplicados: {len(changes)}"),
    #         ],
    #         color="success",
    #         className="shadow-sm",
    #     )

    #     results = dbc.Container(
    #         [
    #             dbc.Row(
    #                 [
    #                     dbc.Col(
    #                         dbc.Card(
    #                             dbc.CardBody(
    #                                 [
    #                                     html.H6("Cambios aplicados"),
    #                                     _render_changes_table(changes),
    #                                 ]
    #                             )
    #                         ),
    #                         md=7,
    #                     ),
    #                     dbc.Col(
    #                         dbc.Card(
    #                             dbc.CardBody(
    #                                 [
    #                                     html.H6("Raw JSON"),
    #                                     html.Pre(
    #                                         enriched.get("llm_raw_response", "")[:12000],
    #                                         style={
    #                                             "maxHeight": "420px",
    #                                             "overflow": "auto",
    #                                             "whiteSpace": "pre-wrap",
    #                                         },
    #                                     ),
    #                                 ]
    #                             )
    #                         ),
    #                         md=5,
    #                     ),
    #                 ],
    #                 className="g-3",
    #             ),
    #         ],
    #         fluid=True,
    #     )

    #     return enriched, summary, results