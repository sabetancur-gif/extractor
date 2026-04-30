"""
src/extraction/block_classifier.py
------------------------------------
Clasificador semántico de bloques PDF.
Identifica: fecha, correo, teléfono, nombre, firma, título, subtítulo,
imagen, tabla, párrafo, monto, expresión matemática, dirección, URL,
identificador, logo, código, sello, encabezado, pie de página.

La clasificación usa:
  - Reglas regex para patrones estructurados (fecha, email, monto, etc.)
  - Análisis tipográfico (font_size, bold, caps)
  - Señales contextuales (hints de texto, etiquetas)
  - Geometría del bloque (área relativa, aspect ratio)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict, field
from typing import Any, Dict

from src.utils.bbox import bbox_area, normalize_bbox

# ── Patrones regex por tipo ─────────────────────────────────────────────────

DATE_RE = re.compile(
    r"\b("
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}"
    r"|\d{1,2}\s+(?:de\s+)?[A-Za-záéíóúñÁÉÍÓÚÑ]+\.?\s+(?:de\s+)?\d{2,4}"
    r"|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}"
    r"|(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{1,2},?\s+\d{4}"
    r")\b",
    re.IGNORECASE,
)

MONEY_RE = re.compile(
    r"(?:"
    r"(?:COP|USD|EUR|MXN|PEN|CLP|ARS|BRL|GBP)\s*[$€£]?"
    r"|[$€£]"
    r"|COP\$"
    r")\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?"
    r"|\b\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?\b"
)

PHONE_RE = re.compile(
    r"(?:\+?[0-9]{1,3}[\s\-\.]?)?(?:\(?[0-9]{2,4}\)?[\s\-\.]?)?[0-9]{3,4}[\s\-\.][0-9]{4}"
    r"|\b[0-9]{10}\b"
    r"|\+[0-9]{10,15}"
)

EMAIL_RE   = re.compile(r"[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}")
URL_RE     = re.compile(r"https?://[^\s,;<>\"']+")
ID_RE      = re.compile(r"\b[0-9]{6,12}\b")
MATH_RE    = re.compile(r"[=+\-×÷∑∏√∫∂∇≤≥≠±∞]{1,}|\b[a-z]+\s*[=<>]\s*[a-z0-9]+", re.I)
NAME_RE    = re.compile(
    r"\b(?:Sr\.?|Sra\.?|Dr\.?|Dra\.?|Ing\.?|Lic\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+){0,3}"
    r"|\b[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+(?:de|del|la|los|las|el))?\s+[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)?"
)

# ── Pistas de contexto por tipo ──────────────────────────────────────────────

ADDRESS_HINTS = (
    "dirección", "direccion", "address", "calle", "cra", "carrera", "cll",
    "avenida", "av.", "nro.", "no.", "número", "numero", "barrio", "sector",
    "ciudad", "municipio", "departamento", "zip", "postal",
)
SIGNATURE_HINTS = (
    "firma", "firmado", "firmante", "signature", "signed", "rúbrica", "rubrica",
    "elaboró", "elaboro", "revisó", "reviso", "aprobó", "aprobo", "autorizado",
    "f.", "sign here",
)
LOGO_HINTS   = ("logo", "marca", "brand", "isotipo", "logotipo", "escudo")
TABLE_HINTS  = ("tabla", "table", "cuadro", "row", "columna", "column")
IMAGE_HINTS  = ("imagen", "image", "figura", "figure", "foto", "photograph", "chart", "gráfico", "grafico", "ilustración")
HEADER_HINTS = ("encabezado", "header", "membrete", "letterhead")
FOOTER_HINTS = ("pie de página", "footer", "confidencial", "página", "page", "pág.", "folio")
CODE_HINTS   = ("def ", "class ", "import ", "function", "var ", "const ", "let ", "SELECT ", "FROM ", "<html", "<?php")

# ── Dataclass de resultado ───────────────────────────────────────────────────

@dataclass
class BlockClassification:
    semantic_type:   str   = "other"
    confidence:      float = 0.5
    is_table_like:   bool  = False
    is_signature:    bool  = False
    is_logo:         bool  = False
    is_image:        bool  = False
    is_address:      bool  = False
    is_date:         bool  = False
    is_amount:       bool  = False
    is_phone:        bool  = False
    is_email:        bool  = False
    is_url:          bool  = False
    is_identifier:   bool  = False
    is_name:         bool  = False
    is_math:         bool  = False
    labels:          list  = field(default_factory=list)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _uppercase_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def _has_hint(lower: str, hints: tuple) -> bool:
    return any(h in lower for h in hints)


# ── Clasificador principal ───────────────────────────────────────────────────

def classify_block(
    block: Dict[str, Any],
    page_width: float | None = None,
    page_height: float | None = None,
) -> Dict[str, Any]:
    """
    Clasifica un bloque de texto/imagen extraído del PDF.

    La clasificación es jerárquica: los tipos con patrones más específicos
    (email, fecha, monto) tienen prioridad sobre los genéricos (párrafo, otro).

    Returns:
        Dict con keys: semantic_type, confidence, is_*, labels.
    """
    text   = _safe_text(block.get("text"))
    lower  = text.lower()
    bbox   = normalize_bbox(block.get("bbox"))
    area   = bbox_area(bbox)
    labels: list[str] = []

    semantic_type = "other"
    confidence    = 0.5

    # Métricas de texto
    token_count = len(re.findall(r"\w+", text))
    line_count  = text.count("\n") + 1
    char_count  = len(text.strip())
    up_ratio    = _uppercase_ratio(text)

    # ── 1. Patrones regex de alta precisión ─────────────────────────────────
    is_email      = bool(EMAIL_RE.search(text))
    is_url        = bool(URL_RE.search(text))
    is_date       = bool(DATE_RE.search(text))
    is_amount     = bool(MONEY_RE.search(text))
    is_phone      = bool(PHONE_RE.search(text))
    is_identifier = bool(ID_RE.search(text)) and not is_date and not is_amount
    is_math       = bool(MATH_RE.search(text)) and token_count < 30
    is_name       = bool(NAME_RE.search(text)) and token_count <= 8

    # Registro de labels de patrones
    if is_email:      labels.append("email")
    if is_url:        labels.append("url")
    if is_date:       labels.append("date")
    if is_amount:     labels.append("amount")
    if is_phone:      labels.append("phone")
    if is_identifier: labels.append("identifier")
    if is_math:       labels.append("math")
    if is_name:       labels.append("name")

    # Asignación por patrón (prioridad descendente)
    if is_email:
        semantic_type, confidence = "email", 0.96
    elif is_url:
        semantic_type, confidence = "url", 0.96
    elif is_date and token_count <= 12:
        semantic_type, confidence = "date", 0.93
    elif is_amount and token_count <= 10:
        semantic_type, confidence = "amount", 0.91
    elif is_phone and token_count <= 6:
        semantic_type, confidence = "phone", 0.92
    elif is_math and semantic_type == "other":
        semantic_type, confidence = "math_expression", 0.85

    # ── 2. Señales contextuales (hints) ─────────────────────────────────────
    is_signature = _has_hint(lower, SIGNATURE_HINTS)
    is_logo      = _has_hint(lower, LOGO_HINTS)
    is_address   = _has_hint(lower, ADDRESS_HINTS)
    is_image     = _has_hint(lower, IMAGE_HINTS)
    is_code      = _has_hint(text, CODE_HINTS)  # case-sensitive para código

    if is_signature and semantic_type == "other":
        semantic_type, confidence = "signature", 0.90
        labels.append("signature")
    if is_logo and semantic_type == "other":
        semantic_type, confidence = "logo", 0.82
        labels.append("logo")
    if is_address and semantic_type == "other":
        semantic_type, confidence = "address", 0.87
        labels.append("address")
    if is_code and semantic_type == "other":
        semantic_type, confidence = "code", 0.88
        labels.append("code")

    # ── 3. Tabla (señales mixtas) ────────────────────────────────────────────
    is_table_like = (
        _has_hint(lower, TABLE_HINTS)
        or text.count("|") >= 2
        or (line_count >= 2 and text.count("  ") >= 3)
        or (line_count >= 3 and token_count >= 15 and any(c.isdigit() for c in text))
    )
    if is_table_like:
        labels.append("table")
        if semantic_type == "other":
            semantic_type, confidence = "table", 0.87

    # ── 4. Análisis geométrico ───────────────────────────────────────────────
    if bbox and page_width and page_height and page_width > 0 and page_height > 0:
        try:
            x0, y0, x1, y1 = bbox
            bw = max(0.0, x1 - x0)
            bh = max(0.0, y1 - y0)
            rel_area = (bw * bh) / (page_width * page_height)
            aspect   = bw / bh if bh > 0 else 0.0
            rel_y    = y0 / page_height  # posición vertical relativa

            # Bloque grande con poco texto → figura/imagen
            if rel_area > 0.15 and token_count < 20 and semantic_type == "other":
                semantic_type, confidence = "figure", 0.78
                labels.append("figure")
                is_image = True

            # Bloque muy pequeño y pocos tokens → sello/stamp
            if rel_area < 0.008 and token_count <= 3 and semantic_type == "other":
                semantic_type, confidence = "stamp", 0.68
                labels.append("stamp")

            # Bloque muy ancho y bajo → encabezado o pie de página
            if aspect > 6 and rel_area < 0.05:
                if rel_y < 0.15:
                    labels.append("page_header")
                    if semantic_type == "other":
                        semantic_type, confidence = "header", 0.72
                elif rel_y > 0.85:
                    labels.append("page_footer")
                    if semantic_type == "other":
                        semantic_type, confidence = "footer", 0.72

        except Exception:
            pass

    # ── 5. Análisis tipográfico ──────────────────────────────────────────────
    font_size = block.get("font_size") or block.get("avg_font_size")
    is_bold   = block.get("is_bold", False) or "Bold" in str(block.get("font_name", ""))

    if semantic_type == "other" and font_size:
        try:
            fs = float(font_size)
            if fs >= 18 and token_count <= 12:
                semantic_type, confidence = "title", 0.88
            elif fs >= 14 and token_count <= 20:
                semantic_type, confidence = "subtitle", 0.82
            elif is_bold and token_count <= 15:
                semantic_type, confidence = "subtitle", 0.76
        except Exception:
            pass

    # ── 6. Mayúsculas (títulos sin info de fuente) ───────────────────────────
    if semantic_type == "other":
        if token_count <= 8 and char_count >= 3 and up_ratio > 0.7:
            semantic_type, confidence = "title", 0.80

    # ── 7. Nombre detectado ──────────────────────────────────────────────────
    if is_name and semantic_type == "other":
        semantic_type, confidence = "name", 0.82

    # ── 8. Clasificación por longitud (fallback) ─────────────────────────────
    if semantic_type == "other":
        if char_count == 0:
            semantic_type, confidence = "empty", 0.99
        elif line_count >= 3 or token_count >= 25:
            semantic_type, confidence = "paragraph", 0.74
        elif token_count <= 10 and char_count >= 3:
            semantic_type, confidence = "header", 0.62
        else:
            semantic_type, confidence = "paragraph", 0.60

    return asdict(BlockClassification(
        semantic_type   = semantic_type,
        confidence      = round(float(min(confidence, 0.99)), 3),
        is_table_like   = is_table_like,
        is_signature    = is_signature,
        is_logo         = is_logo,
        is_image        = is_image,
        is_address      = is_address,
        is_date         = is_date,
        is_amount       = is_amount,
        is_phone        = is_phone,
        is_email        = is_email,
        is_url          = is_url,
        is_identifier   = is_identifier,
        is_name         = is_name,
        is_math         = is_math,
        labels          = sorted(set(labels)) if labels else [],
    ))
