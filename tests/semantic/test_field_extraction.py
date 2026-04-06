import pytest
from src.semantic.field_extraction import FieldExtractor


@pytest.fixture
def sample_pages():
    return [
        {
            "page_number": 1,
            "blocks": [
                {
                    "text": "Contact us at test@example.com on 2024-05-01.",
                    "bbox": [0, 0, 100, 50],
                },
                {
                    "text": "Call +1 555-123-4567 for more info.",
                    "bbox": [0, 60, 100, 100],
                },
            ],
        },
        {
            "page_number": 2,
            "blocks": [
                {
                    "text": "Correo: usuario@correo.com Fecha: 01/06/2024",
                    "bbox": [0, 0, 120, 40],
                }
            ],
        },
    ]


def test_extract_returns_list(sample_pages):
    extractor = FieldExtractor(use_spacy=False)
    results = extractor.extract(sample_pages)

    assert isinstance(results, list)
    assert len(results) > 0


def test_extract_output_structure(sample_pages):
    extractor = FieldExtractor(use_spacy=False)
    results = extractor.extract(sample_pages)

    for r in results:
        assert isinstance(r, dict)
        assert set(r.keys()) == {"field", "value", "page", "bbox", "context"}
        assert isinstance(r["field"], str)
        assert isinstance(r["value"], str)
        assert isinstance(r["page"], int)
        assert isinstance(r["bbox"], list)
        assert isinstance(r["context"], str)


def test_email_and_date_extraction(sample_pages):
    extractor = FieldExtractor(use_spacy=False)
    results = extractor.extract(sample_pages)

    values = [r["value"] for r in results]

    assert "test@example.com" in values
    assert "usuario@correo.com" in values
    assert "2024-05-01" in values
    assert "01/06/2024" in values


def test_phone_extraction(sample_pages):
    extractor = FieldExtractor(use_spacy=False)
    results = extractor.extract(sample_pages)

    phone_values = [r["value"] for r in results if r["field"] == "phone"]

    assert any("555" in v for v in phone_values)


def test_multi_page_extraction(sample_pages):
    extractor = FieldExtractor(use_spacy=False)
    results = extractor.extract(sample_pages)

    pages = {r["page"] for r in results}

    assert pages == {1, 2}


def test_deduplication():
    pages = [
        {
            "page_number": 1,
            "blocks": [
                {
                    "text": "Email test@example.com Email test@example.com",
                    "bbox": [0, 0, 100, 50],
                }
            ],
        }
    ]

    extractor = FieldExtractor(use_spacy=False)
    results = extractor.extract(pages)

    email_results = [r for r in results if r["value"] == "test@example.com"]

    # Debe aparecer solo una vez
    assert len(email_results) == 1


def test_custom_regex_rule():
    pages = [
        {
            "page_number": 1,
            "blocks": [
                {
                    "text": "Invoice ID: INV-2024-001",
                    "bbox": [0, 0, 100, 40],
                }
            ],
        }
    ]

    extractor = FieldExtractor(use_spacy=False)
    extractor.add_regex_rule("invoice_id", r"INV-\d{4}-\d{3}")

    results = extractor.extract(pages)

    assert any(
        r["field"] == "invoice_id" and r["value"] == "INV-2024-001"
        for r in results
    )