# src/extraction/field_detection.py
"""
Módulo para detección y clasificación precisa de campos: teléfonos, correos, fechas, montos, identificadores, etc.
"""
import re
from typing import Optional, Dict

# Regex internacionales y validadores
PHONE_PATTERNS = [
    # Colombia +57
    re.compile(r"(?<!\d)(\+57\s?\d{3}[\s-]?\d{3}[\s-]?\d{3,4})(?!\d)"),
    # USA +1
    re.compile(r"(?<!\d)(\+1\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})(?!\d)"),
    # Genérico internacional (no más de 10-11 dígitos)
    re.compile(r"(?<!\d)(\+\d{1,3}[\s-]?\d{6,11})(?!\d)")
]
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
DATE_PATTERNS = [
    re.compile(r"\b\d{2,4}[/-]\d{1,2}[/-]\d{1,4}\b"),  # 2022-12-31, 31/12/2022
    re.compile(r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b")  # 31 December 2022
]
AMOUNT_PATTERN = re.compile(r"\b\$?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\b")
ID_PATTERNS = [
    re.compile(r"\b\d{6,10}\b"),  # Cédulas, NIT, etc.
    re.compile(r"\b[A-Z]{2,4}-?\d{4,10}\b")  # Pasaportes, RFC, etc.
]

# Palabras clave para refuerzo contextual
PHONE_CONTEXT = ["tel", "phone", "contacto", "cel", "móvil", "telefono", "llamar"]
EMAIL_CONTEXT = ["email", "correo", "e-mail", "mail"]
DATE_CONTEXT = ["fecha", "date", "nacimiento", "expedición", "vencimiento"]
AMOUNT_CONTEXT = ["valor", "monto", "total", "importe", "pago", "price", "amount"]
ID_CONTEXT = ["id", "identificación", "cedula", "nit", "passport", "rfc"]


def classify_field(text: str, context: str = "") -> Optional[Dict]:
    """
    Clasifica y valida el tipo de campo y su valor.
    Devuelve dict con tipo y valor normalizado, o None si no es válido.
    """
    t, c = text.strip(), context.lower()
    # Teléfonos
    for pat in PHONE_PATTERNS:
        m = pat.fullmatch(t.replace(" ", "").replace("-", ""))
        if m:
            # Validar contexto y longitud
            if any(k in c for k in PHONE_CONTEXT) and 8 <= len(re.sub(r"\D", "", t)) <= 11:
                return {"field": "phone", "value": t}
    # Correos
    if EMAIL_PATTERN.fullmatch(t):
        if any(k in c for k in EMAIL_CONTEXT):
            return {"field": "email", "value": t}
    # Fechas
    for pat in DATE_PATTERNS:
        if pat.fullmatch(t):
            if any(k in c for k in DATE_CONTEXT):
                return {"field": "date", "value": t}
    # Montos
    if AMOUNT_PATTERN.fullmatch(t):
        if any(k in c for k in AMOUNT_CONTEXT):
            return {"field": "amount", "value": t}
    # Identificadores
    for pat in ID_PATTERNS:
        if pat.fullmatch(t):
            if any(k in c for k in ID_CONTEXT):
                return {"field": "identifier", "value": t}
    return None


def extract_fields_from_block(text: str, context: str = "") -> Optional[Dict]:
    """
    Extrae TODOS los campos relevantes de un bloque.
    Retorna el campo de mayor score y la lista completa.
    """
    if not text or not text.strip():
        return None
    
    results = []
    ctx = context.lower() if context else text.lower()

    # Teléfonos — usar finditer (no fullmatch)
    for pat in PHONE_PATTERNS:
        for m in pat.finditer(text):
            val = m.group(0)
            digits = re.sub(r"\D", "", val)
            if 7 <= len(digits) <= 15:
                score = 2 if any(k in ctx for k in PHONE_CONTEXT) else 1
                results.append({"field": "phone", "value": val.strip(), "score": score})

    # Correos
    for m in EMAIL_PATTERN.finditer(text):
        score = 2 if any(k in ctx for k in EMAIL_CONTEXT) else 1
        results.append({"field": "email", "value": m.group(0), "score": score})

    # Fechas
    for pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            score = 2 if any(k in ctx for k in DATE_CONTEXT) else 1
            results.append({"field": "date", "value": m.group(0), "score": score})

    # Montos — require keywords cercanos o símbolo de moneda para evitar falsos positivos
    for m in AMOUNT_PATTERN.finditer(text):
        val = m.group(0)
        has_currency_symbol = bool(re.search(r"[\$€£]|COP|USD|EUR", text[max(0,m.start()-10):m.end()+5]))
        score_base = 2 if any(k in ctx for k in AMOUNT_CONTEXT) else (1 if has_currency_symbol else 0)
        if score_base > 0:
            results.append({"field": "amount", "value": val, "score": score_base})

    # Identificadores
    for pat in ID_PATTERNS:
        for m in pat.finditer(text):
            score = 2 if any(k in ctx for k in ID_CONTEXT) else 1
            results.append({"field": "identifier", "value": m.group(0), "score": score})

    # Texto libre — siempre agregar el texto del bloque como campo "text"
    clean = text.strip()
    if clean and len(clean) > 3:
        results.append({"field": "text", "value": clean, "score": 0})

    if not results:
        return None

    results = sorted(results, key=lambda x: (-x["score"]))
    main = results[0]
    return {
        "field": main["field"],
        "value": main["value"],
        "all_fields": [{"field": r["field"], "value": r["value"]} for r in results],
    }