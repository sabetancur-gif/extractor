"""
src/app/handlers/chatbot_handler.py
-------------------------------------
Callbacks de JuanBot: chatbot multi-documento con burbujas de mensajes,
sugerencias rápidas, limpieza de historial y panel lateral de documentos.
"""
from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from src.llm.chatbot import JuanBot
from src.app.ui.chatbot_panel import render_user_message, render_bot_message

_bot = JuanBot()


def register_callbacks_chatbot(app, controller, embedder=None):

    # ── actualizar contexto cuando cambia doc-context ────────────────────────
    @app.callback(
        Output("chatbot-docs-info", "children"),
        Output("chatbot-state",     "data",     allow_duplicate=True),
        Input("doc-context", "data"),
        State("chatbot-state", "data"),
        prevent_initial_call=True,
    )
    def sync_bot_docs(doc_ctx, chat_state):
        if not isinstance(doc_ctx, dict) or not doc_ctx:
            return [html.P("No hay documentos cargados.", className="text-muted small")], {}

        _bot.set_documents(doc_ctx)

        items = []
        for did, ctx in doc_ctx.items():
            if not isinstance(ctx, dict):
                continue
            fn     = ctx.get("file_name", did)
            pages  = ctx.get("pages_total") or len(ctx.get("pages", []) or [])
            fields = len(ctx.get("fields", []) or [])
            blocks = len(ctx.get("classified_blocks", []) or [])
            mode   = ctx.get("processing_mode", "")
            items.append(
                dbc.Card(
                    dbc.CardBody([
                        html.Div(html.Strong(fn[:40], style={"color": "#E3530F"}), className="mb-1"),
                        html.Div([
                            dbc.Badge(f"{pages}p",      color="secondary", className="me-1"),
                            dbc.Badge(f"{fields} camps",color="info",      className="me-1"),
                            dbc.Badge(f"{blocks} blks", color="dark",      className="me-1"),
                            dbc.Badge(mode,             color="outline-secondary"),
                        ]),
                    ], style={"padding": "8px"}),
                    className="mb-2 border-0",
                    style={"background": "#1e2d3d", "border": "1px solid #1a4a7a !important"},
                )
            )

        new_state = {**(chat_state or {}), "n_docs": len(doc_ctx)}
        return items, new_state

    # ── sugerencias rápidas → pre-rellenar el input ───────────────────────────
    @app.callback(
        Output("chatbot-input", "value", allow_duplicate=True),
        Input("quick-summary-btn", "n_clicks"),
        Input("quick-dates-btn",   "n_clicks"),
        Input("quick-amounts-btn", "n_clicks"),
        Input("quick-names-btn",   "n_clicks"),
        prevent_initial_call=True,
    )
    def quick_prompt(s, d, a, n):
        tid = dash.callback_context.triggered_id
        mapping = {
            "quick-summary-btn": "Dame un resumen completo de los documentos procesados.",
            "quick-dates-btn":   "¿Qué fechas aparecen en los documentos? Muéstralas con página.",
            "quick-amounts-btn": "¿Qué montos o valores económicos hay en los documentos?",
            "quick-names-btn":   "¿Qué nombres de personas o empresas se mencionan?",
        }
        return mapping.get(tid, dash.no_update)

    # ── enviar mensaje ────────────────────────────────────────────────────────
    @app.callback(
        Output("chatbot-messages", "children"),
        Output("chatbot-input",    "value"),
        Output("chatbot-state",    "data"),
        Input("chatbot-send-btn", "n_clicks"),
        Input("chatbot-input",    "n_submit"),
        State("chatbot-input",    "value"),
        State("chatbot-messages", "children"),
        State("chatbot-state",    "data"),
        State("doc-context",      "data"),
        prevent_initial_call=True,
    )
    def send_message(n_btn, n_sub, user_input, current_msgs, chat_state, doc_ctx):
        if not user_input or not user_input.strip():
            raise PreventUpdate

        # Asegurarse de que el bot tiene todos los documentos
        doc_hash = str(sorted(doc_ctx.keys())) if isinstance(doc_ctx, dict) else ""
        if chat_state.get("doc_hash") != doc_hash and isinstance(doc_ctx, dict) and doc_ctx:
            _bot.set_documents(doc_ctx)

        response = _bot.chat(user_input.strip())

        msgs = list(current_msgs or [])
        msgs.append(render_user_message(user_input.strip()))
        msgs.append(render_bot_message(str(response)))

        new_state = {
            "doc_hash": doc_hash,
            "turns":    (chat_state or {}).get("turns", 0) + 1,
        }
        return msgs, "", new_state

    # ── limpiar historial ─────────────────────────────────────────────────────
    @app.callback(
        Output("chatbot-messages", "children", allow_duplicate=True),
        Output("chatbot-state",    "data",     allow_duplicate=True),
        Input("chatbot-clear-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_chat(n):
        from src.app.ui.chatbot_panel import _welcome_message
        _bot.clear()
        return [_welcome_message()], {}
