"""
src/app/handlers/visualization_navigation.py
----------------------------------------------
Callbacks de navegación de overlays en el tab de Visualization principal.
"""
from __future__ import annotations

import base64

import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate


def register_callbacks_14(app, controller, embedder=None):

    @app.callback(
        [
            Output("pdf-preview",              "src",      allow_duplicate=True),
            Output("overlay-page-indicator-viz","children"),
            Output("overlay-page-index",        "data",    allow_duplicate=True),
        ],
        [
            Input("overlay-prev-viz",           "n_clicks"),
            Input("overlay-next-viz",           "n_clicks"),
            Input("visualization-pdf-selector", "value"),
            Input("doc-context",                "data"),
        ],
        State("overlay-page-index", "data"),
        prevent_initial_call=True,
    )
    def navigate_viz_overlays(prev, next_, selected_id, doc_ctx, page_index):
        if not doc_ctx:
            raise PreventUpdate

        # Seleccionar documento
        if isinstance(doc_ctx, dict) and selected_id:
            result_ctx = doc_ctx.get(selected_id)
        elif isinstance(doc_ctx, dict):
            result_ctx = next(iter(doc_ctx.values()), None)
        else:
            result_ctx = doc_ctx

        if not isinstance(result_ctx, dict):
            raise PreventUpdate

        overlays = result_ctx.get("overlays") or []
        if not overlays:
            raise PreventUpdate

        triggered = (dash.callback_context.triggered[0]["prop_id"].split(".")[0]
                     if dash.callback_context.triggered else None)

        page_index = page_index or {}
        idx = page_index.get("viz", 0)

        if triggered == "overlay-next-viz":
            idx = min(idx + 1, len(overlays) - 1)
        elif triggered == "overlay-prev-viz":
            idx = max(idx - 1, 0)
        elif triggered in ("visualization-pdf-selector", "doc-context"):
            idx = 0

        ov       = overlays[idx]
        path     = ov.get("path", "")
        img_src  = dash.no_update

        if path:
            try:
                with open(path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                img_src = f"data:image/png;base64,{b64}"
            except Exception:
                pass

        page_num  = ov.get("page", idx + 1)
        indicator = f"Página {idx + 1}/{len(overlays)}  (p{page_num})"

        page_index["viz"] = idx
        return img_src, indicator, page_index
