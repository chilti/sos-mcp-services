# SOS (Science of Science) MCP Services & Agent Skills

## Master User Manual for Google Antigravity & Gemini

> **Computational Scientometrics, Informetric Modeling, Massive Bibliographic Big Data, and Topological Neural Cartography**
> Laboratorio de Dinámica no Lineal, Departamento de Matemáticas, Facultad de Ciencias & Centro de Ciencias de la Complejidad (C3), Universidad Nacional Autónoma de México (UNAM)

---

## Table of Contents

1. [Section 1: Installation &amp; Setup (Basic vs. Advanced GPU Server)](#section-1-installation--setup-basic-vs-advanced-gpu-server)
   - [1.1. Basic One-Click Installation (Zero Database Infrastructure Needed)](#11-basic-one-click-installation-zero-database-infrastructure-needed)
   - [1.2. What Antigravity Executes in Basic Mode](#12-what-antigravity-executes-in-basic-mode)
   - [1.3. (Optional) Advanced Setup: Dedicated GPU Server, Local Embeddings &amp; Docker MCP Services](#13-optional-advanced-setup-dedicated-gpu-server-local-embeddings--docker-mcp-services)
2. [Section 2: Standalone Usage of Agent Skills with Slash Commands](#section-2-standalone-usage-of-agent-skills-with-slash-commands)
   - [2.1. Catalog of Scientific Skill Families](#21-catalog-of-scientific-skill-families)
   - [2.2. Workflows Combining Skills with Slash Commands](#22-workflows-combining-skills-with-slash-commands)
     - [Workflow A: `/plan` + Delineation &amp; Harvesting](#workflow-a-plan--delineation--harvesting)
     - [Workflow B: `/boost` + Research Fronts &amp; Deep Literature](#workflow-b-boost--research-fronts--deep-literature)
     - [Workflow C: `/goal` + Topological Trajectory Mapping (SOM)](#workflow-c-goal--topological-trajectory-mapping-som)
     - [Workflow D: `/browser` + Interactive Visualization Artifacts](#workflow-d-browser--interactive-visualization-artifacts)
     - [Workflow E: `/schedule` + Continuous Literature Surveillance](#workflow-e-schedule--continuous-literature-surveillance)
     - [Workflow F: `/teamwork` + Parallel Swarm Orchestration (`swarm`)](#workflow-f-teamwork--parallel-swarm-orchestration-swarm)
3. [Section 3: Scientific Master Templates &amp; the Curated Laboratory Protocol](#section-3-scientific-master-templates--the-curated-laboratory-protocol)
   - [3.1. The Curated Laboratory Protocol (Exploration, Full Evidence-First &amp; Curation)](#31-the-curated-laboratory-protocol-exploration-full-evidence-first--curation)
   - [3.2. Detailed Guide per Template](#32-detailed-guide-per-template)
     - [Template 1: Original Research Article (IMRaD / IMRyD Format - Q1 Journal)](#template-1-original-research-article-imrad--imryd-format---q1-journal)
     - [Template 2: Institutional Evaluation Technical Report &amp; Peer Benchmarking](#template-2-institutional-evaluation-technical-report--peer-benchmarking)
     - [Template 3: Governance Policy Brief (S&amp;T Policy for Senior Decision-Makers)](#template-3-governance-policy-brief-st-policy-for-senior-decision-makers)
     - [Template 4: Scientific Intelligence Report &amp; Research Fronts Radar](#template-4-scientific-intelligence-report--research-fronts-radar)
     - [Template 5: Exhaustive Multi-Scale Scientometric Study (39 Skills · 4-Wave Swarm)](#template-5-exhaustive-multi-scale-scientometric-study-39-skills--4-wave-swarm)
4. [Appendix: Core Principles &amp; Inviolable Rules](#appendix-core-principles--inviolable-rules)

---

## Section 1: Installation & Setup (Basic vs. Advanced)

This project provides **39 specialized Agent Skills** and modular analytical engines designed for Antigravity (Google's agentic AI assistant) and Gemini.

To ensure universal portability, the ecosystem is built with a **Zero-Barrier Architecture**: **you do NOT need a local database server, ClickHouse cluster, or private OpenAlex snapshot to perform state-of-the-art scientometrics.**

---

### 1.1. Basic One-Click Installation (Zero Database Infrastructure Needed)

In this basic mode, Antigravity operates entirely via:

- **Public Scientific APIs:** Massive cursor-paginated literature extraction directly from the **OpenAlex REST API** (`openalex-harvester`), **PubMed NCBI E-utilities** (`pubmed-harvester`), **arXiv Atom API** (`arxiv-harvester`), and **Semantic Scholar Graph API** (`semantic-scholar-harvester`).
- **Local User Data Files:** Direct ingestion of existing Parquet, CSV, RIS, or KnoMap (`.knoMap`) files.
- **Full Autonomous Computation:** Indicator matrices (42+ metrics), classical bibliometric laws, Leiden network clustering, citation snowballing, Kohonen Self-Organizing Maps (SOM), and publication-ready templates.

#### Copy-Paste Basic Prompt for Antigravity:

Open Antigravity in your workspace and paste the following prompt (it automatically clones the repository if you have not already done so):

```markdown
Hello Antigravity. I want to install and activate the SOS (Science of Science) Agent Skills in BASIC / STANDALONE mode (zero database infrastructure required). Please perform the following steps:

1. Repository & Skills Discovery:
   - Check if this workspace already contains the repository `sos-mcp-services`. If not, clone it using:
     `git clone https://github.com/chilti/sos-mcp-services.git`
   - Locate the `.agents/skills/` directory inside `sos-mcp-services`.
   - Index all 39 skills and make them accessible in my active Antigravity environment (link or copy them into my workspace `.agents/skills/` or global Antigravity skills directory `~/.gemini/antigravity/skills/`).

2. Python Runtime & Scientific Libraries:
   - Use an active Python virtual environment with Python >= 3.10 (or create a local one: `python3 -m venv .venv && source .venv/bin/activate`).
   - Ensure standard scientific dependencies are installed: `pip install -r sos-mcp-services/requirements.txt` (or verify `pandas`, `pyarrow`, `duckdb`, `numpy`, `scipy`, `scikit-learn`, `networkx`, `matplotlib`, `plotly`).
   - Note: Do NOT require or configure any ClickHouse database connection, Docker containers, or private OpenAlex database snapshot servers.

3. Verification:
   - Run a quick syntax and CLI check on:
     * `tlachia-metrics-engine/scripts/tlachia_metrics_cli.py --help`
     * `classical-bibliometrics-laws/scripts/bibliometric_laws_cli.py --help`
     * `openalex-harvester/scripts/openalex_harvest_cli.py --help`
     * `som-methodological-expert/scripts/som_pipeline_cli.py --help`
   - Confirm that all tools are ready to harvest via public REST APIs (OpenAlex, arXiv, PubMed, Semantic Scholar) and process local Parquet/CSV datasets.
   - Report when the environment is ready for scientometric research.
```

---

### 1.2. What Antigravity Executes in Basic Mode

When you paste the basic prompt, Antigravity performs a lightweight setup:

1. **Loads the 39 Skill Definitions:** Automatically scans each `SKILL.md` in `.agents/skills/` and makes them available for natural language triggering and slash command execution.
2. **Binds the Execution Environment:** Configures CLI calls to run with Python >= 3.10, ensuring all data wrangling (`pandas`, `pyarrow`), clustering (`scikit-learn`), and plotting (`plotly`, `matplotlib`) execute without system permission issues.
3. **Applies Universal Language Invariant:** Sets default plot/report labels to English (`--lang en`), while supporting Spanish (`--lang es`) whenever the user interacts in Spanish.
4. **Keeps Everything Local:** All harvested papers, indicator matrices, and reports are saved to your active workspace directory (`./corpus.parquet`, `./matrices/`, `./reportes/`) under the **Workspace-First** principle.

---

### 1.3. (Optional) Advanced Setup: Dedicated GPU Server, Local Embeddings & Docker MCP Services

> [!TIP]
> **Who is this for?** Research groups, university laboratories (such as C3-UNAM), or institutional clusters with dedicated server hardware (NVIDIA GPUs with CUDA support, >= 32 GB RAM, and high-speed NVMe storage). This mode scales the ecosystem to support multiple concurrent Antigravity clients across a local or campus network.

In this advanced deployment, the GPU server hosts three high-performance capabilities:

1. **Local Dense Vector Embeddings (768d Nomic MoE):** Powers semantic search (`openalex-mexico-semantic-search`) and hybrid graph retrieval (`graphrag-scientific-intelligence`) locally with zero token fees and complete query privacy.
2. **ClickHouse Analytical Cluster:** Hosts the full 569M works snapshot in `rag.works_flat` and `rag.works_academic_all` for sub-second, zero-join aggregations.
3. **Containerized MCP Microservices (HTTP/SSE Transport):** Serves the 6 MCP microservices over Docker so multiple Antigravity workstations can connect remotely without duplicating environments.

```mermaid
graph LR
    subgraph "Client Workstations (Antigravity IDE)"
        AG1[User 1: Antigravity]
        AG2[User 2: Antigravity]
        AG3[User N: Antigravity]
    end

    subgraph "Dedicated GPU / Institutional Server"
        SSE[Docker MCP Gateway: Ports 8010–8015 SSE]
        EMB["GPU Embedding Service (LM Studio / vLLM / Ollama)<br>text-embedding-nomic-ai-nomic-embed-text-v2-moe (768d)<br>Port 1234"]
        CH["ClickHouse Columnar Database<br>rag.works_flat (464.8M works)<br>rag.works_academic_all (1.65M works)<br>Port 8124 / 9000"]
    end

    AG1 & AG2 & AG3 -->|SSE HTTP / JSON-RPC| SSE
    SSE --> CH
    SSE --> EMB
    CH -.->|cosineDistance 768d| EMB
```

#### Step 1: Configure Environment on the GPU Server (`.env`)

Create or update your `.env` on the GPU host:

```bash
# ClickHouse Analytical Cluster
CLICKHOUSE_HOST=127.0.0.1
CLICKHOUSE_PORT=8124
CLICKHOUSE_USER=rag_user
CLICKHOUSE_PASSWORD=your_secure_password
CLICKHOUSE_DATABASE=rag

# GPU Local Embedding Service (LM Studio / vLLM / Ollama)
LM_STUDIO_URL=http://127.0.0.1:1234/v1/embeddings
LM_STUDIO_API_KEY=sk-local-token
EMBEDDING_MODEL=text-embedding-nomic-ai-nomic-embed-text-v2-moe

# MCP Transport Mode
MCP_TRANSPORT=sse
```

#### Step 2: Launch the 6 MCP Microservices via Docker Compose

Run the included automated launch script:

```bash
cd sos-mcp-services
./start_mcp_services.sh
```

This launches the 6 isolated containers exposed over Server-Sent Events (SSE):

- **`knomap-mcp`:** `http://<GPU_SERVER_IP>:8010/sse` (Neural SOM, U-Matrix, InCites, PathSOM)
- **`sinapsisai-mcp`:** `http://<GPU_SERVER_IP>:8011/sse` (Neo4j graph, SNII registry, Qdrant)
- **`plmetrix-mcp`:** `http://<GPU_SERVER_IP>:8012/sse` (Lotka, Bradford, Price kinetics, H/G indices)
- **`revistaslatam-mcp`:** `http://<GPU_SERVER_IP>:8013/sse` (Latindex 2.0 audit, Diamond OA, endogamy)
- **`topics-mcp`:** `http://<GPU_SERVER_IP>:8014/sse` (Research Fronts, Leiden CPM, AMI alluvial diagrams)
- **`openalex-mcp`:** `http://<GPU_SERVER_IP>:8015/sse` (High-speed ClickHouse gateway, 569M works)

#### Step 3: Connect Client Antigravity Instances to the GPU Server

On each client workstation running Antigravity, configure `~/.gemini/antigravity/mcp_config.json` with the remote SSE endpoints (replace `<GPU_SERVER_IP>` with your host's LAN or VPN IP):

```json
{
  "mcpServers": {
    "sos_knomap": {
      "url": "http://<GPU_SERVER_IP>:8010/sse"
    },
    "sos_sinapsisai": {
      "url": "http://<GPU_SERVER_IP>:8011/sse"
    },
    "sos_plmetrix": {
      "url": "http://<GPU_SERVER_IP>:8012/sse"
    },
    "sos_revistaslatam": {
      "url": "http://<GPU_SERVER_IP>:8013/sse"
    },
    "sos_topics": {
      "url": "http://<GPU_SERVER_IP>:8014/sse"
    },
    "sos_openalex": {
      "url": "http://<GPU_SERVER_IP>:8015/sse"
    }
  }
}
```

Now, every client Antigravity agent can invoke tools like `mcp_sos_openalex_*`, query the 569M works snapshot in ClickHouse, and compute 768-dimensional local embeddings powered by the central GPU server.

---

## Section 2: Standalone Usage of Agent Skills with Slash Commands

The repository includes **39 modular Agent Skills** (including 5 Master Study Templates). Each skill is a self-contained expert with its own execution CLI, mathematical documentation (`references/*.md`), **Full Evidence-First** audit trails (`*_run_manifest.json`, `*_cluster_eval.csv`, `*_partition_eval.csv`), and bilingual output engine (`--lang en` / `--lang es`).

### 2.1. Catalog of Scientific Skill Families

```mermaid
graph TD
    subgraph "1. Harvesting & Delineation"
        H1[bibliometric-search-strategist]
        H2[openalex-harvester - REST API]
        H3[pubmed / arxiv / s2 / scopus]
        H4[Optional: ClickHouse Local Gateway]
    end

    subgraph "2. Metrics & Classical Laws"
        M1[tlachia-metrics-engine]
        M2[classical-bibliometrics-laws]
        M3[bibliometrix-guide]
    end

    subgraph "3. Networks & Research Fronts"
        N1[topics-research-fronts-intelligence]
        N2[bibliometric-network-analyst]
        N3[deep-literature-researcher]
    end

    subgraph "4. Topological Cartography (SOM)"
        S1[som-methodological-expert]
        S2[som-trajectory-mapping]
        S3[neural-longitudinal-mapping]
        S4[scientometrics-incites-expert]
        S5[knomap-project-resumer]
    end

    subgraph "5. Policy, OA & Geopolitics"
        P1[geopolitical-collaboration-analyst]
        P2[open-access-monitor]
        P3[sdg-impact-intelligence]
        P4[infotlachia-scholar-intelligence]
        P5[revistaslatam-indicators-engine]
        P6[open-access-pdf-downloader]
    end

    H1 --> H2 & H3
    H2 & H3 --> M1
    M1 --> S1 & S2 & S3
    H2 --> N1 --> N3
    M1 --> P1 & P2 & P3
```

---

### 2.2. Workflows Combining Skills with Slash Commands

Antigravity supports slash commands (`/plan`, `/boost`, `/goal`, `/teamwork`, `/browser`, `/schedule`, `/compact`, `/grill-me`) that elevate skill execution into autonomous, rigorous scientific workflows.

#### Workflow A: `/plan` + Delineation & Harvesting into Parquet

* **Goal:** Formulate an ISSI-audited multi-stage search strategy (Huang & Porter) and harvest the target corpus directly into a canonical `./corpus.parquet` table.
* **Prompt Example:**

```markdown
/plan Delineate the global scientific output on "Solid-State Sodium Batteries" using the skill `bibliometric-search-strategist`. 
Follow the GLOBAL guideline (ISSI):
1. Extract conceptual seed blocks (keywords, title phrases, and core CWTS/OpenAlex topics).
2. Harvest the records using `openalex-harvester` (with cursor pagination) or ingest my existing bibliographic table into `./corpus.parquet`.
3. Run `tlachia-metrics-engine` to compute the baseline 42-indicator summary table in `./matrices/summary.parquet`.
```

#### Workflow B: `/boost` + Research Fronts & Deep Literature

* **Goal:** Detect emerging communities via Leiden partitioning on bibliographic coupling networks and extract the substantive scientific discoveries of core papers without hallucinations.
* **Prompt Example:**

```markdown
/boost Analyze the intellectual structure and active research fronts in `./corpus.parquet` using `topics-research-fronts-intelligence` and `deep-literature-researcher`.

Required execution:
1. Build a bibliographic coupling network with Leiden CPM partitioning.
2. Track longitudinal alluvial lineages (AMI) across 3-year periods to detect Persistence, Split, Merge, and Genesis events.
3. Identify the top 3 core papers (highest in-cluster centrality and citation density) for the 5 largest fronts.
4. Synthesize what specific experimental architectures, chemical compositions, or physical mechanisms are reported in those papers (do not merely list metadata—explain the science).
5. Generate `./reportes/alluvial_lineages.html` and `./reportes/fronts_summary.csv`.
```

#### Workflow C: `/goal` + Topological Trajectory Mapping (SOM)

* **Goal:** Train an unsupervised neural network (Kohonen Self-Organizing Map) to trace the historical multi-indicator trajectory of leading countries or institutions over a 15-year horizon.
* **Prompt Example:**

```markdown
/goal Execute a complete neural trajectory mapping over `./matrices/by_country_annual.parquet` using `som-trajectory-mapping` and `som-methodological-expert`.

Execution requirements:
1. Apply Centered Moving Average (CMA, window=3) to smooth indicator noise.
2. Train a 2D hexagonal toroidal SOM grid sized via SVD ratio ($N \times M \approx 25N$).
3. Trace continuous parametric cubic spline trajectories for the top 5 focal countries (e.g., USA, China, Germany, Japan, South Korea).
4. Identify topological inflection points, community maturation phases, and metric paradoxes (such as volume surging while normalized FWCI declines).
5. Persist `./reportes/som_trajectories.png` and `./reportes/som_dashboard.html` with default English labels (`--lang en`).
```

#### Workflow D: `/browser` + Interactive Visualization Artifacts

* **Goal:** Launch and visually inspect interactive HTML dashboards (Plotly / KnoMap Force Graph / PyVis networks) inside Antigravity's browser subagent.
* **Prompt Example:**

```markdown
/browser Generate the Open Access and APC economic breakdown using `open-access-monitor`, render the interactive dashboard with `openalex-mexico-visualizer`, and open `./reportes/oa_dashboard.html` in the browser tab to verify that tooltips, donut slices, and KPI cards render correctly.
```

#### Workflow E: `/schedule` + Continuous Literature Surveillance

* **Goal:** Set up recurring background harvesting to detect emerging preprints or publications on a priority topic every Monday.
* **Prompt Example:**

```markdown
/schedule Run a weekly surveillance query every Monday at 08:00 AM using `arxiv-harvester` and `openalex-harvester` for the topic "Perovskite Solar Cells Degradation". 
Append new records to `./corpus_monitoring.parquet`, flag papers with FWCI > 2.0 or top 10% percentile, and send me a concise executive alert in chat.
```

#### Workflow F: `/teamwork` + Parallel Swarm Orchestration (`swarm`)

* **Goal:** Coordinate multiple worker agents in parallel after harvesting `./corpus.parquet`—either in **bounded mode** (3–4 RQ-targeted families under `template-articulo-cientifico-imryd`) or **full 4-Wave mode** (`template-estudio-cienciometrico-exhaustivo`)—using `workspace: "inherit"` and **strictly disjoint output directories** (`./lab_exploration/` or `./evidence_vault/`).
* **Prompt Example:**

```markdown
/teamwork Run Wave 1–3 exploration in parallel over `./corpus.parquet` and `./matrices/` with disjoint subdirectories:
1. `worker-laws` (`./lab_exploration/01_laws/`): run `classical-bibliometrics-laws` (`growth-phase`, `lotka`, `bradford`, `price-index`).
2. `worker-fronts` (`./lab_exploration/02_networks_fronts/`): run competing `coupling` vs. `cocitation` partitions (`topics-research-fronts-intelligence` + `bibliometric-network-analyst`), persisting `*_partition_eval.csv` and `ami_window_summary.csv`.
3. `worker-lit` (`./lab_exploration/03_deep_lit/`): run `deep-literature-researcher` (+ `open-access-pdf-downloader` where needed) on core front papers, separating Author-Signaled Future Work from Analytically Assessed Unexplored Paths.
4. `worker-som` (`./lab_exploration/04_som/`): run Big SOM (`--norm divmax --grid-type big --max-k 15`) with `som-methodological-expert` and audit `QE`, `TE`, and `*_cluster_eval.csv` (checking `--cluster-strategy local_max_gt2 --min-clusters 3` if K=2 is trivial).
Post only concise summaries and `*_run_manifest.json` paths on the board, then curate into `./reportes/`.
```

---

## Section 3: Scientific Master Templates & the Curated Laboratory Protocol

The repository provides **5 Master Templates** (`template-*`) modeled after the human research workflows of the **Laboratorio de Dinámica no Lineal (Departamento de Matemáticas, Facultad de Ciencias) & Centro de Ciencias de la Complejidad (C3), UNAM** research group (*Sixty Years of Research on Polaritons*, 2025; *Specialization Indicators in Scientometrics*, 2026; *Neural Longitudinal Mapping*, 2024–2025).

### 3.1. The Curated Laboratory Protocol (Exploration, Full Evidence-First & Curation)

Scientific discovery is an empirical, iterative process. Every template enforces explicit separation between exploration, full-evidence persistence, and editorial curation (and uses **OpenAlex-first** portable APIs by default, with optional ClickHouse acceleration when configured):

```
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE I: LABORATORY PHASE (Sequential /goal or Parallel /teamwork)     │
│  - Harvest `./corpus.parquet` via OpenAlex API (or opt-in ClickHouse). │
│  - Compute full 46-column matrices (42 indicators + 4 meta) in Parquet │
│    across focal scales filtered by critical-mass (`min_docs`).         │
│  - Run competing analytical techniques with Full Evidence-First logs:  │
│      * Classical laws (Lotka, Bradford, Price, AIC/RMSE).              │
│      * Networks & Fronts (`*_partition_eval.csv`, Q, AMI lineajes).    │
│      * Big SOM (`--norm divmax --max-k 15`, QE/TE, `*_cluster_eval`).  │
│      * Core paper reading + OA PDF extraction (N/A-strict synthesis).  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE II–III: SCIENTIFIC CURATION, AUDIT & COMPILATION                 │
│  - Build scorecard (`exploration_scorecard.csv` / `diagnostic_scorecard│
│    .csv`) documenting both winning signals AND discarded/trivial runs. │
│  - Select 3–5 narrative blocks (IMRyD) or multi-scale synthesis.       │
│  - Dual Discussion Agenda: Author-Signaled Future Work vs. Unexplored. │
│  - Zero Empty Columns (`N/D`), Sober Tone, Zero-Scaffolding Leakage.   │
│  - 1:1 OpenAlex DOI verification & final `.md`, `.docx`, `.pdf` build. │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 3.2. Detailed Guide per Template

#### Template 1: Original Research Article (IMRaD / IMRyD Format - Q1 Journal)

* **Skill Name:** `template-articulo-cientifico-imryd`
* **Scope:** Hypothesis-driven Q1/Q2 journal article centered on a focused thesis and **3 to 5 curated analytical blocks** across **2–3 RQ-linked entity scales** (unlike `template-estudio-cienciometrico-exhaustivo`, it never runs all 39 skills blindly).
* **Target Venues:** *Journal of Informetrics*, *Scientometrics*, *Quantitative Science Studies*, *Research Evaluation*.
* **Recommended Slash Command Flow:**
  1. `/grill-me` $\to$ Align research questions ($RQ_1 \dots RQ_k$), 2–3 focal scales, and target journal.
  2. `/teamwork` *(optional bounded swarm across 3–4 RQ families)* or `/boost` / `/goal` $\to$ Execute Stage I exploration with Full Evidence-First logs (`exploration_scorecard.csv`) and Stage II curation.
  3. `/compact` $\to$ Clean conversation memory before Stage III drafting, 1:1 OpenAlex audit, and `.docx`/`.pdf` compilation.
* **Full Prompt Example:**

```markdown
/grill-me I want to draft an original scientific research manuscript using `template-articulo-cientifico-imryd` on the global evolution of "Quantum Computing Architectures (Superconducting vs. Trapped Ions vs. Photonic)" from 2000 to 2025. 

Interview me regarding:
1. Research questions and core hypotheses ($RQ_1 \dots RQ_k$).
2. Data sources (harvesting via `openalex-harvester` into `./corpus.parquet` vs. ingesting an existing Parquet/CSV dataset) and the 2–3 focal granularities (e.g., countries + research fronts).
3. Which analytical families to test in competition in Stage I (classical kinetics, competing coupling/co-citation networks, core paper review with OA PDFs, and Big SOM `--norm divmax`).
4. Target journal and preferred execution mode (`/goal` sequential vs. bounded `/teamwork` parallel laboratory).
```

*(Once aligned, proceed with either `/boost` or bounded `/teamwork`:)*

```markdown
/teamwork Proceed with Stage I (Targeted Laboratory Exploration in `./lab_exploration/`), Stage II (Curation), and Stage III (Verification & Compilation) of `template-articulo-cientifico-imryd`.
Compute 46-column matrices in `./matrices/` across our selected 2–3 scales (`min_docs >= 5`), test competing techniques in parallel with Full Evidence-First artifacts (`*_cluster_eval.csv`, `*_partition_eval.csv`, `QE`/`TE`, `--cluster-strategy local_max_gt2` check if K=2 is trivial), summarize candidates in `./reportes/exploration_scorecard.csv` + `exploration_log.md`, separate Author-Signaled Future Work from Analytically Assessed Unexplored Paths in Discussion, verify all citations 1:1 against OpenAlex, and compile `./reportes/manuscript_quantum_computing.{md,docx,pdf}`.
```

---

#### Template 2: Institutional Evaluation Technical Report & Peer Benchmarking

* **Skill Name:** `template-informe-tecnico-institucional`
* **Target Audience:** University Rectors, Institute Directors, Technical Councils, and Scientific Advisory Boards (INB UNAM, ICN, INCan style).
* **Recommended Slash Command Flow:**
  1. `/grill-me` $\to$ Clarify institutional ROR, internal departments, and homologous international peers.
  2. `/goal` $\to$ Execute the full pipeline without interruptions.
* **Full Prompt Example:**

```markdown
/goal Prepare an authoritative Institutional Scientometric Technical Report using `template-informe-tecnico-institucional` for the "Instituto de Neurobiología (INB), UNAM" covering the period 2014–2024.

Execution steps:
1. Load or harvest the institutional corpus into `./corpus_inb.parquet` (using canonical ROR `https://ror.org/01tmp8f25` via `openalex-harvester` or an existing departmental Parquet table).
2. Prepare comparative Parquet tables for 4 specialized homologous institutions of comparable scale (e.g., Montreal Neurological Institute, Instituto Cajal CSIC, Max Planck Institute for Brain Research, and Instituto de Fisiología Celular UNAM).
3. Check hyperauthorship: if works with >20 authors are negligible (<2%), report autonomous output and do not force an empty tripartite table.
4. Compute the 42-indicator battery into `./matrices/inb_benchmarking.parquet` and train both:
   a) A Static SOM benchmarking INB against national and international peers.
   b) A CMA+Splines Trajectory SOM tracing INB's historical path.
5. Audit Open Access routes, commercial APC expenditure (USD), and institutional collaboration networks.
6. Draft the formal technical report in `./reportes/informe_tecnico_inb_2024.md` with executive traffic-light indicators (🟢, 🟡, 🔴).
```

---

#### Template 3: Governance Policy Brief (S&T Policy for Senior Decision-Makers)

* **Skill Name:** `template-policy-brief-gobernanza`
* **Target Audience:** Science Ministers (SECIHTI), University Rectors, Parliamentary Committees, and Research Funding Agencies.
* **Format:** Concise, impactful, evidence-based executive document (2 to 4 pages).
* **Recommended Slash Command Flow:**
  1. `/grill-me` $\to$ Clarify the public policy trade-off and recipient body.
  2. `/plan` $\to$ Ensure adherence to the strict 4-section, 3-table format.
* **Full Prompt Example:**

```markdown
/grill-me I need a high-level Governance Policy Brief using `template-policy-brief-gobernanza` addressing "Commercial APC Expenditure vs. Strengthening Diamond Open Access Infrastructure".

Interview me on:
1. The decision-making audience (e.g., Ministry of Science, University Rectorate, or Funding Agency).
2. The empirical scope (harvested into `./corpus.parquet` via `openalex-harvester` with country/institutional filters or an existing national Parquet dataset).
3. The specific policy instruments to propose in the final recommendations matrix.
```

*(Once aligned, execute:)*

```markdown
/plan Generate the Policy Brief in `./reportes/policy_brief_apc_soberania.md`:
1. Extract observed `apc_paid_usd` and list prices across commercial publishers vs. Diamond repositories using `open-access-monitor`.
2. Train a SOM with `som-methodological-expert` identifying institutional clusters (Frontier vs. Regional Relevance vs. Vulnerable).
3. Structure the document strictly within 4 pages: Executive Synthesis, Quantitative Diagnosis (Table 1), SOM Evidence Against Ranking Reductionism (Table 2), Strategic Trade-Offs, and Actionable Recommendations Matrix (Table 3).
```

---

#### Template 4: Scientific Intelligence Report & Research Fronts Radar

* **Skill Name:** `template-radar-frentes-investigacion`
* **Target Audience:** Research Groups, Corporate R&D, Technology Observatories, and Foresight Panels.
* **Recommended Slash Command Flow:**
  1. `/plan` $\to$ Outline multimodal network comparison (coupling vs. co-citation vs. Topics).
  2. `/boost` $\to$ Deeply analyze alluvial lineages and synthesize core paper findings.
* **Full Prompt Example:**

```markdown
/boost Produce a comprehensive Scientific Intelligence & Technology Radar Report using `template-radar-frentes-investigacion` for "Direct Air Carbon Capture and Storage (DACCS)".

Required laboratory and curation steps:
1. Ingest `./corpus.parquet` (harvested via `openalex-harvester` or existing bibliometric Parquet).
2. Multimodal Front Detection: compare Leiden partitions under Bibliographic Coupling vs. OpenAlex Topics taxonomy. Retain the representation with higher modularity ($Q$).
3. Alluvial Lineage Tracking: compute Adjusted Mutual Information (AMI) across 3 temporal windows (2015–2018, 2019–2021, 2022–2025) and classify Persistence, Split, Merge, and Genesis events.
4. Core Papers Review: inspect the top 3 central papers in each active front and explain the sorbent materials, thermodynamic cycles, and energy requirements discussed.
5. Multidimensional SOM: project fronts across output volume, FWCI, % Top 10%, international collaboration, and patent citation velocity.
6. Save the final report in `./reportes/radar_tecnologico_daccs.md` accompanied by `./reportes/alluvial_lineages.html`.
```

---

#### Template 5: Exhaustive Multi-Scale Scientometric Study (39 Skills · 4-Wave Swarm)

* **Skill Name:** `template-estudio-cienciometrico-exhaustivo`
* **Target Use Cases:** Doctoral state-of-the-art baselines, comprehensive field monographs, and full institutional/national audits where the analyst should not pre-judge which granularity (`country`, `institution`, `source`, `author`, `topic`, `front`) carries the strongest signal.
* **Recommended Slash Command Flow:**
  1. `/plan` or `/grill-me` $\to$ Establish domain query, time window, and infrastructure scope (ClickHouse/SNII/RevistasLATAM/Bibliometrix availability).
  2. `/teamwork` *(4-Wave native `swarm` over `./evidence_vault/`)* or `/goal` *(sequential execution)*.
* **Full Prompt Example:**

```markdown
/teamwork Execute a full-spectrum multi-scale study using `template-estudio-cienciometrico-exhaustivo` on "<Research Domain or Institution>" (2015–2026):

1. Wave 0–1 (Gate & Harvest): Audit every skill in the 39-skill catalog into `./evidence_vault/00_gate/skills_execution_matrix.csv` (`QUEUED` vs `SKIPPED_OUT_OF_SCOPE` vs `SKIPPED_MISSING_DEP`) and harvest `./corpus.parquet` via `bibliometric-search-strategist` + `openalex-harvester`.
2. Wave 2 (4 Parallel Workers in disjoint `./evidence_vault/` dirs):
   - `worker-metrics-laws`: `tlachia-metrics-engine` across all active scales + `classical-bibliometrics-laws` (growth, Lotka, Bradford, Price).
   - `worker-networks-fronts`: `bibliometric-network-analyst` + `topics-research-fronts-intelligence` (`coupling` vs `cocitation` vs `topics`, `*_partition_eval.csv`, AMI alluvial lineages).
   - `worker-context-policy`: `geopolitical-science-mapping` (Salton affinity, sovereignty, 6 OA routes/APC USD, SDGs) + conditional editorial/SNII modules.
   - `worker-deep-lit`: `deep-literature-researcher` + `open-access-pdf-downloader` (`literature_review_draft.md` with N/A-strict synthesis + Author Future Work vs. Unexplored Paths).
3. Wave 3 (Multi-Scale SOM & Manifold): `semantic-manifold-expert` + Big SOM triad (`--norm divmax --grid-type big --max-k 15`, `QE`/`TE`, local-max $K>2$ check) across `country`, `institution`, `source`, `topic`, and `author_core`.
4. Wave 4 (Verifier & Monograph): Build `./evidence_vault/diagnostic_scorecard.csv`, run 1:1 OpenAlex reference verification, and compile `./reportes/estudio_exhaustivo_maestro.{md,docx,pdf}` keeping full reproducibility in `./evidence_vault/`.
```

---

## Appendix: Core Principles & Inviolable Rules

Every skill and script in this repository operates under five foundational principles:

1. **Workspace-First Principle:**

   - Raw data are harvested into `./corpus.parquet`.
   - Indicators and time series are computed into `./matrices/*.parquet` (46 untruncated columns: 42 numerical indicators + 4 metadata fields).
   - Reports, HTML dashboards, and PNG cards are saved to `./reportes/`.
   - LLMs never compute statistics in their context window from raw text; they consume verified columnar files.
2. **Data Integrity & Standardized Columnar Schemas:**

   - Raw bibliometric literature is always represented as a canonical document table in **Parquet format** (`./corpus.parquet`) with verified fields (`publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `author_names`, `institution_names`, `topics`).
   - All multi-indicator matrices are stored as Parquet files (`./matrices/*.parquet`) to guarantee columnar speed, zero data truncation, and perfect type safety across runs.
   - If utilizing the optional Advanced Mode with ClickHouse, queries must strictly respect the ZERO-JOIN policy using native array functions.
3. **Zero-Empty-Columns (`N/D` / `N/A`) Rule in Tables:**

   - If an indicator is unavailable for a given dataset, the column must be omitted from the output table rather than populated with placeholder strings.
4. **Sober Scientific Tone (Anti-Superlative Rule):**

   - No hyperbolic marketing adjectives (*"revolutionary"*, *"unprecedented"*, *"spectacular"*, *"astonishing"*). Writing must remain objective, rigorous, and evidence-grounded.
5. **Universal Language Rule:**

   - Scripts default to English labels and figures (`--lang en`).
   - When users interact in Spanish, the agent passes `--lang es` to all CLIs and writes all narrative prose, section titles, and tables in Spanish.
   - Downstream data schemas, column names, and API keys remain 100% standardized and unchanged across languages.
6. **Full Evidence-First & OpenAlex-First Principle:**

   - Analytical CLIs never discard intermediate curves or baseline diagnostics: SOM scripts persist complete `K = 2..15` curves (`*_cluster_eval.csv/.png`), `QE`/`TE`, SVD audit, `*_cluster_profiles.csv`, and `*_run_manifest.json` (`--norm divmax` default); network/front CLIs persist `*_partition_eval.csv/.png`, modularity `Q`, and `ami_window_summary.csv`.
   - All templates default autonomously to OpenAlex REST APIs (`openalex-harvester`) and 1:1 OpenAlex DOI verification before compiling `.md`, `.docx`, and `.pdf` deliverables, activating local ClickHouse only when explicitly configured (`CLICKHOUSE_HOST`).
