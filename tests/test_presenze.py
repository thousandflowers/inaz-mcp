"""Test parsing export presenze/timbrature Inaz (CSV)."""

from inaz_mcp.presenze import (
    filtra_mese,
    leggi_presenze,
    normalizza_data,
    ore_in_float,
    riepilogo,
)

CSV_STANDARD = """Data;Entrata;Uscita;Ore;Causale
02/03/2026;09:00;17:30;7,5;ORDINARIO
03/03/2026;09:00;13:00;4,0;PERMESSO
"""

CSV_ALIAS = """GIORNO,INGRESSO,USCITA,ORE LAVORATE,GIUSTIFICATIVO
2026-03-02,08:30,17:00,07:30,ORD
"""


def _scrivi(tmp_path, nome, contenuto):
    percorso = tmp_path / nome
    percorso.write_text(contenuto, encoding="utf-8")
    return percorso


def test_intestazioni_standard(tmp_path):
    righe = leggi_presenze(_scrivi(tmp_path, "p.csv", CSV_STANDARD))
    assert len(righe) == 2
    assert righe[0]["data"] == "2026-03-02"
    assert righe[0]["entrata"] == "09:00"
    assert righe[0]["ore"] == 7.5
    assert righe[0]["causale"] == "ORDINARIO"


def test_intestazioni_alias_e_virgola(tmp_path):
    righe = leggi_presenze(_scrivi(tmp_path, "p.csv", CSV_ALIAS))
    assert len(righe) == 1
    assert righe[0]["data"] == "2026-03-02"
    assert righe[0]["ore"] == 7.5
    assert righe[0]["causale"] == "ORD"


def test_ore_in_float():
    assert ore_in_float("7,5") == 7.5
    assert ore_in_float("07:30") == 7.5
    assert ore_in_float("8") == 8.0
    assert ore_in_float("") is None
    assert ore_in_float("abc") is None
    assert ore_in_float("aa:bb") is None


def test_data_non_riconosciuta_resta_invariata():
    assert normalizza_data("marzo boh") == "marzo boh"


def test_csv_vuoto(tmp_path):
    assert leggi_presenze(_scrivi(tmp_path, "vuoto.csv", "")) == []


def test_leggi_presenze_cache_invalidata_da_modifica(tmp_path):
    percorso = _scrivi(tmp_path, "p.csv", CSV_STANDARD)
    assert len(leggi_presenze(percorso)) == 2

    percorso.write_text("Data;Ore\n01/01/2026;1\n02/01/2026;2\n03/01/2026;3\n", encoding="utf-8")
    assert len(leggi_presenze(percorso)) == 3


def test_leggi_presenze_righe_sono_copie_indipendenti(tmp_path):
    percorso = _scrivi(tmp_path, "p.csv", CSV_STANDARD)
    righe = leggi_presenze(percorso)
    righe[0]["causale"] = "MODIFICATO"
    assert leggi_presenze(percorso)[0]["causale"] != "MODIFICATO"


def test_filtra_mese():
    righe = [{"data": "2026-03-02"}, {"data": "2026-04-01"}]
    assert filtra_mese(righe, "2026-03") == [{"data": "2026-03-02"}]
    assert filtra_mese(righe, None) == righe


def test_riepilogo():
    righe = [
        {"data": "2026-03-02", "ore": 7.5, "causale": "ORDINARIO"},
        {"data": "2026-03-03", "ore": 4.0, "causale": "PERMESSO"},
        {"data": "2026-03-03", "ore": 3.5, "causale": "ORDINARIO"},
    ]
    totali = riepilogo(righe)
    assert totali["totale_ore"] == 15.0
    assert totali["giorni"] == 2
    assert totali["per_causale"] == {"ORDINARIO": 11.0, "PERMESSO": 4.0}
