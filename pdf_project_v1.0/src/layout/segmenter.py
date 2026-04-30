"""Layout segmenter mejorado: menos heurístico, mismo resultado.
Devuelve para cada bloque: block["type"], block["confidence"]
Tipos: "title", "table", "figure", "paragraph"
"""

from typing import List, Dict
import math
import re
from collections import Counter
from statistics import median

# Umbrales por defecto (ajustables)
DEFAULTS = {
    "title_size_z": 1.0,        # z-score mínimo para considerar título por tamaño
    "title_short_words": 10,    # nº de palabras máximo probable en título
    "uppercase_ratio": 0.6,     # ratio de mayúsculas para considerar título
    "table_column_consistency": 0.7,  # fracción de líneas con mismo nº de columnas
    "figure_word_max": 6,       # palabras máximas para considerar figura
    "min_lines_for_table": 2,   # mín líneas para chequear tabla
}


def _safe_split_cols(line: str):
    """Intento robusto de contar columnas en una línea de 'tabla'."""
    # Si hay separadores explícitos
    if "|" in line:
        return [c.strip() for c in line.split("|") if c.strip() != ""]
    if "\t" in line:
        return [c.strip() for c in line.split("\t") if c.strip() != ""]
    # fallback: columnas por espacios múltiples (asume separadores por padding)
    cols = re.split(r"\s{2,}", line.strip())
    return [c for c in cols if c != ""]


def _uppercase_ratio(text: str) -> float:
    letters = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]", text)
    if not letters:
        return 0.0
    up = sum(1 for ch in letters if ch.isupper())
    return up / len(letters)


def _word_density(text: str) -> float:
    words = re.findall(r"\w+", text)
    chars = len(text.strip())
    if chars == 0:
        return 0.0
    return len(words) / chars


def _table_score(text: str, defaults=DEFAULTS) -> float:
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < defaults["min_lines_for_table"]:
        return 0.0
    col_counts = []
    sep_present = False
    for l in lines:
        if "|" in l or "\t" in l:
            sep_present = True
        cols = _safe_split_cols(l)
        col_counts.append(len(cols))
    if not col_counts:
        return 0.0
    # Si hay separadores explícitos, meter más peso
    if sep_present:
        # si la mayoría de líneas tienen >1 columna → fuerte señal de tabla
        fraction_multi = sum(1 for c in col_counts if c > 1) / len(col_counts)
        return 0.9 * fraction_multi
    # Si no hay separadores, chequear consistencia de número de columnas
    cnt = Counter(col_counts)
    most_common_count, freq = cnt.most_common(1)[0]
    consistency = freq / len(col_counts)
    # penaliza si la mayoría son 1 columna
    if most_common_count <= 1:
        return 0.0
    return 0.8 * consistency


def _title_score(block: Dict, page_stats: Dict, defaults=DEFAULTS) -> float:
    """Devuelve score (0..1) para ser título basándose en varias features."""
    text = (block.get("text") or "").strip()
    if not text:
        return 0.0

    # ❌ párrafos largos nunca son títulos
    if len(text.split()) > 15:
        return 0.0

    # 1) tamaño relativo de fuente -> z-score sobre la mediana de la página
    fs = block.get("font_size")

    median_font = page_stats.get("median_font")
    if not fs or not median_font or fs <= median_font:
        return 0.0
    
    size_score = 0.0

    if fs and page_stats.get("median_font"):
        med = page_stats["median_font"]
        mad = page_stats.get("mad_font", 1.0)
        z = (fs - med) / mad if mad > 0 else 0.0
        # mapear z a [0,1] suavemente
        size_score = 1.0 / (1.0 + math.exp(-(z - defaults["title_size_z"])))
    # 2) short & uppercase
    words = text.split()
    shortness = 1.0 if len(words) <= defaults["title_short_words"] else 0.0
    up_ratio = _uppercase_ratio(text)
    uppercase_score = 1.0 if up_ratio >= defaults["uppercase_ratio"] else up_ratio * 0.8
    # 3) punctuation / colon patterns (e.g., "INTRODUCTION", "CHAPTER 1", "1. INTRO...")
    punct_score = 0.0
    if re.match(r"^[0-9IVX]+\.\s+", text) or re.match(r"^[A-Z\s0-9\-:]{4,}$", text) and len(words) <= defaults["title_short_words"]:
        punct_score = 0.9

    # combinar features con pesos (tuneables)
    score = 0.5 * size_score + 0.25 * shortness + 0.15 * uppercase_score + 0.1 * punct_score
    return min(1.0, max(0.0, score))


