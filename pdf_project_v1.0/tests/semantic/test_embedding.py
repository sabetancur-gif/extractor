import numpy as np

from src.semantic.embedding import Embedder


def test_embedder_returns_numpy_array_with_correct_dim():
    embedder = Embedder(model_name="all-MiniLM-L6-v2")

    context = {
        "pages": [
            {
                "blocks": [
                    {"type": "title", "text": "Introduction to OCR"},
                    {"type": "paragraph", "text": "This document explains how OCR systems work."},
                    {"type": "table", "text": "Should be ignored"},
                ]
            }
        ]
    }

    vec = embedder.embed_document(context)

    # 1️⃣ Tipo correcto
    assert isinstance(vec, np.ndarray)

    # 2️⃣ Vector 1D
    assert vec.ndim == 1

    # 3️⃣ Dimensión correcta según el modelo
    expected_dim = embedder.model.get_sentence_embedding_dimension()
    assert vec.shape[0] == expected_dim