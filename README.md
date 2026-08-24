# SOS MCP Services (Sistema de Inteligencia Científica UNAM)

Monorepo de microservicios MCP (Model Context Protocol) para el ecosistema de inteligencia cienciométrica y bibliométrica de la UNAM.

Este proyecto desacopla las herramientas analíticas para humanos (Streamlit, React, Dashboards) de los servicios consumibles por Agentes de Inteligencia Artificial (Antigravity / LLMs), soportando transporte dual:
- **Desarrollo:** `stdio` (ejecución directa y veloz como subprocesos en local).
- **Producción / Staging:** `HTTP/SSE` (contenedores Docker orquestados con `docker-compose`).

---

## 🏛️ Servicios del Ecosistema

| Servicio | Directorio | Puerto SSE | Descripción |
|---|---|---|---|
| **knoMap SOM** | `services/knomap` | `8001` | Mapas Auto-Organizados (SOM), Topología U-Matrix, InCites, PathSOM |
| **SinapsisAI** | `services/sinapsisai` | `8002` | Grafo Neo4j, Padrón SNII, Búsqueda Vectorial Qdrant, GraphRAG |
| **PLmetrix** | `services/plmetrix` | `8003` | Leyes Bibliométricas (Lotka, Bradford, Zipf, Price), Índices H/g |
| **RevistasLATAM** | `services/revistaslatam` | `8004` | Evaluación de revistas científicas, Acceso Abierto diamante/oro |
| **Topics** | `services/topics` | `8005` | Detección de frentes de investigación (Research Fronts v5), Geopolítica |
| **OpenAlex Local** | `services/openalex` | `8006` | Gateway MCP sobre ClickHouse local (569M trabajos, 337M autores) |

---

## 🚀 Puesta en Marcha

### 1. Modo Desarrollo (Local stdio)
Para usar directamente desde el IDE Antigravity sin Docker:
1. Copia `.env.example` a `.env` y configura variables de entorno.
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Registra `mcp_config.local.json` en tu configuración de Antigravity IDE (`C:\Users\jlja\.gemini\antigravity-ide\mcp_config.json`).

### 2. Modo Docker / Staging (HTTP / SSE)
Para levantar todos los microservicios en red aislada:
```bash
docker-compose up -d --build
```
Y registra `mcp_config.remote.json` en Antigravity para conectar vía SSE (`http://localhost:800X/sse`).

---

## 📚 Documentación
- [Plan Integral de Implementación](docs/plan_implementacion_sos_mcp.md)