def _figure_score(block: Dict, defaults=DEFAULTS) -> float:
    text = (block.get("text") or "").strip()
    if not text:
        return 0.0
    words = text.split()
    # si tiene la palabra fig/figure o "Fig." fuerte señal
    if re.search(r"\bfig(ure)?\.?\b", text, flags=re.IGNORECASE):
        return 0.95
    # si es extremadamente corto y no alfanumérico, o muy baja densidad
    if len(words) <= defaults["figure_word_max"] and _word_density(text) < 0.12:
        return 0.6
    return 0.0


def _confidence_from_score(score: float, base=0.6, scale=0.4) -> float:
    """Mapeo simple score->confidence dentro de [base, base+scale]."""
    return round(min(base + scale * score, 0.99), 3)


class LayoutSegmenter:
    def __init__(self, defaults: Dict = None):
        self.defaults = DEFAULTS.copy()
        if defaults:
            self.defaults.update(defaults)

    def analyze(self, pages: List[Dict]) -> List[Dict]:
        """
        pages: lista de páginas con estructura:
          {"page_number": int, "blocks": [{"text": str, "bbox": [...], "font_size": float (opt)}]}
        Devuelve las mismas pages con block["type"] y block["confidence"] añadidos.
        """
        # compute per-page stats first (median font size, mad)
        page_stats_map = {}
        for p in pages:
            font_sizes = [b.get("font_size") for b in p.get("blocks", []) if b.get("font_size")]
            if font_sizes:
                med = median(font_sizes)
                # MAD approximate (median absolute deviation)
                abs_dev = [abs(s - med) for s in font_sizes]
                mad = median(abs_dev) if abs_dev else 1.0
                page_stats_map[p.get("page_number")] = {"median_font": med, "mad_font": mad or 1.0}
            else:
                page_stats_map[p.get("page_number")] = {"median_font": None, "mad_font": 1.0}

        # ahora clasificamos cada bloque con scoring
        for p in pages:
            stats = page_stats_map.get(p.get("page_number"), {})
            for b in p.get("blocks", []):
                t = "paragraph"
                conf = 0.7

                # compute scores
                title_s = _title_score(b, stats, self.defaults)
                table_s = _table_score(b.get("text", ""), self.defaults)
                figure_s = _figure_score(b, self.defaults)

                # decidir por máximo score — pero con umbrales suaves
                scores = {"title": title_s, "table": table_s, "figure": figure_s}
                best_type, best_score = max(scores.items(), key=lambda kv: kv[1])

                # reglas adicionales: si el bloque tiene muy poco texto, penalizar título/tabla
                text_len = len((b.get("text") or "").strip())
                if text_len < 3 and best_type == "title":
                    best_type = "figure"
                    best_score = max(best_score, 0.4)

                # Asignar tipo y confianza mapeada
                t = best_type if best_score > 0.05 else "paragraph"
                conf = _confidence_from_score(best_score)

                # fallback para tablas: si heurística de tablas débil, permitir caso clásico
                if t == "paragraph" and table_s > 0.6:
                    t = "table"
                    conf = _confidence_from_score(table_s)

                b["type"] = t
                b["confidence"] = conf

        return pages
