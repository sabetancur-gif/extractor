"""
src/app/handlers/llm_analysis.py
----------------------------------
Callbacks del LLM Enricher:
- Sync dropdown de documentos.
- Ejecutar enriquecimiento y mostrar resultados de forma clara:
  resumen del doc, tabla de cambios aplicados (sin JSON) y raw colapsable.
"""
from __future__ import annotations

import json
from typing import Any

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dash_table, html
from dash.exceptions import PreventUpdate

from src.llm.enricher import LLMEnricher

_llm = LLMEnricher()


def _opts(doc_ctx):
    if not isinstance(doc_ctx, dict):
        return [], None
    opts = [
        {"label": ctx.get("file_name", did), "value": did}
        for did, ctx in doc_ctx.items()
        if isinstance(ctx, dict)
    ]
    return opts, (opts[0]["value"] if opts else None)


def _doc_snapshot(title: str, ctx: dict) -> dbc.Card:
    pages  = ctx.get("pages_total") or len(ctx.get("pages", []) or [])
    fields = len(ctx.get("fields", []) or [])
    blocks = len(ctx.get("classified_blocks", []) or [])
    mode   = ctx.get("processing_mode", "N/A")
    return dbc.Card(
        dbc.CardBody([
            html.Div(html.Strong(title), className="mb-2 small text-muted"),
            html.Div(ctx.get("file_name", ""), className="fw-bold mb-2", style={"color": "#E3530F"}),
            html.Div([
                dbc.Badge(f"📄 {pages} págs",   color="secondary", className="me-1"),
                dbc.Badge(f"📋 {fields} campos", color="info",      className="me-1"),
                dbc.Badge(f"📦 {blocks} bloques",color="warning",   className="me-1"),
            ], className="mb-1"),
            html.Small(f"Modo: {mode}", className="text-muted"),
        ]),
        className="h-100 border-0 shadow-sm",
        style={"background": "#1e1e2e", "border": "1px solid #2a2a5a !important"},
    )


def _changes_table(changes: list[dict]) -> Any:
    if not changes:
        return dbc.Alert(
            [html.I(className="bi-info-circle me-2"),
             "El modelo no encontró campos adicionales o ya estaban completos."],
            color="secondary",
        )

    rows = []
    for c in changes:
        conf = c.get("confidence")
        try:
            conf_str = f"{float(conf)*100:.0f}%" if conf is not None else ""
        except Exception:
            conf_str = str(conf)

        status  = c.get("status", "")
        # Color por estado
        status_cell = status

        rows.append({
            "field":      c.get("field", ""),
            "value":      str(c.get("value", "") or "")[:200],
            "confidence": conf_str,
            "status":     status_cell,
            "reason":     str(c.get("reason", "") or "")[:200],
            "page":       str(c.get("page_number") or ""),
        })

    return dash_table.DataTable(
        id="llm-changes-datatable",
        columns=[
            {"name": "Campo",     "id": "field"},
            {"name": "Valor",     "id": "value"},
            {"name": "Confianza", "id": "confidence"},
            {"name": "Estado",    "id": "status"},
            {"name": "Razón",     "id": "reason"},
            {"name": "Página",    "id": "page"},
        ],
        data=rows,
        page_size=12,
        sort_action="native",
        style_table={"overflowX": "auto", "overflowY": "auto", "maxHeight": "360px"},
        style_cell={
            "textAlign": "left",
            "fontSize": "0.87rem",
            "padding": "8px 12px",
            "maxWidth": "260px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "whiteSpace": "nowrap",
            "backgroundColor": "#1a1a1a",
            "color": "#ddd",
        },
        style_header={
            "fontWeight": "700",
            "fontSize": "0.80rem",
            "backgroundColor": "#1e1e1e",
            "color": "#E3530F",
            "textTransform": "uppercase",
        },
        style_data_conditional=[
            {"if": {"filter_query": "{status} = filled",    "column_id": "status"},
             "color": "#4CAF50", "fontWeight": "bold"},
            {"if": {"filter_query": "{status} = corrected", "column_id": "status"},
             "color": "#2196F3", "fontWeight": "bold"},
            {"if": {"filter_query": "{status} = new",       "column_id": "status"},
             "color": "#FF9800", "fontWeight": "bold"},
            {"if": {"filter_query": "{status} = rejected",  "column_id": "status"},
             "color": "#f44336"},
            {"if": {"row_index": "odd"}, "backgroundColor": "#141414"},
        ],
    )


