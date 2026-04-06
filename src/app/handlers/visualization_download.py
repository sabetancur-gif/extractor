
"""
src/app/handlers/visualization_download.py
------------------------------------------------
Callbacks para visibilidad de tabs principales (layout).
"""

# THIRDPARTY
from dash import Input, Output


def register_callbacks_01(app, controller, embedder=None):
    """
    Registra callback para mostrar/ocultar el contenido de cada tab según el tab activo.
    Relacionado con IDs: tab-visualization-content, tab-pdf-analysis-content, ...
    """
    @app.callback(
        [
            Output("tab-visualization-content", "style"),
            Output("tab-pdf-analysis-content", "style"),
            Output("tab-ocr-processing-content", "style"),
            Output("tab-format-conversion-content", "style"),
            Output("tab-translation-content", "style"),
            Output("tab-toc-extraction-content", "style"),
            Output("tab-clustering-content", "style")
        ],
        [
            Input("sidebar-tabs", "active_tab")
        ]
    )
    def toggle_tab_visibility(active_tab):
        """Solo controla visibilidad, no re-renderiza el contenido."""
        tabs = [
            "tab-visualization",
            "tab-pdf-analysis",
            "tab-ocr-processing",
            "tab-format-conversion",
            "tab-translation",
            "tab-toc-extraction",
            "tab-clustering"
        ]

        styles = [
            {"display": "block" if tab == active_tab else "none"}
            for tab in tabs
        ]
        return styles
