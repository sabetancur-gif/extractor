# src/extraction/block_classifier.py
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict

from src.utils.bbox import bbox_area, normalize_bbox


DATE_RE = re.compile(
    r"\b("
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"|\d{1,2}\s+[A-Za-záéíóúñÁÉÍÓÚÑ]+\s+\d{2,4}"
    r")\b"
)

MONEY_RE = re.compile(
    r"(?:(?:COP|USD|EUR|MXN|PEN|CLP|ARS|BRL)\s*)?"
    r"(?:(?:[$€£]|COP\$)\s*)?"
    r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\b"
)

PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}"
)

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
URL_RE = re.compile(r"https?://[^\s,;]+")
ID_RE = re.compile(r"\b\d{6,12}\b")

ADDRESS_HINTS = (
    "dirección", "direccion", "address", "calle", "cra", "carrera", "cll",
    "avenida", "av", "nro", "no.", "número", "numero", "barrio", "sector",
)

SIGNATURE_HINTS = ("firma", "firmado", "signature", "signed", "rúbrica", "rubrica")
LOGO_HINTS = ("logo", "marca", "brand", "isotipo", "identidad visual")
TABLE_HINTS = ("tabla", "table", "row", "columna", "column", "|", "\t")
IMAGE_HINTS = ("imagen", "image", "figura", "figure", "foto", "photograph", "chart", "gráfico", "grafico")

TEXTUAL_LABELS = {
    "date": DATE_RE,
    "amount": MONEY_RE,
    "phone": PHONE_RE,
    "email": EMAIL_RE,
    "url": URL_RE,
    "identifier": ID_RE,
}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


@dataclass
class BlockClassification:
    semantic_type: str = "other"
    confidence: float = 0.5
    is_table_like: bool = False
    is_signature: bool = False
    is_logo: bool = False
    is_image: bool = False
    is_address: bool = False
    is_date: bool = False
    is_amount: bool = False
    is_phone: bool = False
    is_email: bool = False
    is_url: bool = False
    is_identifier: bool = False
    labels: list[str] | None = None


def classify_block(
    block: Dict[str, Any],
    page_width: int | None = None,
    page_height: int | None = None,
) -> Dict[str, Any]:
    text = _safe_text(block.get("text"))
    lower = text.lower()
    bbox = normalize_bbox(block.get("bbox"))
    area = bbox_area(bbox)
    labels: list[str] = []
    confidence = 0.5
    semantic_type = "other"

    for label, pattern in TEXTUAL_LABELS.items():
        if pattern.search(text):
            labels.append(label)

    is_date = "date" in labels
    is_amount = "amount" in labels
    is_phone = "phone" in labels
    is_email = "email" in labels
    is_url = "url" in labels
    is_identifier = "identifier" in labels

    if is_date:
        semantic_type = "date"
        confidence = 0.92
    elif is_amount:
        semantic_type = "amount"
        confidence = 0.90
    elif is_email:
        semantic_type = "email"
        confidence = 0.95
    elif is_phone:
        semantic_type = "phone"
        confidence = 0.92
    elif is_url:
        semantic_type = "url"
        confidence = 0.95
    elif is_identifier:
        semantic_type = "identifier"
        confidence = 0.80

    token_count = len(re.findall(r"\w+", text))
    line_count = text.count("\n") + 1

    is_table_like = (
        any(h in lower for h in TABLE_HINTS)
        or (
            line_count >= 2
            and (
                text.count("|") >= 1
                or text.count("  ") >= 2
                or (token_count >= 12 and any(ch.isdigit() for ch in text))
            )
        )
    )
    if is_table_like and semantic_type == "other":
        semantic_type = "table"
        labels.append("table")
        confidence = max(confidence, 0.86)

    is_signature = any(h in lower for h in SIGNATURE_HINTS)
    if is_signature:
        semantic_type = "signature"
        labels.append("signature")
        confidence = max(confidence, 0.88)

    is_logo = any(h in lower for h in LOGO_HINTS)
    if is_logo:
        semantic_type = "logo"
        labels.append("logo")
        confidence = max(confidence, 0.80)

    is_address = any(h in lower for h in ADDRESS_HINTS)
    if is_address:
        semantic_type = "address"
        labels.append("address")
        confidence = max(confidence, 0.86)

    is_image = any(h in lower for h in IMAGE_HINTS)
    if is_image:
        semantic_type = "image"
        labels.append("image")
        confidence = max(confidence, 0.84)

    if bbox and page_width and page_height:
        try:
            x0, y0, x1, y1 = bbox
            bw = max(0.0, x1 - x0)
            bh = max(0.0, y1 - y0)
            rel_area = (bw * bh) / float(page_width * page_height)
            aspect = bw / bh if bh else 0.0

            if rel_area > 0.20 and token_count < 25 and semantic_type == "other":
                semantic_type = "figure"
                labels.append("figure")
                confidence = max(confidence, 0.70)

            if rel_area < 0.01 and token_count <= 4 and semantic_type == "other":
                semantic_type = "stamp"
                labels.append("stamp")
                confidence = max(confidence, 0.65)

            if aspect > 8 and token_count <= 12 and semantic_type == "other":
                semantic_type = "header"
                labels.append("header")
                confidence = max(confidence, 0.70)
        except Exception:
            pass

    if semantic_type == "other":
        if token_count <= 8 and text and text == text.upper() and any(c.isalpha() for c in text):
            semantic_type = "title"
            confidence = 0.78
        elif line_count >= 2 or token_count >= 20:
            semantic_type = "paragraph"
            confidence = 0.72

    return asdict(
        BlockClassification(
            semantic_type=semantic_type,
            confidence=round(float(min(confidence, 0.99)), 3),
            is_table_like=is_table_like,
            is_signature=is_signature,
            is_logo=is_logo,
            is_image=is_image,
            is_address=is_address,
            is_date=is_date,
            is_amount=is_amount,
            is_phone=is_phone,
            is_email=is_email,
            is_url=is_url,
            is_identifier=is_identifier,
            labels=sorted(set(labels)) if labels else [],
        )
    )