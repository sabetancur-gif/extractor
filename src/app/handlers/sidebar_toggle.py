
"""
src/app/handlers/sidebar_toggle.py
----------------------------------
Callbacks para mostrar/ocultar el sidebar y ajustar el layout.
"""

# THIRDPARTY
from dash import Input, Output, State


def register_callbacks_09(app, controller, embedder=None):
    """
    Registra callback para mostrar/ocultar el sidebar y ajustar el layout.
    Relacionado con IDs: sidebar, page-content, sidebar-state, btn-toggle-sidebar.
    """

    @app.callback(
        Output("sidebar", "className"),
        Output("page-content", "style"),
        Output("sidebar-state", "data"),
        Input("btn-toggle-sidebar", "n_clicks"),
        State("sidebar-state", "data"),
        State("page-content", "style")
    )
    def toggle_sidebar(n_clicks, is_open, page_style):
        if not n_clicks:
            return "", page_style, True

        is_open = not is_open  # Toggle

        if is_open:
            sidebar_class = ""
            page_style["marginLeft"] = "260px"
        else:
            sidebar_class = "sidebar-hidden"
            page_style["marginLeft"] = "0px"

        return sidebar_class, page_style, is_open
