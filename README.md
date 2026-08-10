# inaz-mcp

> ⚠️ Alpha — in active development. Not ready for daily use yet.

[![ci](https://github.com/thousandflowers/inaz-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/thousandflowers/inaz-mcp/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An MCP server that lets Claude query your **Inaz** exports (Inaz is an Italian HR platform: payslips, attendance records).

Inaz exposes no public API — the official integration path is file-based. This server makes the files you download from the HR portal queryable:

- **Payslip PDFs** → automatic extraction of net pay, earnings, deductions, pay period, tax code
- **Attendance/clock-in CSVs** → normalised rows, per-month filters, hour totals by category (if the Hours column is missing, hours are computed from clock-in/clock-out)

## Requirements

- Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone https://github.com/thousandflowers/inaz-mcp
cd inaz-mcp
uv sync
```

Put the files you downloaded from Inaz in `~/Documents/Inaz` (or set `INAZ_DATA_DIR`). Subfolders are fine: the scan is recursive and files are addressed by their relative path (e.g. `2026/marzo.pdf`).

If your payslips are **password-protected** PDFs (common for the ones sent by email, often protected with your tax code), set `INAZ_PDF_PASSWORD`.

## Registering with Claude Code

```bash
claude mcp add --scope user inaz -- uv --directory ~/Desktop/inaz-mcp run inaz-mcp
```

## Registering with Claude Desktop

In `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "inaz": {
      "command": "uv",
      "args": ["--directory", "/Users/YOUR_USER/Desktop/inaz-mcp", "run", "inaz-mcp"],
      "env": { "INAZ_DATA_DIR": "/Users/YOUR_USER/Documents/Inaz" }
    }
  }
}
```

## Exposed tools

Tool names are the actual API and stay in Italian, matching the implementation.

| Tool | What it does |
|------|--------------|
| `info_cartella_dati` | Configured data folder and file count |
| `lista_cedolini` | All payslip PDFs with the extracted pay fields |
| `leggi_cedolino(nome_file)` | Fields plus full text of a single payslip |
| `cerca_nei_cedolini(testo)` | Full-text search across all payslips |
| `lista_presenze(mese?)` | Attendance rows, optional `"YYYY-MM"` filter |
| `riepilogo_presenze(mese?)` | Total hours, days, hours by category |
| `esegui_comandi(comandi)` | Runs several tools in sequence in a single call |
| `salva_preset(nome, comandi)` | Saves a combination of commands, recallable by name |
| `elenca_preset` | Lists the saved presets |
| `esegui_preset(nome)` | Runs the commands of a saved preset |

Example questions to ask Claude: *"what was my net pay in March?"*, *"how many hours of leave have I taken this year?"*, *"compare the deductions on my last three payslips"*.

## Batch commands and presets

`esegui_comandi` takes a list of `{"tool": name, "argomenti": {...}}` and runs it all in a single call (fewer round-trips, fewer tokens): an error in one command does not block the others, it is reported as `{"tool": name, "errore": ...}`.

```json
[
  {"tool": "riepilogo_presenze", "argomenti": {"mese": "2026-03"}},
  {"tool": "lista_cedolini", "argomenti": {}}
]
```

`salva_preset("riepilogo_mensile", [...])` saves that combination under a name (in `presets.json` inside the data folder); afterwards you just tell Claude *"run the riepilogo_mensile preset"* instead of repeating the commands every time. The batch/preset tools themselves cannot be called from a preset (this avoids infinite recursion).

## Supported formats

Inaz export layouts vary from company to company. Parsing is driven by pattern tables:

- `inaz_mcp/cedolini.py` → `PATTERN_NUMERICI` / `PATTERN_TESTO` (one regex per field, first match wins)
- `inaz_mcp/presenze.py` → `ALIAS_COLONNE` (CSV header variants), `FORMATI_DATA`

If your export uses different labels, add the variant to the table: no code changes needed.

CSVs are decoded by trying UTF-8 and then cp1252/latin-1: Inaz exports are often Windows-encoded, and an accented category label no longer breaks the reading of the whole file.

PDFs and CSVs are held in an in-memory cache (per file, invalidated by mtime + size): repeated reads within the same session do not re-parse from scratch.

A scanned payslip (an image, with no extractable text) is not read silently: `lista_cedolini` and `leggi_cedolino` return an `avviso` field explaining why the pay fields came back empty.

## Development

```bash
uv run pytest --cov=inaz_mcp --cov-report=term-missing  # 56 tests, 100% coverage
uv run ruff check .                                       # lint
uv run ruff format .                                      # formatting
uv run mypy inaz_mcp                                      # type check (strict)
```

CI on GitHub Actions runs all four on Python 3.11/3.12/3.13 on every push.

## Privacy

Everything runs locally: no data leaves your Mac. Payslips contain personal data — the data folder stays outside the repository.

## License

[MIT](LICENSE)
