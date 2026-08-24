import os
from fastmcp import FastMCP
from services.knomap.tools.som_tools import suggest_grid_size, train_som, evaluate_som_clusters, recluster_som
from services.knomap.tools.bibliometrics_tools import parse_bibliographic_file, detect_louvain_communities
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

# Registro de Herramientas Semánticas & UMAP (5.1 - 5.4)
mcp.tool()(generate_document_embeddings)
mcp.tool()(estimate_intrinsic_dimension)
mcp.tool()(reduce_semantic_dimension)
mcp.tool()(cluster_semantic_documents)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        port = int(os.getenv("PORT", 8001))
        print(f"Iniciando knomap-som-engine en modo SSE (http://0.0.0.0:{port}/sse)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
