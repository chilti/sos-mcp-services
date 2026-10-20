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

from services.sinapsisai.tools.graph_tools import (
    query_knowledge_graph_cypher,
    search_scientific_papers_semantic,
    get_entity_statistics,
    query_duckdb_analytics
)
from services.sinapsisai.tools.snii_tools import (
    get_researcher_profile,
    resolve_snii_identity,
    get_snii_historical_trajectory,
    query_snii_census_overview
)

mcp = FastMCP("sinapsisai-graphrag-engine")

# Registro de Herramientas de GraphRAG, SNII 2026, Padrón Histórico y DuckDB Analytics
mcp.tool()(resolve_snii_identity)
mcp.tool()(get_snii_historical_trajectory)
mcp.tool()(query_snii_census_overview)
mcp.tool()(get_researcher_profile)
mcp.tool()(get_entity_statistics)
mcp.tool()(query_knowledge_graph_cypher)
mcp.tool()(search_scientific_papers_semantic)
mcp.tool()(query_duckdb_analytics)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ["http", "sse"]:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8011))
        mcp.settings.host = host
        mcp.settings.port = port
        print(f"Iniciando sinapsisai-graphrag-engine en modo SSE (http://{host}:{port}/sse)...")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio", show_banner=False)
