"""Smoke test: il server si avvia davvero e risponde al protocollo MCP.

Gira come processo separato (python -m inaz_mcp.server): non contribuisce alla
coverage di pytest, ma verifica che l'entry point installato funzioni.
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TIMEOUT_SECONDI = 15


async def _avvia_e_lista_tool() -> list[str]:
    parametri = StdioServerParameters(command=sys.executable, args=["-m", "inaz_mcp.server"])
    async with stdio_client(parametri) as (leggi, scrivi):
        async with ClientSession(leggi, scrivi) as sessione:
            await sessione.initialize()
            risposta = await sessione.list_tools()
            return [tool.name for tool in risposta.tools]


def test_server_si_avvia_ed_espone_tutti_i_tool():
    nomi = asyncio.run(asyncio.wait_for(_avvia_e_lista_tool(), timeout=TIMEOUT_SECONDI))
    assert set(nomi) == {
        "info_cartella_dati",
        "lista_cedolini",
        "leggi_cedolino",
        "cerca_nei_cedolini",
        "lista_presenze",
        "riepilogo_presenze",
        "esegui_comandi",
        "elenca_preset",
        "salva_preset",
        "esegui_preset",
    }
