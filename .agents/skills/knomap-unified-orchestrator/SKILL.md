---
name: knomap-unified-orchestrator
description: Comprehensive orchestrator for the KnoMap and TlachIA ecosystem; coordinates multi-phase pipelines under the Workspace-First principle ("From Harvest to SOM") from field delineation and massive data harvesting to computing 35+ indicator matrices, research front detection, SOM topological modeling, and scientific reporting. Respond and label outputs in the user's language.
---

# KnoMap Unified Orchestrator: The Complete Value Chain ("From Harvest to SOM")

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

This skill acts as the **master conductor** when the user requests a comprehensive scientometric or bibliometric study spanning multiple stages of the ecosystem.

## 1. Workspace Chaining Architecture (`./`)

All ecosystem skills communicate through standardized artifacts in the project working directory (`./`), avoiding passing massive structures in memory:

1. **Workspace Root (`./corpus.parquet`):** Master file containing harvested publications in the canonical schema.
2. **Subdirectory `./matrices/`:** Multidimensional $[N \times D]$ matrices (`.parquet` or `.csv`) with the **35+ indicators** computed by `tlachia-metrics-engine` (without truncating columns), ready to be consumed by the SOM Triad.
3. **Subdirectory `./networks/`:** Graphs and Leiden CPM modular partitions (`.json`, `.gexf`).
4. **Subdirectory `./reports/`:** Trained SOM states (`./reports/som_state.json`), peer diagnostics (`./reports/som_diagnosis.json`), research fronts, bibliometric laws, and interactive HTML/PNG dashboards.

---

## 2. 4-Stage Orchestration Protocol

### Stage 1: Conceptual Delineation, Identity Resolution, and Harvesting (`./corpus.parquet`)
1. **Field Delineation:** Invoke `bibliometric-search-strategist` (`scripts/query_synthesizer.py`) to construct conceptual blocks audited under the GLOBAL (ISSI) guideline and transpile to ClickHouse SQL (`clickhouse_query.sql`), WoS, Scopus, and PubMed.
2. **Entity Resolution (if applicable to Mexico):** Invoke `openalex-mexico-institutions`, `openalex-mexico-author-search`, and `snii-identity-resolver`.
3. **Canonical Corpus Extraction (`./corpus.parquet`):**
   - **Global (464.8M works in `rag.works_flat`):** Use `openalex-search-engineer` (`scripts/openalex_search_cli.py search-works --sql-file ./queries/clickhouse_query.sql --output ./corpus.parquet`) or `openalex-harvester`.
   - **National Mexico (1.65M works in `rag.works_academic_all`):** Use `openalex-mexico-works-search` (`openalex_mexico_cli.py search-works --output ./corpus.parquet`).
   - **Specialized external databases:** Use `scopus-harvester`, `pubmed-harvester`, `arxiv-harvester`, `semantic-scholar-harvester`, or `deep-literature-researcher` (Snowballing).

### Stage 2: Analytical Engines and Matrix Construction (`./matrices/` and `./reports/`)
All Stage 2 skills read `./corpus.parquet` directly:
1. **Multidimensional Indicator Engine (`tlachia-metrics-engine`):**
   - Global summary: `tlachia_metrics_cli.py calculate-summary --input ./corpus.parquet --output ./reports/summary_metrics.json`
   - Entity matrix for Static SOM (35+ indicators without truncation):
     `tlachia_metrics_cli.py by-entity --input ./corpus.parquet --level institution --min-docs 2 --output ./matrices/indicadores_som.parquet`
   - Annual series by entity with Centered Moving Average (CMA) for Trajectory SOM:
     `tlachia_metrics_cli.py annual-series --input ./corpus.parquet --level institution --cma-window 3 --output ./matrices/series_cma_som.parquet`
   - Period series for Warm-Start Longitudinal SOM:
     `tlachia_metrics_cli.py period-series --input ./corpus.parquet --periods "2020-2022,2023-2026" --level institution --output ./matrices/periodos_som.parquet`
2. **Networks and Research Fronts:**
   - Co-authorship, co-occurrence, bibliographic coupling, and co-citation networks: `bibliometric-network-analyst` (`scripts/biblio_network_cli.py`).
   - Research Front Detection (Leiden CPM over coupling/co-citation/direct citation or OpenAlex Topics) and Longitudinal Alluvial Diagrams (AMI): `topics-research-fronts-intelligence` (`build_bibliometric_fronts.py`, `track_longitudinal_lineages.py`).
3. **Classical Laws, Geopolitics, Open Access, and SDGs:**
   - `classical-bibliometrics-laws` (`bibliometric_laws_cli.py`: Lotka, Bradford, Price, Growth).
   - `geopolitical-collaboration-analyst` (`geopolitical_collab_cli.py`: Salton Affinity, Epistemological Sovereignty).
   - `open-access-monitor` (`open_access_monitor_cli.py`: 6 OA routes and observed vs. list APC expenditure in USD).
   - `sdg-impact-intelligence` (`sdg_impact_cli.py`: SDGs 1–17).

### Stage 3: Neurocomputational Cartography (SOM Triad) and Executive Visualization
1. **Note on Dimension Selection:** While there are 4 classical cardinal dimensions (Volume, Citation Impact, Top 10%/1% Excellence, and Collaboration/OA), the agent can choose **any subset of the 35+ indicators** from `./matrices/*.parquet` via `--indicator-cols` tailored to the research question.
2. **Static SOM and Comparable Peers (`som-methodological-expert`):**
   - `scripts/som_pipeline_cli.py --input ./matrices/indicadores_som.parquet --state-out ./reports/som_state.json --html-out ./reports/som_dashboard.html --diagnosis-out ./reports/som_diagnosis.json`
3. **Continuous Trajectory SOM (`som-trajectory-mapping`):**
   - `scripts/som_trajectory_cli.py --input ./matrices/series_cma_som.parquet --top-entities 5 --html-out ./reports/som_trajectories.html --json-out ./reports/som_trajectories.json`
4. **Warm-Start Longitudinal SOM (`neural-longitudinal-mapping`):**
   - `scripts/neural_longitudinal_cli.py prepare` + `analyze` over `./matrices/periodos_som.parquet`.
5. **Executive Visualizer (`openalex-mexico-visualizer`):**
   - `openalex_mexico_viz_cli.py` for rankings, dual time series, OA donuts, and SDG grids in `./reports/`.

### Stage 4: Documentary Synthesis
Integrate all quantitative findings and links to `./reports/` using one of the 4 master templates:
- `template-articulo-cientifico-imryd`
- `template-informe-tecnico-institucional`
- `template-policy-brief-gobernanza`
- `template-radar-frentes-investigacion`
