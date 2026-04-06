import pytest
from src.conversion.formatter import Converter


@pytest.fixture
def sample_document():
    return {
        "pages": [
            {
                "page_number": 1,
                "blocks": [
                    {"type": "title", "text": "Introduction"},
                    {"type": "paragraph", "text": "This is a paragraph."},
                    {"type": "table", "text": "A | B\n1 | 2"},
                ],
            },
            {
                "page_number": 2,
                "blocks": [
                    {"type": "title", "text": "Conclusion"},
                    {"type": "paragraph", "text": "Final thoughts."},
                ],
            },
        ]
    }


def test_to_markdown_returns_string(sample_document):
    converter = Converter()
    md = converter.to_markdown(sample_document)

    assert isinstance(md, str)
    assert md.strip() != ""


def test_titles_are_converted_to_markdown_headers(sample_document):
    converter = Converter()
    md = converter.to_markdown(sample_document)

    assert "# Introduction" in md
    assert "# Conclusion" in md


def test_paragraphs_are_included(sample_document):
    converter = Converter()
    md = converter.to_markdown(sample_document)

    assert "This is a paragraph." in md
    assert "Final thoughts." in md


def test_table_is_included_as_raw_text(sample_document):
    converter = Converter()
    md = converter.to_markdown(sample_document)

    assert "A | B" in md
    assert "1 | 2" in md


def test_page_separator_is_added(sample_document):
    converter = Converter()
    md = converter.to_markdown(sample_document)

    # Debe haber al menos un separador de página
    assert "---" in md


def test_to_html_returns_html(sample_document):
    converter = Converter()
    html = converter.to_html(sample_document)

    assert isinstance(html, str)
    assert "<h1>" in html
    assert "<p>" in html