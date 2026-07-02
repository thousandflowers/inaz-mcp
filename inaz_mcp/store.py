"""Individuazione dei file dati Inaz nella cartella configurata."""

import os
from pathlib import Path

DATA_DIR_DEFAULT = Path.home() / "Documents" / "Inaz"


def data_dir() -> Path:
    """Cartella dati: $INAZ_DATA_DIR se impostata, altrimenti ~/Documents/Inaz."""
    return Path(os.environ.get("INAZ_DATA_DIR", DATA_DIR_DEFAULT)).expanduser()


def trova_file(cartella: Path | str) -> dict[str, list[Path]]:
    """Classifica i file della cartella (ricorsivo): PDF = cedolini, CSV = presenze."""
    cartella = Path(cartella)
    if not cartella.is_dir():
        return {"cedolini": [], "presenze": []}
    return {
        "cedolini": sorted(cartella.rglob("*.pdf")),
        "presenze": sorted(cartella.rglob("*.csv")),
    }


def percorso_sicuro(base: Path | str, nome_file: str) -> Path:
    """Risolve nome_file dentro base; blocca path traversal e file inesistenti."""
    base = Path(base).resolve()
    candidato = (base / nome_file).resolve()
    if not candidato.is_relative_to(base):
        raise ValueError(f"Percorso non consentito: {nome_file}")
    if not candidato.is_file():
        raise FileNotFoundError(f"File non trovato nella cartella dati: {nome_file}")
    return candidato
