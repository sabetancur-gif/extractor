
"""
src/app/handlers/visualization_navigation.py
--------------------------------------------
Callbacks para navegación de overlays en el tab de visualización principal.
"""

# STDLIB
import base64

# THIRDPARTY
import dash
from dash import Input, Output, State


def register_callbacks_14(app, controller, embedder=None):
    """
    Registra callbacks para navegación de overlays en el tab de visualización principal.
    Relacionado con IDs: pdf-preview, overlay-page-indicator-viz, overlay-page-index, overlay-prev-viz, overlay-next-viz, visualization-pdf-selector, doc-context.
    """
    # ===== NAVEGACIÓN DE OVERLAYS - VISUALIZATION =====
    @app.callback(
        [
            Output("pdf-preview", "src", allow_duplicate=True),
            Output("overlay-page-indicator-viz", "children"),
            Output("overlay-page-index", "data", allow_duplicate=True),
        ],
        [
            Input("overlay-prev-viz", "n_clicks"),
            Input("overlay-next-viz", "n_clicks"),
            Input("visualization-pdf-selector", "value"),
            Input("doc-context", "data"),
        ],
        State("overlay-page-index", "data"),
        prevent_initial_call=True,
    )
    def navigate_visualization_overlays(prev_clicks, next_clicks, selected_doc_id, doc_ctx, page_index):
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        # doc_ctx is now a dict of doc_id -> result_ctx
        if isinstance(doc_ctx, dict) and selected_doc_id:
            result_ctx = doc_ctx.get(selected_doc_id)
        elif isinstance(doc_ctx, dict):
            # fallback: pick first
            result_ctx = next(iter(doc_ctx.values()), None)
        else:
            result_ctx = doc_ctx

        if not result_ctx:
            raise dash.exceptions.PreventUpdate

        overlays = []
        if isinstance(result_ctx, dict):
            overlays = result_ctx.get("overlays", [])
        if not overlays:
            raise dash.exceptions.PreventUpdate

        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        current_idx = page_index.get("viz", 0) if page_index else 0

        if triggered_id == "overlay-next-viz":
            current_idx = min(current_idx + 1, len(overlays) - 1)
        elif triggered_id == "overlay-prev-viz":
            current_idx = max(current_idx - 1, 0)
        elif triggered_id == "visualization-pdf-selector":
            current_idx = 0  # reset to first page when switching PDF

        # Cargar imagen del overlay actual
        overlay = overlays[current_idx]
        overlay_path = overlay.get("path")

        img_src = dash.no_update
        if overlay_path:
            try:
                with open(overlay_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                img_src = f"data:image/png;base64,{b64}"
            except Exception:
                pass

        page_num = overlay.get("page", current_idx + 1)
        indicator = f"Page {current_idx + 1}/{len(overlays)} (p{page_num})"

        page_index["viz"] = current_idx

        return img_src, indicator, page_index
