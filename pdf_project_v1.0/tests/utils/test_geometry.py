# tests/test_geometry.py

from src.utils.geometry import area, intersection, iou_bbox, overlaps


def test_area_basic():
    bbox = [0, 0, 10, 5]
    assert area(bbox) == 50


def test_area_invalid_bbox():
    # bbox invertido → área 0
    bbox = [10, 10, 5, 5]
    assert area(bbox) == 0


def test_intersection_identical_boxes():
    a = [0, 0, 10, 10]
    b = [0, 0, 10, 10]
    assert intersection(a, b) == 100


def test_intersection_disjoint_boxes():
    a = [0, 0, 5, 5]
    b = [10, 10, 15, 15]
    assert intersection(a, b) == 0


def test_iou_identical_boxes():
    a = [0, 0, 10, 10]
    b = [0, 0, 10, 10]
    assert iou_bbox(a, b) == 1.0


def test_iou_disjoint_boxes():
    a = [0, 0, 5, 5]
    b = [10, 10, 15, 15]
    assert iou_bbox(a, b) == 0.0


def test_iou_partial_overlap():
    a = [0, 0, 10, 10]
    b = [5, 5, 15, 15]
    # inter = 25, union = 175 → IoU = 25/175
    assert abs(iou_bbox(a, b) - (25 / 175)) < 1e-6


def test_overlaps_true():
    a = [0, 0, 10, 10]
    b = [5, 5, 15, 15]
    assert overlaps(a, b, threshold=0.1)


def test_overlaps_false():
    a = [0, 0, 10, 10]
    b = [9, 9, 20, 20]
    # inter = 1, union = 199 → IoU ≈ 0.005
    assert not overlaps(a, b, threshold=0.1)