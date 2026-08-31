import os
from fastmcp import FastMCP
from services.topics.tools.fronts_tools import detect_research_fronts_multimodal, track_front_evolution_longitudinal
from services.topics.tools.geopolitics_tools import (
    get_geopolitical_collaboration_matrix,
    get_open_access_transition_data,
    get_sdg_impact_matrix
)

mcp = FastMCP("topics-research-fronts-engine")

# Registro de Herramientas 7.1 - 7.5
mcp.tool()(detect_research_fronts_multimodal)
mcp.tool()(track_front_evolution_longitudinal)
mcp.tool()(get_geopolitical_collaboration_matrix)
mcp.tool()(get_open_access_transition_data)
mcp.tool()(get_sdg_impact_matrix)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        port = int(os.getenv("PORT", 8005))
        print(f"Iniciando topics-research-fronts-engine en modo SSE (http://0.0.0.0:{port}/sse)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
