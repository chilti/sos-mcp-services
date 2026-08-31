import os
from fastmcp import FastMCP
from services.openalex.tools.search_tools import openalex_search_authors, openalex_search_works
from services.openalex.tools.entity_tools import openalex_get_entity_by_id, openalex_aggregate_group_by

mcp = FastMCP("openalex-clickhouse-gateway")

# Registro de Herramientas 1.1 - 1.4
mcp.tool()(openalex_search_authors)
mcp.tool()(openalex_search_works)
mcp.tool()(openalex_get_entity_by_id)
mcp.tool()(openalex_aggregate_group_by)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        port = int(os.getenv("PORT", 8006))
        print(f"Iniciando openalex-clickhouse-gateway en modo SSE (http://0.0.0.0:{port}/sse)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
