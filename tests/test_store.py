"""Test individuazione file dati e sicurezza percorsi."""

import pytest

from inaz_mcp.store import percorso_sicuro, trova_file


def test_trova_file_classifica_per_estensione(tmp_path):
    (tmp_path / "cedolino_marzo.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "presenze_marzo.csv").write_text("Data;Ore\n")
    (tmp_path / "note.txt").write_text("ignorami")
    trovati = trova_file(tmp_path)
    assert [p.name for p in trovati["cedolini"]] == ["cedolino_marzo.pdf"]
    assert [p.name for p in trovati["presenze"]] == ["presenze_marzo.csv"]


def test_trova_file_directory_inesistente(tmp_path):
    trovati = trova_file(tmp_path / "non_esiste")
    assert trovati == {"cedolini": [], "presenze": []}


def test_percorso_sicuro_dentro_data_dir(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4")
    assert percorso_sicuro(tmp_path, "a.pdf") == (tmp_path / "a.pdf").resolve()


def test_percorso_sicuro_blocca_traversal(tmp_path):
    with pytest.raises(ValueError):
        percorso_sicuro(tmp_path, "../fuori.pdf")


def test_percorso_sicuro_file_inesistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        percorso_sicuro(tmp_path, "manca.pdf")
