
"""
src/config/paths.py
-------------------
Centraliza rutas a binarios y recursos externos (Poppler, Tesseract) y exporta variables de entorno.
Valida existencia de rutas críticas y advierte si faltan.

Uso:
    from src.config.paths import POPPLER_PATH, TESSERACT_CMD, TESSDATA_DIR
    # Las variables de entorno ya están configuradas al importar este módulo.
"""

import os
from pathlib import Path
import sys

# Ruta base del proyecto (ajustar si cambia la estructura)
BASE_DIR = Path(__file__).resolve().parents[2]

# === POPPLER ===
POPPLER_PATH = BASE_DIR / "engines" / "poppler" / "Library" / "bin"
if not POPPLER_PATH.exists():
    print(f"[WARNING] POPPLER_PATH no existe: {POPPLER_PATH}", file=sys.stderr)

# === TESSERACT ===
TESSERACT_CMD = BASE_DIR / "engines" / "tesseract" / "tesseract.exe"
TESSDATA_DIR = BASE_DIR / "engines" / "tesseract" / "tessdata"
if not TESSERACT_CMD.exists():
    print(f"[WARNING] TESSERACT_CMD no existe: {TESSERACT_CMD}", file=sys.stderr)
if not TESSDATA_DIR.exists():
    print(f"[WARNING] TESSDATA_DIR no existe: {TESSDATA_DIR}", file=sys.stderr)

# Exporta variables de entorno para librerías que las usan
os.environ["TESSDATA_PREFIX"] = str(TESSDATA_DIR)
os.environ["POPPLER_PATH"] = str(POPPLER_PATH)

# (Opcional) Configurar pytesseract de una vez
try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_CMD)
except ImportError:
    print("[INFO] pytesseract no está instalado. Solo necesario para OCR.", file=sys.stderr)
except Exception as e:
    print(f"[WARNING] Error configurando pytesseract: {e}", file=sys.stderr)
