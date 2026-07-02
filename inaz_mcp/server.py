"""Server MCP Inaz: espone cedolini e presenze locali come tool per Claude."""

import re

from mcp.server.fastmcp import FastMCP

from inaz_mcp import cedolini, presenze, store

mcp = FastMCP("inaz")


def _valida_mese(mese: str | None) -> None:
    if mese and not re.fullmatch(r"\d{4}-\d{2}", mese):
        raise ValueError('Mese non valido: usare il formato "AAAA-MM", es. "2026-03"')


@mcp.tool()
def info_cartella_dati() -> dict:
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
def lista_cedolini() -> list[dict]:
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
def leggi_cedolino(nome_file: str) -> dict:
    """Legge un cedolino per nome file: campi estratti + testo completo."""
    percorso = store.percorso_sicuro(store.data_dir(), nome_file)
    testo = cedolini.estrai_testo_pdf(percorso)
    return {
        "file": percorso.name,
        **cedolini.analizza_cedolino(testo),
        "testo": testo,
    }


@mcp.tool()
def cerca_nei_cedolini(testo: str) -> list[dict]:
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
def lista_presenze(mese: str | None = None) -> list[dict]:
    """Righe presenze da tutti i CSV, opzionalmente filtrate per mese "AAAA-MM"."""
    _valida_mese(mese)
    righe = []
    for percorso in store.trova_file(store.data_dir())["presenze"]:
        for riga in presenze.leggi_presenze(percorso):
            righe.append({"file": percorso.name, **riga})
    return presenze.filtra_mese(righe, mese)


@mcp.tool()
def riepilogo_presenze(mese: str | None = None) -> dict:
    """Totale ore, giorni e ore per causale, opzionalmente per mese "AAAA-MM"."""
    _valida_mese(mese)
    righe = lista_presenze(mese)
    return {"mese": mese or "tutti", **presenze.riepilogo(righe)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
