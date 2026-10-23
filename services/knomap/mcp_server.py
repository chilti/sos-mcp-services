import os
import sys
from pathlib import Path

# Configurar sys.path para sos-mcp-services y KnoMap Engine
BASE_DIR = Path(__file__).resolve().parent.parent.parent
KNOMAP_CANDIDATES = [
    Path(r"c:\Users\jlja\Documents\Proyectos\knomap\engine"),
    Path(__file__).resolve().parent.parent.parent.parent / "knomap" / "engine",
    Path("/home/labsom/knomap/engine")
]

sys_paths = [str(BASE_DIR)]
for cand in KNOMAP_CANDIDATES:
    if cand.exists():
        sys_paths.extend([str(cand), str(cand / "lib")])

for p in sys_paths:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from services.knomap.tools.som_tools import (
    suggest_grid_size,
    train_som,
    evaluate_som_clusters,
    recluster_som
)
from services.knomap.tools.bibliometrics_tools import (
    parse_bibliographic_file,
    detect_louvain_communities
)
from services.knomap.tools.incites_tools import (
    inspect_incites_package,
    get_incites_unit_matrix,
    get_incites_temporal_evolution,
    compute_strategic_growth_matrix
)
from services.knomap.tools.semantic_tools import (
    generate_document_embeddings,
    estimate_intrinsic_dimension,
    reduce_semantic_dimension,
    cluster_semantic_documents
)
from services.knomap.tools.tlachia_tools import (
    inspect_tlachia_package,
    get_tlachia_unit_matrix,
    get_tlachia_temporal_evolution,
    get_tlachia_works_metadata
)
from services.knomap.tools.viz_tools import (
    knomap_render_alluvial_diagram,
    knomap_render_dumbbell_chart,
    knomap_render_connection_map,
    knomap_render_exploration_dashboard,
    knomap_render_umatrix_3d,
    knomap_render_component_planes,
    knomap_render_som_dashboard
)

mcp = FastMCP("knomap-som-engine")

# Registro de Herramientas SOM (2.1 - 2.4)
mcp.tool()(suggest_grid_size)
mcp.tool()(train_som)
mcp.tool()(evaluate_som_clusters)
mcp.tool()(recluster_som)

# Registro de Herramientas Bibliometrics (3.1 - 3.2)
mcp.tool()(parse_bibliographic_file)
mcp.tool()(detect_louvain_communities)

# Registro de Herramientas InCites (4.1 - 4.4)
mcp.tool()(inspect_incites_package)
mcp.tool()(get_incites_unit_matrix)
mcp.tool()(get_incites_temporal_evolution)
mcp.tool()(compute_strategic_growth_matrix)

# Registro de Herramientas TlachIA Metrics Packages (4.5 - 4.8)
mcp.tool()(inspect_tlachia_package)
mcp.tool()(get_tlachia_unit_matrix)
mcp.tool()(get_tlachia_temporal_evolution)
mcp.tool()(get_tlachia_works_metadata)

# Registro de Herramientas Semánticas & UMAP (5.1 - 5.4)
mcp.tool()(generate_document_embeddings)
mcp.tool()(estimate_intrinsic_dimension)
mcp.tool()(reduce_semantic_dimension)
mcp.tool()(cluster_semantic_documents)

# Registro de Herramientas de Visualización (Viz Extensions)
mcp.tool()(knomap_render_alluvial_diagram)
mcp.tool()(knomap_render_dumbbell_chart)
mcp.tool()(knomap_render_connection_map)
mcp.tool()(knomap_render_exploration_dashboard)
mcp.tool()(knomap_render_umatrix_3d)
mcp.tool()(knomap_render_component_planes)
mcp.tool()(knomap_render_som_dashboard)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ["http", "sse"]:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8010))
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.transport_security = None
        print(f"Iniciando knomap-som-engine en modo SSE (http://{host}:{port}/sse)...")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio", show_banner=False)
