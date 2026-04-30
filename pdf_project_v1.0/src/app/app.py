
"""
Entrypoint principal de la aplicación Dash.
Instancia la app, pipeline, layout y registra callbacks.
"""

from dash import Dash
import dash_bootstrap_components as dbc

from .callbacks import register_callbacks
from .layout import layout

# --- Componentes del pipeline ---
from src.detection.pdf_type_detector import PDFTypeDetector
from src.extraction.native import NativePDFExtractor
from src.extraction.ocr import OCRExtractor
from src.extraction.hybrid import HybridExtractor
from src.layout.segmenter import LayoutSegmenter
from src.semantic.field_extraction import FieldExtractor
from src.semantic.embedding import Embedder
from src.visualization.overlay import OverlayGenerator
from src.metadata.document_store import DocumentStore
from src.ingest.storage import StorageManager
from src.utils.image import render_page_to_image
from src.core.pipeline import Pipeline
from src.core.controller import Controller
from src.logs.logger import LogManager

# --- Constantes de estilos ---
external_stylesheets = [
    dbc.themes.DARKLY,
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css",
]

# --- Factory para extractores PDF ---
class ExtractorFactory:
    """Factory para seleccionar extractor según tipo de PDF."""
    def __init__(self, native, ocr, hybrid):
        self.native = native
        self.ocr = ocr
        self.hybrid = hybrid

    def create(self, pdf_type):
        if pdf_type == "native":
            return self.native
        if pdf_type == "scanned":
            return self.ocr
        return self.hybrid

# --- Instanciación de componentes principales ---
detector = PDFTypeDetector()
native_ex = NativePDFExtractor()
ocr_ex = OCRExtractor()
hybrid_ex = HybridExtractor(native_ex, ocr_ex)
extractor_factory = ExtractorFactory(native_ex, ocr_ex, hybrid_ex)
segmenter = LayoutSegmenter()
field_extractor = FieldExtractor()
log_mgr = LogManager()

# --- Inicialización de embedder con manejo de error ---
try:
    embedder = Embedder()
except Exception as e:
    print(f"[WARNING] Embedder no inicializado: {e}")
    embedder = None

overlay_gen = OverlayGenerator(log_mgr=log_mgr)
store = DocumentStore()
storage = StorageManager()

# --- Pipeline y controller ---
pipeline = Pipeline(
    detector=detector,
    extractor_factory=extractor_factory,
    segmenter=segmenter,
    field_extractor=field_extractor,
    embedder=embedder,
    overlay_gen=overlay_gen,
    store=store,
    storage=storage,
    image_utils=render_page_to_image,
    log_mgr=log_mgr
)
controller = Controller(pipeline)

# --- Instancia de la app Dash ---
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=external_stylesheets
)
app.layout = layout()

# --- Registro de callbacks globales ---
register_callbacks(app, controller, embedder)

if __name__ == "__main__":
    app.run(debug=True)
