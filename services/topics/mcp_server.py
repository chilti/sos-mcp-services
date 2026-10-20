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

from services.topics.tools.fronts_tools import (
    detect_research_fronts_multimodal,
    track_front_evolution_longitudinal
)
from services.topics.tools.geopolitics_tools import (
    get_geopolitical_collaboration_matrix,
    get_open_access_transition_data,
    get_sdg_impact_matrix
)

mcp = FastMCP("topics-research-fronts-engine")

# Registro de Herramientas de Topics y Frentes de Investigación
mcp.tool()(detect_research_fronts_multimodal)
mcp.tool()(track_front_evolution_longitudinal)
mcp.tool()(get_geopolitical_collaboration_matrix)
mcp.tool()(get_open_access_transition_data)
mcp.tool()(get_sdg_impact_matrix)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ["http", "sse"]:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8014))
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.transport_security = None
        print(f"Iniciando topics-research-fronts-engine en modo SSE (http://{host}:{port}/sse)...")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio", show_banner=False)
