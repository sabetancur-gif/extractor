
# src/utils/image.py
"""
Utilidades para renderizar páginas de PDF a imágenes.
- Intento principal: pdf2image + Poppler local (engines/poppler/Library/bin)
- Fallback: PyMuPDF (fitz) sin dependencias externas
"""

import os
from typing import List
from pathlib import Path

from src.config.paths import POPPLER_PATH  # centralizamos rutas (opcional)


def render_page_to_image(file_path: str, page_num: int, out_path: str, dpi: int = 150, zoom: float = 2.0) -> str:
    """
    Renderiza una sola página del PDF a imagen (PNG/JPEG) en `out_path`.
    page_num es 1-indexed.
    1) Intenta pdf2image con poppler_path
    2) Fallback a PyMuPDF (fitz)
    Retorna: ruta del archivo guardado (out_path)
    """
    # --- Intento 1: pdf2image + Poppler ---
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(
            file_path,
            dpi=dpi,
            first_page=page_num,
            last_page=page_num,
            poppler_path=str(POPPLER_PATH)  # engines/poppler/Library/bin
        )
        if images:
            img = images[0]
            ext = os.path.splitext(out_path)[1].lower()
            fmt = "PNG" if ext == ".png" else ("JPEG" if ext in [".jpg", ".jpeg"] else "PNG")
            img.save(out_path, fmt)
            return out_path
    except Exception:
        # PDFInfoNotInstalledError / FileNotFoundError / etc. -> fallback
        pass

    # --- Fallback: PyMuPDF (fitz) ---
    import fitz  # PyMuPDF
    doc = fitz.open(file_path)
    page = doc[page_num - 1]  # fitz usa 0-index
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    ext = os.path.splitext(out_path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        pix.save(out_path, output="jpg")
    else:
        pix.save(out_path)  # PNG default

    doc.close()
    return out_path


def render_all_pages(file_path: str, out_folder: str, dpi: int = 150, zoom: float = 2.0) -> List[str]:
    """
    Renderiza todas las páginas del PDF a imágenes PNG (por defecto) en `out_folder`.
    1) Intenta pdf2image con poppler_path
    2) Fallback a PyMuPDF (fitz)
    Retorna: lista de rutas de imágenes generadas.
    """
    os.makedirs(out_folder, exist_ok=True)
    paths: List[str] = []

    # --- Intento 1: pdf2image + Poppler ---
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(
            file_path,
            dpi=dpi,
            poppler_path=str(POPPLER_PATH)
        )
        for i, img in enumerate(images, start=1):
            p = os.path.join(out_folder, f"page_{i}.png")
            img.save(p, format="PNG")
            paths.append(p)
        return paths
    except Exception:
        # fallback si algo falla
        pass

    # --- Fallback: PyMuPDF (fitz) ---
    import fitz
    doc = fitz.open(file_path)
    for i, page in enumerate(doc, start=1):
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        p = os.path.join(out_folder, f"page_{i}.png")
        pix.save(p)  # PNG
        paths.append(p)
    doc.close()

    return paths
