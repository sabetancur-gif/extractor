"""
DocumentTextStore: almacena y recupera el texto de cada página de cada PDF para el indexador/buscador.
"""
from typing import Dict, List
import threading

class DocumentTextStore:
    def __init__(self):
        self.texts: Dict[str, Dict[int, str]] = {}  # file_id -> {page_num: text}
        self.lock = threading.Lock()

    def add_document(self, file_id: str, pages: List[str]):
        with self.lock:
            self.texts[file_id] = {i+1: t for i, t in enumerate(pages)}

    def get_page_text(self, file_id: str, page_num: int) -> str:
        with self.lock:
            return self.texts.get(file_id, {}).get(page_num, "")
