# SOS (Science of Science) MCP Services

> **Scientific Intelligence System, Computational Scientometrics, and Informetric Modeling — UNAM**

A monorepo of Model Context Protocol (MCP) microservices and autonomous Agent Skills for the **Science of Science (SOS)**, computational scientometrics, and bibliometric intelligence ecosystem at the National Autonomous University of Mexico (Universidad Nacional Autónoma de México - UNAM). The project name (**SOS**) formally derives from the interdisciplinary field of **Science of Science**, dedicated to the quantification, mathematical modeling, and comprehensive understanding of the scientific enterprise through massive empirical data.

This project decouples human analytical interfaces (Streamlit, React, Web Dashboards) from services consumed by Artificial Intelligence Agents (Google Antigravity, Anthropic Claude, OpenAI ChatGPT, and LLMs), supporting dual-mode transport:
- **Development / Standalone:** `stdio` (fast, direct execution as local sub-processes or standalone Python CLI skills).
- **Production / Staging:** `HTTP/SSE` (Docker-orchestrated microservices via `docker-compose`).

---

## 🏛️ Ecosystem Services

| Service | Directory | SSE Port | Description |
|---|---|---|---|
| **knoMap SOM** | `services/knomap` | `8010` | Self-Organizing Maps (SOM), U-Matrix Topology, Clarivate InCites, PathSOM |
| **SinapsisAI** | `services/sinapsisai` | `8011` | Neo4j Graph, SNII Researcher Registry, Qdrant Vector Search, GraphRAG |
| **PLmetrix** | `services/plmetrix` | `8012` | Classical Bibliometric Laws (Lotka, Bradford, Price doubling time), H/G indices |
| **RevistasLATAM** | `services/revistaslatam` | `8013` | Scientific journal editorial evaluation, Latindex 2.0 audit, Diamond/Gold OA |
| **Topics** | `services/topics` | `8014` | Research Fronts detection (Leiden CPM), Longitudinal AMI Alluvial Lineages, Geopolitics |
| **OpenAlex Local** | `services/openalex` | `8015` | High-speed MCP gateway over ClickHouse columnar database (569M works, 337M authors) |

---

## 🚀 Getting Started

### 1. Basic / Standalone Mode (Zero Database Infrastructure Needed)
To run skills and analytical pipelines locally via standard Python (no Docker or ClickHouse required):
1. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/chilti/sos-mcp-services.git
   cd sos-mcp-services
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Harvest literature directly via public REST APIs (OpenAlex cursor pagination, PubMed, arXiv, Semantic Scholar) into canonical Parquet tables:
   ```bash
   python .agents/skills/openalex-harvester/scripts/openalex_harvest_cli.py \
     --query "Solid-State Sodium Batteries" \
     --output ./corpus.parquet
   ```
3. Compute the full 42-indicator battery:
   ```bash
   python .agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py \
     calculate-summary \
     --input ./corpus.parquet \
     --output ./matrices/summary.parquet
   ```

### 2. Local MCP Mode (stdio)
To register the microservices directly into your AI assistant environment (Antigravity or Claude Desktop):
1. Copy `.env.example` to `.env` and configure environment variables as needed.
2. Register `mcp_config.linux.json` (or `mcp_config.local.json`) in your agent's MCP configuration (`~/.gemini/antigravity/mcp_config.json` for Antigravity or `claude_desktop_config.json` for Claude Desktop).

### 3. Docker / Staging Mode (HTTP / SSE on GPU Servers)
To deploy containerized microservices across an institutional network:
```bash
./start_mcp_services.sh
```
Register the SSE endpoints (`http://<SERVER_IP>:8010/sse` through `8015/sse`) using `mcp_config.remote.json`.

---

## 📚 Documentation & User Manuals
- **[Master User Manual for Google Antigravity & Gemini](docs/antigravity_gemini_manual.md)** (Setup, basic vs. advanced GPU mode, slash commands `/plan`, `/boost`, `/goal`, and master templates)
- **[Master User Manual for Anthropic Claude](docs/claude_manual.md)** (Claude Code CLI, Claude Desktop, Extended Thinking, and mode directives)
- **[Master User Manual for OpenAI ChatGPT](docs/chatgpt_manual.md)** (Code Interpreter, Canvas, reasoning models `o1`/`o3-mini`, and Custom GPTs)
- **[Comprehensive Implementation Plan](docs/plan_implementacion_sos_mcp.md)**

---

## 👥 Authors

- **José Luis Jiménez Andrade** (ORCID: [0000-0003-3453-7159](https://orcid.org/0000-0003-3453-7159))  
  *Faculty of Sciences and Center for Complexity Sciences (C3), Universidad Nacional Autónoma de México (UNAM)*
- **Humberto Andrés Carrillo Calvet** (ORCID: [0000-0003-3659-6769](https://orcid.org/0000-0003-3659-6769))  
  *Faculty of Sciences and Center for Complexity Sciences (C3), Universidad Nacional Autónoma de México (UNAM)*
- **Ricardo Arencibia Jorge** (ORCID: [0000-0001-8907-2454](https://orcid.org/0000-0001-8907-2454))  
  *Center for Complexity Sciences (C3), Universidad Nacional Autónoma de México (UNAM)*

---

## 🙏 Acknowledgements

Our special recognition and gratitude to **Romel Calero Ramos**, for the design, deployment, and administration of the massive analytical database and server infrastructure in **ClickHouse** at the **Center for Complexity Sciences (C3, UNAM)**, an indispensable foundation for high-scale computation and real-time querying across the MCP microservices of this ecosystem.
