import os
import tempfile
from PIL import Image, ImageDraw, ImageFont

from src.extraction.ocr import OCRExtractor


def _create_scanned_pdf(text: str, pdf_path: str):
    """
    Crea un PDF escaneado:
    texto → imagen → PDF (sin texto embebido)
    """
    # Crear imagen en blanco
    img = Image.new("RGB", (1200, 800), color="white")
    draw = ImageDraw.Draw(img)

    # Fuente por defecto (evita dependencias externas)
    font = ImageFont.load_default()

    # Dibujar texto
    draw.text((100, 200), text, fill="black", font=font)

    # Guardar como PDF (imagen embebida)
    img.save(pdf_path, "PDF")


def test_ocr_extraction_from_generated_scanned_pdf():
    """
    Genera un PDF escaneado con texto,
    ejecuta OCR y verifica que el texto no sea vacío.
    """

    test_text = "This is a scanned OCR test"

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "scanned_test.pdf")

        # 1. Crear PDF escaneado
        _create_scanned_pdf(test_text, pdf_path)

        assert os.path.exists(pdf_path), "No se pudo crear el PDF escaneado"

        # 2. Ejecutar OCR
        extractor = OCRExtractor(lang="eng", dpi=300)
        pages = extractor.extract(pdf_path)

        assert len(pages) > 0, "No se extrajeron páginas"

        # 3. Recolectar texto OCR
        extracted_text = []
        for page in pages:
            for block in page["blocks"]:
                extracted_text.append(block["text"])

        full_text = " ".join(extracted_text).strip()

        # 4. Validación clave
        assert full_text != "", "El OCR no extrajo texto"