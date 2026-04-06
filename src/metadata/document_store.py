# src/metadata/document_store.py
import os
import json
import numpy as np
from typing import Dict, Any

class DocumentStore:
    """
    Guarda y carga document.json y embeddings en data/outputs/{doc_id}/
    """
    def __init__(self, base_dir="data/output"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _doc_folder(self, doc_id: str) -> str:
        folder = os.path.join(self.base_dir, doc_id)
        os.makedirs(folder, exist_ok=True)
        return folder

    def save_document(self, context: Dict[str, Any]) -> str:
        """
        Guarda context (serializable) a document.json en la carpeta del doc_id.
        Si context['embedding'] es numpy array o lista la guarda como .npy tambien.
        Retorna path del JSON.
        """
        doc_id = context.get("doc_id") or context.get("docid") or "unknown"
        folder = self._doc_folder(doc_id)
        json_path = os.path.join(folder, "document.json")
        # serializar numpy arrays si existieran
        ctx_copy = dict(context)
        emb = ctx_copy.get("embedding")
        if emb is not None:
            try:
                arr = np.array(emb)
                np.save(os.path.join(folder, "embedding.npy"), arr)
                # keep a small metadata entry in JSON
                ctx_copy["embedding"] = {"saved": "embedding.npy", "shape": arr.shape}
            except Exception:
                # fallback: keep embedding as-is if not savable
                pass
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ctx_copy, f, ensure_ascii=False, indent=2)
        return json_path

    def load_document(self, doc_id: str) -> Dict[str, Any]:
        folder = self._doc_folder(doc_id)
        json_path = os.path.join(folder, "document.json")
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"No document.json for {doc_id}")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_documents(self):
        return [name for name in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, name))]

    def delete_document(self, doc_id: str):
        folder = os.path.join(self.base_dir, doc_id)
        if os.path.exists(folder):
            import shutil
            shutil.rmtree(folder)
            return True
        return False
