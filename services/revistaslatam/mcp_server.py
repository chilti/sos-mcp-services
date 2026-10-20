import os
import sys
from pathlib import Path

# Configurar sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from services.revistaslatam.tools.journals_tools import (
    get_journal_impact_profile,
    compare_journals_benchmarking,
    analyze_country_editorial_landscape
)

mcp = FastMCP("revistaslatam-journals-engine")

# Registro de Herramientas de Revistas Iberoamericanas y Evaluación Editorial
mcp.tool()(get_journal_impact_profile)
mcp.tool()(compare_journals_benchmarking)
mcp.tool()(analyze_country_editorial_landscape)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ["http", "sse"]:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8013))
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.transport_security = None
        print(f"Iniciando revistaslatam-journals-engine en modo SSE (http://{host}:{port}/sse)...")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio", show_banner=False)
