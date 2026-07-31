"""Test parsing cedolini Inaz (testo estratto da PDF)."""

from inaz_mcp.cedolini import analizza_cedolino, estrai_testo_pdf, numero_italiano

TESTO_CEDOLINO = """
INAZ SRL - PROSPETTO PAGA
Azienda: ESEMPIO COSTRUZIONI SPA
Dipendente: ROSSI MARIO
Codice Fiscale: RSSMRA80A01H501U
Periodo di retribuzione: MARZO 2026
TOTALE COMPETENZE 1.850,00
TOTALE TRATTENUTE 415,32
NETTO IN BUSTA 1.434,68
"""


def test_estrae_netto():
    dati = analizza_cedolino(TESTO_CEDOLINO)
    assert dati["netto"] == 1434.68


def test_estrae_periodo():
    dati = analizza_cedolino(TESTO_CEDOLINO)
    assert dati["periodo"] == "MARZO 2026"


def test_estrae_competenze_e_trattenute():
    dati = analizza_cedolino(TESTO_CEDOLINO)
    assert dati["totale_competenze"] == 1850.00
    assert dati["totale_trattenute"] == 415.32


def test_estrae_codice_fiscale():
    dati = analizza_cedolino(TESTO_CEDOLINO)
    assert dati["codice_fiscale"] == "RSSMRA80A01H501U"


def test_campi_mancanti_sono_none():
    dati = analizza_cedolino("testo qualunque senza campi paga")
    assert dati["netto"] is None
    assert dati["periodo"] is None


def test_variante_netto_del_mese():
    dati = analizza_cedolino("NETTO DEL MESE 987,65")
    assert dati["netto"] == 987.65


def test_numero_italiano():
    assert numero_italiano("1.234,56") == 1234.56
    assert numero_italiano("415,32") == 415.32
    assert numero_italiano("1234.56") == 1234.56
    assert numero_italiano("2.500") == 2500.0  # punto = migliaia, nessun decimale
    assert numero_italiano("12.345.678") == 12345678.0
    assert numero_italiano("") is None
    assert numero_italiano("abc") is None


def test_estrai_testo_pdf(tmp_path):
    from conftest import pdf_minimo

    percorso = tmp_path / "cedolino.pdf"
    percorso.write_bytes(pdf_minimo("NETTO IN BUSTA 1.434,68"))
    testo = estrai_testo_pdf(percorso)
    assert "NETTO IN BUSTA" in testo


def test_estrai_testo_pdf_cache_invalidata_da_modifica(tmp_path):
    from conftest import pdf_minimo

    percorso = tmp_path / "cedolino.pdf"
    percorso.write_bytes(pdf_minimo("NETTO IN BUSTA 100,00"))
    primo = estrai_testo_pdf(percorso)
    assert "100,00" in primo

    percorso.write_bytes(pdf_minimo("NETTO IN BUSTA 999,99 DIVERSO"))
    secondo = estrai_testo_pdf(percorso)
    assert "999,99" in secondo
    assert secondo != primo
