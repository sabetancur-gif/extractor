
"""
src/app/handlers/download_visualization.py
------------------------------------------
Callbacks para descarga de la visualización generada (overlay).
"""

# STDLIB
import base64
import json
import os

# THIRDPARTY
import dash
from dash import Input, Output, State, dcc


def register_callbacks_08(app, controller, embedder=None):
    """
    Registra callback para descargar la visualización (overlay) generada.
    Relacionado con IDs: download-visualization, download-visualization-btn, doc-context.
    """

    @app.callback(
        Output("download-visualization", "data"),
        Input("download-visualization-btn", "n_clicks"),
        State("doc-context", "data"),
        prevent_initial_call=True,
    )
    def download_visualization(n, doc_ctx):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        # Cargar overlays desde JSON si existe para coherencia
        json_path = doc_ctx.get("saved_path")
        doc = doc_ctx
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except Exception:
                doc = doc_ctx

        overlays = doc.get("overlays", [])
        if not overlays:
            raise dash.exceptions.PreventUpdate

        try:
            with open(overlays[0]["path"], "rb") as f:
                b64 = base64.b64encode(f.read()).decode()

            # Nota: si prefieres un archivo imagen real, usa send_file si está disponible.
            # Aquí, por simplicidad, enviamos un data URL como texto.
            return dcc.send_string(
                f"data:image/png;base64,{b64}",
                filename=f"{doc.get('doc_id', 'document')}_overlay.txt",
            )
        except Exception:
            raise dash.exceptions.PreventUpdate
