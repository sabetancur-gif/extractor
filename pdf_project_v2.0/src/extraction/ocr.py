"""
src/extraction/ocr.py
---------------------
Extractor OCR para PDFs escaneados o con texto no seleccionable.
Pipeline:
  1. Renderizar cada página a imagen (pdf2image + Poppler, o PyMuPDF)
  2. Pre-procesar imagen para mejorar calidad (denoise, binarización, deskew)
  3. Tesseract OCR → datos por palabra con bounding boxes y confianza
  4. Agrupar palabras en líneas/bloques
  5. Clasificar semánticamente cada bloque
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pytesseract import Output

from .base import BaseExtractor
from .block_classifier import classify_block
from .field_detection import extract_fields_from_block
from src.config.paths import POPPLER_PATH, TESSERACT_CMD, TESSDATA_DIR

# Configurar Tesseract
pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_CMD)
os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

# Confianza mínima para incluir una palabra OCR
MIN_CONF = 30


# ── Pre-procesador de imagen ──────────────────────────────────────────────────

class OCRPreprocessor:
    """
    Pipeline de pre-procesamiento de imagen para mejorar la calidad del OCR.
    Aplica: escala de grises → denoising → binarización adaptativa → deskew.
    """

    def __init__(self, denoise: bool = True, threshold: bool = True, deskew: bool = True):
        self.denoise   = denoise
        self.threshold = threshold
        self.deskew    = deskew

    def process(self, pil_img: Image.Image) -> Image.Image:
        """Procesa una imagen PIL y retorna la imagen mejorada para OCR."""
        arr = np.array(pil_img.convert("L"))  # escala de grises

        if self.denoise:
            arr = cv2.fastNlMeansDenoising(arr, None, h=10, templateWindowSize=7, searchWindowSize=21)

        if self.threshold:
            # Binarización adaptativa: mejor para iluminación irregular
            arr = cv2.adaptiveThreshold(
                arr, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=31, C=10,
            )

        if self.deskew:
            arr = _deskew(arr)

        return Image.fromarray(arr)


def _deskew(arr: np.ndarray) -> np.ndarray:
    """Corrige la inclinación del texto en la imagen."""
    try:
        coords = np.column_stack(np.where(arr < 128))
        if len(coords) < 100:
            return arr
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) < 0.5:
            return arr
        h, w = arr.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(arr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    except Exception:
        return arr


# ── Extractor OCR ─────────────────────────────────────────────────────────────

class OCRExtractor(BaseExtractor):
    """Extractor OCR para PDFs escaneados."""

    def __init__(
        self,
        lang: str = "eng+spa",
        dpi: int  = 300,
        preprocessor: OCRPreprocessor | None = None,
    ):
        self.lang         = lang
        self.dpi          = dpi
        self.preprocessor = preprocessor or OCRPreprocessor()

    def extract(self, file_path: str, return_images: bool = False):
        """
        Extrae texto y bloques OCR de todas las páginas del PDF.

        Args:
            file_path:     Ruta al PDF.
            return_images: Si True, retorna (pages, processed_images).

        Returns:
            Lista de páginas con bloques extraídos, o (páginas, imágenes).
        """
        images = _render_pdf(file_path, self.dpi)
        pages:  list[dict] = []
        proc_images: list[Image.Image] = []

        for pno, img in enumerate(images, start=1):
            proc = self.preprocessor.process(img)
            proc_images.append(proc)

            ocr_data = pytesseract.image_to_data(proc, lang=self.lang, output_type=Output.DICT)
            line_groups = _group_words_to_lines(ocr_data)
            paragraph_blocks = _merge_lines_to_blocks(line_groups)

            blocks: list[dict] = []
            for order, pb in enumerate(paragraph_blocks):
                text = pb["text"].strip()
                if not text:
                    continue

                bbox = _clip_bbox(pb["bbox"], proc.width, proc.height)
                field_info  = extract_fields_from_block(text, context=text)
                field_type  = field_info.get("field")  if field_info else None
                field_value = field_info.get("value")  if field_info else None

                semantic = classify_block(
                    {"text": text, "bbox": bbox},
                    page_width=proc.width,
                    page_height=proc.height,
                )

                blocks.append({
                    "block_id":            f"{pno}_ocr_{order}",
                    "text":                text,
                    "bbox":                bbox,
                    "page":                pno,
                    "page_number":         pno,
                    "source":              "ocr",
                    "order":               order,
                    "confidence":          pb.get("avg_conf"),
                    "field_type":          field_type,
                    "field_value":         field_value,
                    "semantic_type":       semantic["semantic_type"],
                    "semantic_confidence": semantic["confidence"],
                    "semantic_labels":     semantic["labels"],
                    "is_table_like":       semantic["is_table_like"],
                    "is_signature":        semantic["is_signature"],
                    "is_logo":             semantic["is_logo"],
                    "is_image":            semantic["is_image"],
                    "is_address":          semantic["is_address"],
                    "is_date":             semantic["is_date"],
                    "is_amount":           semantic["is_amount"],
                    "is_phone":            semantic["is_phone"],
                    "is_email":            semantic["is_email"],
                    "is_url":              semantic["is_url"],
                    "is_identifier":       semantic["is_identifier"],
                    "is_name":             semantic.get("is_name", False),
                    "is_math":             semantic.get("is_math", False),
                })

            pages.append({
                "page_number": pno,
                "width":       proc.width,
                "height":      proc.height,
                "blocks":      blocks,
            })

        return (pages, proc_images) if return_images else pages


# ── Helpers de agrupación ─────────────────────────────────────────────────────

def _render_pdf(file_path: str, dpi: int) -> list[Image.Image]:
    """Renderiza el PDF a imágenes PIL. Primero Poppler, luego PyMuPDF."""
    try:
        return convert_from_path(file_path, dpi=dpi, poppler_path=str(POPPLER_PATH))
    except Exception:
        import fitz
        doc = fitz.open(file_path)
        images = []
        zoom = dpi / 72.0
        mat  = fitz.Matrix(zoom, zoom)
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
        doc.close()
        return images


def _group_words_to_lines(data: dict) -> list[dict]:
    """Agrupa palabras OCR en líneas usando la jerarquía de Tesseract."""
    groups: dict[tuple, dict] = {}
    n = len(data["text"])

    for i in range(n):
        word = data["text"][i]
        conf = int(data["conf"][i])
        if not word.strip() or conf < MIN_CONF:
            continue

        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        left, top = data["left"][i], data["top"][i]
        w, h = data["width"][i], data["height"][i]

        if key not in groups:
            groups[key] = {
                "words": [],
                "bbox":  [left, top, left + w, top + h],
                "confs": [],
            }

        g = groups[key]
        g["words"].append(word)
        g["bbox"][0] = min(g["bbox"][0], left)
        g["bbox"][1] = min(g["bbox"][1], top)
        g["bbox"][2] = max(g["bbox"][2], left + w)
        g["bbox"][3] = max(g["bbox"][3], top + h)
        if conf >= 0:
            g["confs"].append(conf)

    lines = []
    for key, g in sorted(groups.items()):
        avg_conf = sum(g["confs"]) / len(g["confs"]) if g["confs"] else None
        lines.append({
            "key":      key,
            "text":     " ".join(g["words"]),
            "bbox":     g["bbox"],
            "avg_conf": avg_conf,
        })
    return lines


def _merge_lines_to_blocks(lines: list[dict], gap_threshold: float = 15) -> list[dict]:
    """
    Agrupa líneas cercanas verticalmente en bloques/párrafos.
    Líneas del mismo párrafo suelen tener un gap vertical pequeño.
    """
    if not lines:
        return []

    blocks: list[dict] = []
    current: dict | None = None

    for line in lines:
        x0, y0, x1, y1 = line["bbox"]

        if current is None:
            current = {
                "text":     line["text"],
                "bbox":     list(line["bbox"]),
                "confs":    [line["avg_conf"]] if line["avg_conf"] else [],
            }
        else:
            prev_y1 = current["bbox"][3]
            gap     = y0 - prev_y1

            if gap <= gap_threshold:
                # Mismo bloque: extender
                current["text"] += "\n" + line["text"]
                current["bbox"][0] = min(current["bbox"][0], x0)
                current["bbox"][1] = min(current["bbox"][1], y0)
                current["bbox"][2] = max(current["bbox"][2], x1)
                current["bbox"][3] = max(current["bbox"][3], y1)
                if line["avg_conf"]:
                    current["confs"].append(line["avg_conf"])
            else:
                # Nuevo bloque
                _finalize(current)
                blocks.append(current)
                current = {
                    "text":  line["text"],
                    "bbox":  list(line["bbox"]),
                    "confs": [line["avg_conf"]] if line["avg_conf"] else [],
                }

    if current:
        _finalize(current)
        blocks.append(current)

    return blocks


def _finalize(block: dict) -> None:
    """Calcula la confianza promedio del bloque."""
    confs = block.pop("confs", [])
    block["avg_conf"] = sum(confs) / len(confs) if confs else None


def _clip_bbox(bbox: list, max_w: int, max_h: int) -> list[float]:
    """Recorta el bbox a los límites de la imagen."""
    x0, y0, x1, y1 = bbox
    return [
        round(float(max(0, min(x0, x1))), 2),
        round(float(max(0, min(y0, y1))), 2),
        round(float(max(0, min(max_w, max(x0, x1)))), 2),
        round(float(max(0, min(max_h, max(y0, y1)))), 2),
    ]
