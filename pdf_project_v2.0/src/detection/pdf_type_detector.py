"""Docstring for detection.pdf_type_detector.

Docstring.
"""


import fitz  # pyMuPDF
from src.logs.logger import LogManager
from datetime import datetime
import threading
import os


class PDFTypeDetector:
    """Docstring for PDFTypeDetector.
    """
    def __init__(
            self, sample_pages=4,
            text_area_threshold=0.30,
            image_area_threshold=0.0001,
            min_image_ratio=0.02,  # Lo utilizamos para ignorar imagenes
            log_mgr: LogManager = None
    ):
        self.sample_pages = sample_pages
        self.text_area_threshold = text_area_threshold
        self.image_area_threshold = image_area_threshold
        self.min_image_ratio = min_image_ratio
        self.log_mgr = log_mgr or LogManager()

    def detect(self, file_path) -> str:
        try:
            # Abrir el documento
            doc = fitz.open(file_path)

        except Exception:
            # No se pudo abrir: archivo corrupto, no-PDF, etc
            return "invalid"

        # PDF cifrado sin contraseña: no podemos leer contenido
        if doc.is_encrypted:
            return "encrypted"

        n = len(doc)

        if n == 0:
            # Documento sin paginas: no clasificamos como nativo
            return "empty"

        # Contadores
        text_pages = 0
        image_pages = 0

        total_pages = min(self.sample_pages, len(doc))

        for i in range(total_pages):
            page = doc[i]
            info = page.get_text("dict")

            if not info.get("blocks"):
                self.log_mgr.log({
                    "timestamp": datetime.now().isoformat(),
                    "file_id": file_path,
                    "filename": file_path.split(os.sep)[-1],
                    "step": "DETECT",
                    "page_number": i + 1,
                    "pages_total": n,
                    "worker_id": threading.get_ident(),
                    "status": "scanned_detected",
                    "duration_seconds": None,
                    "avg_sec_per_page": None,
                    "concurrency_count": None,
                    "match_query": None,
                    "context_snippet": "blocks=[] → classified as scanned",
                    "error_message": None
                })
                return "scanned"

            text_ratio = self._text_area_ratio(page)
            image_ratio = self._image_area_ratio(page)
            self.log_mgr.log({
                "timestamp": datetime.now().isoformat(),
                "file_id": file_path,
                "filename": file_path.split(os.sep)[-1],
                "step": "DETECT",
                "page_number": i+1,
                "pages_total": n,
                "worker_id": threading.get_ident(),
                "status": "running",
                "duration_seconds": None,
                "avg_sec_per_page": None,
                "concurrency_count": None,
                "match_query": None,
                "context_snippet": f"text_ratio={text_ratio}, image_ratio={image_ratio}",
                "error_message": None
            })
            if text_ratio > self.text_area_threshold:
                text_pages += 1
            if image_ratio > self.image_area_threshold:
                image_pages += 1

        if text_pages == 0 and image_pages > 0:
            return "scanned"

        if text_pages > 0 and image_pages > 0:
            return "mixed"

        return "native"

    def _text_area_ratio(self, page):
        page_area = page.rect.width * page.rect.height

        if page_area <= 0:
            return 0.0

        info = page.get_text("dict")

        text_area = 0.0

        for block in info.get("blocks", []):
            if block.get("type") == 0 and "bbox" in block:  # texto
                x0, y0, x1, y1 = block["bbox"]
                w = max(0.0, x1 - x0)
                h = max(0.0, y1 - y0)

                text_area += w * h

        ratio = text_area / page_area
        return max(0.0, min(1.0, ratio))

    def _image_area_ratio(self, page):
        page_area = page.rect.width * page.rect.height
        if page_area <= 0:
            return 0.0

        info = page.get_text("dict")
        image_area = 0.0

        for block in info.get("blocks", []):
            if block.get("type") == 1 and "bbox" in block:  # imagen
                x0, y0, x1, y1 = block["bbox"]
                w = max(0.0, x1 - x0)
                h = max(0.0, y1 - y0)
                area = w * h

                # Ignorar imágenes muy pequeñas (logos/íconos)
                if area / page_area >= self.min_image_ratio:
                    image_area += area

        ratio = image_area / page_area
        return max(0.0, min(1.0, ratio))
