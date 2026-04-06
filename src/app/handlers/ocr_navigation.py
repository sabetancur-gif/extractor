
"""
src/app/handlers/ocr_navigation.py
----------------------------------
Callbacks para navegación de overlays en el tab OCR (paginación de imágenes OCR).
"""

# STDLIB
import base64

# THIRDPARTY
import dash
from dash import Input, Output, State, dcc, html


def register_callbacks_12(app, controller, embedder=None):
    """
    Registra callbacks para navegación de overlays OCR (paginación de imágenes OCR).
    Relacionado con IDs: ocr-output, overlay-page-indicator-ocr, overlay-page-index, overlay-prev-ocr, overlay-next-ocr, doc-context.
    """

    @app.callback(
        [
            Output("ocr-output", "children", allow_duplicate=True),
            Output("overlay-page-indicator-ocr", "children"),
            Output("overlay-page-index", "data", allow_duplicate=True),
        ],
        [
            Input("overlay-prev-ocr", "n_clicks"),
            Input("overlay-next-ocr", "n_clicks"),
            Input("doc-context", "data"),
        ],
        State("overlay-page-index", "data"),
        prevent_initial_call=True,
    )
    def navigate_ocr_overlays(prev_clicks, next_clicks, doc_ctx, page_index):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        overlays = doc_ctx.get("overlays", [])
        if not overlays:
            raise dash.exceptions.PreventUpdate

        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        current_idx = page_index.get("ocr", 0) if page_index else 0

        if triggered_id == "overlay-next-ocr":
            current_idx = min(current_idx + 1, len(overlays) - 1)
        elif triggered_id == "overlay-prev-ocr":
            current_idx = max(current_idx - 1, 0)

        # Cargar imagen del overlay actual
        overlay = overlays[current_idx]
        overlay_path = overlay.get("path")

        children = []
        if overlay_path:
            try:
                with open(overlay_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                children.append(html.Img(src=f"data:image/png;base64,{b64}", style={"width": "100%"}))
            except Exception as e:
                children.append(dcc.Markdown(f"Error cargando overlay: {e}"))

        page_num = overlay.get("page", current_idx + 1)
        indicator = f"Page {current_idx + 1}/{len(overlays)} (p{page_num})"

        # Agregar confianza si está disponible
        avg_conf = doc_ctx.get("ocr_average_confidence")
        if avg_conf is not None:
            children.append(dcc.Markdown(f"**Confianza promedio OCR:** {avg_conf:.1f}"))

        page_index["ocr"] = current_idx

        return html.Div(children), indicator, page_index
