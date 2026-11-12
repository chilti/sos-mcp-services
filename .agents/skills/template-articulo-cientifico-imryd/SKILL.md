---
name: template-articulo-cientifico-imryd
description: >-
  Drafting of original scientific research manuscripts or scientometric reviews using the canonical IMRaD/IMRyD structure for submission to Q1/Q2 journals in Scientometrics and Science of Science (Polaritons / JoI Specialization style). Operates under a 2-stage protocol: I) Empirical workspace exploration across the full menu of Agent Skills (field delineation, ZERO-JOIN harvesting, 42+ indicator engine, classical laws, networks and research fronts, deep review of core papers, static/trajectory/longitudinal SOM triad, geopolitics, specialization, and OA/APC), and II) Scientific curation to discard non-informative techniques and build the manuscript narrative strictly around the strongest, most revealing empirical findings. Respond and label outputs in the user's language.
---

# Master Template: Original Scientific Research Article / Scientometric Review (IMRaD / IMRyD Format - Q1 Journal)
### *Inspired by the human research workflow of the LabSOM / C3-UNAM group (e.g., Sixty Years of Research on Polaritons, 2025; Specialization Indicators in Scientometrics, 2026; Neural Longitudinal & Trajectory Mapping, 2024–2025)*

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish). Write all section headers and prose of the generated manuscript in the user's language (e.g., **IMRaD** in English or **IMRyD** in Spanish depending on the user prompt).

This template guides the agent to investigate and draft an **ORIGINAL SCIENTIFIC RESEARCH MANUSCRIPT OR SCIENTOMETRIC REVIEW** following the canonical **IMRaD / IMRyD** structure at a publication-ready standard for international Q1/Q2 journals (*Journal of Informetrics*, *Scientometrics*, *Quantitative Science Studies*, *Research Evaluation*, *Engineering Reports*).

Unlike a rigid form, this template emulates the **real process of human scientific inquiry**: first the researcher formulates hypotheses, explores the corpus using a **broad menu of analytical techniques** in their workspace (*Laboratory Phase*), evaluates which methods yield structural patterns, statistical fit, or revealing discoveries, **discards techniques that carry no signal or break the narrative thread**, and finally structures the article around the **scientific story backed by the strongest empirical evidence** (*Curation and Drafting Phase*).

---

## Stage I: Menu of Agent Skills for Empirical Exploration (*Laboratory Phase*)

To guarantee methodological rigor, reproducibility, and zero hallucinations, the agent operates under the **Workspace-First** principle (`./corpus.parquet` $\to$ `./matrices/*.parquet` $\to$ `./reportes/`) by delegating computations to the following **Menu of Agent Skills**:

### 1. Mandatory Foundation: Field Delineation, Harvesting, and Multidimensional Matrices
*(If `./corpus.parquet` and `./matrices/` already exist in the workspace, the agent reuses them directly without re-downloading).*

- **Field Delineation and Search Strategy:**
  * [`bibliometric-search-strategist`](../bibliometric-search-strategist/SKILL.md): Multi-stage field delineation (Huang, Schiebel & Porter, 2011), auditing under the **GLOBAL (ISSI)** guideline, and transpilation to ClickHouse SQL (`rag.works_flat` for global scope or `rag.works_academic_all` for Mexico, with **ZERO JOINs**) or native WoS/Scopus/PubMed syntax.
- **Corpus Harvesting into `./corpus.parquet`:**
  * [`openalex-search-engineer`](../openalex-search-engineer/SKILL.md): Columnar extraction from global ClickHouse (`rag.works_flat`, 464M+ works) including `referenced_works`, `all_country_codes`, `keywords`, and impact metrics.
  * [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md): National orchestrator over `rag.works_academic_all` (1.65M Mexican scholarly works).
  * Optional external harvesters: [`openalex-harvester`](../openalex-harvester/SKILL.md), [`scopus-harvester`](../scopus-harvester/SKILL.md), [`pubmed-harvester`](../pubmed-harvester/SKILL.md), [`arxiv-harvester`](../arxiv-harvester/SKILL.md), [`semantic-scholar-harvester`](../semantic-scholar-harvester/SKILL.md), or [`scientometrics-incites-expert`](../scientometrics-incites-expert/SKILL.md).
