import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from services.plmetrix.tools.laws_tools import (
    analyze_lotka_law,
    analyze_bradford_law,
    analyze_price_index,
    analyze_scientific_growth_phases,
    compute_author_impact_metrics,
    compute_gini_inequality,
)

mcp = FastMCP("plmetrix-laws-engine")

# Registro de Herramientas de Leyes Bibliométricas e Impacto
mcp.tool()(analyze_lotka_law)
mcp.tool()(analyze_bradford_law)
mcp.tool()(analyze_price_index)
mcp.tool()(analyze_scientific_growth_phases)
mcp.tool()(compute_author_impact_metrics)
mcp.tool()(compute_gini_inequality)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ["http", "sse"]:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8012))
        mcp.settings.host = host
        mcp.settings.port = port
        print(f"Iniciando plmetrix-laws-engine en modo SSE (http://{host}:{port}/sse)...")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")

