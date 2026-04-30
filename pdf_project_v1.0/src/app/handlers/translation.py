
"""
src/app/handlers/translation.py
-------------------------------
Callbacks para traducción de documento.
"""

# STDLIB
import json
import os

# THIRDPARTY
import dash
from dash import Input, Output, State

# FIRSTPARTY
from src.translation.translator import Translator


def register_callbacks_06(app, controller, embedder=None):
    """
    Registra callback para traducir el documento al idioma seleccionado.
    Relacionado con IDs: translation-output, run-translation, target-language, doc-context.
    """
    translator = Translator()

    @app.callback(
        Output("translation-output", "children"),
        Input("run-translation", "n_clicks"),
        State("doc-context", "data"),
        State("target-language", "value"),
        prevent_initial_call=True,
    )
    def translate_doc(n_clicks, doc_ctx, target):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        # Preferir cargar desde JSON si existe (por consistencia)
        json_path = doc_ctx.get("saved_path")
        doc = doc_ctx
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except Exception:
                doc = doc_ctx

        pages = doc.get("pages", [])
        if not pages:
            return "No pages to translate"

        # Simple demo: toma los primeros 10 bloques de la primera página
        text = " ".join([b.get("text", "") for b in pages[0].get("blocks", [])[:10]])
        translated = translator.translate(text, target)
        return translated
