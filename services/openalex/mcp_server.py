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
from services.openalex.tools.viz_tools import (
    openalex_plot_timeseries,
    openalex_plot_oa_donut,
    openalex_plot_top_ranking,
    openalex_plot_sunburst,
    openalex_plot_sdg_grid,
    openalex_plot_dossier_works,
    openalex_plot_collaboration_network,
    openalex_render_visualization_from_json,
    openalex_plot_quadrant_matrix,
    openalex_plot_geopolitical_sankey,
    openalex_plot_multidimensional_radar,
    openalex_plot_topic_dynamics,
    openalex_plot_collaborating_countries,
    openalex_plot_scientific_vocabulary,
    openalex_plot_coauthra_network,
)
from starlette.responses import FileResponse, Response
from starlette.requests import Request

mcp = FastMCP("openalex-clickhouse-gateway")

REPORTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "reports"))
os.makedirs(REPORTS_DIR, exist_ok=True)

@mcp.custom_route("/reports/{filename:path}", methods=["GET"])
async def serve_report(request: Request) -> Response:
    filename = request.path_params.get("filename", "")
    safe_path = os.path.abspath(os.path.join(REPORTS_DIR, filename))
    if not safe_path.startswith(REPORTS_DIR):
        return Response("Forbidden", status_code=403)
    if not os.path.isfile(safe_path):
        return Response(f"Report '{filename}' not found", status_code=404)
    return FileResponse(
        safe_path,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
        }
    )

# Registro de Herramientas Analíticas OpenAlex México
mcp.tool()(openalex_get_institution)
mcp.tool()(openalex_search_authors)
mcp.tool()(openalex_search_works)
mcp.tool()(openalex_aggregate_mexico)
mcp.tool()(openalex_top_entities)
mcp.tool()(openalex_semantic_search)
mcp.tool()(openalex_run_select_query)

# Registro de Herramientas de Visualización y Artefactos OpenAlex México
mcp.tool()(openalex_plot_timeseries)
mcp.tool()(openalex_plot_oa_donut)
mcp.tool()(openalex_plot_top_ranking)
mcp.tool()(openalex_plot_sunburst)
mcp.tool()(openalex_plot_sdg_grid)
mcp.tool()(openalex_plot_dossier_works)
mcp.tool()(openalex_plot_collaboration_network)
mcp.tool()(openalex_render_visualization_from_json)
mcp.tool()(openalex_plot_quadrant_matrix)
mcp.tool()(openalex_plot_geopolitical_sankey)
mcp.tool()(openalex_plot_multidimensional_radar)
mcp.tool()(openalex_plot_topic_dynamics)
mcp.tool()(openalex_plot_collaborating_countries)
mcp.tool()(openalex_plot_scientific_vocabulary)
mcp.tool()(openalex_plot_coauthra_network)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ["http", "sse"]:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8015))
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.transport_security = None
        print(f"Iniciando openalex-clickhouse-gateway en modo SSE (http://{host}:{port}/sse)...")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")

