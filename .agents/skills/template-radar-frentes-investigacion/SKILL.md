---
name: template-radar-frentes-investigacion
description: >-
  Scientometric cartography of emerging research fronts, technology radar, thematic evolution, and AMI alluvial lineages. Operates under a 2-stage protocol: I) Workspace exploration across the menu of Agent Skills (multimodal detection of fronts via bibliographic coupling, co-citation, direct citation, or Macro/Meso/Micro Topics; reading of core papers; 42+ indicator engine; growth kinetics; geopolitical affinity; static/trajectory/longitudinal SOM triad; and SDG alignment), and II) Scientific curation to select the network representation and subset of techniques that best reveal the structure and evolution of the fronts. Respond and label outputs in the user's language.
---

# Master Template: Scientific Intelligence Report, Research Fronts Radar, and Topological SOM Cartography
### *Inspired by multimodal research front mapping, thematic evolution, and SOM analysis (Polaritons / Topics & Research Fronts Intelligence style)*

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish). Write all section headers and prose of the generated report in the user's language.

This template guides the preparation of a high-value prospective **SCIENTIFIC INTELLIGENCE AND RESEARCH FRONTS RADAR REPORT** for research groups, vice-rectorates for research, technology observatories, and funding agencies.

Following the principle of **human exploration and curation**, the template provides the agent with the **full menu of Agent Skills** to explore the intellectual and temporal structure of the field in the workspace (`./corpus.parquet`), allows **comparing multiple research front detection strategies** (bibliographic coupling, co-citation, direct citation, co-occurrence, or Macro/Meso/Micro Topic taxonomies) and multiple **SOM** configurations, and instructs the agent to **discard techniques that yield noisy or redundant partitions**, building the report around the results with the highest explanatory power and combining quantitative cartography with a substantive review of the core papers in each front.

---

## Stage I: Menu of Agent Skills for Research Front Exploration (*Laboratory Phase*)

The agent operates under the **Workspace-First** principle (`./corpus.parquet` $\to$ `./matrices/*.parquet` $\to$ `./reportes/`) and uses the following menu of skills:

1. **Field Delineation and Corpus Harvesting (`./corpus.parquet`):**
   - [`bibliometric-search-strategist`](../bibliometric-search-strategist/SKILL.md): Multi-stage field delineation (Huang, Schiebel & Porter, 2011), GLOBAL (ISSI) auditing, and SQL transpilation to ClickHouse (`rag.works_flat` for global studies or `rag.works_academic_all` for Mexico-focused studies, with **ZERO JOINs**).
   - [`openalex-search-engineer`](../openalex-search-engineer/SKILL.md) (global `rag.works_flat`), [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md) (national `rag.works_academic_all`), or harvesters [`openalex-harvester`](../openalex-harvester/SKILL.md), [`scopus-harvester`](../scopus-harvester/SKILL.md), [`pubmed-harvester`](../pubmed-harvester/SKILL.md), [`arxiv-harvester`](../arxiv-harvester/SKILL.md).
2. **Multimodal Detection of Research Fronts and Longitudinal Lineages (Explore and Compare):**
   - [`topics-research-fronts-intelligence`](../topics-research-fronts-intelligence/SKILL.md) and [`research-fronts-detection-expert`](../research-fronts-detection-expert/SKILL.md):
     * Enables testing different network modalities on `./corpus.parquet`: **bibliographic coupling** (optimal for detecting active and emerging fronts), **co-citation** (optimal for foundational theoretical schools), **direct citation**, or **native OpenAlex Topics taxonomy** (`domain` $\to$ `field` $\to$ `subfield` $\to$ `topic`).
     * Community partitioning via the **Leiden algorithm (CPM / Modularity)** and intertemporal tracking via **Adjusted Mutual Information (AMI)** to classify evolutionary events (*Persistence*, *Merge*, *Split*, *Genesis*) and generate interactive alluvial diagrams (`alluvial_lineages.html`).
   - [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md): Conceptual co-occurrence, co-authorship, and coupling networks with *Association Strength* normalization (VOSviewer / Force Graph).
3. **Substantive Inspection of Seminal and Core Papers (*Core Papers* per Front):**
   - [`deep-literature-researcher`](../deep-literature-researcher/SKILL.md) and direct inspection of `./reportes/corpus_with_fronts.parquet`: Identify the papers of highest impact, centrality, or density ($k \ge 2$, Glänzel et al., 2009) within each detected front to synthesize what scientific problems, architectures, or phenomena each cluster actually investigates.
