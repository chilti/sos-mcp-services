# SOS (Science of Science) MCP Services & Agent Skills

## Master User Manual for OpenAI ChatGPT (Web, Advanced Data Analysis, Canvas & Custom GPTs)

> **Computational Scientometrics, Informetric Modeling, Bibliographic Big Data, and Topological Neural Cartography**
> Centro de Ciencias de la Complejidad (C3) & Facultad de Ciencias, Universidad Nacional Autónoma de México (UNAM)

---

## Table of Contents

1. [Introduction: How ChatGPT Handles Slash Command Workflows](#introduction-how-chatgpt-handles-slash-command-workflows)
2. [Section 1: Installation &amp; Setup (ChatGPT Work, Codex &amp; Custom GPTs)](#section-1-installation--setup-chatgpt-work-codex--custom-gpts)
   - [1.1. Copy-Paste Kickoff Prompt for ChatGPT Work, Team &amp; Web (Project / Custom Instructions)](#11-copy-paste-kickoff-prompt-for-chatgpt-work-team--web-project--custom-instructions)
   - [1.2. Copy-Paste Setup Prompt for OpenAI Codex &amp; CLI Agents](#12-copy-paste-setup-prompt-for-openai-codex--cli-agents)
   - [1.3. Manual Local CLI Setup &amp; Uploading Parquet Datasets](#13-manual-local-cli-setup--uploading-parquet-datasets)
   - [1.4. (Optional) Packaging as an Institutional Custom GPT](#14-optional-packaging-as-an-institutional-custom-gpt)
3. [Section 2: Operating Modes &amp; Equivalents to Slash Commands in ChatGPT](#section-2-operating-modes--equivalents-to-slash-commands-in-chatgpt)
   - [2.1. Mapping Antigravity Commands to ChatGPT Features](#21-mapping-antigravity-commands-to-chatgpt-features)
   - [2.2. Workflows Combining Skills with ChatGPT Directives](#22-workflows-combining-skills-with-chatgpt-directives)
     - [Workflow A: `[PLAN MODE]` + Field Delineation &amp; Harvesting into Parquet](#workflow-a-plan-mode--field-delineation--harvesting-into-parquet)
     - [Workflow B: Reasoning Models (`o1` / `o3-mini`) + Research Fronts &amp; Deep Literature](#workflow-b-reasoning-models-o1--o3-mini--research-fronts--deep-literature)
     - [Workflow C: `[AUTONOMOUS PIPELINE]` + Neural Trajectory Mapping (SOM)](#workflow-c-autonomous-pipeline--neural-trajectory-mapping-som)
     - [Workflow D: `[CANVAS MODE]` + Interactive Document Drafting](#workflow-d-canvas-mode--interactive-document-drafting)
4. [Section 3: Scientific Master Templates &amp; the 2-Stage Protocol](#section-3-scientific-master-templates--the-2-stage-protocol)
   - [3.1. The 2-Stage Protocol (Exploration vs. Curation) in ChatGPT](#31-the-2-stage-protocol-exploration-vs-curation-in-chatgpt)
   - [3.2. Detailed Guide per Template for ChatGPT](#32-detailed-guide-per-template-for-chatgpt)
     - [Template 1: Original Research Article (IMRaD / IMRyD Format - Q1 Journal)](#template-1-original-research-article-imrad--imryd-format---q1-journal)
     - [Template 2: Institutional Evaluation Technical Report &amp; Peer Benchmarking](#template-2-institutional-evaluation-technical-report--peer-benchmarking)
     - [Template 3: Governance Policy Brief (S&amp;T Policy for Senior Decision-Makers)](#template-3-governance-policy-brief-st-policy-for-senior-decision-makers)
     - [Template 4: Scientific Intelligence Report &amp; Research Fronts Radar](#template-4-scientific-intelligence-report--research-fronts-radar)
5. [Appendix: Core Principles &amp; Standardized Parquet Schemas](#appendix-core-principles--standardized-parquet-schemas)

---

## Introduction: How ChatGPT Handles Slash Command Workflows

Unlike command-line developer agents, standard ChatGPT Web does not feature slash commands (`/plan`, `/boost`, etc.). However, ChatGPT achieves equivalent or superior capabilities through **four native platform features**:

1. **Reasoning Models (`o1`, `o3-mini`):**
   - Direct architectural equivalent to `/boost`. These models use internal chain-of-thought tokens to deliberate on methodological trade-offs, test statistical distributions, and curate scientific evidence without hallucinating.
2. **Advanced Data Analysis (Code Interpreter Sandbox):**
   - ChatGPT can execute Python in a secure container, load `.parquet` and `.csv` files, compute 42+ indicators, run Leiden community detection, generate matplotlib/seaborn charts, and export `.parquet`, `.png`, and `.docx` packages for download.
3. **Canvas Interface:**
   - Dedicated side-by-side editing environment within ChatGPT, ideal for drafting and refining canonical IMRaD articles and policy briefs section by section.
4. **Structured Mode Directives (Prefix Prompts):**
   - By prepending structured tags (e.g., `[PLAN]`, `[INTERVIEW]`, `[AUTONOMOUS PIPELINE]`), you instruct ChatGPT to adopt specific agentic workflows (such as conducting an alignment interview before generating code).

---

## Section 1: Installation & Setup (ChatGPT Work, Codex & Custom GPTs)

To ensure universal portability, the ecosystem is built with a **Zero-Barrier Architecture**: **you do NOT need a local database server, ClickHouse cluster, or private OpenAlex snapshot to perform state-of-the-art scientometrics.**

---

### 1.1. Copy-Paste Kickoff Prompt for ChatGPT Work, Team & Web (Project / Custom Instructions)

If you use **ChatGPT Work, Team, Enterprise, or Plus** in the browser (with Advanced Data Analysis and Canvas), paste the following Master Kickoff Prompt as your first message—or save it permanently inside your ChatGPT **Project Instructions** or **Custom Instructions**:

```markdown
You are now acting as the **SOS (Science of Science) Scientometric Copilot**, developed by the Centro de Ciencias de la Complejidad (C3) and Facultad de Ciencias, UNAM (LabSOM research group).

Your methodological specialization covers:
1. Computational Scientometrics, informetric modeling, and classical bibliometric laws (Lotka, Bradford, Price, Egghe).
2. Columnar processing of scientific corpora in Parquet/CSV (`corpus.parquet`, `summary.parquet`) using Advanced Data Analysis (Python Code Interpreter).
3. The 42-indicator scientometric battery (FWCI, % Top 10%, international collaboration rates, Gini specialization, 6 Open Access pathways, and commercial APC expenditure in USD).
4. Research fronts cartography using Leiden community detection on bibliographic coupling networks and longitudinal alluvial tracking with Adjusted Mutual Information (AMI).
5. Topological neural cartography and multidimensional performance trajectories using Kohonen Self-Organizing Maps (SOM).

Core Operating Principles You Must Strictly Enforce:
- **The 2-Stage Protocol:**
  * Stage I (Laboratory): Use Python (Code Interpreter) to explore datasets, compute metrics, test statistical fits, and uncover latent patterns.
  * Stage II (Curation & Synthesis): Discard uninformative fits, prune noisy variables, structure the narrative into 3–5 core analytical blocks, and draft prose in Canvas.
- **Zero Empty Columns Rule:** Never output tables with columns filled with `N/A`, `N/D`, or placeholders. Only report verified, computed metrics.
- **Sober Academic Tone:** Strictly prohibit marketing hype, buzzwords, and superlatives ("groundbreaking", "revolutionary", "fascinating"). Maintain a measured, evidence-grounded scientific register.
- **Grounded Evidence Extraction:** Never fabricate sample sizes ($N$) or metrics. If an abstract or full text lacks a datum, explicitly state `N/A (Not declared in text)`.
- **Bilingual Execution:** Default to English. When I interact in Spanish, generate all prose, table headers, and plot labels in Spanish (`--lang es`).

Mode Directives You Support:
- `[PLAN MODE]`: Outline a step-by-step analytical roadmap and wait for my confirmation before executing Python code.
- `[DEEP REASONING]`: Engage deep deliberative reasoning (`o1` / `o3-mini`) to evaluate methodological trade-offs and curate scientific evidence without hallucinations.
- `[INTERVIEW MODE]`: Interview me with 3–5 concise multiple-choice questions to align research scope and criteria before running analyses.
- `[AUTONOMOUS PIPELINE]`: Execute the end-to-end Python pipeline in one run (inspect -> compute indicators -> cluster -> plot -> summarize).
- `[CANVAS MODE]`: Open the manuscript or report draft directly in ChatGPT Canvas for side-by-side iterative editing.

Acknowledge your role and confirm that you are ready to receive my research questions, seed DOIs, or uploaded Parquet/CSV files.
```

---

### 1.2. Copy-Paste Setup Prompt for OpenAI Codex & CLI Agents

If you use **OpenAI Codex CLI** or an autonomous OpenAI coding agent directly in your terminal workspace, paste the following prompt to automatically clone the repository, index all **38 Agent Skills**, and verify the Python runtime:

```markdown
Hello Codex. I want to set up and activate the SOS (Science of Science) Agent Skills in BASIC / STANDALONE mode (zero database infrastructure required). Please perform the following steps:

1. Repository & Skills Discovery:
   - Check if this workspace already contains `sos-mcp-services`. If not, clone it using:
     `git clone https://github.com/chilti/sos-mcp-services.git`
   - Locate the `.agents/skills/` directory inside `sos-mcp-services`.
   - Index all 38 skills and create or update `AGENTS.md` (or `CODEX.md`) in this directory so you can invoke their CLI tools and workflows anytime.

2. Python Runtime & Scientific Libraries:
   - Use an active Python virtual environment with Python >= 3.10 (or create one: `python3 -m venv .venv && source .venv/bin/activate`).
   - Ensure standard scientific dependencies are installed: `pip install -r sos-mcp-services/requirements.txt` (or verify `pandas`, `pyarrow`, `duckdb`, `numpy`, `scipy`, `scikit-learn`, `networkx`, `matplotlib`, `plotly`).
   - Note: Do NOT require or configure any ClickHouse database connection, Docker containers, or private OpenAlex database snapshot servers.

3. Verification:
   - Run a quick syntax and CLI check on:
     * `python sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py --help`
     * `python sos-mcp-services/.agents/skills/classical-bibliometrics-laws/scripts/bibliometric_laws_cli.py --help`
     * `python sos-mcp-services/.agents/skills/openalex-harvester/scripts/openalex_harvest_cli.py --help`
     * `python sos-mcp-services/.agents/skills/deep-literature-researcher/scripts/citation_snowball.py --help`
     * `python sos-mcp-services/.agents/skills/open-access-pdf-downloader/scripts/download_oa_pdfs.py --help`
   - Confirm that all tools are ready to harvest via public REST APIs (OpenAlex, arXiv, PubMed, Semantic Scholar) and process local Parquet/CSV datasets.
   - Report when the environment is ready for scientometric research.
```

---

### 1.3. Manual Local CLI Setup & Uploading Parquet Datasets

If you prefer to prepare your datasets manually on your local machine before uploading them to ChatGPT Web:

```bash
# 1. Clone the repository
git clone https://github.com/chilti/sos-mcp-services.git
cd sos-mcp-services

# 2. Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Harvest your corpus via public REST APIs (OpenAlex cursor pagination, arXiv, PubMed)
python .agents/skills/openalex-harvester/scripts/openalex_harvest_cli.py \
  --query "Solid-State Sodium Batteries" \
  --output ./corpus.parquet

# 5. Compute the 42-indicator battery
python .agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py \
  calculate-summary \
  --input ./corpus.parquet \
  --output ./matrices/summary.parquet
```

#### Uploading to ChatGPT (Advanced Data Analysis):
1. Open ChatGPT (select **GPT-4o** or **o1** / **o3-mini**).
2. Attach `./corpus.parquet` and any files from `./matrices/` using the paperclip / upload button.
3. Paste the prompt directive corresponding to your desired template or skill (see Section 2 and 3). ChatGPT will use its Python sandbox to inspect columns, calculate matrices, generate plots, and draft the text.

---

### 1.4. (Optional) Packaging as an Institutional Custom GPT

If you want your research group or university to have a permanent **"SOS Scientometric Copilot"** in ChatGPT:

1. In ChatGPT, go to **Explore GPTs** $\to$ **Create a GPT**.
2. **Name:** `SOS Science of Science Copilot`
3. **Description:** `Expert in computational scientometrics, informetric modeling, research fronts, and Kohonen SOM topological cartography.`
4. **Instructions:** Copy and paste the core methodological rules from this manual (the 2-Stage Protocol, zero empty columns rule, anti-superlative tone, and 42-indicator definitions).
5. **Knowledge:** Upload the reference files:
   - `references/tlachia_indicators_mathematical_handbook.md`
   - `references/classical_laws_mathematical_foundations.md`
   - `references/alluvial_longitudinal_guide.md`
   - `docs/antigravity_gemini_manual.md`
6. **Capabilities:** Enable **Code Interpreter & Data Analysis**.

---

## Section 2: Operating Modes & Equivalents to Slash Commands in ChatGPT

### 2.1. Mapping Antigravity Commands to ChatGPT Features

| Antigravity Command     | ChatGPT Equivalent                               | How to Trigger in ChatGPT                                               | Purpose & Behavior                                                                                                                                                    |
| :---------------------- | :----------------------------------------------- | :---------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`/boost`**    | **Reasoning Models (`o1`, `o3-mini`)** | Select model `o1` or `o3-mini`, or prefix with `[DEEP REASONING]` | Multi-perspective scientific deliberation; evaluates competing network models, audits statistical fits, and curates evidence without hallucinations.                  |
| **`/plan`**     | **Step-by-Step Plan Directive**            | Prefix prompt with `[PLAN MODE]`                                      | Forces ChatGPT to generate an exploratory roadmap first, describe the Python analysis pipeline, and wait for confirmation before computing.                           |
| **`/grill-me`** | **Alignment Interview Directive**          | Prefix prompt with `[INTERVIEW MODE]`                                 | Instructs ChatGPT to act as a rigorous peer reviewer, asking 3–5 multiple-choice questions to settle research questions, filters, and benchmarking pairs.            |
| **`/goal`**     | **Autonomous Python Pipeline**             | Prefix prompt with `[AUTONOMOUS PIPELINE]`                            | Instructs ChatGPT's Code Interpreter to execute all pipeline stages (inspect $\to$ indicators $\to$ clusters $\to$ tables $\to$ plots) in one continuous run. |
| **`/compact`**  | **Memory Checkpoint Directive**            | Prefix prompt with `[CHECKPOINT & RECAP]`                             | Instructs ChatGPT to summarize confirmed statistical findings and clear intermediate code logs before drafting prose.                                                 |
| **`/browser`**  | **Canvas Document Editor**                 | Prefix prompt with `[OPEN IN CANVAS]`                                 | Opens ChatGPT Canvas for side-by-side iterative drafting of manuscripts, reports, and tables.                                                                         |

---

### 2.2. Workflows Combining Skills with ChatGPT Directives

#### Workflow A: `[PLAN MODE]` + Field Delineation & Harvesting into Parquet

```markdown
[PLAN MODE] I want to analyze the global scientific output on "Solid-State Sodium Batteries" following the GLOBAL guideline (ISSI) and the methodology of `bibliometric-search-strategist`.

Please outline a step-by-step analytical plan:
1. Formulation of conceptual seed blocks (keywords, title terms, core CWTS/OpenAlex topics).
2. Verification steps for `./corpus.parquet`.
3. Computation of the baseline 42-indicator summary table in `./matrices/summary.parquet` using `tlachia-metrics-engine`.

Present the plan first and wait for my approval before executing any code in Python.
```

#### Workflow B: Reasoning Models (`o1` / `o3-mini`) + Research Fronts & Deep Literature

*(Select model `o1` or `o3-mini` in ChatGPT and attach `./corpus.parquet`)*

```markdown
[DEEP REASONING] Analyze the intellectual structure and active research fronts in the attached `corpus.parquet` file.

Execution requirements:
1. In Python, construct a bibliographic coupling network between works with Leiden community detection.
2. Identify the top 5 largest fronts and find the top 3 core papers (highest in-cluster degree and citation density) for each front.
3. Substantive Review: Read the titles and abstracts of those core papers in the dataset and explain what specific experimental architectures, chemical compositions, or physical mechanisms are reported (explain the real scientific findings—do not merely list metadata).
4. Track intertemporal transitions across 3-year windows (Persistence, Split, Merge, Genesis).
5. Output an executive summary table of the fronts and generate a Plotly or Matplotlib network diagram.
```

#### Workflow C: `[AUTONOMOUS PIPELINE]` + Neural Trajectory Mapping (SOM)

*(Attach `./corpus.parquet` or `./matrices/by_country_annual.parquet`)*

```markdown
[AUTONOMOUS PIPELINE] Execute a complete multidimensional trajectory analysis over the attached dataset in Python:

1. Filter the top 5 most productive countries over the last 15 years.
2. Apply a Centered Moving Average (CMA, window=3) to smooth indicator noise.
3. Compute the multidimensional performance profile using volume, citations per doc, normalized FWCI, % Top 10%, and % international collaboration.
4. Model continuous cubic spline trajectories across time for the 5 entities.
5. Generate a high-resolution Matplotlib plot showing the orbits and label any topological inflection points or metric paradoxes.
6. Provide a download link for the generated trajectory plot and processed metrics table.
```

#### Workflow D: `[CANVAS MODE]` + Interactive Document Drafting

```markdown
[OPEN IN CANVAS] Draft an executive summary and key indicator diagnosis based on the attached `corpus.parquet`. Open the draft in Canvas so we can iteratively refine the methodological notes and policy recommendations side by side.
```

---

## Section 3: Scientific Master Templates & the 2-Stage Protocol

The repository includes **4 Master Templates** (`template-*`) modeled after the human research workflows of the LabSOM / C3-UNAM scientometric research group.

### 3.1. The 2-Stage Protocol (Exploration vs. Curation) in ChatGPT

```
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE I: LABORATORY PHASE (Workspace-First Data Analysis)              │
│  - Load `./corpus.parquet` into Python sandbox (Code Interpreter).     │
│  - Compute full 46-column matrix (42 indicators + 4 meta) in Parquet.  │
│  - Execute exploratory skills: growth kinetics, Leiden coupling,       │
│    SOM static/trajectories, core paper reading.                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STAGE II: SCIENTIFIC CURATION & PRUNING PROTOCOL (Canvas / o1)         │
│  - Select the primary narrative arc (3 to 5 core analytical blocks).   │
│  - Discard noisy networks and uninformative fits.                      │
│  - Zero Empty Columns: Never include columns filled with N/D or N/A.   │
│  - Strict Academic Tone: Absolute ban on superlatives / hype words.    │
│  - Anti-Scaffolding Leakage: Zero internal prompts/scripts in prose.   │
│  - Draft full paper/report in the user's language (English or Spanish).│
└────────────────────────────────────────────────────────────────────────┘
```

---

### 3.2. Detailed Guide per Template for ChatGPT

#### Template 1: Original Research Article (IMRaD / IMRyD Format - Q1 Journal)

* **Skill Name:** `template-articulo-cientifico-imryd`
* **Target Venues:** *Journal of Informetrics*, *Scientometrics*, *Quantitative Science Studies*, *Research Evaluation*.
* **Step 1: Alignment Interview:**

```markdown
[INTERVIEW MODE] I want to draft an original scientific research manuscript using `template-articulo-cientifico-imryd` on the global evolution of "Quantum Computing Architectures (Superconducting vs. Trapped Ions vs. Photonic)" from 2000 to 2025. 

Interview me regarding:
1. Research questions and core hypotheses.
2. Data sources (harvesting via `openalex-harvester` into `./corpus.parquet` vs. ingesting an existing Parquet/CSV dataset).
3. The analytical families to test in the laboratory phase (classical growth kinetics, Leiden bibliographic coupling, core paper reading, and Kohonen SOM).
4. The target journal (e.g., Scientometrics or Journal of Informetrics).
```

* **Step 2: Execution & Drafting with o1 / Canvas:**

```markdown
[CANVAS MODE] [DEEP REASONING] Proceed with Stage I (Laboratory Exploration) and Stage II (Curation & Drafting) of `template-articulo-cientifico-imryd` using the attached `corpus.parquet`. 

Analyze the data in Python, log curation decisions, and write the complete manuscript in Canvas with full canonical IMRaD sections and zero empty table columns.
```

---

#### Template 2: Institutional Evaluation Technical Report & Peer Benchmarking

* **Skill Name:** `template-informe-tecnico-institucional`
* **Target Audience:** University Leadership, Institute Directors, Technical Councils (INB UNAM, ICN, INCan style).

```markdown
[AUTONOMOUS PIPELINE] Prepare an authoritative Institutional Scientometric Technical Report using `template-informe-tecnico-institucional` for the "Instituto de Neurobiología (INB), UNAM" covering the period 2014–2024 using the attached dataset:

Execution steps:
1. Inspect the attached `corpus_inb.parquet` and benchmarking datasets for 4 specialized homologous institutions of comparable scale (e.g., Montreal Neurological Institute, Instituto Cajal CSIC, Max Planck Institute for Brain Research, and Instituto de Fisiología Celular UNAM).
2. Check hyperauthorship: if works with >20 authors are negligible (<2%), report autonomous output and do not force an empty tripartite table.
3. Compute the 42-indicator battery and evaluate:
   a) Static multidimensional benchmarking against peers.
   b) Historical trajectory of INB's performance over time.
4. Audit Open Access routes and commercial APC expenditure (USD).
5. Open the technical report draft in Canvas, including executive traffic-light indicators (🟢, 🟡, 🔴) and zero empty columns.
```

---

#### Template 3: Governance Policy Brief (S&T Policy for Senior Decision-Makers)

* **Skill Name:** `template-policy-brief-gobernanza`
* **Format:** 2 to 4 pages for Science Ministers (SECIHTI), Rectors, and Legislative Committees.

```markdown
[INTERVIEW MODE] I need a high-level Governance Policy Brief using `template-policy-brief-gobernanza` addressing "Commercial APC Expenditure vs. Strengthening Diamond Open Access Infrastructure".

Interview me on:
1. The decision-making audience (e.g., Ministry of Science, University Rectorate, or Funding Agency).
2. The empirical scope (from the attached `corpus.parquet`).
3. The specific policy instruments to propose in the final recommendations matrix.
```

*(After answering the interview, execute with:)*

```markdown
[CANVAS MODE] Generate the Policy Brief based on the attached dataset:
1. In Python, compute observed `apc_paid_usd` and list prices across commercial publishers vs. Diamond repositories.
2. Group institutions into cluster profiles (Frontier vs. Regional Relevance vs. Vulnerable).
3. Structure the document strictly within 4 pages in Canvas: Executive Synthesis, Quantitative Diagnosis (Table 1), Multidimensional Profile Evidence (Table 2), Strategic Trade-Offs, and Actionable Recommendations Matrix (Table 3).
```

---

#### Template 4: Scientific Intelligence Report & Research Fronts Radar

* **Skill Name:** `template-radar-frentes-investigacion`
* **Target Audience:** Research Groups, Technology Observatories, and Foresight Panels.

```markdown
[DEEP REASONING] Produce a comprehensive Scientific Intelligence & Technology Radar Report using `template-radar-frentes-investigacion` for "Direct Air Carbon Capture and Storage (DACCS)" from the attached `corpus.parquet`.

Required laboratory and curation steps:
1. In Python, execute community detection (Leiden CPM) on the bibliographic coupling matrix.
2. Alluvial Lineage Tracking: compute transitions across 3 temporal windows (Persistence, Split, Merge, Genesis).
3. Core Papers Review: inspect the top 3 central papers in each active front and explain the sorbent materials, thermodynamic cycles, and energy requirements discussed.
4. Multidimensional Profile: evaluate fronts across volume, FWCI, % Top 10%, international collaboration, and patent citations.
5. Draft the complete report in Canvas with high-resolution plots.
```

---

## Appendix: Core Principles & Standardized Parquet Schemas

1. **Workspace-First Principle:**
   - Raw data are saved in `./corpus.parquet`.
   - Indicators and time series are computed in `./matrices/*.parquet` (46 untruncated columns: 42 numerical indicators + 4 metadata fields).
   - Artifacts, reports, and HTML viewers are persisted in `./reportes/`.
2. **Data Integrity & Standardized Columnar Schemas:**
   - The canonical table `./corpus.parquet` contains verified fields (`publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `author_names`, `institution_names`, `topics`).
   - All indicator matrices use Parquet to ensure zero truncation, high compression, and consistent data types across Python and Code Interpreter.
3. **Zero Empty Columns (`N/D` / `N/A`) Rule:**
   - Never generate tables with columns populated by placeholders. Only report verified, computed indicators.
4. **Sober Scientific Tone:**
   - Prohibit superlatives and marketing hype. Maintain a measured, evidence-grounded academic register.
5. **Universal Language Rule:**
   - Scripts default to English (`--lang en`). Pass `--lang es` when users interact in Spanish, ensuring all figures, axis titles, and report sections match the user's language.
