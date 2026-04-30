"""
Advanced search engine for PDF corpus using InvertedIndex.
Supports word, phrase, and fuzzy search. Thread-safe.
"""
from typing import List, Dict, Optional
from src.indexer.inverted_index import InvertedIndex

class SearchEngine:
    """
    Search API for indexed PDF corpus.
    """
    def __init__(self, index: Optional[InvertedIndex] = None):
        self.index = index or InvertedIndex()

    def add_pdf(self, file_id: str, filename: str, pages: List[str]):
        """
        Add a PDF to the index.
        Args:
            file_id: Unique document ID
            filename: Name of the PDF file
            pages: List of page texts
        """
        self.index.add_document(file_id, filename, pages)

    def search(self, query: str, fuzzy: bool = False) -> List[Dict]:
        """
        Search the corpus for a word, phrase, or fuzzy match.
        Returns list of dicts: filename, file_id, page_number, context_snippet, match_positions
        """
        return self.index.search(query, fuzzy=fuzzy)
