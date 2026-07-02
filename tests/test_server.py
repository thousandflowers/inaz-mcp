"""Test dei tool MCP: chiamano le funzioni registrate su una cartella dati finta."""

import pytest
from conftest import pdf_minimo

from inaz_mcp import server

CSV_PRESENZE = """Data;Entrata;Uscita;Ore;Causale
02/03/2026;09:00;17:30;7,5;ORDINARIO
01/04/2026;09:00;13:00;4,0;PERMESSO
"""


@pytest.fixture
def cartella_dati(tmp_path, monkeypatch):
    (tmp_path / "cedolino_2026_03.pdf").write_bytes(
        pdf_minimo("NETTO IN BUSTA 1.434,68")
    )
    (tmp_path / "presenze.csv").write_text(CSV_PRESENZE, encoding="utf-8")
    monkeypatch.setenv("INAZ_DATA_DIR", str(tmp_path))
    return tmp_path


def test_info_cartella_dati(cartella_dati):
    info = server.info_cartella_dati()
    assert info["esiste"] is True
    assert info["cedolini_pdf"] == 1
    assert info["presenze_csv"] == 1


def test_info_cartella_inesistente(tmp_path, monkeypatch):
    monkeypatch.setenv("INAZ_DATA_DIR", str(tmp_path / "vuota"))
    info = server.info_cartella_dati()
    assert info["esiste"] is False
    assert info["suggerimento"] is not None


def test_lista_cedolini(cartella_dati):
    elenco = server.lista_cedolini()
    assert len(elenco) == 1
    assert elenco[0]["file"] == "cedolino_2026_03.pdf"
    assert elenco[0]["netto"] == 1434.68


def test_leggi_cedolino(cartella_dati):
    dati = server.leggi_cedolino("cedolino_2026_03.pdf")
    assert dati["netto"] == 1434.68
    assert "NETTO IN BUSTA" in dati["testo"]


def test_leggi_cedolino_blocca_traversal(cartella_dati):
    with pytest.raises(ValueError):
        server.leggi_cedolino("../../etc/passwd")


def test_cerca_nei_cedolini(cartella_dati):
    trovati = server.cerca_nei_cedolini("netto")
    assert len(trovati) == 1
    assert trovati[0]["righe"] == ["NETTO IN BUSTA 1.434,68"]


def test_cerca_testo_vuoto(cartella_dati):
    with pytest.raises(ValueError):
        server.cerca_nei_cedolini("   ")


def test_lista_presenze_filtro_mese(cartella_dati):
    tutte = server.lista_presenze()
    assert len(tutte) == 2
    marzo = server.lista_presenze("2026-03")
    assert len(marzo) == 1
    assert marzo[0]["causale"] == "ORDINARIO"


def test_lista_presenze_mese_non_valido(cartella_dati):
    with pytest.raises(ValueError):
        server.lista_presenze("marzo")


def test_pdf_corrotto_non_blocca(cartella_dati):
    (cartella_dati / "rotto.pdf").write_bytes(b"non sono un pdf")
    elenco = server.lista_cedolini()
    rotto = next(voce for voce in elenco if voce["file"] == "rotto.pdf")
    assert "errore" in rotto
    trovati = server.cerca_nei_cedolini("netto")
    assert [voce["file"] for voce in trovati] == ["cedolino_2026_03.pdf"]


def test_riepilogo_presenze(cartella_dati):
    totali = server.riepilogo_presenze()
    assert totali["totale_ore"] == 11.5
    assert totali["per_causale"] == {"ORDINARIO": 7.5, "PERMESSO": 4.0}
