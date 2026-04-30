"""
src/app/callbacks.py
---------------------
Centraliza el registro de todos los callbacks Dash.
Cada handler implementa un grupo de callbacks para una feature/tab.

Índice de handlers:
  01 - Descarga de visualización
  02 - Upload y análisis de PDF
  03 - Búsqueda avanzada (PDF Analysis)
  04 - Procesamiento OCR
  05 - Exportación / conversión de formatos
  06 - Traducción
  07 - Extracción de TOC
  08 - Descarga de archivo
  09 - Toggle del sidebar
  10 - Dropdowns de búsqueda
  11 - Clustering y embeddings
  12 - Navegación OCR (overlay-page-index)
  13 - Overlays y crop (preview de regiones)
  14 - Navegación de overlays en Visualization
  15 - LLM Enricher
  CB - Chatbot (JuanBot)
"""

from src.app.handlers.visualization_download import register_callbacks_01
from src.app.handlers.upload_and_analysis    import register_callbacks_02
from src.app.handlers.document_search        import register_callbacks_03
from src.app.handlers.ocr_processing         import register_callbacks_04
from src.app.handlers.export_converters      import register_callbacks_05
from src.app.handlers.translation            import register_callbacks_06
from src.app.handlers.toc_extration          import register_callbacks_07
from src.app.handlers.download_visualization import register_callbacks_08
from src.app.handlers.sidebar_toggle        import register_callbacks_09
from src.app.handlers.search_dropdowns       import register_callbacks_10
from src.app.handlers.clustering             import register_callbacks_11
from src.app.handlers.ocr_navigation         import register_callbacks_12
from src.app.handlers.overlays               import register_callbacks_13
from src.app.handlers.visualization_navigation import register_callbacks_14
from src.app.handlers.llm_analysis           import register_callbacks_15
from src.app.handlers.chatbot_handler        import register_callbacks_chatbot


def register_callbacks(app, controller, embedder=None):
    """
    Registra todos los callbacks Dash.
    Si un handler falla, muestra advertencia sin romper la app.
    """
    handlers = [
        ("01-visualization_download",    register_callbacks_01),
        ("02-upload_and_analysis",       register_callbacks_02),
        ("03-document_search",           register_callbacks_03),
        ("04-ocr_processing",            register_callbacks_04),
        ("05-export_converters",         register_callbacks_05),
        ("06-translation",               register_callbacks_06),
        ("07-toc_extraction",            register_callbacks_07),
        ("08-download_visualization",    register_callbacks_08),
        ("09-sidebar_toggle",            register_callbacks_09),
        ("10-search_dropdowns",          register_callbacks_10),
        ("11-clustering",                register_callbacks_11),
        ("12-ocr_navigation",            register_callbacks_12),
        ("13-overlays",                  register_callbacks_13),
        ("14-visualization_navigation",  register_callbacks_14),
        ("15-llm_analysis",              register_callbacks_15),
        ("CB-chatbot",                   register_callbacks_chatbot),
    ]

    for name, fn in handlers:
        try:
            fn(app, controller, embedder)
            print(f"  ✅ Callbacks registrados: {name}")
        except Exception as e:
            print(f"  ⚠️  Error registrando {name}: {e}")
