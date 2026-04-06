# src/semantic/field_extraction.py
"""
Field extraction improved:
- mantiene la salida original: list of {"field","value","page","bbox","context"}
- añade más reglas regex (dates en varios formatos, phone, currency, url)
- soporta idiomas: 'en', 'es' (spaCy carga modelos por idioma si están disponibles)
- combina regex + spaCy NER y evita duplicados
"""

import re
import warnings
from typing import Iterable, List, Dict, Tuple, Optional

# Optional dependencies (silenciosas si no están presentes)
try:
    import spacy
except Exception:
    spacy = None


# Default regex rules (language-agnostic or language-specific keys)
_DEFAULT_REGEX = [
    # ISO date (YYYY-MM-DD)
    ("date_iso", r"\b\d{4}-\d{2}-\d{2}\b"),
    # common european date (DD/MM/YYYY or D/M/YY)
    ("date_ddmm", r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b"),
    # email
    ("email", r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    # phone Colombia (3xx xxx xxxx, +57)
    ("phone_col", r"(?:\+57)?\s?3\d{2}[\s-]?\d{3}[\s-]?\d{4}"),
    # phone USA (xxx-xxx-xxxx, (xxx) xxx-xxxx, +1)
    ("phone_usa", r"(?:\+1)?\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}"),
    # NIT Colombia (xx.xxx.xxx-x)
    ("nit_col", r"\b\d{1,3}\.?\d{3}\.?\d{3}-\d{1}\b"),
    # SSN USA (xxx-xx-xxxx)
    ("ssn_usa", r"\b\d{3}-\d{2}-\d{4}\b"),
    # ID Colombia (cédula, pasaporte, etc.)
    ("id_col", r"\b\d{6,10}\b"),
    # Nombre propio (mayúscula inicial, dos palabras mín.)
    ("name", r"\b[A-ZÁÉÍÓÚ][a-záéíóú]+\s+[A-ZÁÉÍÓÚ][a-záéíóú]+\b"),
    # currency (USD/EUR symbol + numbers)
    ("currency", r"(?:(?:USD|\$)|(?:EUR|€))\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?"),
    # URL
    ("url", r"https?://[^\s,;]+"),
]


# Mapping language codes to spaCy model names
_SPACY_MODEL_MAP = {
    "en": "en_core_web_sm",
    "es": "es_core_news_sm",
}


class FieldExtractor:
    def normalize_field(self, name: str, value: str) -> str:
        """Normaliza el valor extraído según el tipo de campo."""
        if name.startswith("date"):
            # Normalizar fechas a YYYY-MM-DD si es posible
            import dateutil.parser
            try:
                dt = dateutil.parser.parse(value, dayfirst=True, yearfirst=False)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return value
        if name in ("phone_col", "phone_usa", "phone"):
            # Solo dígitos, formato internacional
            digits = re.sub(r"\D", "", value)
            if len(digits) == 10:
                return f"+57 {digits[:3]} {digits[3:6]} {digits[6:]}"
            if len(digits) == 11 and digits.startswith("1"):
                return f"+1 {digits[1:4]} {digits[4:7]} {digits[7:]}"
            return digits
        if name == "nit_col":
            # Formato estándar NIT
            return value.replace(".", "").replace(" ", "")
        if name == "ssn_usa":
            return value.replace(" ", "")
        if name == "email":
            return value.lower()
        return value
    def __init__(
        self,
        regex_rules: Optional[Iterable[Tuple[str, str]]] = None,
        languages: Iterable[str] = ("en",),
        use_spacy: bool = True,
    ):
        """
        Args:
            regex_rules: optional list of (name, pattern) to override defaults.
            languages: iterable of language codes to consider (e.g. ("en","es")).
            use_spacy: try to use spaCy NER models if available.
        """
        # compile regex rules (user rules override defaults if provided)
        rules = list(regex_rules) if regex_rules is not None else _DEFAULT_REGEX
        self.compiled_rules = [(name, re.compile(pattern, flags=re.IGNORECASE)) for name, pattern in rules]

        # languages handling
        self.languages = list(languages) if isinstance(languages, (list, tuple)) else [languages]

        # spaCy models per language (lazy load attempted here)
        self.nlp_models = {}
        if use_spacy and spacy is not None:
            for lang in self.languages:
                model_name = _SPACY_MODEL_MAP.get(lang)
                if model_name is None:
                    warnings.warn(f"No spaCy model mapping for language '{lang}', skipping spaCy for this lang.")
                    continue
                try:
                    # try load; if not installed, skip with warning
                    self.nlp_models[lang] = spacy.load(model_name)
                except Exception as e:
                    warnings.warn(
                        f"spaCy model '{model_name}' for lang '{lang}' could not be loaded: {e}. "
                        "NER will be skipped for this language."
                    )
        else:
            if use_spacy and spacy is None:
                warnings.warn("spaCy not installed; NER will be disabled.")

    def add_regex_rule(self, name: str, pattern: str):
        """Add a custom regex rule at runtime."""
        self.compiled_rules.append((name, re.compile(pattern, flags=re.IGNORECASE)))

    def extract(self, pages: List[Dict]) -> List[Dict]:
        """
        Extract fields from pages.

        Input:
            pages: list of pages with 'page_number' and 'blocks' where each block has 'text' and 'bbox'

        Output:
            list of dicts: {"field": name, "value": str, "page": int, "bbox": [..], "context": str}
        """
        results: List[Dict] = []
        seen = set()  # dedupe by (field, value, page)

        for p in pages:
            page_num = p.get("page_number", p.get("page", None))
            for b in p.get("blocks", []):
                txt = (b.get("text") or "").strip()
                if not txt:
                    continue

                # 1) Regex-based extraction (high precision)
                for name, pattern in self.compiled_rules:
                    for m in pattern.finditer(txt):
                        value = m.group().strip()
                        norm_value = self.normalize_field(name, value)
                        key = (name, norm_value, page_num)
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append({
                            "field": name,
                            "value": norm_value,
                            "page": page_num,
                            "bbox": b.get("bbox"),
                            "context": txt,
                        })

                # 2) spaCy NER (if models available for any configured language)
                for lang, nlp in self.nlp_models.items():
                    try:
                        doc = nlp(txt)
                    except Exception:
                        continue
                    for ent in doc.ents:
                        field = ent.label_
                        value = ent.text.strip()
                        norm_value = self.normalize_field(field, value)
                        key = (field, norm_value, page_num)
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append({
                            "field": field,
                            "value": norm_value,
                            "page": page_num,
                            "bbox": b.get("bbox"),
                            "context": txt,
                        })

        return results
