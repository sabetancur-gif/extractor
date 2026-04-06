# tests/test_segmenter.py
from src.layout.segmenter import LayoutSegmenter


def _page(blocks, page_number=1):
    """Helper para construir una página fake."""
    return {
        "page_number": page_number,
        "blocks": blocks,
    }


def test_segmenter_detects_title():
    pages = [
        _page([
            {
                "text": "INTRODUCTION",
                "font_size": 20,      # grande respecto al resto
                "bbox": [0, 0, 500, 50],
            },
            {
                "text": "This is a normal paragraph of text explaining things.",
                "font_size": 10,
                "bbox": [0, 60, 500, 200],
            },
        ])
    ]

    seg = LayoutSegmenter()
    out = seg.analyze(pages)

    title_block = out[0]["blocks"][0]

    assert title_block["type"] == "title"
    assert title_block["confidence"] >= 0.7


def test_segmenter_detects_table():
    pages = [
        _page([
            {
                "text": "Name | Age | Country\nAlice | 30 | USA\nBob | 25 | UK",
                "font_size": 10,
                "bbox": [0, 0, 500, 150],
            }
        ])
    ]

    seg = LayoutSegmenter()
    out = seg.analyze(pages)

    block = out[0]["blocks"][0]

    assert block["type"] == "table"
    assert block["confidence"] >= 0.7


def test_segmenter_detects_paragraph():
    pages = [
        _page([
            {
                "text": (
                    "This is a long paragraph of text that contains multiple words "
                    "and sentences, written in normal case and typical font size."
                ),
                "font_size": 11,
                "bbox": [0, 0, 500, 300],
            }
        ])
    ]

    seg = LayoutSegmenter()
    out = seg.analyze(pages)

    block = out[0]["blocks"][0]

    assert block["type"] == "paragraph"
    assert 0.6 <= block["confidence"] <= 0.9