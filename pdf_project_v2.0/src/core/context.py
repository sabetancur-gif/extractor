# src/core/context.py
from dataclasses import dataclass, field
import time
from typing import List, Dict

@dataclass
class DocumentContext:
    doc_id: str
    file_path: str
    file_name: str
    pdf_type: str = None
    pages: List[Dict] = field(default_factory=list)
    fields: List[Dict] = field(default_factory=list)
    overlays: List[Dict] = field(default_factory=list)
    embedding = None
    logs: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
