
"""
src/app/handlers/export_converters.py
-------------------------------------
Callbacks para exportar/conversiones de formato (Markdown, HTML).
"""

# STDLIB
import json
import os

# THIRDPARTY
import dash
from dash import Input, Output, State, dcc

# FIRSTPARTY
from src.conversion.formatter import Converter


def register_callbacks_05(app, controller, embedder=None):
    """
    Registra callbacks para exportar el documento a Markdown y HTML.
    Relacionado con IDs: download-md, download-html, convert-md, convert-html, doc-context.
    """
    converter = Converter()

    @app.callback(
        Output("download-md", "data"),
        Input("convert-md", "n_clicks"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def convert_to_md(n, doc_ctx):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        # Si existe un JSON persistido, úsalo
        json_path = doc_ctx.get("saved_path")
        doc = doc_ctx
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except Exception:
                doc = doc_ctx

        md = converter.to_markdown(doc)
        return dcc.send_string(md, filename=f"{doc_ctx['doc_id']}.md")

    # ===== 4) Conversión a HTML =====
    @app.callback(
        Output("download-html", "data"),
        Input("convert-html", "n_clicks"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def convert_to_html(n, doc_ctx):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        json_path = doc_ctx.get("saved_path")
        doc = doc_ctx
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except Exception:
                doc = doc_ctx

        html_out = converter.to_html(doc)
        return dcc.send_string(html_out, filename=f"{doc_ctx['doc_id']}.html")
