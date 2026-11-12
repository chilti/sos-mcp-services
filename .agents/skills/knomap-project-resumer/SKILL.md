---
name: knomap-project-resumer
description: Opens or creates KnoMap project files (.knoMap v2.1, server .json.gz, or .knomap v2.0), inspects all scientific modules and the complete AI Assistant history (Visual Copilot, Autonomous Agent, maps, HTML/SVG/PNG artifacts, and LLM caches) under the File-Output First principle, reconstructs the workspace to resume research, and packages complete investigations back into a .knoMap file ready to open in the web interface. Respond and label outputs in the user's language.
metadata:
  python: ">=3.10"
  tools: ["knomap-som-engine"]
---

# KnoMap Project Resumer: Resuming Saved Research Projects

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Overview and Purpose

This skill enables **opening a `.knoMap` file saved from the web/desktop application** (or a `.json.gz` stored on the KnoMap server, or a `.knomap` v2.0 package from the SQLite/MCP hub) and **resuming an investigation right where it left off**, preserving:

1. **Matrices and Indicators:** Primary SOM matrix (`dataMatrix` and `originalDataMatrix`), pre-loaded **TlachIA Metrics** and **InCites** units (`Locations`, `Organizations`, `Sources`, `Topics`, etc.), and dimensionality reduction tables.
2. **Trained Models and Maps:** SOM neural weights (`weights`), U-Matrix, clusters, mapped labels (`mapped_labels`), cluster names (`clusterLabels`), UMAP coordinates, multi-experiment history (`savedRuns`), and longitudinal results (`longitudinalResults`).
3. **Bibliometric Networks and EDA:** Graphs (`network.json`), `vosviewer.json` files, co-occurrence matrices, networks by year, EDA reports (`bradford_law`, `lotka_law`, author metrics), and semantic records (`semanticRecords`, clusters, and 2D coordinates).
4. **Complete AI Assistant Memory:**
   - **Study Context** (`studyContext`).
   - **Visual Copilot** (`aiReport.entries`): generated analytical text, multi-turn dialogues, captured data, and exported figures (`.png` / `.svg`).
   - **Autonomous Agent** (`aiReport.agentMessages`): conversational history, executed tools, and interactive artifacts (`.html` / `.svg`).
   - **AI Card Caches** (`incitesLlmCache` and `tlachiaLlmCache`).

---

## 2. Dependencies and Value Chain

- **Upstream Input:** Exported KnoMap file (`*.knoMap`), server backup (`*.json.gz`), or portable package (`*.knomap`).
- **Downstream Skills (Continuing Work on the Extracted Workspace):**
  - `som-methodological-expert` — Retrain or recluster on `./matrices/som_matrix.parquet`, or diagnose peers and generate dashboards from `./reports/som_state.json`.
  - `som-trajectory-mapping` / `neural-longitudinal-mapping` — Continue temporal analysis on `*_time_series.json` / `*_longitudinal.json` series or `./reports/longitudinal_state.json`.
  - `bibliometric-network-analyst` — Resume graphs and communities on `./networks/network.json`, `./networks/vosviewer.json`, or `./networks/cooccurrence.csv`.
  - `scientometrics-incites-expert` / `tlachia-metrics-handler` — Work on extracted matrices `./matrices/incites_*.csv` and `./matrices/tlachia_*.csv`.
  - `semantic-manifold-expert` — Resume reduction/clustering on `./matrices/semantic_records.parquet` and `./reports/semantic_clusters_state.json`.
  - `template-articulo-cientifico-imryd`, `template-informe-tecnico-institucional`, `template-policy-brief-gobernanza`, `template-radar-frentes-investigacion` — Draft or expand the scientific document using `./reports/assistant_history.md` and `./reports/assistant_figures/`.
- **Environment and Primary Script:**
  - Python `>=3.10` with `pandas` and `pyarrow` (optional for `.parquet`; automatic fallback to `.csv` and `.json`).
  - Executable script: `scripts/knomap_resume_cli.py` (invoke with `python scripts/knomap_resume_cli.py ...` from the skill directory or specifying its relative path).
  - Complementary MCP tool: `knomap-som-engine` (`knomap_render_som_dashboard`, `train_som`, `recluster_som`).

