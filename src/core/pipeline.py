
"""
src/core/pipeline.py
--------------------
Orquesta el procesamiento completo de un documento PDF: detección, extracción, segmentación, campos, embeddings, overlays y persistencia.
"""

from typing import Any, Dict, List
import sys
from src.indexer.inverted_index import InvertedIndex
from src.indexer.document_text_store import DocumentTextStore
from src.search.search_engine import SearchEngine

class Pipeline:
    """
    Pipeline de procesamiento de documentos PDF.
    Flujo: detección tipo → extracción → segmentación → campos → embeddings → overlays → persistencia.
    """
    def __init__(
        self,
        detector,
        extractor_factory,
        segmenter,
        field_extractor,
        embedder,
        overlay_gen,
        store,            # DocumentStore (persistencia JSON/embedding)
        storage,          # StorageManager (paths de caché por página)
        image_utils,      # función: render_page_to_image(file_path, page_num, out_path)
        index: InvertedIndex = None,
        text_store: DocumentTextStore = None,
        search_engine: SearchEngine = None,
        log_mgr=None
    ):
        self.detector = detector
        self.extractor_factory = extractor_factory
        self.segmenter = segmenter
        self.field_extractor = field_extractor
        self.embedder = embedder
        self.overlay_gen = overlay_gen
        self.store = store
        self.storage = storage
        self.image_utils = image_utils
        self.text_store = text_store or DocumentTextStore()
        self.index = index or InvertedIndex()
        self.search_engine = search_engine or SearchEngine(self.index)
        self.log_mgr = log_mgr

    def run(self, context, fast_mode: bool = False):
        """
        Ejecuta el pipeline de procesamiento sobre el contexto dado.
        Args:
            context: Objeto tipo DocumentContext (mutable).
            fast_mode (bool): Si True, usa procesamiento rápido (no implementado por defecto).
        Returns:
            context: El mismo objeto, enriquecido con resultados.
        """
        try:
            # 1. Detecta tipo si no está
            context.pdf_type = context.pdf_type or self.detector.detect(context.file_path)

            # 2. Crea extractor según tipo
            extractor = self.extractor_factory.create(context.pdf_type)

            # 3. Extrae páginas con barra de progreso rich
            log_mgr = self.log_mgr
            pages = []
            with log_mgr.show_progress(total=1, description=f"Extract {context.file_name}") as progress:
                task = progress.add_task("Extract", total=1)
                pages = extractor.extract(context.file_path)
                progress.update(task, advance=1)
            context.pages = pages

            # 3b. Guardar texto de cada página para indexación/búsqueda (robusto)
            page_texts = []
            for p in pages:
                if isinstance(p, dict):
                    page_texts.append(p.get("text", ""))
                else:
                    page_texts.append(getattr(p, "text", ""))
            self.text_store.add_document(context.doc_id, page_texts)
            self.index.add_document(context.doc_id, context.file_name, page_texts)

            # 4. Layout segmentation
            context.pages = self.segmenter.analyze(context.pages)

            # 5. Extracción de campos
            context.fields = self.field_extractor.extract(context.pages)

            # 6. Embeddings (Embedder acepta objeto o dict)
            if not self.embedder:
                print("[WARNING] Embedder no inicializado, se omite embeddings.", file=sys.stderr)
                context.embedding = None
            else:
                context.embedding = self.embedder.embed_document(context)

            # 7. Render de imágenes + overlays para TODAS las páginas
            overlays: List[Dict[str, Any]] = []
            if not self.overlay_gen:
                print("[WARNING] OverlayGenerator no inicializado, se omiten overlays.", file=sys.stderr)
            else:
                for p in context.pages:
                    page_num = p["page_number"] if isinstance(p, dict) else getattr(p, "page_number", None)
                    blocks = p["blocks"] if isinstance(p, dict) else getattr(p, "blocks", [])
                    page_width = p["width"] if isinstance(p, dict) else getattr(p, "width", None)
                    page_height = p["height"] if isinstance(p, dict) else getattr(p, "height", None)
                    if page_num is None:
                        continue
                    page_img_path = self.storage.page_cache_path(context.doc_id, page_num)
                    page_img = self.image_utils(context.file_path, page_num, page_img_path)
                    overlay_path = self.overlay_gen.render_page_overlay(
                        page_img, blocks, context.doc_id, page_num, page_width, page_height
                    )
                    overlays.append({"page": page_num, "path": overlay_path})
            context.overlays = overlays

            # 8. Persistencia (DocumentStore guarda JSON y embedding.npy si aplica)
            saved_path = self.store.save_document(context.__dict__)
            context.logs["saved_path"] = saved_path

        except Exception as e:
            print(f"[ERROR] Error en pipeline: {e}", file=sys.stderr)
            context.logs = context.logs if hasattr(context, "logs") else {}
            context.logs["error"] = str(e)
        return context
