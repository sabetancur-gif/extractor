import numpy as np
import warnings

from src.semantic.clustering import Clusterer


def test_clusterer_outputs_labels_with_correct_length():
    np.random.seed(42)

    n = 20
    dim = 8
    embeddings = np.random.randn(n, dim)

    clusterer = Clusterer(min_cluster_size=2)
    labels = clusterer.cluster(embeddings)

    # 1️⃣ Debe devolver una etiqueta por embedding
    assert isinstance(labels, np.ndarray)
    assert len(labels) == n


def test_reduce_2d_outputs_correct_shape():
    np.random.seed(42)

    n = 15
    dim = 10
    embeddings = np.random.randn(n, dim)

    clusterer = Clusterer()  # ✅ DEFINIDO AQUÍ

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        coords = clusterer.reduce_2d(embeddings)

    assert isinstance(coords, np.ndarray)
    assert coords.shape == (n, 2)