---

## 3. Step-by-Step Execution Protocol

> **Strict Rule (*File-Output First*):** A `.knoMap` file can weigh tens of megabytes (matrices, neural weights, thousands of semantic records, base64 PNGs). **NEVER** read the full `.knoMap` file directly into the chat context or print its matrices to `stdout`. Always run `inspect` first and then `extract-workspace`.

### 3.1 Step 1: Inspect the Project (`inspect`)

Obtain a compact inventory of available modules, SOM runs, study context, and assistant entries without saturating the context window:

```bash
python scripts/knomap_resume_cli.py inspect \
  --input ./my_study.knoMap \
  --output ./reports/project_inventory.json
```

Review `./reports/project_inventory.json` to decide which artifacts to extract and which lines of inquiry already exist in the project.

### 3.2 Step 2: Reconstruct the Workspace (`extract-workspace`)

Extract tabular matrices, normalized SOM states, bibliometric networks, prior assistant text, and all figures/artifacts to disk under `./matrices/`, `./networks/`, and `./reports/`:

```bash
python scripts/knomap_resume_cli.py extract-workspace \
  --input ./my_study.knoMap \
  --workspace-dir . \
  --output ./reports/resume_manifest.json
```

#### Generated Workspace Artifacts

| Directory | Primary Files | Downstream Usage |
| :--- | :--- | :--- |
| `./matrices/` | `som_matrix.csv`, `som_matrix.parquet`, `som_matrix_original.csv`, `som_matrix_run_<N>_*.csv/.parquet`, `incites_<unit>.csv`, `tlachia_<unit>.csv`, `semantic_records.parquet` | SOM training, statistical analysis, laws, trajectories |
| `./networks/` | `network.json`, `vosviewer.json`, `networks_by_year.json`, `cooccurrence.csv`, `eda_report.json`, `sankey_data.json` | Co-occurrence/co-authorship networks, Leiden/Louvain, EDA |
| `./reports/` | `som_state.json`, `som_state_run_*.json`, `saved_runs_index.json`, `longitudinal_state.json`, `semantic_clusters_state.json` | Visualization (`knomap_render_som_dashboard`), peer diagnosis |
| `./reports/` | `assistant_history.md`, `assistant_history.json`, `resume_manifest.json` | Read prior interpretations, open questions, and context |
| `./reports/assistant_figures/` | `copilot_*.png`, `copilot_*.svg`, `copilot_*_data.json`, `agent_*.html`, `agent_*.svg` | Reuse generated maps and figures in IMRaD reports |

### 3.3 Step 3: Read Prior State and Resume the Investigation

1. Read `./reports/assistant_history.md` to recover:
   - The **study objective and context** (`studyContext`).
   - Which **maps and charts were already interpreted** by the Visual Copilot and where their figures are stored.
   - Which **tools, responses, and HTML5 artifacts** were already produced by the Autonomous Agent.
   - What interpretations exist in the InCites / TlachIA caches.
2. Check `./reports/resume_manifest.json` for prior experiments (`savedRuns`) or unmodeled data (e.g., if `tlachia_locations.csv` exists without `som_state.json`, or if longitudinal/network analyses are missing).
3. Continue with the corresponding specialized skill over the files extracted into `./matrices/`, `./networks/`, and `./reports/`.

### 3.4 Step 4 (Optional): Save New Findings Back into the `.knoMap` (`update-knomap`)

If after continuing the analysis you want the user to be able to **reopen the updated `.knoMap` in the KnoMap web interface** with the new text, an interactive HTML map, or a new `som_state.json`:

```bash
python scripts/knomap_resume_cli.py update-knomap \
  --input ./my_study.knoMap \
  --output ./my_study_continued.knoMap \
  --add-note-title "Complementary Longitudinal Analysis" \
  --add-note-file ./reports/new_interpretation.md \
  --add-html-artifact ./reports/som_dashboard.html \
  --as-agent-message \
  --som-state-file ./reports/som_state.json
```

