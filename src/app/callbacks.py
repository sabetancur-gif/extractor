
"""
src/app/callbacks.py
--------------------
Centraliza el registro de todos los callbacks Dash de la app.
Cada grupo de callbacks está delegado a un handler en handlers/ siguiendo la convención register_callbacks_XX.

Relación handlers/tabs/features:
    01: Visualización de tabs principales
    02: Upload y análisis de PDF
    03: Búsqueda avanzada en documento
    04: Procesamiento OCR
    05: Exportación/conversión de formatos
    06: Traducción de documento
    07: Extracción de TOC
    08: Descarga de visualización
    09: Toggle sidebar
    10: Dropdowns de búsqueda
    11: Clustering y embeddings
    12: Navegación OCR
    13: Overlays
    14: Navegación visualización
    15: LLM enrichment and correction
"""

from src.app.handlers.visualization_download import register_callbacks_01
from src.app.handlers.upload_and_analysis import register_callbacks_02
from src.app.handlers.document_search import register_callbacks_03
from src.app.handlers.ocr_processing import register_callbacks_04
from src.app.handlers.export_converters import register_callbacks_05
from src.app.handlers.translation import register_callbacks_06
from src.app.handlers.toc_extration import register_callbacks_07
from src.app.handlers.download_visualization import register_callbacks_08
from src.app.handlers.sidebar_toggle import register_callbacks_09
from src.app.handlers.search_dropdowns import register_callbacks_10
from src.app.handlers.clustering import register_callbacks_11
from src.app.handlers.ocr_navigation import register_callbacks_12
from src.app.handlers.overlays import register_callbacks_13
from src.app.handlers.visualization_navigation import register_callbacks_14
from src.app.handlers.llm_analysis import register_callbacks_15

def register_callbacks(app, controller, embedder=None):
    """
    Registra todos los callbacks Dash de la app.
    Cada handler implementa un grupo de callbacks para una feature/tab.
    Si un handler falla al registrar, muestra advertencia en consola.
    """
    for idx, fn in enumerate([
        register_callbacks_01,
        register_callbacks_02,
        register_callbacks_03,
        register_callbacks_04,
        register_callbacks_05,
        register_callbacks_06,
        register_callbacks_07,
        register_callbacks_08,
        register_callbacks_09,
        register_callbacks_10,
        register_callbacks_11,
        register_callbacks_12,
        register_callbacks_13,
        register_callbacks_14,
        register_callbacks_15,
    ], start=1):
        try:
            fn(app, controller, embedder=embedder)
        except Exception as e:
            print(f"[WARNING] Error registrando callbacks handler {idx:02d}: {e}")

    # --- Callback para sincronizar el valor de analysis-target con visualization-pdf-selector ---
    import dash
    from dash import Input, Output, State
    @app.callback(
        Output("analysis-target", "value", allow_duplicate=True),
        Input("visualization-pdf-selector", "value"),
        State("analysis-target", "options"),
        prevent_initial_call=True,
    )
    def sync_analysis_target_from_visualization(selected_doc_id, analysis_options):
        if not selected_doc_id or not analysis_options:
            return dash.no_update

        valid_values = {
            opt.get("value")
            for opt in analysis_options
            if isinstance(opt, dict) and "value" in opt
        }

        if selected_doc_id not in valid_values:
            return dash.no_update

        return [selected_doc_id]
    # @app.callback(
    #     Output("analysis-target", "value", allow_duplicate=True),
    #     Input("visualization-pdf-selector", "value"),
    #     State("analysis-target", "options"),
    #     prevent_initial_call=True
    # )
    # def sync_analysis_target_from_visualization(selected_doc_id, analysis_options):
    #     # Si el usuario selecciona un documento en visualization, lo seleccionamos en analysis-target
    #     if not selected_doc_id or not analysis_options:
    #         raise Exception("No doc seleccionado o no hay opciones")
    #     # analysis-target es multi, así que debe ser lista
    #     values = [selected_doc_id] if selected_doc_id else []
    #     # Validar que el valor esté en las opciones
    #     valid_values = [opt["value"] for opt in analysis_options]
    #     return [v for v in values if v in valid_values]