4. **Multidimensional Indicator Engine and SOM Cartography (Static, Trajectories, and Longitudinal):**
   - [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Generates in `./matrices/` the **42+ untruncated indicators** aggregated by front/topic, institution, or country (`by-entity`), CMA annual series (`annual-series --cma-window 3`), and period windows (`period-series`).
   - [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Topological SOM projection of fronts, Topics, or leading countries/institutions by selecting the most informative indicator subset (`--indicator-cols`), U-Matrix, Component Planes, and Vesanto meta-clustering with Silhouette ($s^*$).
   - [`som-trajectory-mapping`](../som-trajectory-mapping/SKILL.md) and [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md): Temporal evolution of fronts or leading actors via cubic-spline orbits ($\le 5$ entities) or Warm-Start intertemporal chaining ($\Delta W$).
5. **Complementary Modules for Kinetics, Geopolitics, Open Access, and SDGs:**
   - [`classical-bibliometrics-laws`](../classical-bibliometrics-laws/SKILL.md): Price's exponential/logistic growth kinetics ($\alpha, t_d$), Lotka, Bradford, and Price's Index.
   - [`geopolitical-collaboration-analyst`](../geopolitical-collaboration-analyst/SKILL.md): International collaboration matrix (Salton's Cosine $S_{ij}$) and leadership by country/bloc.
   - [`open-access-monitor`](../open-access-monitor/SKILL.md), [`sdg-impact-intelligence`](../sdg-impact-intelligence/SKILL.md), and [`openalex-mexico-visualizer`](../openalex-mexico-visualizer/SKILL.md).

---

## Stage II: Curation and Technique Selection Criteria

Before drafting the report, the agent evaluates the artifacts generated in `./reportes/` and applies the following rules:

1. **Selecting the Winning Research Front Detection Method:**
   - If the agent tested bibliographic coupling, co-citation, and/or OpenAlex Topic grouping, it must evaluate which partition exhibits higher modularity ($Q$), non-trivial corpus coverage, and clear thematic differentiation. The technique with the strongest signal leads the report; if two modalities complement each other (as in the *Polaritons* study, where Macro/Meso/Micro Topic evolution complements bibliographic coupling fronts), articulate them in successive sections.
2. **Selecting SOM Dimensions and Variant:**
   - Choose from `./matrices/` the indicators that best discriminate the nature of the fronts or actors (e.g., volume, FWCI, % Top 10%, citations/doc, H/G index, % international collaboration, mean publication year/recency, or OA route), verifying the Silhouette coefficient ($s^*$).
   - If the time horizon or sample size per window does not justify running all 3 SOM variants simultaneously, retain the variant (Static, Trajectories, or Warm-Start Longitudinal) that most clearly reveals the differentiation and maturation of the fronts.
3. **Conditional Modules (SDGs, APCs, Geopolitics, Classical Laws):**
   - Include SDG analysis (`sdg-impact-intelligence`) or APC cost auditing (`open-access-monitor`) only when relevant empirical signal exists in the corpus or when requested by the user. Never pad tables with zeros or `N/D` / `N/A` merely to satisfy a fixed template.
4. **Exploration Log (`./reportes/exploration_log.md`):**
   - Record in `./reportes/exploration_log.md` which methods and parameters were tested and why the final selections were chosen for the report.

---

## Data Availability and Anti-Fabrication Rules

1. **Verified tables in ClickHouse (`rag.works_flat` global and `rag.works_academic_all` Mexico):** Use strictly verified columns (`publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `keywords`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `referenced_works`).
2. **Tables tailored to real indicators:** Design the columns of every table around the metrics actually computed in `./matrices/` and `./reportes/`. Printing empty columns filled with `N/D` or `N/A` is strictly prohibited.
3. **Specialization Indicators ($AI$, $\text{F-measure}$, $DShareC$, $CShareD$):** Apply the analytical context criteria of Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet (2026, *Journal of Informetrics*).
4. **Sober tone and Zero-Scaffolding Leakage:** Absolute prohibition of superlatives (*"revolutionary"*, *"unprecedented"*, *"spectacular"*, or their Spanish equivalents). Do not mention CLI commands or prompts in the main narrative.

---

# Modular Structure of the Research Fronts Radar Report
*(Note: Write all section headers and prose in the user's language).*

# [Report Title: Scientometric Radar, Evolution of Research Fronts, and Topological SOM Cartography in [Domain / Topic], [Year_i – Year_f]]

## 1. EXECUTIVE SUMMARY AND DOMAIN LANDSCAPE (RESUMEN EJECUTIVO Y PANORAMA DEL DOMINIO)
- **1.1. Global Diagnosis and Methodological Traceability (GLOBAL Guideline - ISSI):**
  * Synthesis of corpus magnitude ($N$ documents, citations, FWCI, % Top 10%, annual growth rate, and doubling time $t_d$), declaring the data source (`rag.works_flat` / `rag.works_academic_all` / others), cutoff date, field delineation strategy, and research front detection method selected after the exploratory phase.
- **1.2. Table 1: Identified Research Fronts Matrix:**
  * Present the primary detected fronts with their real computed metrics (e.g., Front ID, Thematic Label, Document Volume, Total Citations / Citations per Doc, FWCI or Impact, Mean Publication Year / Maturity Phase, and Core Terms or Leading Authors/Institutions).

---

## 2. TAXONOMIC ARCHITECTURE AND CONCEPTUAL NETWORKS OF THE FIELD (ARQUITECTURA TAXONÓMICA Y REDES CONCEPTUALES DEL CAMPO)
- **2.1. Disciplinary Convergence (Macro / Meso / Micro):**
  * Distribution of scholarly output across domains, fields, subfields, and topics, complemented by a **Mermaid** diagram of the corpus's actual thematic architecture.
- **2.2. Knowledge Network Structure:**
  * Analysis of the bibliographic coupling, co-citation, or conceptual co-occurrence network (`network_keywords.html`, `fronts_summary.csv`), highlighting interdisciplinary bridges and modular cohesion ($Q$).

---

## 3. DEEP ANALYSIS OF RESEARCH FRONTS AND LONGITUDINAL LINEAGES — AMI (ANÁLISIS PROFUNDO DE LOS FRENTES DE INVESTIGACIÓN Y LINAJES LONGITUDINALES)
- **3.1. Substantive Characterization of Each Active Front (Scientometrics + Literature Review):**
  * For each major front identified in Table 1, present an analytical subsection explaining:
     1. *The central scientific or technological problem addressed by the front.*
     2. *The findings, methodologies, or architectures proposed in its most-cited/central core papers within the corpus.*
     3. *Its impact profile, growth velocity, and leading institutions/countries.*
- **3.2. Evolutionary Dynamics and Alluvial Lineages (AMI):**
  * Analysis of intertemporal transitions across time windows (`alluvial_lineages.html`, `alluvial_events.csv`): which fronts exhibit **Persistence** (consolidated thread), which underwent **Splitting (*Split*)** into specialized sub-lines, which emerged via **Merging (*Merge*)** of prior communities, and which represent recent **Genesis** events.

---

## 4. MULTIDIMENSIONAL TOPOLOGICAL CARTOGRAPHY WITH SOM NETWORKS — KOHONEN (CARTOGRAFÍA TOPOLÓGICA MULTIDIMENSIONAL CON REDES SOM)
- **4.1. Multidimensional Positioning in the LabSOM Triad:**
  * Interpretation of the **U-Matrix**, **Component Planes** (across the dimensions selected from the 42 available), and **Vesanto Meta-clustering** (optimal $K^*$ by Silhouette $s^*$), classifying the leading fronts, countries, or institutions without scalar ranking reductionism.
- **4.2. SOM Cluster Table and Temporal Evolution (CMA+Splines Trajectories and/or Warm-Start Longitudinal):**
  * Present the SOM cluster characterization table (Strengths in red zones, vulnerabilities in green zones, and representative members) and discuss the dynamic evolution observed in the trajectories (`som_trajectories.html`) or longitudinal mapping (`longitudinal_som_report.md`).

---

## 5. GEOPOLITICAL DYNAMICS, SPECIALIZATION, AND COMPLEMENTARY DIMENSIONS — BY EMPIRICAL SIGNAL (DINÁMICA GEOPOLÍTICA, ESPECIALIZACIÓN Y DIMENSIONES COMPLEMENTARIAS)
*(Include the subsections that yielded significant findings during exploration):*
- **5.1. Geopolitics of Collaboration and Specialization ($CShareD$, $DShareC$, Salton):**
  * Leading national and institutional poles, highest-affinity bilateral Salton corridors (`geopolitical_dashboard.html`), and thematic specialization patterns.
- **5.2. (Conditional) Publication Channels, Open Access / APC Routes, and SDG Alignment:**
  * Distribution across Open Access routes (e.g., weight of preprints/Green OA vs. commercial Gold APC and Diamond OA) and/or contribution to the Sustainable Development Goals when relevant signal exists in the corpus.

---

## 6. CONCLUSIONS AND PROSPECTIVE IMPLICATIONS — ROADMAP (CONCLUSIONES E IMPLICACIONES PROSPECTIVAS)
- Identification of frontier research opportunities (fronts with high acceleration or emerging high impact and niches open to collaboration) and a short- and medium-term strategic roadmap.

---

## ANNEXES, REFERENCES, AND AUDITABLE SUPPLEMENTARY MATERIAL (ANEXOS, REFERENCIAS Y MATERIAL SUPLEMENTARIO AUDITABLE)
- **Bibliographic References:** Seminal corpus works discussed in Section 3 and methodological references (Carrillo-Calvet et al., 2025; Jiménez-Andrade et al., 2024, 2025, 2026; Ruiz-Sánchez et al., 2025; Villaseñor-García et al., 2017; Traag et al., 2019; Huang et al., 2011).
- **Workspace Artifact Catalog:** Table with links to `./corpus.parquet`, `./matrices/*.parquet`, `./reportes/fronts_summary.csv`, `./reportes/alluvial_lineages.html`, `./reportes/som_dashboard.html`, `./reportes/som_trajectories.html`, and `./reportes/exploration_log.md`.
