---
name: bibliometrix-guide
description: >-
  Science mapping, bibliometric network analysis, and thematic cartography using the canonical R package bibliometrix (Aria & Cuccurullo, 2017) and its web interface Biblioshiny. Orchestrates multi-database import (Scopus, WoS, PubMed, Dimensions, OpenAlex), co-citation, coupling, Callon's strategic diagrams (Centrality vs. Density), and longitudinal thematic evolution. Respond and label outputs in the user's language.
metadata:
  language: "R / Python"
  r_package: "bibliometrix >=4.0"
  scripts:
    - "scripts/bibliometrix_cli.py"
    - "scripts/bibliometrix_runner.R"
---

# Bibliometrix Guide: Science Mapping and Thematic Cartography in R

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Overview and Purpose

The **`bibliometrix`** ecosystem (Massimo Aria & Corrado Cuccurullo, 2017; *Journal of Informetrics*) is one of the most established open-source packages internationally for comprehensive bibliometric analysis and **Science Mapping**.

This skill provides an exhaustive operational guide and orchestration tools for agents and analysts, covering the full lifecycle of knowledge discovery in bibliographic databases (KDD):
1. **Multi-database ingestion and normalization:** Uniform conversion to canonical data frames with `convert2df()` from Scopus, Web of Science, PubMed, Dimensions, Cochrane, and OpenAlex.
2. **Descriptive and production analysis:** Global metrics, annual growth rates, productivity laws, and dominant sources with `biblioAnalysis()`.
3. **Intellectual Structure and Networks:** Reference/author co-citation, bibliographic coupling, and collaboration networks with `biblioNetwork()`.
4. **Conceptual Structure and Callon's Diagrams:** Term co-occurrence, factorial analysis (MCA/CA), and **Callon's Strategic Four-Quadrant Diagram** (Centrality vs. Density) with `thematicMap()`.
5. **Longitudinal Thematic Evolution:** Mapping alluvial (Sankey) flows across time slices with `thematicEvolution()`.
6. **No-Code Web Interface:** Interactive browser deployment via `biblioshiny()`.

---

