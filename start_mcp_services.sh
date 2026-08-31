#!/bin/bash
# start_mcp_services.sh - Iniciar o reiniciar los microservicios MCP en Docker
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

echo "🚀 Iniciando microservicios MCP..."

if ! docker ps >/dev/null 2>&1; then
    sudo docker compose -f "$COMPOSE_FILE" up -d --build
    echo ""
    echo "📋 Estado actual de los contenedores MCP:"
    sleep 3
    sudo docker ps --filter "name=mcp"
else
    docker compose -f "$COMPOSE_FILE" up -d --build
    echo ""
    echo "📋 Estado actual de los contenedores MCP:"
    sleep 3
    docker ps --filter "name=mcp"
fi

echo ""
echo "✅ Microservicios MCP disponibles:"
echo " - knomap-mcp:        http://localhost:8010/sse"
echo " - sinapsisai-mcp:    http://localhost:8011/sse"
echo " - plmetrix-mcp:      http://localhost:8012/sse"
echo " - revistaslatam-mcp: http://localhost:8013/sse"
echo " - topics-mcp:        http://localhost:8014/sse"
echo " - openalex-mcp:      http://localhost:8015/sse"
