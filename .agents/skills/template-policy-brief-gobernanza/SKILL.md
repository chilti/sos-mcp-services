---
name: template-policy-brief-gobernanza
description: >-
  Preparation of executive science and technology policy briefs (2 to 4 pages) for university leadership, science ministries (SECIHTI), legislative committees, and funding agencies. Operates under a 2-stage protocol: I) Empirical workspace exploration across the menu of Agent Skills (national/institutional aggregations, 42+ indicator engine, OA/APC audit, SNII census, AI/F-measure specialization, strategic fronts, SDGs, and SOM cartography), and II) Executive curation to select strictly the 3 to 4 most compelling empirical findings that underpin public policy recommendations. Respond and label outputs in the user's language.
---

# Master Template: Governance Policy Brief, Science & Technology (S&T) Policy, and Multidimensional SOM Evidence
### *Specialized in evidence-based executive synthesis for senior decision-makers (2 to 4 pages)*

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish). Write all section headers and prose of the generated Policy Brief in the user's language.

This template guides the preparation of a concise, direct, and rigorously evidence-based **POLICY BRIEF** addressed to university rectors, the Ministry of Science, Humanities, Technology, and Innovation (SECIHTI), research councils, and legislative committees.

An effective Policy Brief is **not an exhaustive dump of every possible calculation**: it requires the agent to first explore the data using its menu of skills in the workspace (*Stage I*) and then perform **strict executive curation (*Stage II*)** to select only the most compelling empirical findings and the **Kohonen Self-Organizing Map (SOM)** configuration (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor-García et al., 2017) that most clearly demonstrates why public policies must be designed around differentiated profiles and missions rather than one-dimensional rankings (*weighing and summing*).

---

## Stage I: Menu of Agent Skills for Evidence Exploration (*Laboratory Phase*)

The agent operates under the **Workspace-First** principle (`./corpus.parquet` $\to$ `./matrices/*.parquet` $\to$ `./reportes/`) and uses the following menu to build the evidence base:

