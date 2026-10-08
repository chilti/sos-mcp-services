import os
import sys

# Asegurar path de sos-mcp-services
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from services.openproject.tools.project_tools import (
    openproject_list_projects,
    openproject_get_project,
    openproject_create_project,
    openproject_list_work_packages,
    openproject_get_work_package,
    openproject_create_work_package,
    openproject_update_work_package,
    openproject_add_comment,
    openproject_list_types,
    openproject_list_statuses,
    openproject_list_users,
)

mcp = FastMCP("openproject-pm-gateway")

mcp.tool()(openproject_list_projects)
mcp.tool()(openproject_get_project)
mcp.tool()(openproject_create_project)
mcp.tool()(openproject_list_work_packages)
mcp.tool()(openproject_get_work_package)
mcp.tool()(openproject_create_work_package)
mcp.tool()(openproject_update_work_package)
mcp.tool()(openproject_add_comment)
mcp.tool()(openproject_list_types)
mcp.tool()(openproject_list_statuses)
mcp.tool()(openproject_list_users)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        port = int(os.getenv("PORT", 8010))
        print(f"Iniciando openproject-pm-gateway en modo SSE (http://0.0.0.0:{port}/sse)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
