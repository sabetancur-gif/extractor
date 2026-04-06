import pytest
from src.layout.reading_order import simple_order, column_aware_order


def _block(x1, y1, x2, y2, text):
    return {
        "bbox": [x1, y1, x2, y2],
        "text": text
    }


def test_simple_order_top_down_left_right():
    blocks = [
        _block(300, 50, 400, 80, "B"),
        _block(100, 10, 200, 40, "A"),
        _block(100, 90, 200, 120, "C"),
    ]

    out = simple_order(blocks)

    texts = [b["text"] for b in out]
    assert texts == ["A", "B", "C"]


def test_column_aware_two_columns_reading_order():
    """
    Layout simulado:

    Col 1        Col 2
    A (y=10)     C (y=10)
    B (y=60)     D (y=60)
    """

    blocks = [
        _block(50, 10, 150, 40, "A"),
        _block(50, 60, 150, 90, "B"),
        _block(300, 10, 400, 40, "C"),
        _block(300, 60, 400, 90, "D"),
    ]

    out = column_aware_order(blocks)

    texts = [b["text"] for b in out]

    # lectura correcta: columna izquierda completa, luego derecha
    assert texts == ["A", "B", "C", "D"]


def test_column_aware_respects_vertical_order_inside_column():
    blocks = [
        _block(50, 100, 150, 130, "B"),
        _block(50, 10, 150, 40, "A"),
        _block(300, 10, 400, 40, "C"),
    ]

    out = column_aware_order(blocks)

    texts = [b["text"] for b in out]
    assert texts[:2] == ["A", "B"]


def test_single_column_falls_back_to_simple_order():
    blocks = [
        _block(100, 50, 200, 80, "B"),
        _block(100, 10, 200, 40, "A"),
        _block(100, 90, 200, 120, "C"),
    ]

    out = column_aware_order(blocks)

    texts = [b["text"] for b in out]
    assert texts == ["A", "B", "C"]