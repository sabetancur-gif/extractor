# # src/semantic/embeddings.py
# from sentence_transformers import SentenceTransformer
# import numpy as np

# class Embedder:
#     def __init__(
#         self,
#         model_name="all-MiniLM-L6-v2",
#         normalize=True,
#         title_weight=1.5,
#         paragraph_weight=1.0
#     ):
#         self.model = SentenceTransformer(model_name)
#         self.normalize = normalize
#         self.weights = {
#             "title": title_weight,
#             "paragraph": paragraph_weight
#         }

#     def embed_document(self, context: dict, max_chars=4000) -> np.ndarray:
#         texts = []
#         weights = []
#         total_chars = 0

#         for p in context.get("pages", []):
#             for b in p.get("blocks", []):
#                 btype = b.get("type")
#                 text = (b.get("text") or "").strip()

#                 if btype not in self.weights or not text:
#                     continue

#                 # control de longitud global
#                 if total_chars + len(text) > max_chars:
#                     text = text[: max_chars - total_chars]

#                 if not text:
#                     break

#                 texts.append(text)
#                 weights.append(self.weights[btype])
#                 total_chars += len(text)

#             if total_chars >= max_chars:
#                 break

#         # fallback seguro
#         if not texts:
#             return np.zeros(self.model.get_sentence_embedding_dimension())

#         # embeddings por bloque
#         vecs = self.model.encode(
#             texts,
#             show_progress_bar=False,
#             normalize_embeddings=self.normalize
#         )

#         weights = np.array(weights).reshape(-1, 1)

#         # mean pooling ponderado
#         doc_vec = (vecs * weights).sum(axis=0) / weights.sum()

#         return doc_vec.astype(np.float32)


# src/semantic/embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np

class Embedder:
    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
        normalize=True,
        title_weight=1.5,
        paragraph_weight=1.0
    ):
        self.model = SentenceTransformer(model_name)
        self.normalize = normalize
        self.weights = {
            "title": title_weight,
            "paragraph": paragraph_weight
        }

    # --- Helpers para soportar dict u objeto ---
    def _get_pages(self, context):
        """Devuelve lista de páginas sin importar si context es dict u objeto."""
        if isinstance(context, dict):
            return context.get("pages", [])
        return getattr(context, "pages", []) or []

    def _iter_blocks(self, page):
        if isinstance(page, dict):
            return page.get("blocks", [])
        return getattr(page, "blocks", []) or []

    def _block_type(self, block):
        if isinstance(block, dict):
            return block.get("type")
        return getattr(block, "type", None)

    def _block_text(self, block):
        if isinstance(block, dict):
            return (block.get("text") or "").strip()
        return (getattr(block, "text", "") or "").strip()

    def embed_document(self, context, max_chars=4000) -> np.ndarray:
        texts = []
        weights = []
        total_chars = 0

        pages = self._get_pages(context)

        for p in pages:
            for b in self._iter_blocks(p):
                btype = self._block_type(b)
                text = self._block_text(b)

                if btype not in self.weights or not text:
                    continue

                # control de longitud global
                if total_chars + len(text) > max_chars:
                    text = text[: max_chars - total_chars]

                if not text:
                    break

                texts.append(text)
                weights.append(self.weights[btype])
                total_chars += len(text)

            if total_chars >= max_chars:
                break

        # fallback: vector cero si no hay texto
        if not texts:
            dim = self.model.get_sentence_embedding_dimension()
            return np.zeros(dim, dtype=np.float32)

        # embeddings por bloque
        vecs = self.model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=self.normalize
        )
        vecs = np.asarray(vecs, dtype=np.float32)

        weights_arr = np.array(weights, dtype=np.float32).reshape(-1, 1)

        # mean pooling ponderado
        doc_vec = (vecs * weights_arr).sum(axis=0) / weights_arr.sum()

        return doc_vec.astype(np.float32)
