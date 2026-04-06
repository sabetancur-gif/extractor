# src/semantic/clustering.py
import hdbscan
import umap
import numpy as np

class Clusterer:
    def __init__(self, min_cluster_size=2):
        self.min_cluster_size = min_cluster_size  # tamaño mínimo para que un grupo sea considerado cluster
        # Grupos más pequeños → marcados como ruido (-1)

    def cluster(self, embeddings: np.ndarray):
        # Recibe una matriz N x D de embeddings
        model = hdbscan.HDBSCAN(min_cluster_size=self.min_cluster_size)  # Ejecuta HDBSCAN
        labels = model.fit_predict(embeddings)  # Devuelve un vector labels de tamaño N
        return labels  # [-1, 0, 0, 1, 1, 1, -1]

    def reduce_2d(self, embeddings: np.ndarray):
        # Reduce embeddings de alta dimensión (ej. 384) a 2 dimensiones
        reducer = umap.UMAP(n_components=2, random_state=42)
        coords = reducer.fit_transform(embeddings)
        return coords  # Devuelve matriz N x 2