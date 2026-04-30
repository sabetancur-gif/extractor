"""
src/app/handlers/ocr_navigation.py
-------------------------------------
Callbacks de navegación OCR por overlay-page-index (compatibilidad con el layout original).
La lógica real de navegación por overlays está en ocr_processing.py.
Este handler mantiene la sincronización del store overlay-page-index.
"""
from __future__ import annotations

import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate


def register_callbacks_12(app, controller, embedder=None):
    """
    Mantiene sincronizado overlay-page-index.ocr cuando cambia doc-context.
    La navegación real está en ocr_processing.register_callbacks_04.
    """
    @app.callback(
        Output("overlay-page-index", "data", allow_duplicate=True),
        Input("doc-context", "data"),
        State("overlay-page-index", "data"),
        prevent_initial_call=True,
    )
    def reset_ocr_index_on_new_doc(doc_ctx, page_index):
        if not doc_ctx:
            raise PreventUpdate
        pi = dict(page_index or {})
        pi["ocr"] = 0
        return pi
