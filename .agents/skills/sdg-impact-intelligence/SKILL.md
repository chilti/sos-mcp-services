---
name: sdg-impact-intelligence
description: Mapping, alignment, quantification, and interactive visualization of scientific output across the 17 United Nations Sustainable Development Goals (SDGs / Agenda 2030). Operates Workspace-First by directly consuming ./corpus.parquet. Respond and label outputs in the user's language.
entrypoint: scripts/sdg_impact_cli.py
inputs:
  type: object
  properties:
    workspace:
      type: string
      description: Root workspace directory where corpus.parquet resides and reports will be generated (default '.').
    input:
      type: string
      description: Explicit path to the tabular publications file (.parquet, .json, .csv).
    sdg_col:
      type: string
      description: Column containing SDG metadata (default auto-detects 'sdgs', 'sdg_ids', 'ODS_ID').
    title:
      type: string
      description: Title for the report and interactive HTML dashboard.
    output_html:
      type: string
      description: Path to the interactive HTML visualizer (default './reportes/sdg_impact_dashboard.html').
    output_json:
      type: string
      description: Path to the structured JSON summary (default './reportes/sdg_impact_summary.json').
    output_md:
      type: string
      description: Path to the Markdown executive report (default './reportes/sdg_impact_report.md').
---

# SDG Impact Intelligence: Mapping and Visualizer for the 17 UN SDGs

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Purpose and Methodological Foundation
This skill formalizes the scientometric evaluation of societal impact and sustainability in scientific research by quantifying the thematic contribution of a corpus to the **17 United Nations Sustainable Development Goals (SDGs / Agenda 2030)**:
- **SDGs 1 through 17:** Coverage of global goals (No Poverty, Good Health and Well-being, Quality Education, Gender Equality, Industry and Innovation, Reduced Inequalities, Climate Action, Peace and Justice, etc.).
- **Quantitative and Normalized Metrics:** For each goal, it computes absolute publication volume ($N$), percentage share of total corpus (%), cumulative citations, **weighted mean FWCI** (Field-Weighted Citation Impact), **Top 10%** excellence share, and **Diamond Open Access** rate.

---

## 2. Workspace-First Principle ("From Harvest to SDG")
The skill autonomously consumes data previously downloaded by harvesting skills (`openalex-harvester`, `openalex_search`, `arxiv-harvester`, `scopus-harvester`, `pubmed-harvester`) stored in the workspace:

```
<workspace>/
├── corpus.parquet                <-- Primary input tabular file
└── reportes/
    ├── sdg_impact_summary.json   <-- Structured JSON summary
    ├── sdg_impact_report.md      <-- Analytical report with tables and key papers
    └── sdg_impact_dashboard.html <-- Official interactive visualizer of the 17 SDGs
```

---

## 3. Interactive 17-SDG Visualizer (SinapsisAI / KnoMap Aesthetic)
Integrates the interactive visualizer designed in the `sinapsisai` project (`lib/viz_ods.py`):
- **Responsive 17-Card Grid:** Displays official UN icons with their canonical color codes.
- **Active vs. Inactive Goal Identification:** SDGs without presence in the corpus are rendered in attenuated grayscale (`sdg-inactive`), activating in color on hover.
- **Metrics Overlay:** Corpus percentage and document count overlaid with a legible gradient.
- **Informative Tooltips:** Formal SDG name, count, and percentage on hover.
- **Detailed Table with FWCI Badges:** Numerical summary with field-normalized impact badges per goal.

---

## 4. Command-Line Usage (CLI)

```bash
# Standard execution over the workspace (English default)
/home/ambientesPy/revistaslatam/bin/python scripts/sdg_impact_cli.py \
  --workspace ./ \
  --title "SDG Alignment: Scientific Output in Artificial Intelligence and Causality" \
  --lang en

# Specifying an explicit input file and Spanish labels
/home/ambientesPy/revistaslatam/bin/python scripts/sdg_impact_cli.py \
  --input ./data/my_publications.parquet \
  --workspace ./ \
  --lang es
```

---

## 5. Outputs Generated in `./reportes/`

1. **`sdg_impact_dashboard.html`:** Standalone interactive dashboard (no heavy external dependencies) ready to open in any browser.
2. **`sdg_impact_summary.json`:** Structured dictionary with statistics per SDG (1 to 17) for consumption by other skills, agents, or LLMs.
3. **`sdg_impact_report.md`:** Markdown table formatted for direct inclusion in IMRaD manuscripts, institutional reports, or Policy Briefs.