*(Without `--as-agent-message`, the note is inserted as a new entry in the **Visual Copilot**.)*

### 3.5 Step 5 (Reverse Flow Agent → Human): Create a New `.knoMap` Project from Scratch (`create-knomap`)

When an agent completes an autonomous investigation in a workspace (e.g., after running `som-methodological-expert`, `som-trajectory-mapping`, `bibliometric-network-analyst`, or `semantic-manifold-expert`), it can package **matrices, trained SOM models (`savedRuns`), networks, trajectories, PNG figures, interactive HTML artifacts, and the complete scientific report** into a brand-new `.knoMap` (`version 2.1`) or `.json.gz` file so the human user can open it directly in KnoMap Web:

```bash
python scripts/knomap_resume_cli.py create-knomap \
  --workspace-dir . \
  --output ./reports/my_complete_research.knoMap \
  --title "Comprehensive Scientometric Study" \
  --study-desc "Multidimensional SOM analysis, bibliometric networks, and trajectories." \
  --report-md ./reports/final_report.md \
  --add-copilot-entry "Trajectory Map|./reports/som_trajectories_en.png|./reports/som_interpretation.md" \
  --add-html-artifact ./reports/som_dashboard.html \
  --auto-attach-figures \
  --lang en
```

**Behavior of `create-knomap`:**
- **Workspace auto-discovery:** If `--som-state` is omitted, it automatically searches for `./reports/som_state_run_*.json` or `./reports/som_state.json`, pairs their normalized/original matrices in `./matrices/`, builds `hexGrid`, converts `umatrix` to 2D, and automatically detects `XX_ENTITY` trajectories (or uses `--trajectories A,B,C`).
- **Complementary modules:** If present in `./networks/` or `./reports/`, it automatically embeds `network.json`, `vosviewer.json`, `eda_report.json`, `longitudinal_state.json`, `semantic_records.parquet`, and `dim_reduction_state.json`.
- **AI Assistant ready for human review:** Attaches the final report in `aiReport.agentMessages` (along with interactive HTML artifacts) and each figure+analysis pair in `aiReport.entries` (Visual Copilot).

---

## 4. Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1:** Opening a `.knoMap` directly with `read_file` or printing `json.load()` to `stdout`.  
  **Solution:** Always use `inspect --output ...` and `extract-workspace` so as not to overflow the context window with matrices and base64 PNGs.
- ❌ **Anti-pattern 2:** Assuming the `.knoMap` extension is always plain JSON or always gzip.  
  **Solution:** Projects exported from the web interface are usually plain JSON (`v2.1`), whereas server backups (`.json.gz`) are gzip-compressed and CLI hub packages (`.knomap v2.0`) use a different schema. `knomap_resume_cli.py` detects all three automatically.
- ❌ **Anti-pattern 3:** Passing the raw web `.knoMap` `result` directly to `knomap_render_som_dashboard`.  
  **Solution:** The web format uses camelCase keys (`mappedLabels`, `compNames`, `config.rows`, 2D `umatrix`), whereas the Python engine expects snake_case (`mapped_labels`, `indicators`, `rows`, 1D `umatrix`). `extract-workspace` generates `./reports/som_state.json` already converted and normalized (reconstructing `mapped_labels` from `bmus` + `labels` if needed).
- ❌ **Anti-pattern 4:** Re-harvesting data from OpenAlex or InCites when it is already inside the `.knoMap`.  
  **Solution:** Check `./matrices/incites_*.csv`, `./matrices/tlachia_*.csv`, and `./matrices/semantic_records.parquet` extracted by `extract-workspace` first.
- ❌ **Anti-pattern 5:** Ignoring the prior assistant history when continuing the analysis.  
  **Solution:** Always read `./reports/assistant_history.md` before drafting new interpretations to maintain terminological consistency, hypotheses, and tone with prior work.

---

## 5. Technical References

- [`scripts/knomap_resume_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/knomap-project-resumer/scripts/knomap_resume_cli.py)
- [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)
- [`tlachia-metrics-handler`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md)
- [`bibliometric-network-analyst`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/bibliometric-network-analyst/SKILL.md)
