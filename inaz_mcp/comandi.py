"""Esecuzione di comandi in batch e preset di comandi salvati su file.

Un comando è {"tool": nome_tool, "argomenti": {...}}. Un preset è un elenco di
comandi salvato con un nome in presets.json, dentro la cartella dati.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

NOME_FILE_PRESET = "presets.json"


def esegui(
    registro: dict[str, Callable[..., Any]], comandi: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Esegue in sequenza i comandi; un errore in uno non blocca gli altri."""
    risultati = []
    for comando in comandi:
        nome = comando.get("tool", "")
        argomenti = comando.get("argomenti") or {}
        funzione = registro.get(nome)
        if funzione is None:
            risultati.append({"tool": nome, "errore": f"Tool sconosciuto: {nome}"})
            continue
        try:
            risultati.append({"tool": nome, "risultato": funzione(**argomenti)})
        except Exception as errore:
            risultati.append({"tool": nome, "errore": str(errore)})
    return risultati


def _percorso_preset(cartella_dati: Path) -> Path:
    return cartella_dati / NOME_FILE_PRESET


def carica_preset(cartella_dati: Path) -> dict[str, list[dict[str, Any]]]:
    """Carica i preset salvati; file assente o corrotto → nessun preset."""
    percorso = _percorso_preset(cartella_dati)
    if not percorso.is_file():
        return {}
    try:
        dati: dict[str, list[dict[str, Any]]] = json.loads(percorso.read_text(encoding="utf-8"))
        return dati
    except json.JSONDecodeError:
        return {}


def salva_preset(
    cartella_dati: Path,
    nome: str,
    comandi: list[dict[str, Any]],
    nomi_tool_validi: set[str],
) -> dict[str, list[dict[str, Any]]]:
    """Valida e salva un preset (sovrascrive se il nome esiste già)."""
    for comando in comandi:
        nome_tool = comando.get("tool")
        if nome_tool not in nomi_tool_validi:
            raise ValueError(f"Tool sconosciuto nel preset: {nome_tool}")
    preset = carica_preset(cartella_dati)
    preset[nome] = comandi
    cartella_dati.mkdir(parents=True, exist_ok=True)
    _percorso_preset(cartella_dati).write_text(
        json.dumps(preset, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return preset
