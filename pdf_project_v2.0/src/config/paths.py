"""src/config/paths.py — Rutas centralizadas del proyecto."""
from pathlib import Path

BASE_DIR     = Path(__file__).resolve().parents[2]
POPPLER_PATH = BASE_DIR / "engines" / "poppler" / "Library" / "bin"
TESSERACT_CMD= BASE_DIR / "engines" / "tesseract" / "tesseract.exe"
TESSDATA_DIR = BASE_DIR / "engines" / "tesseract" / "tessdata"
CACHE_DIR    = BASE_DIR / "data" / "cache"
LOGS_DIR     = BASE_DIR / "data" / "logs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
