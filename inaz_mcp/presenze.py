"""Parsing export presenze/timbrature Inaz (CSV con intestazioni variabili)."""

import csv
from collections.abc import Sequence
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

# Alias di intestazione visti nei tracciati presenze: chiave normalizzata → varianti.
ALIAS_COLONNE: dict[str, tuple[str, ...]] = {
    "data": ("data", "giorno", "date"),
    "entrata": ("entrata", "ingresso", "in"),
    "uscita": ("uscita", "out"),
    "ore": ("ore", "ore lavorate", "tot ore", "durata"),
    "causale": ("causale", "giustificativo", "voce", "descrizione"),
}

FORMATI_DATA = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y")


def _mappa_intestazioni(intestazioni: Sequence[str]) -> dict[str, str]:
    """Mappa nome colonna originale → chiave normalizzata."""
    mappa = {}
    for originale in intestazioni:
        pulito = originale.strip().lower()
        for chiave, alias in ALIAS_COLONNE.items():
            if pulito in alias:
                mappa[originale] = chiave
                break
    return mappa


def normalizza_data(testo: str) -> str:
    """Porta una data in formato ISO (aaaa-mm-gg); se non riconosciuta la lascia com'è."""
    testo = testo.strip()
    for formato in FORMATI_DATA:
        try:
            return datetime.strptime(testo, formato).date().isoformat()
        except ValueError:
            continue
    return testo


def ore_in_float(testo: str) -> float | None:
    """Converte "7,5", "07:30" o "8" in ore decimali."""
    testo = testo.strip()
    if not testo:
        return None
    if ":" in testo:
        ore, _, minuti = testo.partition(":")
        try:
            return round(int(ore) + int(minuti) / 60, 2)
        except ValueError:
            return None
    try:
        return float(testo.replace(",", "."))
    except ValueError:
        return None


def _rileva_delimitatore(prima_riga: str) -> str:
    return ";" if prima_riga.count(";") >= prima_riga.count(",") else ","


@lru_cache(maxsize=256)
def _leggi_presenze_cache(percorso: str, mtime_ns: int, dimensione: int) -> list[dict[str, Any]]:
    contenuto = Path(percorso).read_text(encoding="utf-8-sig")
    righe_grezze = contenuto.splitlines()
    if not righe_grezze:
        return []
    delimitatore = _rileva_delimitatore(righe_grezze[0])
    lettore = csv.DictReader(righe_grezze, delimiter=delimitatore)
    mappa = _mappa_intestazioni(lettore.fieldnames or [])
    righe: list[dict[str, Any]] = []
    for grezza in lettore:
        riga: dict[str, Any] = {}
        for originale, chiave in mappa.items():
            valore = (grezza.get(originale) or "").strip()
            if chiave == "data":
                riga[chiave] = normalizza_data(valore)
            elif chiave == "ore":
                riga[chiave] = ore_in_float(valore)
            else:
                riga[chiave] = valore
        righe.append(riga)
    return righe


def leggi_presenze(percorso: Path | str) -> list[dict[str, Any]]:
    """Legge un CSV presenze e restituisce righe con chiavi normalizzate (cache in memoria)."""
    percorso = Path(percorso)
    stat = percorso.stat()
    righe = _leggi_presenze_cache(str(percorso), stat.st_mtime_ns, stat.st_size)
    return [dict(riga) for riga in righe]


def filtra_mese(righe: list[dict[str, Any]], mese: str | None) -> list[dict[str, Any]]:
    """Filtra le righe per mese ISO "aaaa-mm". mese=None → tutte."""
    if not mese:
        return righe
    return [riga for riga in righe if str(riga.get("data", "")).startswith(mese)]


def riepilogo(righe: list[dict[str, Any]]) -> dict[str, Any]:
    """Totale ore, giorni distinti e ore per causale."""
    per_causale: dict[str, float] = {}
    totale = 0.0
    for riga in righe:
        ore = riga.get("ore") or 0.0
        totale += ore
        causale = riga.get("causale") or "SENZA CAUSALE"
        per_causale[causale] = round(per_causale.get(causale, 0.0) + ore, 2)
    return {
        "totale_ore": round(totale, 2),
        "giorni": len({riga.get("data") for riga in righe if riga.get("data")}),
        "per_causale": per_causale,
    }
