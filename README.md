# inaz-mcp

[![ci](https://github.com/thousandflowers/inaz-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/thousandflowers/inaz-mcp/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Server MCP per interrogare da Claude i tuoi export **Inaz** (il gestionale HR: cedolini, presenze).

Inaz non espone API pubbliche: l'integrazione ufficiale avviene via file. Questo server rende interrogabili i file che scarichi dal portale HR:

- **Cedolini PDF** → estrazione automatica di netto, competenze, trattenute, periodo, codice fiscale
- **Presenze/timbrature CSV** → righe normalizzate, filtri per mese, riepiloghi ore per causale

## Requisiti

- Python ≥ 3.11 e [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone https://github.com/thousandflowers/inaz-mcp
cd inaz-mcp
uv sync
```

Metti i file scaricati da Inaz in `~/Documents/Inaz` (o imposta `INAZ_DATA_DIR`).

## Registrazione in Claude Code

```bash
claude mcp add --scope user inaz -- uv --directory ~/Desktop/inaz-mcp run inaz-mcp
```

## Registrazione in Claude Desktop

In `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "inaz": {
      "command": "uv",
      "args": ["--directory", "/Users/TUO_UTENTE/Desktop/inaz-mcp", "run", "inaz-mcp"],
      "env": { "INAZ_DATA_DIR": "/Users/TUO_UTENTE/Documents/Inaz" }
    }
  }
}
```

## Tool esposti

| Tool | Cosa fa |
|------|---------|
| `info_cartella_dati` | Cartella configurata e conteggio file |
| `lista_cedolini` | Tutti i cedolini PDF con campi paga estratti |
| `leggi_cedolino(nome_file)` | Campi + testo completo di un cedolino |
| `cerca_nei_cedolini(testo)` | Ricerca full-text in tutti i cedolini |
| `lista_presenze(mese?)` | Righe presenze, filtro `"AAAA-MM"` opzionale |
| `riepilogo_presenze(mese?)` | Totale ore, giorni, ore per causale |

Esempi di domande a Claude: *"quanto ho preso netto a marzo?"*, *"quante ore di permesso ho fatto quest'anno?"*, *"confronta le trattenute degli ultimi tre cedolini"*.

## Formati supportati

I tracciati Inaz variano per azienda. Il parsing è guidato da tabelle di pattern:

- `inaz_mcp/cedolini.py` → `PATTERN_NUMERICI` / `PATTERN_TESTO` (regex per campo, vince il primo match)
- `inaz_mcp/presenze.py` → `ALIAS_COLONNE` (varianti di intestazione CSV), `FORMATI_DATA`

Se il tuo export usa etichette diverse, aggiungi la variante alla tabella: nessuna modifica al codice.

## Sviluppo

```bash
uv run pytest --cov=inaz_mcp --cov-report=term-missing  # 32 test, copertura 100%
uv run ruff check .                                       # lint
uv run ruff format .                                      # formattazione
uv run mypy inaz_mcp                                      # type check (strict)
```

CI su GitHub Actions esegue tutti e quattro su Python 3.11/3.12/3.13 a ogni push.

## Privacy

Tutto gira in locale: nessun dato lascia il tuo Mac. I cedolini contengono dati personali — la cartella dati resta fuori dal repository.

## Licenza

[MIT](LICENSE)
