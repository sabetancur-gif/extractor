
import pytest
from typing import List, Dict

# Ajusta el import a tu módulo real
from src.extraction.base import BaseExtractor


def validate_page_list_schema(pages: List[Dict]) -> None:
    """
    Valida que 'pages' cumpla el contrato:
    - Lista de dicts con claves: page_number, width, height, blocks
    - 'blocks' es lista de dicts con claves obligatorias:
        block_id, text, bbox (len=4), page, source, order
    - Tipos básicos y rangos obvios.
    Lanza AssertionError si algo no cumple.
    """
    assert isinstance(pages, list), "El retorno debe ser una lista"
    assert len(pages) > 0, "Debe haber al menos una página"

    for i, page in enumerate(pages, start=1):
        assert isinstance(page, dict), f"Página #{i} debe ser dict"
        # Claves base de página
        for key in ("page_number", "width", "height", "blocks"):
            assert key in page, f"Falta clave '{key}' en página #{i}"

        assert isinstance(page["page_number"], int), "page_number debe ser int"
        assert page["page_number"] > 0, "page_number debe ser >= 1"
        assert isinstance(page["width"], (int, float)), "width debe ser numérico"
        assert page["width"] > 0, "width debe ser > 0"
        assert isinstance(page["height"], (int, float)), "height debe ser numérico"
        assert page["height"] > 0, "height debe ser > 0"
        assert isinstance(page["blocks"], list), "blocks debe ser lista"

        # Validación de bloques
        for j, block in enumerate(page["blocks"], start=1):
            assert isinstance(block, dict), f"Bloque #{j} de página #{i} debe ser dict"
            for bkey in ("block_id", "text", "bbox", "page", "source", "order"):
                assert bkey in block, f"Falta clave '{bkey}' en bloque #{j} (página #{i})"

            assert isinstance(block["block_id"], (str, int)), "block_id debe ser str|int"
            assert isinstance(block["text"], str), "text debe ser str"
            assert isinstance(block["bbox"], (list, tuple)), "bbox debe ser lista/tupla"
            assert len(block["bbox"]) == 4, "bbox debe tener 4 números [x0, y0, x1, y1]"
            x0, y0, x1, y1 = block["bbox"]
            for coord in (x0, y0, x1, y1):
                assert isinstance(coord, (int, float)), "bbox coords deben ser numéricas"
            assert x1 >= x0 and y1 >= y0, "bbox debe tener x1>=x0 y y1>=y0"

            assert isinstance(block["page"], int), "page en bloque debe ser int"
            assert block["page"] == page["page_number"], "block.page debe igualar al número de página"
            assert isinstance(block["source"], str), "source debe ser str"
            assert block["source"] in {"native", "ocr", "hybrid"}, "source debe ser 'native'|'ocr'|'hybrid'"
            assert isinstance(block["order"], int), "order debe ser int"
            assert block["order"] >= 1, "order debe ser >= 1"

            # Opcionales: si existen, validar tipo
            if "font_size" in block:
                assert isinstance(block["font_size"], (int, float)), "font_size debe ser numérico"
            if "font_name" in block:
                assert isinstance(block["font_name"], str), "font_name debe ser str"


def test_base_extractor_contract():
    """
    - Crea una subclase de prueba inline (DummyExtractor) que implementa extract.
    - Instancia y verifica isinstance(sub, BaseExtractor).
    - Ejecuta extract y valida el esquema del resultado.
    """
    class DummyExtractor(BaseExtractor):
        def extract(self, file_path: str) -> List[Dict]:
            # Validación mínima del parámetro
            if not isinstance(file_path, str) or not file_path:
                raise ValueError("file_path debe ser un string no vacío")

            # Simulamos un documento de 1 página con 2 bloques
            return [
                {
                    "page_number": 1,
                    "width": 595.0,
                    "height": 842.0,
                    "blocks": [
                        {
                            "block_id": "1-001",
                            "text": "Título del documento",
                            "bbox": [72.0, 770.0, 523.0, 800.0],
                            "page": 1,
                            "source": "native",
                            "order": 1,
                            "font_size": 18.0,
                            "font_name": "Times-Bold",
                        },
                        {
                            "block_id": "1-002",
                            "text": "Contenido de ejemplo...",
                            "bbox": [72.0, 740.0, 523.0, 765.0],
                            "page": 1,
                            "source": "native",
                            "order": 2,
                        },
                    ],
                }
            ]

    sub = DummyExtractor()
    assert isinstance(sub, BaseExtractor), "La subclase debe ser instancia de BaseExtractor"

    result = sub.extract("docs/ejemplo.pdf")
    validate_page_list_schema(result)


def test_base_extractor_invalid_input_raises():
    """
    Comprueba que la implementación maneja entradas inválidas con errores claros.
    """
    class DummyExtractor(BaseExtractor):
        def extract(self, file_path: str) -> List[Dict]:
            if not isinstance(file_path, str) or not file_path:
                raise ValueError("file_path debe ser un string no vacío")
            # retorno mínimo válido
            return [
                {
                    "page_number": 1,
                    "width": 100.0,
                    "height": 200.0,
                    "blocks": [
                        {
                            "block_id": 1,
                            "text": "Hola",
                            "bbox": [0.0, 0.0, 10.0, 10.0],
                            "page": 1,
                            "source": "native",
                            "order": 1,
                        }
                    ],
                }
            ]

    sub = DummyExtractor()
    with pytest.raises(ValueError):
        sub.extract("")  # vacío
    with pytest.raises(ValueError):
        sub.extract(None)  # tipo incorrecto
