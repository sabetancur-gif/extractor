"""Docstring for extraction.base.

Docstring.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseExtractor(ABC):
    """Interfaz para extractores: native, ocr, hybrid.

    Devuelven List[page_dict] con:
        page_dict = {
            "page_number": int,
            "width": float,
            "height": float,
            "blocks": [ { block dict } ]
        }
    block dict must include:
        block_id, text, bbox [x0, y0, x1, y1], page, source, order, optional(font_size, font_name)
    """
    @abstractmethod
    def extract(self, file_path: str) -> List[Dict]:
        raise NotImplementedError
