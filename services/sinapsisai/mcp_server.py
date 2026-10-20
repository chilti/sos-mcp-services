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
    resolve_snii_identity
)

mcp = FastMCP("sinapsisai-graphrag-engine")

# Registro de Herramientas de GraphRAG, SNII y DuckDB Analytics
mcp.tool()(query_knowledge_graph_cypher)
mcp.tool()(search_scientific_papers_semantic)
mcp.tool()(get_researcher_profile)
mcp.tool()(get_entity_statistics)
mcp.tool()(resolve_snii_identity)
mcp.tool()(query_duckdb_analytics)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        port = int(os.getenv("PORT", 8002))
        print(f"Iniciando sinapsisai-graphrag-engine en modo SSE (http://0.0.0.0:{port}/sse)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
