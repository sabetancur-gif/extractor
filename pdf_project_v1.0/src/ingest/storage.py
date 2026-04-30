"""Docstring for ingest.storage.

Docstring
"""

import os
import shutil


class StorageManager:
    def __init__(self, outputs_dir="data/output", cache_dir="data/cache", raw_dir="data/raw"):
        self.outputs_dir = outputs_dir
        self.cache_dir = cache_dir
        self.raw_dir = raw_dir

        os.makedirs(self.outputs_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)

    # Crea la carpeta final de resultados de un documento
    # 📂 data/output/<doc_id>/
    def create_doc_folder(self, doc_id: str) -> str:
        folder = os.path.join(self.outputs_dir, doc_id)
        os.makedirs(folder, exist_ok=True)
        return folder

    # Devuelve la ruta donde debe guardarse la imagen renderizada de un página
    # 📂 data/cache/<doc_id>/pages/page_3.png
    def page_cache_path(self, doc_id: str, page_num: int, ext="png") -> str:
        folder = os.path.join(self.cache_dir, doc_id, "pages")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"page_{page_num}.{ext}")

    # Genera la ruta para imágenes de overlay (debug visual)
    # 📂 data/cache/<doc_id>/overlays/overlay_p3.png
    def overlay_path(self, doc_id: str, page_num: int) -> str:
        folder = os.path.join(self.cache_dir, doc_id, "overlays")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"overlay_p{page_num}.png")

    # Elimina toda la caché de un documento, la recrea vacía
    def clear_cache(self, doc_id: str):
        folder = os.path.join(self.cache_dir, doc_id)
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
