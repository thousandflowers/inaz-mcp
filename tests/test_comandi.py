"""Test esecuzione batch e preset di comandi."""

import pytest

from inaz_mcp.comandi import carica_preset, esegui, salva_preset


def _somma(a, b):
    return a + b


REGISTRO = {"somma": _somma}


def test_esegui_esegue_in_ordine_e_riporta_risultati():
    risultati = esegui(
        REGISTRO,
        [
            {"tool": "somma", "argomenti": {"a": 1, "b": 2}},
            {"tool": "somma", "argomenti": {"a": 10, "b": 5}},
        ],
    )
    assert [r["risultato"] for r in risultati] == [3, 15]


def test_esegui_tool_sconosciuto_non_blocca_gli_altri():
    risultati = esegui(
        REGISTRO,
        [
            {"tool": "non_esiste", "argomenti": {}},
            {"tool": "somma", "argomenti": {"a": 1, "b": 1}},
        ],
    )
    assert "errore" in risultati[0]
    assert risultati[1]["risultato"] == 2


def test_esegui_argomenti_sbagliati_riporta_errore():
    risultati = esegui(REGISTRO, [{"tool": "somma", "argomenti": {"a": 1}}])
    assert "errore" in risultati[0]


def test_carica_preset_assente(tmp_path):
    assert carica_preset(tmp_path) == {}


def test_salva_e_carica_preset(tmp_path):
    comandi_preset = [{"tool": "somma", "argomenti": {"a": 1, "b": 2}}]
    salva_preset(tmp_path, "prova", comandi_preset, {"somma"})
    assert carica_preset(tmp_path) == {"prova": comandi_preset}


def test_salva_preset_tool_sconosciuto_solleva_errore(tmp_path):
    with pytest.raises(ValueError):
        salva_preset(tmp_path, "prova", [{"tool": "boh", "argomenti": {}}], {"somma"})


def test_carica_preset_file_corrotto(tmp_path):
    (tmp_path / "presets.json").write_text("non json valido", encoding="utf-8")
    assert carica_preset(tmp_path) == {}
