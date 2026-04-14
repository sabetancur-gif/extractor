# src/extraction/ocr.py
from .base import BaseExtractor
from pdf2image import convert_from_path
import pytesseract
from pytesseract import image_to_data, Output
from PIL import Image
import numpy as np
import cv2
from pathlib import Path
import os

from src.extraction.block_classifier import classify_block
# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]

POPPLER_PATH = BASE_DIR / "engines" / "poppler" / "Library" / "bin"

# === TESSERACT ===
TESSERACT_CMD = BASE_DIR / "engines" / "tesseract" / "tesseract.exe"
TESSDATA_DIR = BASE_DIR / "engines" / "tesseract" / "tessdata"

# Decirle explícitamente a pytesseract dónde está Tesseract
pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_CMD)

# Decirle a Tesseract dónde están los idiomas
os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)

# ==============================================================================

# Objectivo: Mejorar la calidad del OCR antes de enviarlo al Tesseract
class OCRPreprocessor:
    # Definir que pasos aplicar
    def __init__(self, denoise=True, threshold=True, deskew=False):
        self.denoise = denoise  # Ruido
        self.threshold = threshold  # Binarizar la imagen
        self.deskew = deskew  # Enderezar texto torcido

    # Devuelve una nueva imagen PIL lista para OCR
    # 👉 Este paso impacta directamente la calidad del texto.
    def process(self, pil_img: Image.Image) -> Image.Image:
        # Convertir la imagen a escala de grises
        arr = np.array(pil_img.convert("L"))
        # Aplica denoise
        if self.denoise:
            arr = cv2.fastNlMeansDenoising(arr, None, 10, 7, 21)
        # Binarización automática
        if self.threshold:
            _, arr = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # deskew optional (skipped for brevity)
        return Image.fromarray(arr)

