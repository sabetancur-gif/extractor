# src/semantic/clustering_manager.py
"""
Gestor incremental de embeddings y clustering para múltiples documentos.
"""
import os
import numpy as np
from sklearn.cluster import KMeans

class ClusteringManager:
    def __init__(self, outputs_dir="data/output"):
        self.outputs_dir = outputs_dir
        self.embeddings = []
        self.doc_ids = []
        self._load_all_embeddings()

    def _load_all_embeddings(self):
        self.embeddings = []
        self.doc_ids = []
        for doc_id in os.listdir(self.outputs_dir):
            folder = os.path.join(self.outputs_dir, doc_id)
            emb_path = os.path.join(folder, "embedding.npy")
            if os.path.exists(emb_path):
                arr = np.load(emb_path)
                self.embeddings.append(arr)
                self.doc_ids.append(doc_id)

    def add_embedding(self, doc_id, emb_path):
        arr = np.load(emb_path)
        self.embeddings.append(arr)
        self.doc_ids.append(doc_id)

    def get_embeddings(self):
        return self.embeddings, self.doc_ids

    def cluster(self, n_clusters=2):
        if len(self.embeddings) < n_clusters:
            return None, None
        X = np.stack(self.embeddings)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(X)
        clusters = {}
        for idx, label in enumerate(labels):
            clusters.setdefault(label, []).append(self.doc_ids[idx])
        return labels, clusters
