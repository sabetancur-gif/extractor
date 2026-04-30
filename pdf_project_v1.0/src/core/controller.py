
"""
src/core/controller.py
----------------------
Orquesta el procesamiento de documentos PDF usando el pipeline.
Define la estructura DocumentContext para encapsular el estado de procesamiento.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
import sys

@dataclass
class DocumentContext:
    """
    Estructura de datos para encapsular el estado de procesamiento de un documento PDF.
    Se usa como intercambio entre el pipeline y la UI/callbacks.
    """
    doc_id: str
    file_path: str
    file_name: str
    pdf_type: Optional[str] = None
    pages: List[Dict] = field(default_factory=list)
    fields: List[Dict] = field(default_factory=list)
    overlays: List[Dict] = field(default_factory=list)
    embedding: Any = None
    logs: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el contexto a un dict serializable para la UI/callbacks."""
        return {
            "doc_id": self.doc_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "pdf_type": self.pdf_type,
            "pages": self.pages,
            "fields": self.fields,
            "overlays": self.overlays,
            "embedding": self.embedding,
            "logs": self.logs,
            "created_at": self.created_at,
        }

class Controller:
    """
    Orquestador principal: recibe paths y metadatos, ejecuta el pipeline y devuelve el contexto procesado.
    """
    def __init__(self, pipeline):
        self.pipeline = pipeline
        # Si el pipeline tiene index y text_store, enlazarlos
        if hasattr(pipeline, "index") and hasattr(pipeline, "text_store"):
            pipeline.index.set_text_store(pipeline.text_store)

    def process(self, file_path: str, file_name: str, doc_id: str, fast_mode: bool = False) -> Dict[str, Any]:
        """
        Procesa un documento PDF usando el pipeline y devuelve el contexto como dict.
        Args:
            file_path (str): Ruta al archivo PDF.
            file_name (str): Nombre del archivo.
            doc_id (str): ID único del documento.
            fast_mode (bool): Si True, usa procesamiento rápido (opcional).
        Returns:
            dict: Contexto procesado listo para la UI/callbacks.
        """
        if not file_path or not file_name or not doc_id:
            raise ValueError("file_path, file_name y doc_id son obligatorios")
        ctx = DocumentContext(doc_id=doc_id, file_path=file_path, file_name=file_name)
        try:
            ctx = self.pipeline.run(ctx, fast_mode=fast_mode)
        except Exception as e:
            print(f"[ERROR] Error en pipeline: {e}", file=sys.stderr)
            ctx.logs["error"] = str(e)
        return ctx.to_dict()