def register_callbacks_15(app, controller, embedder=None):

    @app.callback(
        Output("llm-doc-selector", "options"),
        Output("llm-doc-selector", "value"),
        Input("doc-context", "data"),
    )
    def sync_selector(doc_ctx):
        return _opts(doc_ctx)

    @app.callback(
        Output("llm-context",        "data"),
        Output("llm-summary-output", "children"),
        Output("llm-results-output", "children"),
        Input("run-llm-btn", "n_clicks"),
        State("llm-doc-selector", "value"),
        State("llm-mode",         "value"),
        State("doc-context",      "data"),
        prevent_initial_call=True,
    )
    def run_enrichment(n_clicks, doc_id, mode, doc_ctx):
        if not n_clicks or not doc_id or not isinstance(doc_ctx, dict):
            raise PreventUpdate
        selected = doc_ctx.get(doc_id)
        if not isinstance(selected, dict):
            raise PreventUpdate

        try:
            enriched = _llm.enrich_document(selected, mode=mode or "auto_fill_missing")
        except Exception as e:
            err = dbc.Alert([html.H5("Error en el LLM", className="mb-1"), html.Div(str(e))],
                            color="danger")
            return {}, err, err

        changes  = enriched.get("llm_applied_changes", []) or []
        summary  = enriched.get("llm_document_summary", "")
        doc_type = enriched.get("llm_document_type", "")
        warnings = enriched.get("llm_warnings", [])
        raw_resp = enriched.get("llm_raw_response", "")

        # ── banner de resumen ─────────────────────────────────────────────────
        n_filled    = sum(1 for c in changes if c.get("status") in ("filled", "corrected", "new"))
        n_rejected  = sum(1 for c in changes if c.get("status") == "rejected")

        summary_card = dbc.Alert(
            dbc.Row([
                dbc.Col([
                    html.H5([html.I(className="bi-robot me-2"), "Enriquecimiento completado"],
                            className="mb-1"),
                    html.Div(selected.get("file_name", doc_id), className="text-muted small mb-2"),
                    html.Div([
                        dbc.Badge(f"✅ {n_filled} aplicados",  color="success", className="me-2"),
                        dbc.Badge(f"❌ {n_rejected} rechazados",color="danger",  className="me-2"),
                        dbc.Badge(f"📋 {len(changes)} total",  color="primary"),
                    ]),
                ], md=8),
                dbc.Col([
                    html.Div(f"Tipo: {doc_type}", className="small text-muted mb-1") if doc_type else None,
                    html.Div(f"Modo: {mode or 'auto_fill_missing'}", className="small text-muted"),
                ], md=4),
            ]),
            color="success" if n_filled > 0 else "secondary",
            className="border-0",
        )

        # ── resumen del documento (si lo generó el LLM) ──────────────────────
        summary_section = []
        if summary:
            summary_section = [
                dbc.Card(
                    dbc.CardBody([
                        html.H6([html.I(className="bi-file-text me-2"), "Resumen del documento"],
                                className="mb-2", style={"color": "#E3530F"}),
                        html.P(summary, className="mb-0", style={"color": "#ccc"}),
                    ]),
                    className="mb-3 border-0 shadow-sm",
                    style={"background": "#1e2d1e", "border": "1px solid #2a5a2a !important"},
                )
            ]

        # ── warnings ──────────────────────────────────────────────────────────
        warn_section = []
        if warnings:
            warn_section = [
                dbc.Alert(
                    [html.I(className="bi-exclamation-triangle me-2")] +
                    [html.Div(str(w)) for w in warnings],
                    color="warning",
                    className="small mb-3",
                )
            ]

        # ── comparativa base vs enriquecido ───────────────────────────────────
        comp_row = dbc.Row([
            dbc.Col(_doc_snapshot("📄 Extracción base",     selected), md=4),
            dbc.Col(_doc_snapshot("🤖 Documento enriquecido", enriched), md=4),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H6("📊 Distribución de cambios", className="mb-2"),
                        html.Div([
                            dbc.Progress(
                                value=int(n_filled / max(len(changes), 1) * 100),
                                label=f"Aplicados {n_filled}",
                                color="success",
                                style={"height": "22px"},
                                className="mb-2",
                            ),
                            dbc.Progress(
                                value=int(n_rejected / max(len(changes), 1) * 100),
                                label=f"Rechazados {n_rejected}",
                                color="danger",
                                style={"height": "22px"},
                            ),
                        ]),
                    ]),
                    className="h-100 border-0 shadow-sm",
                    style={"background": "#1e2d3d", "border": "1px solid #1a4a7a !important"},
                ),
                md=4,
            ),
        ], className="g-3 mb-3")

        # ── tabla de cambios ──────────────────────────────────────────────────
        changes_card = dbc.Card([
            dbc.CardHeader(
                html.Div([
                    html.I(className="bi-table me-2", style={"color": "#E3530F"}),
                    html.Span("Cambios aplicados por el LLM", className="fw-bold"),
                ]),
                style={"background": "#1e1e1e"},
            ),
            dbc.CardBody(_changes_table(changes), style={"background": "#1a1a1a", "padding": "0"}),
        ], className="mb-3 border-0 shadow-sm", style={"border": "1px solid #333 !important"})

        # ── respuesta raw colapsable ──────────────────────────────────────────
        raw_card = dbc.Card([
            dbc.CardHeader(
                dbc.Button(
                    [html.I(className="bi-code me-2"), "Ver respuesta raw del modelo"],
                    id="llm-raw-collapse-btn",
                    color="link",
                    className="p-0 text-muted small",
                    n_clicks=0,
                ),
                style={"background": "#1e1e1e"},
            ),
            dbc.Collapse(
                dbc.CardBody(
                    html.Pre(
                        raw_resp[:8000] if raw_resp else "(sin respuesta)",
                        style={
                            "maxHeight": "320px",
                            "overflow": "auto",
                            "whiteSpace": "pre-wrap",
                            "fontSize": "0.78rem",
                            "color": "#9cdcfe",
                            "background": "#141414",
                        },
                    )
                ),
                id="llm-raw-collapse",
                is_open=False,
            ),
        ], className="border-0 shadow-sm", style={"border": "1px solid #333 !important"})

        results = html.Div(
            summary_section + warn_section + [comp_row, changes_card, raw_card]
        )

        store = {
            "doc_id":   doc_id,
            "mode":     mode,
            "changes":  changes,
            "raw":      raw_resp[:4000],
        }
        return store, summary_card, results

    # ── colapsar/expandir raw ─────────────────────────────────────────────────
    @app.callback(
        Output("llm-raw-collapse", "is_open"),
        Input("llm-raw-collapse-btn", "n_clicks"),
        State("llm-raw-collapse",   "is_open"),
        prevent_initial_call=True,
    )
    def toggle_raw(n, is_open):
        return not is_open
