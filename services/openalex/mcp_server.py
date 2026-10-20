import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from services.openalex.tools.mexico_tools import (
    openalex_get_institution,
    openalex_search_authors,
    openalex_search_works,
    openalex_aggregate_mexico,
    openalex_top_entities,
    openalex_semantic_search,
    openalex_run_select_query,
)

mcp = FastMCP("openalex-clickhouse-gateway")

# Registro de Herramientas Analíticas OpenAlex México
mcp.tool()(openalex_get_institution)
mcp.tool()(openalex_search_authors)
mcp.tool()(openalex_search_works)
mcp.tool()(openalex_aggregate_mexico)
mcp.tool()(openalex_top_entities)
mcp.tool()(openalex_semantic_search)
mcp.tool()(openalex_run_select_query)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http" or transport == "sse":
        port = int(os.getenv("PORT", 8006))
        print(f"Iniciando openalex-clickhouse-gateway en modo SSE (http://0.0.0.0:{port}/sse)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")

