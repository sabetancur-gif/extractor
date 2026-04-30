""""Docstring for layout.reading_order.

Docstring."""
from sklearn.cluster import KMeans
import numpy as np

def simple_order(blocks):
    """
    Orden básico top-down, left-right.
    """
    return sorted(blocks, key=lambda b: (b["bbox"][1], b["bbox"][0]))


def _x_center(b):
    return (b["bbox"][0] + b["bbox"][2]) / 2


def _estimate_columns(x_centers, page_width):
    """
    Estima número de columnas usando gaps horizontales reales.
    """
    if len(x_centers) < 3:
        return 1

    xs = np.sort(x_centers / page_width)
    gaps = np.diff(xs)

    # gap significativo = percentil alto, no threshold fijo
    significant = gaps > np.percentile(gaps, 90)

    return int(significant.sum() + 1)


def column_aware_order(blocks, ncols=None):
    """
    Ordena bloques respetando estructura de columnas.
    """
    if not blocks:
        return []

    # 1) centros X
    x_centers = np.array([_x_center(b) for b in blocks])

    # 2) ancho de página aproximado
    page_width = max(b["bbox"][2] for b in blocks)

    # 3) estimar columnas si no vienen dadas
    if ncols is None:
        ncols = _estimate_columns(x_centers, page_width)

    # 4) si solo hay una columna → orden simple
    if ncols <= 1:
        return simple_order(blocks)

    # 5) clustering estable (n_init alto)
    X = (x_centers / page_width).reshape(-1, 1)
    kmeans = KMeans(n_clusters=ncols, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X)

    # 6) agrupar por columna
    columns = {}
    for i, label in enumerate(labels):
        columns.setdefault(label, []).append(blocks[i])

    # 7) ordenar columnas por centro medio
    ordered = []
    for col in sorted(
        columns.keys(),
        key=lambda c: np.mean([_x_center(b) for b in columns[c]])
    ):
        ordered.extend(sorted(columns[col], key=lambda b: b["bbox"][1]))

    return ordered
