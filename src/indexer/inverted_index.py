"""
Inverted index for fast full-text search across multiple PDFs.
Supports word, phrase, and fuzzy search. Designed for concurrent updates.
"""
from typing import Dict, List, Tuple, Set, Optional
import threading
import re

class InvertedIndex:
    """
    Thread-safe inverted index for PDF corpus.
    """
    def __init__(self):
        self.index: Dict[str, List[Tuple[str, int, int]]] = {}
        self.lock = threading.Lock()
        self.doc_map: Dict[str, Dict] = {}  # file_id -> metadata

    def add_document(self, file_id: str, filename: str, pages: List[str]):
        """
        Indexes all words in all pages of a document.
        Args:
            file_id: Unique document ID
            filename: Name of the PDF file
            pages: List of page texts
        """
        with self.lock:
            self.doc_map[file_id] = {"filename": filename, "pages_total": len(pages)}
            for page_num, text in enumerate(pages, 1):
                for match in re.finditer(r"\\w+", text, re.UNICODE):
                    word = match.group(0).lower()
                    self.index.setdefault(word, []).append((file_id, page_num, match.start()))

    def search(self, query: str, fuzzy: bool = False) -> List[Dict]:
        """
        Search for a word, phrase, or fuzzy match in the corpus.
        Returns list of dicts: filename, file_id, page_number, context_snippet, match_positions
        """
        results = []
        q = query.lower()
        with self.lock:
            if not fuzzy and " " not in q:
                # Simple word search
                hits = self.index.get(q, [])
                for file_id, page_num, pos in hits:
                    snippet = self._get_snippet(file_id, page_num, pos, q)
                    results.append({
                        "filename": self.doc_map[file_id]["filename"],
                        "file_id": file_id,
                        "page_number": page_num,
                        "context_snippet": snippet,
                        "match_positions": [pos]
                    })
            else:
                # Phrase or fuzzy search
                for file_id, meta in self.doc_map.items():
                    for page_num in range(1, meta["pages_total"] + 1):
                        page_text = self._get_page_text(file_id, page_num)
                        for m in re.finditer(re.escape(q), page_text, re.IGNORECASE):
                            snippet = self._get_snippet(file_id, page_num, m.start(), q)
                            results.append({
                                "filename": meta["filename"],
                                "file_id": file_id,
                                "page_number": page_num,
                                "context_snippet": snippet,
                                "match_positions": [m.start()]
                            })
                        if fuzzy:
                            # Simple fuzzy: allow 1 char difference
                            for word in set(re.findall(r"\\w+", page_text)):
                                if self._levenshtein(word.lower(), q) == 1:
                                    for m in re.finditer(word, page_text, re.IGNORECASE):
                                        snippet = self._get_snippet(file_id, page_num, m.start(), word)
                                        results.append({
                                            "filename": meta["filename"],
                                            "file_id": file_id,
                                            "page_number": page_num,
                                            "context_snippet": snippet,
                                            "match_positions": [m.start()]
                                        })
        return results

    def set_text_store(self, text_store):
        self.text_store = text_store

    def _get_page_text(self, file_id: str, page_num: int) -> str:
        if hasattr(self, "text_store") and self.text_store:
            return self.text_store.get_page_text(file_id, page_num)
        return ""

    def _get_snippet(self, file_id: str, page_num: int, pos: int, query: str, window: int = 60) -> str:
        # Placeholder: should be replaced with actual page text retrieval
        return f"...{query}..."

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        # Simple Levenshtein distance for fuzzy search
        if a == b:
            return 0
        if abs(len(a) - len(b)) > 1:
            return 2
        if len(a) < len(b):
            a, b = b, a
        if len(a) == len(b):
            return sum(x != y for x, y in zip(a, b))
        for i in range(len(a)):
            if a[:i] + a[i+1:] == b:
                return 1
        return 2
