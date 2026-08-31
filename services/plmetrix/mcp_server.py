import os
from fastmcp import FastMCP
from services.plmetrix.tools.laws_tools import (
    analyze_lotka_law,
    analyze_bradford_law,
    analyze_price_index,
    analyze_scientific_growth_phases
)

mcp = FastMCP("plmetrix-laws-engine")

# Registro de Herramientas 8.1 - 8.4
mcp.tool()(analyze_lotka_law)
mcp.tool()(analyze_bradford_law)
mcp.tool()(analyze_price_index)
mcp.tool()(analyze_scientific_growth_phases)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        port = int(os.getenv("PORT", 8003))
        print(f"Iniciando plmetrix-laws-engine en modo SSE (http://0.0.0.0:{port}/sse)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
