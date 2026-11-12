---
name: template-informe-tecnico-institucional
description: >-
  Preparation of authoritative institutional scientometric evaluation technical reports (Instituto de Neurobiología / INB UNAM, ICN, INCan style). Operates under a 2-stage protocol: I) Empirical workspace exploration across the menu of Agent Skills (ROR identity and academic departments, global/national harvesting, benchmarking against specialized peer institutions, untruncated 42+ indicator engine, SNII faculty census, collaboration networks, thematic evolution, OA/APC audit, and static/trajectory/longitudinal SOM triad), and II) Scientific curation to discard non-informative analyses and structure the report around the dimensions and indicators of highest diagnostic value. Respond and label outputs in the user's language.
---

# Master Template: Institutional Evaluation Technical Report, Peer Benchmarking, and Multidimensional SOM Diagnosis
### *Inspired by the C3-UNAM / LabSOM scientometric reports for academic departments and research institutes (Instituto de Neurobiología / INB, ICN, INCan)*

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish). Write all section headers and prose of the generated technical report in the user's language.

This template guides the preparation of an authoritative **INSTITUTIONAL EVALUATION TECHNICAL REPORT** for university leadership, institute directors, technical councils, and science policy committees.

It integrates the **neurocomputational framework for multidimensional performance profile analysis based on Kohonen Self-Organizing Maps (SOM)** (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor-García et al., 2017; Jiménez-Andrade et al., 2024, 2025, 2026) to overcome the reductionism of one-dimensional rankings (*weighing and summing*), evaluating the institution **against specialized homologous institutions and legitimate peers** (as in the comparative study of the INB against national and international neuroscience centers).

---

## Stage I: Menu of Agent Skills for Institutional Exploration (*Laboratory Phase*)

The agent operates under the **Workspace-First** principle (`./corpus.parquet` $\to$ `./matrices/*.parquet` $\to$ `./reportes/`) and uses the following **Menu of Agent Skills** to explore the dimensions of the evaluated institution:

1. **Institutional Identity, Harvesting, and Comparison Universe (`./corpus.parquet`):**
   - [`openalex-mexico-institutions`](../openalex-mexico-institutions/SKILL.md) and [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md): Resolution of the canonical **ROR** code (e.g., UNAM `https://ror.org/01tmp8f25`, Cinvestav `https://ror.org/05cb51e40`) and isolation of university departments, faculties, or campuses (e.g., *Instituto de Neurobiología*, *Instituto de Ciencias Nucleares*) via case- and diacritic-insensitive filtering on `institution_names` over `rag.works_academic_all` (ZERO JOINs).
   - [`openalex-search-engineer`](../openalex-search-engineer/SKILL.md) (`rag.works_flat`) and [`scientometrics-incites-expert`](../scientometrics-incites-expert/SKILL.md): Extraction of output and indicators for **international or national homologous institutions specialized in the same domain and of comparable scale** (following Section 2 of the *2022 INB Report*).
