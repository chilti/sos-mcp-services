import os
from fastmcp import FastMCP
from services.revistaslatam.tools.journals_tools import (
    get_journal_impact_profile,
    compare_journals_benchmarking,
    analyze_country_editorial_landscape
)

mcp = FastMCP("revistaslatam-journals-engine")

# Registro de Herramientas 9.1 - 9.3
mcp.tool()(get_journal_impact_profile)
mcp.tool()(compare_journals_benchmarking)
mcp.tool()(analyze_country_editorial_landscape)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        port = int(os.getenv("PORT", 8004))
        print(f"Iniciando revistaslatam-journals-engine en modo SSE (http://0.0.0.0:{port}/sse)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
