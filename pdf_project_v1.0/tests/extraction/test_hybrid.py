import pytest
from src.extraction.hybrid import HybridExtractor


# ---------
# FAKES
# ---------

class FakeNativeExtractor:
    def extract(self, file_path: str):
        return [
            {
                "page_number": 1,
                "width": 1000,
                "height": 1000,
                "blocks": [
                    {
                        "block_id": "1_native_0",
                        "text": "TEXTO NATIVO",
                        "bbox": [50, 50, 300, 100],
                        "page": 1,
                        "source": "native",
                        "order": 0,
                    }
                ],
            }
        ]


class FakeOCRExtractor:
    def extract(self, file_path: str):
        return [
            {
                "page_number": 1,
                "width": 1000,
                "height": 1000,
                "blocks": [
                    {
                        "block_id": "1_ocr_0",
                        "text": "TEXTO OCR",
                        "bbox": [50, 200, 300, 250],  # NO solapa
                        "page": 1,
                        "source": "ocr",
                        "order": 0,
                    }
                ],
            }
        ]


# ---------
# TESTS
# ---------

def test_hybrid_keeps_native_and_adds_ocr():
    extractor = HybridExtractor(
        native=FakeNativeExtractor(),
        ocr=FakeOCRExtractor(),
        iou_thresh=0.3,
    )

    pages = extractor.extract("dummy.pdf")

    assert len(pages) == 1

    blocks = pages[0]["blocks"]
    texts = [b["text"] for b in blocks]
    sources = [b["source"] for b in blocks]

    # Texto nativo permanece
    assert "TEXTO NATIVO" in texts

    # OCR se añade
    assert "TEXTO OCR" in texts

    # Ambos orígenes presentes
    assert "native" in sources
    assert "ocr" in sources


def test_hybrid_no_duplicate_blocks_when_overlap():
    class OCRWithOverlap(FakeOCRExtractor):
        def extract(self, file_path: str):
            return [
                {
                    "page_number": 1,
                    "width": 1000,
                    "height": 1000,
                    "blocks": [
                        {
                            "block_id": "1_ocr_dup",
                            "text": "TEXTO NATIVO",
                            "bbox": [55, 55, 290, 95],  # SOLAPA con nativo
                            "page": 1,
                            "source": "ocr",
                            "order": 0,
                        }
                    ],
                }
            ]

    extractor = HybridExtractor(
        native=FakeNativeExtractor(),
        ocr=OCRWithOverlap(),
        iou_thresh=0.9,
    )

    pages = extractor.extract("dummy.pdf")
    blocks = pages[0]["blocks"]
    texts = [b["text"] for b in blocks]

    # No debe duplicar
    assert texts.count("TEXTO NATIVO") == 1