2. **42+ Multidimensional Indicator Engine (Without Column Truncation):**
   - [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Generates in `./matrices/` the full **46-column matrix (42 numerical indicators + 4 metadata columns)** for the institution, its comparable peers, its researchers, or its thematic areas (`by-entity`), as well as the Centered Moving Average smoothed annual time series (`annual-series --cma-window 3`) and period-by-period evolution (`period-series`).
3. **Menu of Exploratory Analytical Modules (Test and Select According to the Institution's Profile):**
   - **Hyperauthorship and Autonomous Capacity Module:** Breakdown of output by `length(author_names)` ($\le 20$ authors vs. mega-consortia $> 20$ authors) when the institute participates in *Big Science* collaborations (e.g., high-energy physics at ICN, genomics, or astronomy).
   - **Thematic Evolution and Specialization Module ($AI$, $\text{F-measure}$, $DShareC$, $CShareD$):** [`topics-research-fronts-intelligence`](../topics-research-fronts-intelligence/SKILL.md) and category/subfield analysis to identify the institute's thematic development stages, internal prioritization ($DShareC$), and weight in the national/global context ($CShareD$) (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2026).
   - **Institutional and International Collaboration Networks Module:** [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md) and [`geopolitical-collaboration-analyst`](../geopolitical-collaboration-analyst/SKILL.md) to map intramural, national, and international co-authorship networks.
   - **Multidimensional SOM Cartography Module (The 3 LabSOM Variants):**
     * [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Positioning of the institute relative to its universe of homologous peer institutions in the static SOM, selecting the indicators with the highest diagnostic power (`--indicator-cols`), U-Matrix, Component Planes, and comparable-peer clusters.
     * [`som-trajectory-mapping`](../som-trajectory-mapping/SKILL.md) and [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md): Historical evolution of the institute's own performance profile across years (continuous CMA+Splines trajectory, as in Section 5 of the *INB Report*) or across administrative terms/periods (Warm-Start $\Delta W$).
   - **Academic Faculty and SNII Registry Module:** [`snii-identity-resolver`](../snii-identity-resolver/SKILL.md), [`openalex-mexico-author-search`](../openalex-mexico-author-search/SKILL.md), and [`infotlachia-scholar-intelligence`](../infotlachia-scholar-intelligence/SKILL.md) (distribution across Candidate to Emeritus levels, Lotka concentration, and generational renewal).
   - **Open Access, APC Costs, Journals, and SDGs Module:** [`open-access-monitor`](../open-access-monitor/SKILL.md) (6 OA routes and APC expenditure in USD), [`journal-editorial-intelligence`](../journal-editorial-intelligence/SKILL.md), [`sdg-impact-intelligence`](../sdg-impact-intelligence/SKILL.md), and [`openalex-mexico-visualizer`](../openalex-mexico-visualizer/SKILL.md).

---

## Stage II: Curation and Pruning Criteria in Institutional Reports

Every institution has a distinct mission, scale, and structural profile (evaluating a nuclear physics institute participating in CERN mega-consortia differs fundamentally from evaluating a neurobiology institute or a social research institute). The agent must apply these rules before drafting:

1. **Adaptation to the Institution's Vocation (Test and Prune):**
   - **Hyperauthorship Filter ($\le 20$ vs. $> 20$ authors):** If exploring `./corpus.parquet` shows that articles with $> 20$ authors represent a significant share or distort the institutional FWCI, the tripartite breakdown becomes a central axis of the report. Conversely, if $\ge 98\%$ of output has $\le 20$ authors, **do not force an artificial section or table on mega-consortia**: simply note the statistic in one methodological sentence and devote the space to thematic evolution and peer benchmarking.
   - **Dimension Selection in the SOM:** Explore in `./matrices/` which combination of indicators best captures both the strengths and areas of opportunity of the entity relative to its peers (e.g., volume, FWCI, % Top 10%, % international collaboration, H/G index, Diamond OA route, or specialization), verifying the Silhouette coefficient ($s^*$).
   - **Own-Profile Evolution vs. Peer Benchmarking:** Following the *INB Report* model, combine—whenever data permit—(a) the comparative SOM against homologous institutions, and (b) the evolutionary trajectory SOM of the institution itself across years or periods.
2. **Zero Empty Columns (`N/D` / `N/A`) in Tables:**
   - Build all report tables **exclusively with indicators computed from real data**. If an indicator (such as first-author rate from `raw_data`, or the SNII registry when evaluating a foreign entity) is absent from the workspace data, omit that column from the table instead of filling it with `N/D` or `N/A`.
3. **Exploration Log (`./reportes/exploration_log.md`):**
   - Document in `./reportes/exploration_log.md` the analyses carried out in the workspace and the rationale for the dimensions selected for the final report.

---

## Data Availability, Anti-Fabrication Rules, and Editorial Standards

1. **Verified tables and columns in ClickHouse (`rag.works_academic_all` and `rag.works_flat`):** `publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `keywords`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `is_doaj_journal`, `is_core_journal`, `referenced_works`.
2. **Disambiguation of university departments/institutes:** The ROR identifies the parent university (e.g., UNAM). To isolate a specific faculty, school, or research institute, filter by `institution_names` and explicitly state the scope of the toponymic filter in the methodological note.
3. **Sober executive tone and Zero-Scaffolding Leakage:** Absolute prohibition of hyperbolic adjectives (*"spectacular"*, *"revolutionary"*, *"unprecedented"*, or their Spanish equivalents). Never mention prompts or chat tools in the body of the report.

---

# Modular Structure of the Institutional Technical Report (Adapt to Curated Findings)
*(Note: Write all section headers and prose in the user's language).*

# [Official Title: Scientometric Evaluation, Thematic Evolution, and Multidimensional SOM Diagnosis of [Institution / Department Name], Period [Year_i – Year_f]]

## 1. EXECUTIVE SUMMARY AND SITUATIONAL DIAGNOSIS (RESUMEN EJECUTIVO Y DIAGNÓSTICO SITUACIONAL)
- **1.1. Institutional Context and Positioning Synthesis:**
  * Mission of the entity, historical and recent output volume, normalized citation impact (FWCI), placement in the top decile (Top 10%), and primary structural strengths and tensions identified.
- **1.2. Table 1: Key Institutional Performance Indicators (Diagnostic Traffic Light):**
  * Present the indicators actually computed for the institution contrasted against its benchmark (parent university average, national or global average, or homologous peers) and its diagnostic status (🟢 Optimal / Strength, 🟡 Preventive Alert, 🔴 Priority Attention Area).

---

## 2. MATERIALS, METHODS, AND TRACEABILITY (MATERIALES, MÉTODO Y TRAZABILIDAD — GLOBAL GUIDELINE - ISSI)
- **2.1. Information Sources and Institutional Output Delineation:**
  * Databases used (`rag.works_academic_all`, `rag.works_flat`, InCites/WoS/Scopus, SNII Registry), ROR identifier, department disambiguation criteria, cutoff date, and counting methods (full vs. fractional; plus hyperauthorship breakdown where applicable).
- **2.2. Indicators and Neurocomputational SOM Methodology:**
  * Definition of the indicators selected after exploration and explanation of multidimensional profile and trajectory modeling using Kohonen Self-Organizing Maps (SOM).

---

## 3. SCIENTIFIC OUTPUT DYNAMICS AND COMPARATIVE STUDY WITH HOMOLOGOUS INSTITUTIONS (DINÁMICA DE LA PRODUCCIÓN CIENTÍFICA Y ESTUDIO COMPARATIVO CON INSTITUCIONES HOMÓLOGAS)
- **3.1. Historical Evolution of Productivity and Visibility:**
  * Analysis of the entity's growth stages and its percentage share relative to the parent institution, country, and region (including, where disciplinary norms warrant, the comparison between autonomous output $\le 20$ authors and consortia $> 20$ authors).
- **3.2. Benchmarking Against Specialized Homologous Institutions:**
  * Performance comparison across volume, normalized citation impact (FWCI), excellence (% Top 10% / Top 1%), and collaboration against national and international institutions of similar mission and scale.

---

## 4. THEMATIC EVOLUTION, RESEARCH FRONTS, AND COLLABORATION NETWORKS (EVOLUCIÓN TEMÁTICA, FRENTES DE INVESTIGACIÓN Y REDES DE COLABORACIÓN)
- **4.1. Specialization and Thematic Evolution ($DShareC$, $CShareD$, $AI$, $\text{F-measure}$, and Fronts):**
  * Distribution of output across areas, subfields, and active research fronts; identification of consolidated lines of inquiry and emerging topics over time.
- **4.2. Scientific Collaboration Structure:**
  * Co-authorship networks with other university departments, national institutions, and international partners (`network_institutions.html` / `geopolitical_dashboard.html`).

---

## 5. MULTIDIMENSIONAL PERFORMANCE PROFILE AND SOM EVOLUTION (PERFIL MULTIDIMENSIONAL DE DESEMPEÑO Y EVOLUCIÓN EN EL SOM - KOHONEN)
- **5.1. Positioning Relative to Comparable Peers in the LabSOM Triad:**
  * Analysis across the **U-Matrix**, **Component Planes** (Green-Yellow-Red), and **Vesanto Meta-clustering** (optimal $K^*$ by Silhouette $s^*$), identifying the institution's cluster of legitimate peers, its cardinal strengths (red zones), and its relative vulnerabilities (green zones).
- **5.2. Cluster Table and Temporal Evolution of the Institutional Profile (SOM Trajectory / Longitudinal):**
  * Characterization table of the SOM clusters and analysis of the institution's own evolutionary trajectory across the studied time windows (`som_dashboard.html`, `som_trajectories.html`, and/or `longitudinal_som_report.md`).

---

## 6. GOVERNANCE DIMENSIONS: ACADEMIC FACULTY, OPEN ACCESS, AND APC COSTS (DIMENSIONES DE GOBERNANZA: CLAUSTRO ACADÉMICO, ACCESO ABIERTO Y COSTOS APC — AS APPLICABLE)
*(Include and develop in depth the subsections supported by the study's data):*
- **6.1. Faculty Structure, Author Productivity, and SNII Registry:**
  * Composition across SNII levels, researcher productivity distribution, and generational renewal diagnosis.
- **6.2. Audit of the 6 Open Access Routes and Publication Costs in APCs (USD):**
  * Table and analysis of the distribution across the 6 OA routes (`diamond`, `gold`, `hybrid`, `green`, `bronze`, `closed`), observed/estimated expenditure in commercial APC fees (USD), and cost-saving opportunities via Diamond OA and Green repositories.

---

## 7. FINAL CONSIDERATIONS AND STRATEGIC RECOMMENDATIONS MATRIX — 1, 3, AND 5 YEARS (CONSIDERACIONES FINALES Y MATRIZ DE RECOMENDACIONES ESTRATÉGICAS)
- Integrative synthesis of findings and **Actionable Recommendations Table** for governing bodies and collegiate councils (Short term: 1 year; Medium term: 3 years; Long term: 5 years) with verifiable indicators.

---

## ANNEXES, REFERENCES, AND AUDITABLE SUPPLEMENTARY MATERIAL (ANEXOS, REFERENCIAS Y MATERIAL SUPLEMENTARIO AUDITABLE)
- **Methodological References:** Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge (2025); Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet (2025, 2026); Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet (2024); Villaseñor-García et al. (2017); Vesanto & Alhoniemi (2000); Hicks et al. (2015).
- **Workspace Artifact Catalog:** Links to `./corpus.parquet`, `./matrices/*.parquet`, interactive HTML dashboards in `./reportes/`, and the exploration log `./reportes/exploration_log.md`.
