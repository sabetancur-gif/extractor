
# tests/test_pdf_type_detector.py
import io
import os
from pathlib import Path

import pytest
import fitz  # PyMuPDF
from PIL import Image, ImageDraw

# Importa tu clase
# Ajusta el import según tu estructura real de paquetes
from src.detection.pdf_type_detector import PDFTypeDetector


# ---------- Utilidades para crear PDFs de prueba ----------

def create_text_pdf(path: Path, text="Lorem ipsum " * 200, pages=1):
    """Crea un PDF con texto abundante (nativo)."""
    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page(width=595, height=842)  # A4 en puntos
        # insertar bloque de texto grande
        rect = fitz.Rect(50, 50, 545, 792)
        page.insert_textbox(
            rect, text,
            fontsize=12,
            align=fitz.TEXT_ALIGN_LEFT
        )
    doc.save(path)
    doc.close()


def create_image(path: Path, size=(1200, 1600), color=(200, 200, 200)):
    """Crea y guarda una imagen PNG simple."""
    img = Image.new("RGB", size, color)
    d = ImageDraw.Draw(img)
    d.rectangle(
        [100, 100, size[0]-100, size[1]-100],
        outline=(0, 0, 0),
        width=8
    )
    img.save(path, format="PNG")


def create_scanned_pdf(path: Path, pages=1):
    """Crea un PDF estilo escaneado: imagen grande ocupando la página."""
    # Genera una imagen temporal
    img_path = path.with_suffix(".png")
    create_image(img_path, size=(2000, 2800), color=(220, 220, 220))

    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page(width=595, height=842)  # A4
        # inserta imagen casi a página completa
        rect = fitz.Rect(10, 10, 585, 832)
        page.insert_image(rect, filename=str(img_path))
    doc.save(path)
    doc.close()

    # limpia imagen auxiliar
    try:
        os.remove(img_path)
    except OSError:
        pass


def create_mixed_pdf(path: Path):
    """Crea PDF mixto de 2 páginas:
       - Página 1: texto abundante (similar a create_text_pdf).
       - Página 2: imagen grande estilo escaneado (similar a create_scanned_pdf).
    """
    # Preparar imagen temporal para la segunda página
    img_path = path.with_suffix(".png")
    create_image(img_path, size=(2000, 2800), color=(220, 220, 220))

    doc = fitz.open()
    try:
        # --- Página 1: SOLO TEXTO (A4 con caja amplia) ---
        page1 = doc.new_page(width=595, height=842)  # A4 en puntos
        rect_text = fitz.Rect(50, 50, 545, 792)      # márgenes 50 pt
        page1.insert_textbox(
            rect_text,
            (
                "Texto de prueba"
            ) * 200,
            fontname="Times-Roman",  # explícito
            fill=(0, 0, 0),
            fontsize=12,
            align=fitz.TEXT_ALIGN_LEFT,
        )

        # --- Página 2: IMAGEN GRANDE (estilo escaneado) ---
        page2 = doc.new_page(width=595, height=842)  # A4
        rect_img = fitz.Rect(10, 10, 585, 832)       # casi a página completa
        page2.insert_image(rect_img, filename=str(img_path))

        # Guardar PDF
        doc.save(path)
    finally:
        doc.close()
        # limpiar la imagen temporal
        try:
            os.remove(img_path)
        except OSError:
            pass


def create_encrypted_pdf(path: Path, owner_pw="owner", user_pw="user"):
    """Crea un PDF con texto y lo guarda cifrado (sin contraseña para abrir)."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_textbox(fitz.Rect(50, 50, 545, 792), "Documento cifrado", fontsize=14)
    # Guarda cifrado
    doc.save(
        path,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw=owner_pw,
        user_pw=user_pw,
        permissions=(
            fitz.PDF_PERM_PRINT
            | fitz.PDF_PERM_COPY
            | fitz.PDF_PERM_ANNOTATE
        ),
    )
    doc.close()


def create_invalid_file(path: Path):
    """Crea un archivo no-PDF (binario basura)."""
    path.write_bytes(b"This is not a PDF file.")


# ---------- Tests ----------

def test_detect_native(tmp_path: Path):
    pdf_path = tmp_path / "native.pdf"
    # texto abundante, sin imágenes relevantes
    create_text_pdf(pdf_path, pages=2)
    detector = PDFTypeDetector(
        sample_pages=2,
        text_area_threshold=0.30,
        image_area_threshold=0.50,
        min_image_ratio=0.02,
    )
    result = detector.detect(str(pdf_path))
    assert result == "native"


def test_detect_scanned(tmp_path: Path):
    pdf_path = tmp_path / "scanned.pdf"
    # imagen casi a página completa
    create_scanned_pdf(pdf_path, pages=2)
    detector = PDFTypeDetector(
        sample_pages=2,
        text_area_threshold=0.30,
        image_area_threshold=0.50,
        min_image_ratio=0.02,
    )
    result = detector.detect(str(pdf_path))
    assert result == "scanned"


def test_detect_mixed(tmp_path: Path):
    pdf_path = tmp_path / "mixed.pdf"
    # texto + imagen relevante
    create_mixed_pdf(pdf_path)
    detector = PDFTypeDetector(
        sample_pages=2
    )
    result = detector.detect(str(pdf_path))
    assert result == "mixed"


def test_detect_invalid(tmp_path: Path):
    bad_path = tmp_path / "not_pdf.bin"
    create_invalid_file(bad_path)
    detector = PDFTypeDetector(sample_pages=1)
    result = detector.detect(str(bad_path))
    assert result == "invalid"


def test_detect_encrypted(tmp_path: Path):
    pdf_path = tmp_path / "encrypted.pdf"
    create_encrypted_pdf(pdf_path)
    # Reabrir sin contraseña y pasar al detector
    detector = PDFTypeDetector(sample_pages=1)
    result = detector.detect(str(pdf_path))
    assert result == "encrypted"


def test_detect_empty_monkeypatched(tmp_path: Path, monkeypatch):
    """
    PyMuPDF no permite guardar un PDF con 0 páginas.
    Simulamos 'empty' monkeypatching a fitz.open para devolver un objeto con len==0.
    """

    class FakeDoc:
        is_encrypted = False
        def __len__(self):
            return 0

    def fake_open(_file_path):
        return FakeDoc()

    monkeypatch.setattr(fitz, "open", fake_open)

    detector = PDFTypeDetector(sample_pages=1)
    result = detector.detect("whatever.pdf")
    assert result == "empty"
