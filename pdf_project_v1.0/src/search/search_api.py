"""
API de búsqueda para exponer búsqueda sobre todos los PDFs procesados.
"""
from src.search.search_engine import SearchEngine
from typing import List, Dict

class SearchAPI:
    def __init__(self, search_engine: SearchEngine):
        self.engine = search_engine

    def search(self, query: str, fuzzy: bool = False) -> List[Dict]:
        """
        Busca en todo el corpus. Devuelve lista de dicts con filename, file_id, page_number, context_snippet, match_positions.
        """
        return self.engine.search(query, fuzzy=fuzzy)