- **Computation of the Full Indicator Battery (Without Column Truncation):**
  * [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Computes the global summary (`summary`) and generates in `./matrices/` the **46-column matrices (42 numerical indicators + 4 metadata columns)** by country, institution, author, source, or topic (`by-entity`), Centered Moving Average smoothed annual series (`annual-series --cma-window 3`), and multi-year period windows (`period-series`).
  * [`bibliometric-eda-profiler`](../bibliometric-eda-profiler/SKILL.md): Exploratory profiling, H/G/M indices, and dispersion metrics.

### 2. Menu of Exploratory Analytical Families (Select, Test, and Evaluate)

The agent has 5 families of techniques to explore its research questions ($RQ_1, RQ_2, \dots$):

| Analytical Family | Available Agent Skills | What It Enables Exploring and Testing in the Laboratory |
| :--- | :--- | :--- |
| **Family A: Temporal Dynamics and Classical Laws** | [`classical-bibliometrics-laws`](../classical-bibliometrics-laws/SKILL.md) | Price's exponential vs. logistic growth fitting ($R^2$, growth rate $\alpha$, doubling time $t_d$), detection of inflection points/structural breaks ($\tau$), Lotka's productivity law (full vs. fractional counting, KS test), Bradford zones, and Price's Obsolescence Index. |
| **Family B: Intellectual Structure, Networks, and Research Fronts** | [`topics-research-fronts-intelligence`](../topics-research-fronts-intelligence/SKILL.md), [`research-fronts-detection-expert`](../research-fronts-detection-expert/SKILL.md), [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md) | Compare **bibliographic coupling** (emerging recent fronts), **co-citation** (foundational intellectual bases), **direct citation**, or **conceptual co-occurrence** using Leiden partitioning (CPM/Modularity). Track longitudinal evolution and AMI alluvial events (persistence, merge, split, genesis) across time windows or Macro/Meso/Micro levels. |
| **Family C: Deep Literature Review and Core Papers** | [`deep-literature-researcher`](../deep-literature-researcher/SKILL.md), [`graphrag-scientific-intelligence`](../graphrag-scientific-intelligence/SKILL.md) | Citation Snowballing with Glänzel's density filter ($k \ge 2$) for state-of-the-art review, and **substantive reading of the most cited/central papers within each detected front** in `./corpus.parquet` to explain the real scientific findings of each community (following Section 6 of the *Polaritons* article). |
| **Family D: Neurocomputational SOM Cartography (The 3 LabSOM Variants)** | [`som-methodological-expert`](../som-methodological-expert/SKILL.md), [`som-trajectory-mapping`](../som-trajectory-mapping/SKILL.md), [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md), [`semantic-manifold-expert`](../semantic-manifold-expert/SKILL.md) | 1) **Static SOM:** Multidimensional profiles of countries, institutions, or fronts across any subset of the 42 indicators (`--indicator-cols`), U-Matrix, Component Planes, and Vesanto meta-clustering optimized by Silhouette ($s^*$).<br>2) **Trajectory SOM:** Continuous temporal evolution smoothed with CMA and cubic splines ($\le 5$ focal entities or global profile).<br>3) **Warm-Start Longitudinal SOM:** Synaptic drift ($\Delta W$) and intertemporal cohort rotation across periods. |
| **Family E: Geopolitics, Specialization, OA/APC Routes, and SDGs (Modular)** | [`geopolitical-collaboration-analyst`](../geopolitical-collaboration-analyst/SKILL.md), [`open-access-monitor`](../open-access-monitor/SKILL.md), [`sdg-impact-intelligence`](../sdg-impact-intelligence/SKILL.md), [`journal-editorial-intelligence`](../journal-editorial-intelligence/SKILL.md) | Bilateral affinity (Salton's Cosine $S_{ij}$), authorship leadership, specialization indicators ($AI$, $\text{F-measure}$, $DShareC$, and $CShareD$), auditing of the 6 Open Access routes and APC expenditure (USD), and alignment with SDGs 1–17. |

---

## Stage II: Scientific Curation and Pruning Protocol (*From Lab Data to the Paper's Narrative*)

In real scientific research, **not every exploratory analysis belongs in the published manuscript**. Before drafting the article, the agent must evaluate the results obtained in Stage I and apply the following **Selection and Pruning Rules**:

1. **Narrative Thread Criterion (*Scientific Storytelling*):**
   - Define the central thesis and narrative arc of the article backed by the strongest evidence (e.g., *the emergence of a new hegemonic pole such as China in Polaritons? The bifurcation of a theoretical front toward engineering applications? A paradox between output volume and normalized citation impact revealed by the SOM?*).
   - Select strictly between **3 and 5 main analytical blocks** that connect organically to answer the research questions ($RQ_1 \dots RQ_k$).

2. **Methodological Competition and Signal Quality Criterion (Test and Prune):**
   - **In Research Fronts and Networks:** If multiple network modalities were tested (e.g., bibliographic coupling vs. co-citation vs. co-occurrence), retain for the main text the representation offering higher modularity ($Q$), thematically coherent clusters, and clearer historical resolution, discarding noisy or redundant networks.
   - **In Indicator Selection and SOM Variants:**
     * The agent has 42 numerical indicators in `./matrices/`. Instead of blindly using a fixed list, select the dimensions that carry theoretical meaning for the research question (e.g., including *Global Share* $CShareD$ and *National Share* $DShareC$, FWCI, % Top 10%, % International Collaboration, G/M index, or Diamond OA route) and verify that they yield a partition with a solid **Silhouette coefficient ($s^*$)** and interpretable gradients across the Component Planes.
     * Choose the SOM variant best suited to the study design: **Static SOM** (for cross-sectional profile benchmarking), **CMA+Splines Trajectory SOM** (when annual time series span a sufficient horizon to trace smooth orbits of $\le 5$ leading actors), and/or **Warm-Start Longitudinal SOM** (when contrasting discrete multi-year windows). If one variant adds no new insight beyond another, omit it from the main text.
   - **In Classical Bibliometric Laws:** If the time horizon is very short (e.g., 3–5 years) and logistic fitting or Price's Index is uninformative, or if Bradford/Lotka distributions are tangential to the study's thematic focus, report only the relevant growth kinetics and discard curve fits that add no analytical value.
   - **In Specialized Modules (OA/APC, SDGs, Geopolitics):** Include Open Access/APC or SDG sections/tables **only if** they are part of the study objectives or if exploration uncovered a compelling empirical finding (e.g., a stark asymmetry between Green/arXiv and commercial Gold APC routes, or strong concentration in a specific SDG). Never shoehorn disconnected subsections into the central thesis.

3. **Transparent Logging in the Exploration Log (`./reportes/exploration_log.md`):**
   - Before drafting the manuscript, save or update `./reportes/exploration_log.md` briefly summarizing: (a) which menu techniques were executed, (b) which were selected for the main body of the manuscript based on empirical robustness, and (c) which were discarded or moved to Supplementary Material and why.

---

## Data Availability and Anti-Fabrication Rules (Inviolable)

**Verified tables and columns in ClickHouse (`rag.works_flat` for global scope with 464.8M works and `rag.works_academic_all` for Mexican output with 1.65M works)**: `publication_year`, `cited_by_count`, `is_oa`, `oa_status` (`closed`, `green`, `diamond`, `gold`, `bronze`, `hybrid`), `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `keywords`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `is_doaj_journal`, `is_core_journal`, `referenced_works`.

1. **Table Design with Zero Empty Columns (`N/D` / `N/A`):** Construct manuscript tables **exclusively with indicator columns that were actually computed and contain real data in the workspace**. Never include entire columns filled with `N/D` or `N/A` (such as JCR/Scimago quartiles, industry collaboration, or first-author rates when not extracted from `raw_data`). If an unavailable schema indicator is conceptually relevant, mention it briefly in the methodological limitations.
2. **Author count and hyperauthorship:** Use `length(author_names)`. Apply the breakdown by authorship regimes ($\le 20$ vs. $> 20$ authors) when the studied field exhibits genuine hyperauthorship (*Big Science*); do not force an empty tripartite table if all or nearly all works in the corpus have $\le 20$ authors.
3. **APC:** Use `apc_paid_usd` (observed) and `apc_list_usd` (list price) or the audited estimate from `open-access-monitor`, always specifying which metric is reported.
4. **Specialization Indicators ($AI$, $\text{F-measure}$, $DShareC$, and $CShareD$):** Following Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet (2026, *Journal of Informetrics*), rigorously distinguish between **internal prioritization of a domain within an entity ($DShareC$, *National/Institutional Share*)** and **the entity's share in the global total of the domain ($CShareD$, *Global Share*)**, noting that when comparing countries within a fixed domain, $AI$ is rank-equivalent to $DShareC$ and the $\text{F-measure}$ acts as a proxy for $CShareD$, whereas when comparing domains within a single country the pattern is inverted.
5. **Salton's Cosine:** Verify $S_{ij} = C_{ij}/\sqrt{C_i C_j}$ from co-authorship counts ($C_{ij}$, $C_i$, $C_j$).
6. **Matrix Computation and SOM Training:** Always first generate `./matrices/*.parquet` with `tlachia_metrics_cli.py` (46 untruncated columns) and train the SOM with `som_pipeline_cli.py`, `som_trajectory_cli.py`, or `neural_longitudinal_cli.py`, persisting `./reportes/som_state.json` and `./reportes/som_dashboard.html`.

---

## Strict Editorial Rules

- **MEASURED AND SOBER ACADEMIC TONE (ABSOLUTE PROHIBITION OF SUPERLATIVES):** Employ a strictly academic, neutral, evidence-based style. Hyperbolic adjectives are strictly forbidden (*"revolutionary"*, *"unprecedented"*, *"extraordinary"*, *"spectacular"*, *"overwhelming"*, *"pioneering"*, *"astonishing"*, or their Spanish equivalents *"revolucionario"*, *"sin precedentes"*, *"espectacular"*, etc.).
- **ZERO-SCAFFOLDING LEAKAGE:** The manuscript must read like a formal peer-reviewed journal article. Do not mention internal script names, CLI commands, prompts, or chat environments in the main body of the article (reserve script names for the Data & Code Availability and Supplementary Material sections).
- **INTEGRATION OF SCIENTOMETRICS + SUBSTANTIVE DOMAIN CONTENT:** Especially when analyzing research fronts (following *Polaritons*, Ruiz-Sánchez et al., 2025), do not merely list cluster numbers: **discuss what scientific problems, methods, or discoveries are addressed by the seminal and most-cited papers of each front**.

---

# Modular Structure of the IMRaD / IMRyD Manuscript (Adapt Subsections to Curated Findings)
*(Note: Write all section headers and body text in the user's language—e.g., English IMRaD headers or Spanish IMRyD headers depending on the user's prompt).*

# [Formal, Descriptive, and Informative Title in the User's Language (and/or Bilingual Title)]

> ## ABSTRACT / RESUMEN
> Present a cohesive abstract (or structured into *Objective, Methodology, Results, and Conclusions*) synthesizing the scientific problem studied, the analyzed corpus, the specific combination of techniques selected after curation (e.g., bibliographic coupling networks, literature review, and multidimensional SOM mapping), and the main quantitative and substantive findings.
>
> **Keywords / Palabras clave:** (5 to 7 canonical terms in alphabetical order).

---

## 1. INTRODUCTION AND DOMAIN BACKGROUND (INTRODUCCIÓN Y ANTECEDENTES DEL DOMINIO)
- **1.1. Phenomenology and Scientific Significance of the Studied Field:**
  * Explain the origin and conceptual or technological milestones of the analyzed topic (e.g., from foundational theoretical predictions to contemporary applications) and why its current structure warrants a computational and scientometric cartography.
- **1.2. State of the Art (Background) and Analytical Gap:**
  * Critical synthesis of prior bibliometric studies or reviews on the topic or related areas (supported by a comparative table of previous studies when helpful).
  * Explicit articulation of the research questions ($RQ_1, RQ_2, \dots$) and the differential contribution of the study.

---

## 2. MATERIALS AND METHODS (MATERIALES Y MÉTODO: DATA SOURCES, INDICATORS & WORKFLOW)
- **2.1. Data Sources, Search Strategy, and Selection Criteria (GLOBAL Guideline - ISSI):**
  * Declare the database used (OpenAlex / ClickHouse `rag.works_flat` or `rag.works_academic_all`, Web of Science, Scopus, InCites), exact cutoff date, search query equation, time window, included document types, and final size of the curated corpus ($N$).
  * Include a **Methodological Workflow Diagram (Mermaid)** illustrating the actual stages applied in the study (Corpus harvesting and filtering $\to$ Computed indicators $\to$ Selected analytical workflows: e.g., LabSOM Workflow and Networks/Fronts Workflow).
- **2.2. Selected Scientometric Indicators:**
  * Formally define—with their mathematical formulation—**only the indicators used in the analyses that passed the curation phase** (e.g., productivity, growth rates, FWCI/CNCI, % Top 10%, % Top 1%, *Global Share* $CShareD$, *National/Institutional Share* $DShareC$, Activity Index $AI$, $\text{F-measure}$, H/G/M indices, % International Collaboration, Open Access routes, or Salton's Cosine).
- **2.3. Data Processing, Network Analysis, and Neurocomputational SOM Modeling:**
  * Explain with technical rigor the methodologies used in the selected results:
    - *If kinetic/laws analysis is included:* mathematical formulation of the fitted models.
    - *If network and research front analysis is included:* selected network modality (e.g., bibliographic coupling, co-citation, or co-occurrence), normalization (*Association Strength* or Salton's Cosine), partitioning algorithm (Leiden CPM/Modularity), resolution parameter ($\gamma$), and longitudinal tracking method (time windows or AMI alluvial lineages).
    - *If SOM Cartography is included (Static, CMA+Splines Trajectories, and/or Warm-Start Longitudinal):* formulation of the vector space $\mathbb{R}^D$, hexagonal topology, SVD spectral sizing ($\sigma_1/\sigma_2$), U-Matrix, diverging Component Planes (Green-Yellow-Red), Vesanto & Alhoniemi meta-clustering optimized with Silhouette ($s^*$), and, where applicable, Centered Moving Average smoothing and parametric cubic spline interpolation (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2025; Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet, 2024; Villaseñor-García et al., 2017).

---

## 3. RESULTS (RESULTADOS: STRUCTURED ACCORDING TO CURATED MODULES)
*(Organize the Results sections or subsections following the logical order of the scientific narrative, activating only the modules backed by solid empirical findings in `./reportes/`):*

- **Module A — Output Evolution, Growth Kinetics, and Global Profile:**
  * Analysis of the historical stages of the field, growth rates ($\alpha$), doubling times ($t_d$), inflection points, and evolution of collaboration or global impact.
- **Module B — Multidimensional Performance Profiles and SOM Evolution (Countries / Institutions / Actors):**
  * Characterization of the most productive entities in the static SOM (clusters, strengths in red zones vs. depressed areas in green zones, comparable-peer diagnosis, and metric paradoxes such as FWCI vs. Percentile or $DShareC$ vs. $CShareD$).
  * Analysis of temporal evolution via the **Trajectory SOM** (orbits of the $\le 5$ leading entities or global trajectory) and/or the **Warm-Start Longitudinal SOM** (synaptic drift $\Delta W$, convergence, divergence, and persistent core).
- **Module C — Thematic Evolution and Network Structure (Macro, Meso, and Micro / Co-occurrence / Geopolitics):**
  * Distribution and evolution of thematic areas, subfields, or Topics over time, and/or structure of international collaboration networks (Salton's Cosine, geopolitical blocs).
- **Module D — Research Fronts: Bibliometric Cartography + Substantive Literature Review:**
  * Identification of active research fronts and their longitudinal genealogy (AMI alluvial transitions or period-by-period evolution).
  * **Substantive analysis of each front (LabSOM / Polaritons Hallmark):** For each main front or temporal stage, integrate cluster metrics with a scientific discussion of its foundational and highest-impact papers in the corpus, explaining the theoretical, methodological, or experimental contributions that define each community.
- **Module E (Optional / Conditional) — Political Economy of Open Access, APCs, or SDGs:**
  * Include when it reveals empirical findings relevant to the research question (e.g., transition toward preprints/Green OA, concentration of APC expenditure in USD, or contribution to Agenda 2030 SDGs).

---

## 4. DISCUSSION AND IMPLICATIONS (DISCUSIÓN E IMPLICACIONES)
- Integrative synthesis connecting the macro, meso, and micro findings of the study with prior literature and the research questions ($RQ_1 \dots RQ_k$).
- Discussion of structural tensions, specialization dynamics, or methodological and technological challenges in the studied field.
- **Study Limitations:** Coverage of the database used, scope of the temporal cutoff, or lexical/toponymic filters applied.

---

## 5. CONCLUSIONS (CONCLUSIONES)
- Precise and concise recapitulation of the empirical and methodological contributions of the work, along with open avenues for future research.

---

## REFERENCES (REFERENCIAS BIBLIOGRÁFICAS)
*(Include all disciplinary references cited from the corpus alongside the methodological references actually used in the article, formatted in APA 7th edition or the target journal's citation style).*

**Core Group and Classical Methodological References (Cite those corresponding to the applied techniques):**
1. **Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025).** Redes neuronales autoorganizadas y mapeos de la ciencia. In S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 271–292). UNAM, IIBI. ISBN-e: 978-607-642-193-2.
2. **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA. In S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 293–313). UNAM, IIBI.
3. **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2026).** Specialization indicators in scientometrics: Understanding the Activity Index and the F-measure through their underlying components. *Journal of Informetrics*, 20, 101880. https://doi.org/10.1016/j.joi.2026.101880
4. **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** Neural longitudinal mapping of multidimensional performance profiles of Latin American universities. *Iberoamerican Journal of Science Measurement and Communication*, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92
5. **Ruiz-Sánchez, R., Arencibia-Jorge, R., Jiménez-Andrade, J. L., Tagüeña, J., Carrillo-Calvet, H., & Rubo, Y. G. (2025).** Sixty years of research on polaritons: A scientometric review. *Engineering Reports*, 7, e70045. https://doi.org/10.1002/eng2.70045
6. **Villaseñor-García, E. A., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2017).** Multiparametric characterization of scientometric performance profiles assisted by neural networks: A study of Mexican higher education institutions. *Scientometrics*, 110(1), 77–104. https://doi.org/10.1007/s11192-016-2166-0
7. **Vesanto, J., & Alhoniemi, E. (2000).** Clustering of the Self-Organizing Map. *IEEE Transactions on Neural Networks*, 11(3), 586–600.
8. **Perianes-Rodriguez, A., Waltman, L., & van Eck, N. J. (2016).** Constructing bibliometric networks: A comparison between full and fractional counting. *Journal of Informetrics*, 10(4), 1178–1195.
9. **Traag, V. A., Waltman, L., & van Eck, N. J. (2019).** From Louvain to Leiden: guaranteeing well-connected communities. *Scientific Reports*, 9(1), 5233.
10. **Huang, C., Schiebel, E., & Porter, A. L. (2011).** A multi-stage approach to mapping emerging technologies: the case of DNA sequencing technology. *Scientometrics*, 87(2), 241–260.
11. **Hicks, D., Wouters, P., Waltman, L., de Rijcke, S., & Rafols, I. (2015).** Bibliometrics: The Leiden Manifesto for research metrics. *Nature*, 520(7548), 429–431.

---

## DATA & CODE AVAILABILITY AND SUPPLEMENTARY MATERIAL STATEMENTS (DECLARACIONES DE DISPONIBILIDAD DE DATOS, CÓDIGO Y MATERIAL SUPLEMENTARIO)
- **Data & Code Availability Statement:** Specify the primary data source, cutoff date, and reproducible artifacts generated in the workspace (`./corpus.parquet`, `./matrices/*.parquet`, `./reportes/som_state.json`, interactive HTML dashboards, and `./reportes/exploration_log.md`).
- **Supplementary Material Index:** List in a table all datasets, neural state files, interactive HTML figures (`som_dashboard.html`, `som_trajectories.html`, `alluvial_lineages.html`, networks), and the exploration log documenting the additional evaluated techniques.
