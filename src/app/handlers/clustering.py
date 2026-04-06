
"""
src/app/handlers/clustering.py
------------------------------
Callbacks para clustering y visualización de embeddings.
"""

# THIRDPARTY
import dash
from dash import Input, Output, State, dcc, html


def register_callbacks_11(app, controller, embedder=None):
    """
    Registra callback para mostrar detalles de clusters y embeddings.
    Relacionado con IDs: cluster-details-panel, cluster-select-dropdown, doc-context, clustering-reduction, clustering-method, clustering-param.
    """

    @app.callback(
        Output("cluster-details-panel", "children"),
        Input("cluster-select-dropdown", "value"),
        State("doc-context", "data"),
        State("clustering-reduction", "value"),
        State("clustering-method", "value"),
        State("clustering-param", "value"),
        prevent_initial_call=True,
    )
    def show_cluster_details(cluster_id, doc_ctx, reduction, method, param):
        # THIRDPARTY
        import numpy as np

        # FIRSTPARTY
        from src.semantic.clustering_manager import ClusteringManager
        if not doc_ctx:
            return "No hay información de clustering."
        cm = ClusteringManager()
        embeddings, doc_ids = cm.get_embeddings()
        if not embeddings:
            return "No existen embeddings cargados."
        X = np.stack(embeddings)
        # Recalcular clustering igual que en run_clustering
        n_samples = X.shape[0]
        try:
            if reduction == "umap" and n_samples > 2:
                # THIRDPARTY
                import umap
                reducer = umap.UMAP(n_components=2, random_state=42)
                coords = reducer.fit_transform(X)
            else:
                # THIRDPARTY
                from sklearn.decomposition import PCA
                reducer = PCA(n_components=2)
                coords = reducer.fit_transform(X)
        except Exception:
            # THIRDPARTY
            from sklearn.decomposition import PCA
            reducer = PCA(n_components=2)
            coords = reducer.fit_transform(X)
        if method == "hdbscan":
            # THIRDPARTY
            import hdbscan
            clusterer = hdbscan.HDBSCAN(min_cluster_size=param or 2)
            labels = clusterer.fit_predict(X)
        else:
            # THIRDPARTY
            from sklearn.cluster import KMeans
            clusterer = KMeans(n_clusters=param or 2, random_state=42)
            labels = clusterer.fit_predict(X)
        # Filtrar docs del cluster seleccionado
        indices = np.where(labels == cluster_id)[0]
        if len(indices) == 0:
            return html.Div(
                "No hay documentos en este cluster.",
                className="text-muted"
            )
        doc_list = [str(doc_ids[i]) for i in indices]
        # Estadísticas básicas
        centroid = np.mean(X[indices], axis=0)
        distancias = np.linalg.norm(X[indices] - centroid, axis=1)
        avg_dist = float(np.mean(distancias)) if len(distancias) > 0 else 0.0
        return html.Div([
            html.H6(f"Cluster {cluster_id} — {len(indices)} documentos"),
            html.Ul([
                html.Li(f"IDs de documentos: {', '.join(doc_list)}"),
                html.Li(f"Distancia promedio al centroide: {avg_dist:.3f}"),
            ]),
            html.H6("Lista de documentos"),
            html.Ul([
                html.Li(doc_ids[i]) for i in indices
            ])
        ], className="bg-light p-2 rounded")

    # ===== 9) Clustering & Embeddings =====
    @app.callback(
        Output("clustering-output", "children"),
        Input("run-clustering", "n_clicks"),
        State("doc-context", "data"),
        State("clustering-reduction", "value"),
        State("clustering-method", "value"),
        State("clustering-param", "value"),
        prevent_initial_call=True,
    )
    def run_clustering(n_clicks, doc_ctx, reduction, method, param):

        # THIRDPARTY
        import hdbscan
        import numpy as np
        import plotly.graph_objs as go
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA
        import umap

        # FIRSTPARTY
        from src.semantic.clustering_manager import ClusteringManager
        if not doc_ctx:
            raise dash.exceptions.PreventUpdate

        cm = ClusteringManager()
        embeddings, doc_ids = cm.get_embeddings()
        if not embeddings:
            return html.Div("No existen embeddings cargados para clustering.", className="text-danger")

        X = np.stack(embeddings)
        # Reducción dimensional robusta
        n_samples = X.shape[0]
        if reduction == "umap" and n_samples > 2:
            reducer = umap.UMAP(n_components=2, random_state=42)
            coords = reducer.fit_transform(X)
        else:
            # Si hay muy pocos documentos, UMAP falla: usar PCA
            reducer = PCA(n_components=2)
            coords = reducer.fit_transform(X)

        # Clustering
        if method == "hdbscan":
            clusterer = hdbscan.HDBSCAN(min_cluster_size=param or 2)
            labels = clusterer.fit_predict(X)
        else:
            clusterer = KMeans(n_clusters=param or 2, random_state=42)
            labels = clusterer.fit_predict(X)

        # Visualización 2D
        fig = go.Figure()
        palette = [
            "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
            "#FFA15A", "#19D3F3", "#FF6692", "#B6E880",
            "#FF97FF", "#FECB52"
        ]
        for i in np.unique(labels):
            mask = labels == i
            fig.add_trace(go.Scatter(
                x=coords[mask, 0], y=coords[mask, 1],
                mode="markers",
                marker=dict(
                    size=14,
                    color=palette[i % len(palette)] if i != -1 else "#888",
                    line=dict(width=2, color="#fff")
                ),
                name=f"Cluster {i}" if i != -1 else "Ruido",
                text=[f"Doc: {doc_ids[j]}" for j in np.where(mask)[0]],
                hoverinfo="text",
                customdata=[str(doc_ids[j]) for j in np.where(mask)[0]]
            ))
        fig.update_layout(
            title="Clustering de documentos (2D)",
            margin=dict(l=40, r=40, t=40, b=40),
            height=500
        )

        # Métricas de calidad
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = np.sum(labels == -1)
        cluster_info = html.Div([
            html.H5("Clusters encontrados", className="mb-3 text-info"),
            html.Ul([
                html.Li(f"Clusters: {n_clusters}"),
                html.Li(f"Ruido: {n_noise} documentos"),
                html.Li(f"Total documentos: {len(labels)}"),
            ])
        ])

        # Botón de información sobre métodos
        method_info = {
            "pca": "PCA (Análisis de Componentes Principales) es un método lineal para reducción dimensional, útil para datos bien distribuidos.",
            "umap": "UMAP es un método no lineal que preserva la estructura local y global, ideal para datos complejos y agrupaciones naturales.",
            "kmeans": "KMeans agrupa los datos en k clusters según la distancia euclidiana, útil para clusters bien separados.",
            "hdbscan": "HDBSCAN detecta clusters de densidad variable y puede identificar ruido, útil para datos con agrupaciones irregulares."
        }
        info_buttons = html.Div([
            html.Button("¿Qué es PCA?", id="info-pca-btn", className="btn btn-outline-info mx-1", n_clicks=0),
            html.Button("¿Qué es UMAP?", id="info-umap-btn", className="btn btn-outline-info mx-1", n_clicks=0),
            html.Button("¿Qué es KMeans?", id="info-kmeans-btn", className="btn btn-outline-info mx-1", n_clicks=0),
            html.Button("¿Qué es HDBSCAN?", id="info-hdbscan-btn", className="btn btn-outline-info mx-1", n_clicks=0)
        ], className="mb-3")

        # Panel interactivo para explorar clusters
        cluster_explorer = html.Div([
            html.H6("Explora los clusters"),
            dcc.Dropdown(
                id="cluster-select-dropdown",
                options=[{"label": f"Cluster {i}", "value": i} for i in np.unique(labels)],
                value=np.unique(labels)[0] if len(np.unique(labels)) > 0 else None,
                clearable=False,
                className="mb-2"
            ),
            html.Div(id="cluster-details-panel", className="p-2 border rounded")
        ], className="mt-3")

        # Panel de ayuda y explicación
        info_panel = html.Div([
            html.H6("¿Cómo interpretar el clustering?", className="mt-4 text-secondary"),
            html.Ul([
                html.Li("Cada punto representa un documento subido."),
                html.Li("Los colores indican el cluster asignado por el algoritmo."),
                html.Li("Ruido = documentos que no pertenecen a ningún cluster (solo en HDBSCAN)."),
                html.Li("Puedes cambiar el método de reducción y clustering arriba."),
                html.Li("UMAP solo está disponible si hay más de 3 documentos."),
                html.Li("Usa los botones para aprender sobre cada método."),
                html.Li("Explora los clusters usando el panel interactivo abajo."),
            ])
        ], className="alert alert-info")

        return html.Div([
            info_buttons,
            dcc.Graph(figure=fig, config={"displayModeBar": True}),
            cluster_info,
            cluster_explorer,
            info_panel
        ])
