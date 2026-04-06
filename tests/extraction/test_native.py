
import pytest
import fitz  # PyMuPDF
from typing import List, Dict

# Ajusta el import según tu estructura real
from src.extraction.native import NativePDFExtractor


def create_sample_pdf(path):
    """Crea un PDF con una página y varios textos para generar bloques."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 en puntos (~72dpi)

    # Inserta algunos textos en posiciones diferentes
    page.insert_text((72, 100), "Título del documento", fontsize=18)
    page.insert_text((72, 140), "Línea 1 de contenido")
    page.insert_text((72, 160), "Línea 2 de contenido")
    page.insert_text((72, 180), "Más texto para asegurar múltiples spans")

    # Guardar en ruta
    doc.save(path)
    doc.close()


def test_native_pdf_extractor_basic_structure(tmp_path):
    """
    - Crea un PDF temporal con texto.
    - Ejecuta NativePDFExtractor.extract(file_path).
    - Assert: retorno es lista.
    - Assert: pages[0]["blocks"] no vacío.
    - Assert: cada bloque tiene 'bbox' y 'text'.
    """
    pdf_path = tmp_path / "sample.pdf"
    create_sample_pdf(str(pdf_path))

    extractor = NativePDFExtractor()
    pages = extractor.extract(str(pdf_path))

    # Assert: return es lista
    assert isinstance(pages, list), "El método extract debe devolver una lista"

    # Debe haber al menos una página
    assert len(pages) >= 1, "Debe extraerse al menos una página"

    first_page = pages[0]
    assert "blocks" in first_page, "La página debe incluir la clave 'blocks'"

    # Assert: pages[0]["blocks"] no vacío
    blocks = first_page["blocks"]
    assert isinstance(blocks, list), "'blocks' debe ser una lista"
    assert len(blocks) > 0, "La lista de 'blocks' no debe estar vacía"

    # Assert: cada block tiene bbox y text
    for idx, block in enumerate(blocks, start=1):
        assert "bbox" in block, f"Bloque #{idx} debe incluir 'bbox'"
        assert "text" in block, f"Bloque #{idx} debe incluir 'text'"

        # Validaciones mínimas de tipos
        bbox = block["bbox"]
        assert isinstance(bbox, (list, tuple)), f"'bbox' del bloque #{idx} debe ser lista/tupla"
        assert len(bbox) == 4, f"'bbox' del bloque #{idx} debe tener 4 números [x0, y0, x1, y1]"
        for c in bbox:
            assert isinstance(c, (int, float)), f"Coordenadas de 'bbox' deben ser numéricas en bloque #{idx}"

        text = block["text"]
        assert isinstance(text, str), f"'text' del bloque #{idx} debe ser str"
        assert text.strip() != "", f"'text' del bloque #{idx} no debe estar vacío"

        # (Opcional) Validar que 'order' sea incremental
        assert "order" in block and isinstance(block["order"], int), "Cada bloque debe tener 'order' int"


def test_native_pdf_extractor_multiple_pages(tmp_path):
    """
    Verifica que el extractor maneja múltiples páginas y
    mantiene la estructura por cada página.
    """
    pdf_path = tmp_path / "multi.pdf"

    # Crear PDF con 2 páginas
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((72, 100), "Página 1 - Texto")

    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((72, 100), "Página 2 - Texto")

    doc.save(str(pdf_path))
    doc.close()

    extractor = NativePDFExtractor()
    pages = extractor.extract(str(pdf_path))

    assert isinstance(pages, list)
    assert len(pages) == 2, "Debe extraer exactamente dos páginas"

    for i, page in enumerate(pages, start=1):
        assert "page_number" in page and page["page_number"] == i
        assert "blocks" in page and isinstance(page["blocks"], list)
        assert len(page["blocks"]) > 0, f"La página {i} debe tener al menos un bloque"
        for block in page["blocks"]:
            assert "bbox" in block and isinstance(block["bbox"], (list, tuple))
            assert "text" in block and isinstance(block["text"], str)
            assert block["text"].strip() != ""