## 2. Scope of Application and Scientometric Questions

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   ANALYSIS TYPOLOGIES IN R BIBLIOMETRIX                                │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ Analysis Typology        │ Canonical R Functions       │ Question / Decision Answered  │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 1. Descriptive           │ `convert2df()`,             │ What is the global volume,    │
│    Statistics            │ `biblioAnalysis()`,         │ annual growth rate, and top   │
│                          │ `summary()`                 │ authors and journals?         │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 2. Intellectual          │ `citations()`,              │ What are the foundational     │
│    Structure             │ `biblioNetwork(co-citation)`│ documents and authors jointly │
│                          │ `histNetwork()` (HistCite)  │ cited in the field?           │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 3. Social Structure      │ `biblioNetwork(collab)`     │ How do authors, institutions, │
│                          │ `networkPlot(kamada)`       │ and countries group into      │
│                          │ `metaTagExtraction()`       │ invisible colleges?           │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 4. Conceptual Structure  │ `thematicMap()`             │ What are the motor, niche,    │
│    (Callon's Diagram)    │ (Centrality vs. Density)    │ basic, or emerging/declining  │
│                          │ `biblioNetwork(co-occur)`   │ themes?                       │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 5. Longitudinal          │ `thematicEvolution()`       │ How do thematic fronts merge  │
│    Thematic Evolution    │ `plotThematicEvolution()`   │ or split across historical    │
│                          │                             │ periods?                      │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

### 2.1 Callon's Strategic Diagram (1991)
The package classifies thematic clusters into 4 analytical quadrants based on two orthogonal coordinates centered on their medians:
* **Callon's Centrality (X-Axis - External Links):** Measures the transversality and interconnection of the cluster with the rest of the discipline.
* **Callon's Density (Y-Axis - Internal Links):** Measures the conceptual cohesion and internal maturity of the cluster.

1. **Quadrant I: Motor Themes (High Centrality, High Density):** Well-developed and influential research lines that structure the discipline.
2. **Quadrant II: Niche Themes (Low Centrality, High Density):** Highly developed but marginal or isolated specialties.
3. **Quadrant III: Emerging or Declining Themes (Low Centrality, Low Density):** Embryonic fronts or obsolete research lines.
4. **Quadrant IV: Basic and Transversal Themes (High Centrality, Low Density):** Core concepts shared across the entire corpus without internal hyper-specialization.

---

## 3. Dependencies and Value Chain

```
┌─────────────────────────────────┐
│     Upstream Skills             │
│ • openalex-mexico-works-search  │──┐
│ • scopus-harvester / pubmed     │  │  Tabular exports
│ • tlachia-metrics-handler (ZIP) │  │  (CSV, BibTeX, TXT, Parquet)
└─────────────────────────────────┘  │
                                     ▼
                     ┌───────────────────────────────┐
                     │      bibliometrix-guide       │
                     │  (Science Mapping R / Python) │
                     └───────────────────────────────┘
                                     │
                                     ▼  Network matrices, cluster JSON, and PNG figures
┌────────────────────────────────────┴────────────────────────────────────┐
│                       Downstream Skills                                 │
│ • som-methodological-expert (Cross-comparison with self-organizing SOM) │
│ • bibliometric-network-analyst (Leiden algorithm & strict modularity)   │
│ • classical-bibliometrics-laws (Empirical Lotka / Bradford validation)  │
│ • Executive science policy and institutional benchmarking reports       │
└─────────────────────────────────────────────────────────────────────────┘
```

* **Upstream Skills (Corpus Providers):**
  - [`scopus-harvester`](../scopus-harvester/SKILL.md) / [`pubmed-harvester`](../pubmed-harvester/SKILL.md): Literature downloads with cited references.
  - [`openalex-mexico-works-search`](../openalex-mexico-clickhouse/openalex-mexico-works-search/SKILL.md): Publications from Mexico with normalized DOIs and fields.
  - [`tlachia-metrics-handler`](../tlachia-metrics-handler/SKILL.md): ZIP packages of document metadata.
* **Downstream Skills (Analysis Consumers):**
  - [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Neurocomputational SOM projection of scientometric profiles.
  - [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md): Complex network partitioning with the Leiden algorithm.
  - [`classical-bibliometrics-laws`](../classical-bibliometrics-laws/SKILL.md): Comparison against Lotka, Bradford, and Price laws.
* **Software Environment and Resources:**
  - **R Environment (Primary):** R `>= 4.0` with `bibliometrix` and `jsonlite` libraries.
  - **Python Environment (Orchestrator / Fallback):** Python `>= 3.10` with `numpy`, `matplotlib`, `pandas`.
  - **CLI Scripts:**
    - [`scripts/bibliometrix_runner.R`](scripts/bibliometrix_runner.R): Standalone script for unattended R execution via `Rscript`.
    - [`scripts/bibliometrix_cli.py`](scripts/bibliometrix_cli.py): Python CLI orchestrator that generates `.R` recipes, runs the R runner, or natively computes Callon's diagram.

---

## 4. CLI Execution Protocol (File-Output First)

### 4.1 Generating Reproducible R Recipes (`generate-script`)
When the agent or user needs a ready-to-run `.R` script for RStudio or the terminal:
```bash
python scripts/bibliometrix_cli.py generate-script \
  --input ./data/corpus_scopus.csv \
  --output ./scripts/thematic_analysis.R \
  --analysis thematic \
  --field DE
```
Options for `--analysis`: `summary`, `co-citation`, `collaboration`, `thematic`, `evolution`, `biblioshiny`.

### 4.2 Native Execution of Callon's Diagram (`callon-map`)
Computes Callon's strategic diagram (Centrality vs. Density) directly on `.parquet`, `.csv`, or `.json` files without requiring `Rscript`:
```bash
python scripts/bibliometrix_cli.py callon-map \
  --input ./data/corpus_mexico.parquet \
  --field DE \
  --top-terms 50 \
  --min-freq 3 \
  --plot-output ./data/callon_map.png \
  --output ./data/callon_clusters.json
```

### 4.3 Unattended Execution with Rscript (`run`)
Invokes the R runner for large-scale analyses on servers or environments with R installed:
```bash
python scripts/bibliometrix_cli.py run \
  --command thematic \
  --input ./data/scopus_export.csv \
  --field DE \
  --plot-output ./data/callon_r.png \
  --output ./data/thematic_output.json
```

---

## 5. Canonical R Recipes (Quick Reference)

### 5.1 Multi-Database Loading and Import
```r
library(bibliometrix)

# Scopus CSV
M <- convert2df("scopus.csv", dbsource = "scopus", format = "csv")

# Web of Science Plain Text
M <- convert2df("savedrecs.txt", dbsource = "wos", format = "plaintext")

# PubMed MEDLINE format
M <- convert2df("pubmed-set.txt", dbsource = "pubmed", format = "pubmed")
```

### 5.2 Global Descriptive Analysis
```r
results <- biblioAnalysis(M, sep = ";")
summary(results, k = 10, pause = FALSE)
plot(x = results, k = 10, pause = FALSE)
```

### 5.3 Bibliometric Networks
```r
# 1. Reference co-citation
NetMatrix <- biblioNetwork(M, analysis = "co-citation", network = "references", sep = ";")
net <- networkPlot(NetMatrix, n = 40, Title = "Co-Citation Network", type = "fruchterman", size = TRUE)

# 2. Country collaboration
M <- metaTagExtraction(M, Field = "AU_CO", sep = ";")
NetMatrix <- biblioNetwork(M, analysis = "collaboration", network = "countries", sep = ";")
net <- networkPlot(NetMatrix, n = 30, Title = "International Collaboration", type = "circle")

# 3. Author keyword co-occurrence
NetMatrix <- biblioNetwork(M, analysis = "co-occurrences", network = "keywords", sep = ";")
net <- networkPlot(NetMatrix, n = 50, Title = "Conceptual Network", type = "kamada")
```

### 5.4 Callon's Four-Quadrant Thematic Map
```r
Map <- thematicMap(M, field = "DE", n = 250, minfreq = 5,
                  stemming = FALSE, size = 0.5, n.labels = 3, repel = TRUE)
plot(Map$map)
```

### 5.5 Launching Biblioshiny (Web Interface)
```r
biblioshiny()
```

---

## 6. Common Mistakes and Anti-Patterns

- ❌ **Anti-pattern 1: Mixing Scopus and WoS exports without prior DOI deduplication**  
  Loading files from multiple databases with cross-formats without unifying unique identifiers (`DI` / `UT`). This creates duplicate documents that heavily bias co-citation networks and inflate productivity counts.  
  **Solution:** Deduplicate with `bibliometrix::mergeDbSources()` or pre-filter in Python by normalized DOI before conversion.
- ❌ **Anti-pattern 2: Setting minimum co-occurrence or co-citation thresholds too low**  
  Running `biblioNetwork()` or `thematicMap()` with `minfreq = 1` or without capping `n`. This produces massive graphs with thousands of sporadic edges that exhaust R memory and yield illegible "hairball" visualizations.  
  **Solution:** Always set a bounded `n` (e.g., `n = 30` to `50` nodes) and `minfreq >= 3` to `5`.
- ❌ **Anti-pattern 3: Confusing Author Keywords (`DE`) with Keywords Plus (`ID`)**  
  Using `field = "ID"` for Callon diagrams expecting to capture researchers' direct vocabulary. Keywords Plus are algorithmically generated from cited article titles and introduce generic terms (e.g., *system*, *model*, *performance*) that pollute motor themes.  
  **Solution:** Use `field = "DE"` (Author Keywords) for emerging fronts and rigorous conceptual thematic analysis.
- ❌ **Anti-pattern 4: Omitting random seed initialization (`set.seed`) in network layouts**  
  Generating networks with force-directed algorithms (*Fruchterman-Reingold* or *Kamada-Kawai*) without setting a stochastic seed. Each run reorders nodes into different coordinates, hindering reproducibility in scientific reports.  
  **Solution:** Call `set.seed(1234)` before any `networkPlot()` or `thematicMap()`.
- ❌ **Anti-pattern 5: Failing to normalize name variants or institutional acronyms**  
  Building co-authorship or institutional networks directly from raw data. The same author may appear as `GARCIA, J.`, `GARCIA, J.L.`, and `GARCIA-ANDRADE, J.`, fragmenting their network centrality.  
  **Solution:** Use synonym tables (*thesaurus*) in `thematicMap(synonyms = ...)` or normalize Hispanic name variants beforehand.

---

## 7. Technical References

- [Theoretical Foundations of Callon's Strategic Diagram (1991)](references/callon_thematic_quadrants_theory.md)
- [Canonical Field Tags Dictionary (`AU`, `DE`, `CR`, etc.)](references/bibliometrix_field_tags_guide.md)
- [Standalone R Execution Script](scripts/bibliometrix_runner.R)
- [Python CLI Orchestrator and Bridge](scripts/bibliometrix_cli.py)
- [Official Bibliometrix Website](https://www.bibliometrix.org/)
- Aria, M. & Cuccurullo, C. (2017). "bibliometrix: An R-tool for comprehensive science mapping analysis." *Journal of Informetrics*, 11(4), 959–975. [DOI: 10.1016/j.joi.2017.08.007](https://doi.org/10.1016/j.joi.2017.08.007).
