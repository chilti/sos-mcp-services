# SOS (Science of Science) MCP Services & Agent Skills
## Master User Manual for Anthropic Claude (Claude Code, Claude Desktop & Claude Projects)

> **Computational Scientometrics, Informetric Modeling, Bibliographic Big Data, and Topological Neural Cartography**
> Laboratorio de Dinámica no Lineal, Departamento de Matemáticas, Facultad de Ciencias & Centro de Ciencias de la Complejidad (C3), Universidad Nacional Autónoma de México (UNAM)

---

## Table of Contents
1. [Introduction: Claude's Equivalent to Slash Commands](#introduction-claudes-equivalent-to-slash-commands)
2. [Section 1: Installation & Setup (Basic vs. Advanced)](#section-1-installation--setup-basic-vs-advanced)
   - [1.1. Basic Standalone Setup in Claude Code (CLI)](#11-basic-standalone-setup-in-claude-code-cli)
   - [1.2. Basic Setup in Claude Desktop (`claude_desktop_config.json`)](#12-basic-setup-in-claude-desktop-claude_desktop_configjson)
   - [1.3. (Optional) Advanced Setup: Remote GPU Server via MCP SSE](#13-optional-advanced-setup-remote-gpu-server-via-mcp-sse)
3. [Section 2: Operating Modes & Equivalents to Slash Commands in Claude](#section-2-operating-modes--equivalents-to-slash-commands-in-claude)
   - [2.1. Mapping Antigravity Commands to Claude Capabilities](#21-mapping-antigravity-commands-to-claude-capabilities)
   - [2.2. Workflows Combining Skills with Claude Directives](#22-workflows-combining-skills-with-claude-directives)
     - [Workflow A: `[PLAN MODE]` + Delineation & Harvesting into Parquet](#workflow-a-plan-mode--delineation--harvesting-into-parquet)
     - [Workflow B: Extended Thinking + Research Fronts & Deep Literature](#workflow-b-extended-thinking--research-fronts--deep-literature)
     - [Workflow C: `[AUTONOMOUS GOAL]` + Neural Trajectory Mapping (SOM)](#workflow-c-autonomous-goal--neural-trajectory-mapping-som)
     - [Workflow D: Artifacts + Interactive Visualization Dashboards](#workflow-d-artifacts--interactive-visualization-dashboards)
     - [Workflow E: `[PARALLEL SWARM]` + Subagents with Disjoint Directories](#workflow-e-parallel-swarm--subagents-with-disjoint-directories)
4. [Section 3: Scientific Master Templates & the Curated Laboratory Protocol](#section-3-scientific-master-templates--the-curated-laboratory-protocol)
   - [3.1. The Curated Laboratory Protocol (Exploration, Full Evidence-First & Curation) in Claude](#31-the-curated-laboratory-protocol-exploration-full-evidence-first--curation-in-claude)
   - [3.2. Detailed Guide per Template for Claude](#32-detailed-guide-per-template-for-claude)
     - [Template 1: Original Research Article (IMRaD / IMRyD Format - Q1 Journal)](#template-1-original-research-article-imrad--imryd-format---q1-journal)
     - [Template 2: Institutional Evaluation Technical Report & Peer Benchmarking](#template-2-institutional-evaluation-technical-report--peer-benchmarking)
     - [Template 3: Governance Policy Brief (S&T Policy for Senior Decision-Makers)](#template-3-governance-policy-brief-st-policy-for-senior-decision-makers)
     - [Template 4: Scientific Intelligence Report & Research Fronts Radar](#template-4-scientific-intelligence-report--research-fronts-radar)
     - [Template 5: Exhaustive Multi-Scale Scientometric Study (39 Skills · 4-Wave Swarm)](#template-5-exhaustive-multi-scale-scientometric-study-39-skills--4-wave-swarm)
5. [Appendix: Core Principles & Standardized Parquet Schemas](#appendix-core-principles--standardized-parquet-schemas)

---

## Introduction: Claude's Equivalent to Slash Commands

While Antigravity uses chat slash commands (`/plan`, `/boost`, `/grill-me`, `/goal`), Anthropic Claude implements these capabilities through three complementary mechanisms:

1. **Native Slash Commands in Claude Code (CLI Agent):**
   - Claude Code (`claude`) includes built-in commands like `/compact` (compresses conversation history to free context window), `/clear` (resets session), `/cost` (tracks token expenditure), and `/init` (creates or updates project guidelines in `CLAUDE.md`).
2. **Extended Thinking Mode (Claude 3.7 Sonnet / Claude 3.5):**
   - Claude's toggleable **Extended Thinking** (high thinking token budget) is the direct architectural equivalent to `/boost`. It forces the model to deliberate on methodological trade-offs, test alternative network partitions, and curate scientific evidence before responding.
3. **Prompt Mode Directives (Prefix Triggers):**
   - For behavioral workflows like `/plan`, `/grill-me`, and `/goal`, Claude responds with high precision to structured mode prefixes (e.g., `[PLAN]`, `[INTERVIEW]`, `[AUTONOMOUS GOAL]`) backed by persistent instructions in `CLAUDE.md`.

---

## Section 1: Installation & Setup (Basic vs. Advanced)

To ensure universal portability, the ecosystem is built with a **Zero-Barrier Architecture**: **you do NOT need a local database server, ClickHouse cluster, or private OpenAlex snapshot to perform state-of-the-art scientometrics.**

---

### 1.1. Basic Standalone Setup in Claude Code (CLI)

Claude Code operates directly inside your terminal workspace. 

#### Copy-Paste Initial Prompt for Claude Code:

Launch `claude` in your target research folder and paste:

```markdown
Hello Claude. I want to set up and activate the SOS (Science of Science) Agent Skills in BASIC / STANDALONE mode (zero database infrastructure required). Please perform the following steps:

1. Repository & Skills Discovery:
   - Check if this workspace contains `sos-mcp-services`. If not, clone it:
     `git clone https://github.com/chilti/sos-mcp-services.git`
   - Locate the `.agents/skills/` directory inside `sos-mcp-services`.
   - Index the 39 skills and add their reference instructions to `CLAUDE.md` in this directory so you can invoke their CLI tools anytime.

2. Python Runtime & Scientific Libraries:
   - Use an active Python virtual environment with Python >= 3.10 (or create one: `python3 -m venv .venv && source .venv/bin/activate`).
   - Ensure standard scientific dependencies are installed: `pip install -r sos-mcp-services/requirements.txt` (or verify `pandas`, `pyarrow`, `duckdb`, `numpy`, `scipy`, `scikit-learn`, `networkx`, `matplotlib`, `plotly`).
   - Note: Do NOT require or configure any ClickHouse database connection, Docker containers, or private OpenAlex database snapshot servers.

3. Verification:
   - Run a quick syntax and CLI check on:
     * `python sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py --help`
     * `python sos-mcp-services/.agents/skills/classical-bibliometrics-laws/scripts/bibliometric_laws_cli.py --help`
     * `python sos-mcp-services/.agents/skills/openalex-harvester/scripts/openalex_harvest_cli.py --help`
     * `python sos-mcp-services/.agents/skills/som-methodological-expert/scripts/som_pipeline_cli.py --help`
   - Confirm that all tools are ready to harvest via public REST APIs (OpenAlex, arXiv, PubMed, Semantic Scholar) and process local Parquet/CSV datasets.
   - Report when the environment is ready for research.
```

---

### 1.2. Basic Setup in Claude Desktop (`claude_desktop_config.json`)

If you use the **Claude Desktop** application, you can register the analytical MCP services directly. Anthropic created the Model Context Protocol (MCP), so configuration is native.

Edit your Claude Desktop configuration file:
* **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
* **Linux:** `~/.config/Claude/claude_desktop_config.json`

Add the standalone analytical microservices pointing to your local Python interpreter:

```json
{
  "mcpServers": {
    "sos_plmetrix": {
      "command": "python",
      "args": ["/path/to/sos-mcp-services/services/plmetrix/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/sos-mcp-services",
        "MCP_TRANSPORT": "stdio"
      }
    },
    "sos_knomap": {
      "command": "python",
      "args": ["/path/to/sos-mcp-services/services/knomap/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/sos-mcp-services",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

---

### 1.3. (Optional) Advanced Setup: Remote GPU Server via MCP SSE

If your research group operates a central GPU server hosting ClickHouse (569M works snapshot) and containerized MCP services, connect Claude Desktop directly via SSE:

```json
{
  "mcpServers": {
    "sos_knomap": {
      "url": "http://<GPU_SERVER_IP>:8010/sse"
    },
    "sos_plmetrix": {
      "url": "http://<GPU_SERVER_IP>:8012/sse"
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

---

## Section 2: Operating Modes & Equivalents to Slash Commands in Claude

### 2.1. Mapping Antigravity Commands to Claude Capabilities

| Antigravity Command | Claude Equivalent | How to Trigger in Claude | Purpose & Behavior |
| :--- | :--- | :--- | :--- |
| **`/boost`** | **Extended Thinking (High Budget)** | Enable **Thinking** in Claude UI or add directive `[THINK DEEP / METHODOLOGICAL CURATION]` | Deep multi-perspective reasoning; tests competing models (e.g., bibliographic coupling vs. co-citation), audits statistical fits, and curates evidence without hallucinations. |
| **`/plan`** | **Structured Plan Directive** | Prefix prompt with `[PLAN MODE]` | Forces Claude to generate an exploratory roadmap first, enumerate tools to run, and wait for user confirmation before executing commands. |
| **`/grill-me`** | **Alignment Interview Directive** | Prefix prompt with `[INTERVIEW MODE]` | Instructs Claude to act as a rigorous scientific editor, asking 3–5 multiple-choice questions to settle research questions, filters, and benchmarking pairs. |
| **`/goal`** | **Autonomous End-to-End Execution** | Prefix prompt with `[AUTONOMOUS GOAL]` | Instructs Claude Code to execute all pipeline stages (harvesting $\to$ matrices $\to$ SOM $\to$ report) autonomously without pausing for trivial acknowledgments. |
| **`/compact`** | **Native `/compact` Command** | Type `/compact` directly in Claude Code | Summarizes conversation context, preserving memory of generated Parquet files while clearing token clutter. |
| **`/teamwork`** | **Claude Code Parallel Subagents** | Prefix prompt with `[PARALLEL SWARM]` (enable Agent Teams / subagents in Claude Code) | Fans out independent exploratory branches (laws, networks/fronts, deep review, SOM) across disjoint workspace subfolders after `./corpus.parquet` is ready, returning only manifest paths and scorecards to the coordinator. |
| **`/browser`** | **Claude Artifacts / HTML Preview** | Request output as a standalone HTML artifact | Renders interactive Plotly charts, KnoMap force-directed graphs, and PyVis networks inside Claude's Artifact pane. |

---

### 2.2. Workflows Combining Skills with Claude Directives

#### Workflow A: `[PLAN MODE]` + Delineation & Harvesting into Parquet
```markdown
[PLAN MODE] Delineate the global scientific output on "Solid-State Sodium Batteries" using the skill `bibliometric-search-strategist`. 

Follow the GLOBAL guideline (ISSI):
1. Extract conceptual seed blocks (keywords, title phrases, and core CWTS/OpenAlex topics).
2. Harvest the records using `openalex-harvester` (with cursor pagination) into `./corpus.parquet`.
3. Run `tlachia-metrics-engine` to compute the baseline 42-indicator summary table in `./matrices/summary.parquet`.

Present the planned steps and parameters first, and ask for my confirmation before downloading data.
```

#### Workflow B: Extended Thinking + Research Fronts & Deep Literature
*(Turn ON Extended Thinking in Claude)*
```markdown
[THINK DEEP] Analyze the intellectual structure and active research fronts in `./corpus.parquet` using `topics-research-fronts-intelligence` and `deep-literature-researcher`.

Required execution:
1. Build a bibliographic coupling network with Leiden CPM partitioning.
2. Track longitudinal alluvial lineages (AMI) across 3-year periods to detect Persistence, Split, Merge, and Genesis events.
3. Identify the top 3 core papers (highest in-cluster centrality and citation density) for the 5 largest fronts.
4. Read the core papers substantive text in the corpus and synthesize what experimental architectures, materials, or mechanisms are actually discovered (explain the science, do not merely list metadata).
5. Generate `./reportes/alluvial_lineages.html` and `./reportes/fronts_summary.csv`.
```

#### Workflow C: `[AUTONOMOUS GOAL]` + Neural Trajectory Mapping (SOM)
```markdown
[AUTONOMOUS GOAL] Execute a complete neural trajectory mapping over `./matrices/by_country_annual.parquet` using `som-trajectory-mapping` and `som-methodological-expert`.

Execution requirements:
1. Apply Centered Moving Average (CMA, window=3) to smooth indicator noise.
2. Train a 2D hexagonal toroidal SOM grid sized via SVD ratio ($N \times M \approx 25N$).
3. Trace continuous parametric cubic spline trajectories for the top 5 focal countries (e.g., USA, China, Germany, Japan, South Korea).
4. Identify topological inflection points, community maturation phases, and metric paradoxes (such as volume surging while normalized FWCI declines).
5. Persist `./reportes/som_trajectories.png` and `./reportes/som_dashboard.html` with default English labels (`--lang en`).
```

#### Workflow D: Artifacts + Interactive Visualization Dashboards
```markdown
Generate the Open Access and APC economic breakdown for `./corpus.parquet` using `open-access-monitor`. 
Render the interactive dashboard as an HTML artifact so I can view the Plotly donut charts, annual transition lines, and sovereign vs. commercial APC KPI cards directly in the Claude preview panel.
```

#### Workflow E: `[PARALLEL SWARM]` + Subagents with Disjoint Directories
*(Recommended in Claude Code CLI after `./corpus.parquet` and `./matrices/` are prepared)*
```markdown
[PARALLEL SWARM] Dispatch parallel Claude Code subagents over `./corpus.parquet` and `./matrices/`, assigning strictly disjoint output folders:
1. Subagent A (`./lab_exploration/01_laws/`): run `classical-bibliometrics-laws` (`growth-phase`, `lotka`, `bradford`, `price-index`).
2. Subagent B (`./lab_exploration/02_networks_fronts/`): run competing `coupling` vs. `cocitation` partitions (`topics-research-fronts-intelligence` + `bibliometric-network-analyst`), persisting `*_partition_eval.csv` and `ami_window_summary.csv`.
3. Subagent C (`./lab_exploration/03_deep_lit/`): run `deep-literature-researcher` (+ `open-access-pdf-downloader`) with strict N/A synthesis, separating Author-Signaled Future Work from Analytically Assessed Unexplored Paths.
4. Subagent D (`./lab_exploration/04_som/`): run Big SOM (`--norm divmax --grid-type big --max-k 15`) with `som-methodological-expert`, saving `QE`, `TE`, and `*_cluster_eval.csv` (checking local maxima K>2 if K=2 is trivial).
Collect only summary metrics and `*_run_manifest.json` paths, consolidate `./reportes/exploration_scorecard.csv`, and curate the final deliverable.
```

---

## Section 3: Scientific Master Templates & the Curated Laboratory Protocol

The repository includes **5 Master Templates** (`template-*`) adapted from the Laboratorio de Dinámica no Lineal (Departamento de Matemáticas, Facultad de Ciencias) & Centro de Ciencias de la Complejidad (C3), UNAM scientometric research group.

### 3.1. The Curated Laboratory Protocol (Exploration, Full Evidence-First & Curation) in Claude

```
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE I: LABORATORY PHASE (Sequential or Parallel Subagents)           │
│  - Harvest literature into `./corpus.parquet` (OpenAlex-first API).    │
│  - Compute full 46-column matrices (42 indicators + 4 meta) in Parquet │
│    across focal scales filtered by critical-mass (`min_docs`).         │
│  - Execute competing skills preserving Full Evidence-First logs:       │
│      * Growth kinetics, Lotka/Bradford, Price Index (`AIC`, `RMSE`).   │
│      * Networks & Fronts (`*_partition_eval.csv`, Q, AMI lineages).    │
│      * Big SOM (`--norm divmax --max-k 15`, QE/TE, `*_cluster_eval`).  │
│      * Core paper reading + OA PDF extraction (N/A-strict synthesis).  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE II–III: CURATION, AUDIT & COMPILATION (Extended Thinking)        │
│  - Summarize candidates in `exploration_scorecard.csv` / `diagnostic_  │
│    scorecard.csv` (preserving negative or degenerate K=2 findings).    │
│  - Select the primary narrative arc (3–5 blocks for IMRyD articles).   │
│  - Dual Discussion: Author-Signaled Future Work vs. Unexplored Paths.  │
│  - Zero Empty Columns (`N/D`), Sober Tone, Zero-Scaffolding Leakage.   │
│  - 1:1 OpenAlex DOI verification & compile `.md`, `.docx`, `.pdf`.     │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 3.2. Detailed Guide per Template for Claude

#### Template 1: Original Research Article (IMRaD / IMRyD Format - Q1 Journal)
* **Skill Name:** `template-articulo-cientifico-imryd`
* **Scope:** Focused Q1/Q2 manuscript centered on 3–5 curated analytical blocks and **2–3 RQ-linked scales** (not a 39-skill sweep; escalate to `template-estudio-cienciometrico-exhaustivo` if full-spectrum exploration across every scale is needed).
* **Target Venues:** *Journal of Informetrics*, *Scientometrics*, *Quantitative Science Studies*, *Research Evaluation*.
* **Step 1: Alignment Interview:**
```markdown
[INTERVIEW MODE] I want to draft an original scientific research manuscript using `template-articulo-cientifico-imryd` on the global evolution of "Quantum Computing Architectures (Superconducting vs. Trapped Ions vs. Photonic)" from 2000 to 2025. 

Interview me regarding:
1. Research questions and core hypotheses ($RQ_1 \dots RQ_k$).
2. Data sources (harvesting via `openalex-harvester` into `./corpus.parquet` vs. ingesting an existing Parquet/CSV dataset) and the 2–3 focal granularities (`min_docs >= 3-5`).
3. Which analytical families to test in competition in Stage I (classical kinetics, Leiden coupling vs. co-citation, core paper review + OA PDFs, and Big SOM `--norm divmax`).
4. Target journal and execution mode (`[AUTONOMOUS GOAL]` sequential vs. bounded `[PARALLEL SWARM]` across 3–4 RQ families).
```
* **Step 2: Execution & Drafting with Extended Thinking (or Bounded Subagents):**
```markdown
[THINK DEEP / METHODOLOGICAL CURATION] Proceed with Stage I (Targeted Laboratory Exploration in `./lab_exploration/`), Stage II (Curation), and Stage III (1:1 OpenAlex Audit & Compilation) of `template-articulo-cientifico-imryd`. 

Compute full 46-column matrices in `./matrices/` for the selected 2–3 scales, preserve Full Evidence-First curves (`*_cluster_eval.csv`, `*_partition_eval.csv`, `QE`/`TE`, `--cluster-strategy local_max_gt2` check if K=2 is trivial), consolidate `./reportes/exploration_scorecard.csv` + `exploration_log.md`, contrast Author-Signaled Future Work vs. Analytically Assessed Unexplored Paths in Discussion, and compile `./reportes/manuscript_quantum_computing.{md,docx,pdf}` with zero empty table columns.
```
*(Tip: In Claude Code, run `/compact` before drafting the full discussion to maximize context clarity).*

---

#### Template 2: Institutional Evaluation Technical Report & Peer Benchmarking
* **Skill Name:** `template-informe-tecnico-institucional`
* **Target Audience:** University Leadership, Institute Directors, Technical Councils (INB UNAM, ICN, INCan style).
```markdown
[AUTONOMOUS GOAL] Prepare an authoritative Institutional Scientometric Technical Report using `template-informe-tecnico-institucional` for the "Instituto de Neurobiología (INB), UNAM" covering the period 2014–2024.

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
* **Format:** 2 to 4 pages for Science Ministers (SECIHTI), Rectors, and Legislative Committees.
```markdown
[INTERVIEW MODE] I need a high-level Governance Policy Brief using `template-policy-brief-gobernanza` addressing "Commercial APC Expenditure vs. Strengthening Diamond Open Access Infrastructure".

Interview me on:
1. The decision-making audience (e.g., Ministry of Science, University Rectorate, or Funding Agency).
2. The empirical scope (harvested into `./corpus.parquet` via `openalex-harvester` with country/institutional filters or an existing national Parquet dataset).
3. The specific policy instruments to propose in the final recommendations matrix.
```
*(After answering the interview, execute with:)*
```markdown
[PLAN MODE] Generate the Policy Brief in `./reportes/policy_brief_apc_soberania.md`:
1. Extract observed `apc_paid_usd` and list prices across commercial publishers vs. Diamond repositories using `open-access-monitor`.
2. Train a SOM with `som-methodological-expert` identifying institutional clusters (Frontier vs. Regional Relevance vs. Vulnerable).
3. Structure the document strictly within 4 pages: Executive Synthesis, Quantitative Diagnosis (Table 1), SOM Evidence Against Ranking Reductionism (Table 2), Strategic Trade-Offs, and Actionable Recommendations Matrix (Table 3).
```

---

#### Template 4: Scientific Intelligence Report & Research Fronts Radar
* **Skill Name:** `template-radar-frentes-investigacion`
* **Target Audience:** Research Groups, Technology Observatories, and Foresight Panels.
```markdown
[THINK DEEP] Produce a comprehensive Scientific Intelligence & Technology Radar Report using `template-radar-frentes-investigacion` for "Direct Air Carbon Capture and Storage (DACCS)".

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
* **Target Use Cases:** Comprehensive field monographs, doctoral state-of-the-art baselines, and full institutional/national audits across all applicable skills and scales (`country`, `institution`, `source`, `author`, `topic`, `front`).
```markdown
[PARALLEL SWARM] [AUTONOMOUS GOAL] Execute `template-estudio-cienciometrico-exhaustivo` for "<Research Domain or Institution>" (2015–2026):

1. Wave 0–1 (Gate & Harvest): Write `./evidence_vault/00_gate/skills_execution_matrix.csv` auditing all 39 skills (`QUEUED` / `SKIPPED_OUT_OF_SCOPE` / `SKIPPED_MISSING_DEP`) and harvest `./corpus.parquet` via `bibliometric-search-strategist` + `openalex-harvester`.
2. Wave 2 (Parallel Subagents in disjoint `./evidence_vault/` folders):
   - Metrics & Laws (`./evidence_vault/02_metrics/` & `03_laws/`): `tlachia-metrics-engine` across all active scales + `classical-bibliometrics-laws`.
   - Networks & Fronts (`./evidence_vault/04_networks/` & `05_fronts/`): `bibliometric-network-analyst` + `topics-research-fronts-intelligence` (`coupling` vs `cocitation` vs `topics`, `*_partition_eval.csv`, AMI alluvial lineages).
   - Context & Policy (`./evidence_vault/06_context/`): `geopolitical-science-mapping` + conditional editorial/SNII modules.
   - Deep Literature (`./evidence_vault/07_literature/`): `deep-literature-researcher` + `open-access-pdf-downloader` (`literature_review_draft.md` separating Author-Signaled Future Work from Unexplored Paths).
3. Wave 3 (Multi-Scale SOM): Run `semantic-manifold-expert` + Big SOM triad (`--norm divmax --grid-type big --max-k 15`, `QE`/`TE`, local-max K>2 check) sequentially across `country`, `institution`, `source`, `topic`, and `author_core`.
4. Wave 4 (Verifier & Compilation): Consolidate `./evidence_vault/diagnostic_scorecard.csv`, verify every reference 1:1 against OpenAlex, and compile `./reportes/estudio_exhaustivo_maestro.{md,docx,pdf}`.
```

---

## Appendix: Core Principles & Standardized Parquet Schemas

1. **Workspace-First Principle:**
   - Raw data are saved in `./corpus.parquet`.
   - Indicators and time series are computed in `./matrices/*.parquet` (46 untruncated columns: 42 numerical indicators + 4 metadata fields).
   - Artifacts, reports, and HTML viewers are persisted in `./reportes/`.
2. **Data Integrity & Standardized Columnar Schemas:**
   - The canonical table `./corpus.parquet` contains verified fields (`publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `author_names`, `institution_names`, `topics`).
   - All indicator matrices use Parquet to ensure zero truncation, high compression, and consistent data types across Python and R (`bibliometrix`).
3. **Zero Empty Columns (`N/D` / `N/A`) Rule:**
   - Never generate tables with columns populated by placeholders. Only report verified, computed indicators.
4. **Sober Scientific Tone:**
   - Prohibit superlatives and marketing hype. Maintain a measured, evidence-grounded academic register.
5. **Universal Language Rule:**
   - Scripts default to English (`--lang en`). Pass `--lang es` when users interact in Spanish, ensuring all figures, axis titles, and report sections match the user's language.
6. **Full Evidence-First & OpenAlex-First Rule:**
   - Analytical CLIs persist complete `K = 2..15` curves (`*_cluster_eval.csv/.png`), `QE`/`TE`, SVD ratios, `*_cluster_profiles.csv`, modularity curves (`*_partition_eval.csv`), `ami_window_summary.csv`, and `*_run_manifest.json` (`--norm divmax` default).
   - All templates default to public OpenAlex APIs and enforce 1:1 OpenAlex DOI verification before compiling `.md`, `.docx`, and `.pdf` deliverables.

