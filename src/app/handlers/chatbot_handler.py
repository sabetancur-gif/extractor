# src/app/handlers/chatbot_handler.py
from __future__ import annotations
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from src.llm.chatbot import PDFChatbot


_chatbot = PDFChatbot()


def register_callbacks_chatbot(app, controller, embedder=None):

    @app.callback(
        Output("chatbot-messages", "children"),
        Output("chatbot-input", "value"),
        Output("chatbot-state", "data"),
        Input("chatbot-send-btn", "n_clicks"),
        Input("chatbot-input", "n_submit"),
        State("chatbot-input", "value"),
        State("chatbot-messages", "children"),
        State("chatbot-state", "data"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def send_message(n_clicks, n_submit, user_input, current_msgs, chat_state, doc_ctx):
        if not user_input or not user_input.strip():
            raise PreventUpdate

        # Inicializar chatbot con el documento si no está listo
        doc_hash = str(sorted(doc_ctx.keys())) if isinstance(doc_ctx, dict) else ""
        if not chat_state or chat_state.get("doc_hash") != doc_hash:
            if isinstance(doc_ctx, dict) and doc_ctx:
                first_ctx = next(iter(doc_ctx.values()), {})
                _chatbot.set_document(first_ctx)

        response = _chatbot.chat(user_input.strip())

        msgs = list(current_msgs or [])
        msgs.append(
            dbc.Card(
                dbc.CardBody([
                    html.Strong("Tú: "),
                    html.Span(user_input),
                ]),
                className="mb-2 bg-light border-0",
            )
        )
        msgs.append(
            dbc.Card(
                dbc.CardBody([
                    html.Strong("Asistente: "),
                    html.Span(response),
                ]),
                className="mb-2 border-primary",
                style={"borderLeft": "3px solid #0d6efd"},
            )
        )

        new_state = {"doc_hash": doc_hash, "turns": (chat_state or {}).get("turns", 0) + 1}
        return msgs, "", new_state

    @app.callback(
        Output("chatbot-messages", "children", allow_duplicate=True),
        Output("chatbot-state", "data", allow_duplicate=True),
        Input("chatbot-clear-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_chat(n_clicks):
        _chatbot.clear()
        return [], {}
