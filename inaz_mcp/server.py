"""Server MCP Inaz: espone cedolini e presenze locali come tool per Claude."""

import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from inaz_mcp import cedolini, comandi, presenze, store

mcp = FastMCP("inaz")


def _valida_mese(mese: str | None) -> None:
    if mese and not re.fullmatch(r"\d{4}-\d{2}", mese):
        raise ValueError('Mese non valido: usare il formato "AAAA-MM", es. "2026-03"')


@mcp.tool()
def info_cartella_dati() -> dict[str, Any]:
    """Mostra la cartella dati Inaz configurata e quanti file contiene."""
    cartella = store.data_dir()
    trovati = store.trova_file(cartella)
    return {
        "cartella": str(cartella),
        "esiste": cartella.is_dir(),
        "cedolini_pdf": len(trovati["cedolini"]),
        "presenze_csv": len(trovati["presenze"]),
        "suggerimento": "Imposta INAZ_DATA_DIR per cambiare cartella"
        if not cartella.is_dir()
        else None,
    }


@mcp.tool()
def lista_cedolini() -> list[dict[str, Any]]:
    """Elenca i cedolini PDF nella cartella dati con i campi paga principali."""
    risultati = []
    for percorso in store.trova_file(store.data_dir())["cedolini"]:
        try:
            dati = cedolini.analizza_cedolino(cedolini.estrai_testo_pdf(percorso))
        except Exception as errore:  # PDF corrotto: segnala, non bloccare la lista
            dati = {"errore": f"PDF non leggibile: {errore}"}
        risultati.append({"file": percorso.name, **dati})
    return risultati


@mcp.tool()
def leggi_cedolino(nome_file: str) -> dict[str, Any]:
    """Legge un cedolino per nome file: campi estratti + testo completo."""
    percorso = store.percorso_sicuro(store.data_dir(), nome_file)
    testo = cedolini.estrai_testo_pdf(percorso)
    return {
        "file": percorso.name,
        **cedolini.analizza_cedolino(testo),
        "testo": testo,
    }


@mcp.tool()
def cerca_nei_cedolini(testo: str) -> list[dict[str, Any]]:
    """Cerca una stringa (case-insensitive) in tutti i cedolini; righe che matchano."""
    if not testo.strip():
        raise ValueError("Testo di ricerca vuoto")
    ago = testo.lower()
    risultati = []
    for percorso in store.trova_file(store.data_dir())["cedolini"]:
        try:
            contenuto = cedolini.estrai_testo_pdf(percorso)
        except Exception:
            continue
        righe = [r.strip() for r in contenuto.splitlines() if ago in r.lower()]
        if righe:
            risultati.append({"file": percorso.name, "righe": righe})
    return risultati


@mcp.tool()
def lista_presenze(mese: str | None = None) -> list[dict[str, Any]]:
    """Righe presenze da tutti i CSV, opzionalmente filtrate per mese "AAAA-MM"."""
    _valida_mese(mese)
    righe = []
    for percorso in store.trova_file(store.data_dir())["presenze"]:
        for riga in presenze.leggi_presenze(percorso):
            righe.append({"file": percorso.name, **riga})
    return presenze.filtra_mese(righe, mese)


@mcp.tool()
def riepilogo_presenze(mese: str | None = None) -> dict[str, Any]:
    """Totale ore, giorni e ore per causale, opzionalmente per mese "AAAA-MM"."""
    _valida_mese(mese)
    righe = lista_presenze(mese)
    return {"mese": mese or "tutti", **presenze.riepilogo(righe)}


# Solo i tool di sola lettura sopra: mai includere qui i tool batch/preset
# stessi, altrimenti un preset che si autorichiama va in ricorsione infinita.
_REGISTRO_TOOL: dict[str, Any] = {
    "info_cartella_dati": info_cartella_dati,
    "lista_cedolini": lista_cedolini,
    "leggi_cedolino": leggi_cedolino,
    "cerca_nei_cedolini": cerca_nei_cedolini,
    "lista_presenze": lista_presenze,
    "riepilogo_presenze": riepilogo_presenze,
}


@mcp.tool()
def esegui_comandi(comandi_richiesti: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Esegue più tool in sequenza in una sola chiamata (fa risparmiare round-trip).

    Ogni comando: {"tool": nome, "argomenti": {...}}. Un errore in un comando
    non blocca gli altri: viene riportato come {"tool": nome, "errore": ...}.
    """
    return comandi.esegui(_REGISTRO_TOOL, comandi_richiesti)


@mcp.tool()
def elenca_preset() -> dict[str, list[dict[str, Any]]]:
    """Elenca i preset salvati (combinazioni di comandi) con i loro comandi."""
    return comandi.carica_preset(store.data_dir())


@mcp.tool()
def salva_preset(
    nome: str, comandi_richiesti: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Salva (o sovrascrive) un preset: una combinazione di comandi richiamabile per nome."""
    return comandi.salva_preset(store.data_dir(), nome, comandi_richiesti, set(_REGISTRO_TOOL))


@mcp.tool()
def esegui_preset(nome: str) -> list[dict[str, Any]]:
    """Esegue i comandi di un preset salvato per nome."""
    preset = comandi.carica_preset(store.data_dir())
    if nome not in preset:
        raise ValueError(f"Preset non trovato: {nome}")
    return comandi.esegui(_REGISTRO_TOOL, preset[nome])


def main() -> None:  # pragma: no cover - avvio stdio bloccante, coperto dallo smoke test JSON-RPC
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
