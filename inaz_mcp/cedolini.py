"""Parsing cedolini Inaz: estrazione testo dal PDF e campi paga dal testo."""

import os
import re
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader

# I tracciati Inaz variano per azienda: per ogni campo una lista di pattern,
# vince il primo che matcha. Aggiungere qui le varianti, non nel codice.
PATTERN_NUMERICI: dict[str, list[str]] = {
    "netto": [
        r"NETTO\s+(?:IN\s+BUSTA|DEL\s+MESE|A\s+PAGARE)\s*[:€]?\s*([\d.,]+)",
    ],
    "totale_competenze": [r"TOTALE\s+COMPETENZE\s*[:€]?\s*([\d.,]+)"],
    "totale_trattenute": [r"TOTALE\s+TRATTENUTE\s*[:€]?\s*([\d.,]+)"],
}

PATTERN_TESTO: dict[str, list[str]] = {
    "periodo": [r"Periodo(?:\s+di\s+retribuzione)?\s*[:\-]?\s*([A-ZÀ-Ù]+\s+\d{4})"],
    "codice_fiscale": [r"Codice\s+Fiscale\s*[:\-]?\s*([A-Z0-9]{16})"],
    "azienda": [r"Azienda\s*[:\-]?\s*(\S.*)"],
    "dipendente": [r"Dipendente\s*[:\-]?\s*(\S.*)"],
}


def numero_italiano(testo: str) -> float | None:
    """Converte un importo in formato italiano ("1.234,56") in float."""
    testo = testo.strip()
    if not testo:
        return None
    if "," in testo:
        testo = testo.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", testo):
        # Punto come separatore migliaia senza decimali ("2.500" = 2500).
        # "1234.56" non matcha (4 cifre iniziali / .56 non è un gruppo da 3): resta decimale.
        testo = testo.replace(".", "")
    try:
        return float(testo)
    except ValueError:
        return None


def _primo_match(testo: str, pattern: list[str]) -> str | None:
    for espressione in pattern:
        trovato = re.search(espressione, testo, re.IGNORECASE)
        if trovato:
            return trovato.group(1).strip()
    return None


def analizza_cedolino(testo: str) -> dict[str, str | float | None]:
    """Estrae i campi principali dal testo di un cedolino. Campi assenti = None."""
    dati: dict[str, str | float | None] = {}
    for campo, pattern in PATTERN_TESTO.items():
        dati[campo] = _primo_match(testo, pattern)
    for campo, pattern in PATTERN_NUMERICI.items():
        grezzo = _primo_match(testo, pattern)
        dati[campo] = numero_italiano(grezzo) if grezzo else None
    return dati


@lru_cache(maxsize=256)
def _estrai_testo_pdf_cache(percorso: str, mtime_ns: int, dimensione: int) -> str:
    lettore = PdfReader(percorso)
    if lettore.is_encrypted:
        # Cedolini via email spesso protetti (di solito col codice fiscale):
        # prova la password da INAZ_PDF_PASSWORD; la stringa vuota di default
        # copre anche i PDF cifrati senza password di apertura.
        lettore.decrypt(os.environ.get("INAZ_PDF_PASSWORD", ""))
    return "\n".join(pagina.extract_text() or "" for pagina in lettore.pages)


def estrai_testo_pdf(percorso: Path | str) -> str:
    """Estrae il testo da tutte le pagine di un PDF (cache in memoria per file invariato)."""
    percorso = Path(percorso)
    stat = percorso.stat()
    return _estrai_testo_pdf_cache(str(percorso), stat.st_mtime_ns, stat.st_size)