1. **Baseline Quantitative Extraction and Diagnosis:**
   - [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md) and [`openalex-mexico-aggregations`](../openalex-mexico-aggregations/SKILL.md) (for national/institutional science policy over `rag.works_academic_all` with **ZERO JOINs**), or [`openalex-search-engineer`](../openalex-search-engineer/SKILL.md) (`rag.works_flat`) and [`scientometrics-incites-expert`](../scientometrics-incites-expert/SKILL.md) for international comparisons.
   - [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Computation of the full **46-column matrix (42 numerical indicators + 4 metadata columns)** without truncation in `./matrices/`.
2. **Menu of Public Policy Dimensions to Explore:**
   - **Multidimensional SOM Evidence Against Ranking Reductionism:** [`som-methodological-expert`](../som-methodological-expert/SKILL.md), [`som-trajectory-mapping`](../som-trajectory-mapping/SKILL.md), and [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md) to identify typologies of institutions, states, or thematic areas based on their real performance profiles.
   - **Editorial Sovereignty and APC Expenditure (USD):** [`open-access-monitor`](../open-access-monitor/SKILL.md) and [`journal-editorial-intelligence`](../journal-editorial-intelligence/SKILL.md) to quantify the 6 Open Access routes and commercial APC fee expenditure versus the Diamond OA route.
   - **Academic Demographics and SNII Registry:** [`snii-identity-resolver`](../snii-identity-resolver/SKILL.md) and [`infotlachia-scholar-intelligence`](../infotlachia-scholar-intelligence/SKILL.md) to evaluate critical mass, territorial decentralization, and generational renewal.
   - **Thematic Specialization, Strategic Fronts, and Agenda 2030 (SDGs):** [`topics-research-fronts-intelligence`](../topics-research-fronts-intelligence/SKILL.md), [`geopolitical-collaboration-analyst`](../geopolitical-collaboration-analyst/SKILL.md), [`sdg-impact-intelligence`](../sdg-impact-intelligence/SKILL.md), and indicators of internal prioritization ($DShareC$, $AI$) vs. global share ($CShareD$, $\text{F-measure}$) (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2026).

---

## Stage II: Executive Curation and Pruning Criteria

To preserve the punchiness of a 2-to-4-page document for decision-makers, the agent applies the following rules:

1. **Focus on the Public Policy Problem:**
   - Select from the laboratory **only the indicators and dimensions that directly underpin the public policy trade-off posed by the user** (e.g., if the Policy Brief addresses frontier science funding or transitioning to Diamond Open Access, prioritize those metrics and omit peripheral analyses that would distract the decision-maker).
2. **Selection of SOM Dimensions with Maximum Normative Clarity:**
   - Choose in `--indicator-cols` the subset of indicators from `./matrices/` that produces the sharpest cluster typology (highest Silhouette coefficient $s^*$) and allows associating each cluster with a **differentiated public policy instrument** (e.g., *International Frontier Cluster*, *Regional Relevance & Diamond Sovereignty Cluster*, *Consolidating Cluster*).
3. **Clean Tables with Zero `N/D` / `N/A` Columns:**
   - Present compact tables containing strictly verified variables with real signal in the workspace. Empty rows or columns filled with `N/D` or `N/A` are prohibited.
4. **Evidence Log (`./reportes/exploration_log.md`):**
   - Retain in `./reportes/exploration_log.md` the record of all calculations performed in the workspace as technical backing for review committees.

---

## Data Availability and Strict Editorial Rules

- **Verified columns in ClickHouse (`rag.works_academic_all` and `rag.works_flat`):** `publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `keywords`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `is_doaj_journal`, `is_core_journal`.
- **Executive, Sober, and Action-Oriented Language:** Absolute prohibition of hyperbolic adjectives (*"revolutionary"*, *"unprecedented"*, *"spectacular"*, or their Spanish equivalents). Zero mentions of prompts, tokens, or internal commands in the body of the document.

---

# Modular Structure of the Policy Brief
*(Note: Write all section headers and prose in the user's language).*

# [Policy Brief Title: Multidimensional Evidence and Science Policy Options for [Topic / Subsystem / Institution]]

> ## EXECUTIVE SYNTHESIS FOR DECISION-MAKERS (SÍNTESIS EJECUTIVA PARA DECISORES)
> - **The Strategic Problem:** Concise definition (1 paragraph) of the structural tension or governance challenge addressed.
> - **Core Evidence:** 3 to 4 key quantitative facts derived from the scientometric analysis and SOM cartography in the workspace.
> - **Primary Recommendation:** Priority regulatory or budgetary action offering the highest epistemic, institutional, and social return.

---

## 1. QUANTITATIVE DIAGNOSIS OF THE PROBLEM (DIAGNÓSTICO CUANTITATIVO DEL PROBLEMA)
- **1.1. Context and Empirical Magnitude:**
  * Synthesis of the main findings selected after exploring the corpus.
- **1.2. Table 1: Key Diagnostic Indicators:**
  * Executive table featuring the variables actually computed and relevant to the case (e.g., autonomous volume and impact, $DShareC / CShareD$ specialization, Open Access routes and APC expenditure in USD, collaboration, or SNII faculty structure), their benchmark parameter, and their operational implication.

---

## 2. MULTIDIMENSIONAL SOM EVIDENCE FOR DIFFERENTIATED POLICY DESIGN (EVIDENCIA MULTIDIMENSIONAL SOM PARA EL DISEÑO DE POLÍTICAS DIFERENCIADAS)
*Why single scalar indicators distort resource allocation (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2026; Leiden Manifesto, Hicks et al., 2015).*

- **2.1. Methodological Critique of Ranking Reductionism ("Weighing and Summing"):**
  * Concise explanation of how one-dimensional rankings penalize diversity of institutional missions and research oriented toward strategic or regional problems.
- **2.2. Table 2: Cluster Typology Revealed by the SOM and Differentiated Public Policy:**
  * Present the real clusters obtained in `./reportes/som_diagnosis.json` (including their representative entities or fronts, strengths in red zones, vulnerabilities in green zones, and the differentiated policy instrument recommended for each profile).

---

## 3. STRATEGIC TRADE-OFFS AND PROSPECTIVE SCENARIOS (DISYUNTIVAS ESTRATÉGICAS Y ESCENARIOS PROSPECTIVOS)
- Articulation of the **2 or 3 real governance dilemmas** backed by the study's evidence (e.g., *Induced visibility vs. autonomous leadership and specialization*; *Budgetary drain in commercial APC fees vs. strengthening Diamond and Green Open Access ecosystems*; *Concentration vs. inter-institutional network articulation*).
- Concise contrast between the **Inertial Scenario (Status Quo)** and the **Multidimensional Profile-Based Intervention Scenario**.

---

## 4. PRIORITY RECOMMENDATIONS MATRIX AND COURSES OF ACTION (MATRIZ DE RECOMENDACIONES PRIORITARIAS Y CURSOS DE ACCIÓN)
Present **Table 3: Actionable Recommendations Matrix for Decision-Making Bodies**:

| Decision Level / Responsible Body | Recommended Policy Action | Implementation Horizon | Success Indicator / Verifiable Target |
| :--- | :--- | :--- | :--- |
| **[e.g., Rectorate / SECIHTI / Directorate]** | [Concrete data-driven action] | Short Term (0–12 months) | [Auditable quantitative metric] |
| **[e.g., Technical Councils / Evaluation Committees]** | [Adoption of SOM comparable-profile evaluation / specialization criteria] | Short–Medium Term (1–2 years) | [Verifiable metric or guideline] |
| **[e.g., Coordinations / Sectoral Funds]** | [Targeted incentive based on study findings] | Medium Term (1–3 years) | [Impact, collaboration, or cost-saving target] |

---

## TECHNICAL FACT SHEET AND AUDITABLE SOURCES (FICHA TÉCNICA Y FUENTES AUDITABLES)
- Declaration of data sources (`rag.works_academic_all` / `rag.works_flat` / SNII Registry), cutoff date, filtering parameters, reproducible artifacts in `./matrices/` and `./reportes/` (including `som_dashboard.html` and `exploration_log.md`), and methodological references (Carrillo-Calvet et al., 2025; Jiménez-Andrade et al., 2024, 2025, 2026; Villaseñor-García et al., 2017; Hicks et al., 2015; GLOBAL Guideline - ISSI).