# Hereda de BaseExtractor, así que respeta el mismo contrato que el extractor nativo.
class OCRExtractor(BaseExtractor):
    def __init__(self, lang="eng+spa", dpi=400, preprocessor=None):
        self.lang = lang  # idioma de Tesseract
        self.dpi = dpi  # Resolución de renderizado
        self.preprocessor = preprocessor or OCRPreprocessor()  # Pipeline de limpieza de imagenes

    def extract(self, file_path: str, return_images: bool = False):
        """
        Extrae texto y bloques OCR de un PDF. Si return_images=True, retorna (pages, processed_images).
        """
        from .field_detection import extract_fields_from_block
        images = convert_from_path(
            file_path,
            dpi=self.dpi,
            poppler_path=str(POPPLER_PATH)
        )
        pages = []
        processed_images = []
        for pno, img in enumerate(images, start=1):
            proc = self.preprocessor.process(img)
            processed_images.append(proc)
            data = image_to_data(proc, lang=self.lang, output_type=Output.DICT)
            blocks = self._group(data, pno)
            for block in blocks:
                bbox = block.get("bbox", [0, 0, 0, 0])
                x0, y0, x1, y1 = bbox if len(bbox) == 4 else (0,0,0,0)
                x0, x1 = sorted([x0, x1])
                y0, y1 = sorted([y0, y1])
                x0, x1 = max(0, x0), min(proc.width, x1)
                y0, y1 = max(0, y0), min(proc.height, y1)
                block["bbox"] = [round(float(x0)), round(float(y0)), round(float(x1)), round(float(y1))]
                text = block.get("text", "")
                context = text
                field_info = extract_fields_from_block(text, context)
                if field_info:
                    block["field_type"] = field_info["field"]
                    block["field_value"] = field_info["value"]
                    block["all_fields"] = field_info.get("all_fields", [])
                font_size = block.get("font_size", None)
                text_len = len(text)
                text_lower = text.lower()
                if font_size and font_size > 16 and text_len < 80:
                    block["block_type"] = "title"
                elif "table" in text_lower or "tabla" in text_lower:
                    block["block_type"] = "table"
                elif any(k in text_lower for k in ["total", "monto", "$", "importe"]):
                    block["block_type"] = "amount"
                elif any(k in text_lower for k in ["fecha", "date"]):
                    block["block_type"] = "date"
                elif text_len > 200:
                    block["block_type"] = "paragraph"
                elif text_len < 30 and font_size and font_size > 10:
                    block["block_type"] = "header"
                else:
                    block["block_type"] = "other"

                semantic = classify_block(
                    block,
                    page_width=proc.width,
                    page_height=proc.height
                )

                block.update(
                    {
                        "semantic_type": semantic["semantic_type"],
                        "semantic_confidence": semantic["confidence"],
                        "semantic_labels": semantic["labels"],
                        "is_table_like": semantic["is_table_like"],
                        "is_signature": semantic["is_signature"],
                        "is_logo": semantic["is_logo"],
                        "is_image": semantic["is_image"],
                        "is_address": semantic["is_address"],
                        "is_date": semantic["is_date"],
                        "is_amount": semantic["is_amount"],
                        "is_phone": semantic["is_phone"],
                        "is_email": semantic["is_email"],
                        "is_url": semantic["is_url"],
                        "is_identifier": semantic["is_identifier"],
                    }
                )


            pages.append({"page_number": pno, "width": proc.width, "height": proc.height, "blocks": blocks})
        if return_images:
            return pages, processed_images
        return pages

    def _group(self, data, page_num):
        # Diccionario para agrupar palabras OCR por línea
        # key = (block_num, par_num, line_num)
        groups = {}

        # Número total de elementos reconocidos por Tesseract
        n = len(data["text"])

        # Recorremos palabra por palabra en el orden original del OCR
        for i in range(n):
            text = data["text"][i]

            # Ignorar strings vacíos o solo espacios (ruido OCR)
            if not text.strip():
                continue

            # Clave jerárquica OCR:
            # block_num -> par_num -> line_num
            # Esto agrupa palabras que pertenecen a la misma línea
            key = (
                data["block_num"][i],
                data["par_num"][i],
                data["line_num"][i],
            )

            # Bounding box de la palabra actual
            left, top = data["left"][i], data["top"][i]
            w, h = data["width"][i], data["height"][i]

            # Confianza OCR de la palabra (-1 significa inválida)
            conf = int(data["conf"][i])

            # Si es la primera palabra de este grupo (línea),
            # inicializamos la estructura del bloque
            if key not in groups:
                groups[key] = {
                    "texts": [],                               # palabras de la línea
                    "bbox": [left, top, left + w, top + h],   # bbox inicial
                    "confs": []                                # confidencias válidas
                }

            # Referencia corta al grupo actual
            g = groups[key]

            # Agregamos la palabra al texto del bloque
            g["texts"].append(text)

            # Expandimos el bounding box para cubrir todas las palabras de la línea
            g["bbox"][0] = min(g["bbox"][0], left)
            g["bbox"][1] = min(g["bbox"][1], top)
            g["bbox"][2] = max(g["bbox"][2], left + w)
            g["bbox"][3] = max(g["bbox"][3], top + h)

            # Solo guardamos confidencias válidas (>= 0)
            if conf >= 0:
                g["confs"].append(conf)

        # Lista final de bloques OCR por página
        blocks = []

        # Ordenamos los grupos según su orden lógico OCR
        # (block_num, par_num, line_num)
        for order, ((b, p, l), g) in enumerate(sorted(groups.items())):
            # Confianza promedio del bloque (línea)
            avg_conf = (
                sum(g["confs"]) / len(g["confs"])
                if g["confs"] else None
            )

            # Construcción del bloque final compatible con el pipeline
            blocks.append({
                "block_id": f"{page_num}_ocr_{order}",  # ID único por página
                "text": " ".join(g["texts"]),           # texto completo de la línea
                "bbox": g["bbox"],                      # bounding box consolidado
                "page": page_num,                       # número de página
                "source": "ocr",                        # origen del texto
                "order": order,                         # orden real de lectura
                "confidence": avg_conf                  # calidad del OCR
            })

        # Devuelve los bloques listos para clustering / layout / Dash
        return blocks
