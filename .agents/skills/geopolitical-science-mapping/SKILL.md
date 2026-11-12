---
name: geopolitical-science-mapping
description: Geopolitical mapping of science, ISO-3166-1 alpha-3 international co-authorship networks, bilateral Salton affinity, epistemological sovereignty, Open Access monitoring, and SDG alignment. Orchestrates geopolitical-collaboration-analyst, open-access-monitor, and sdg-impact-intelligence over ./corpus.parquet. Respond and label outputs in the user's language.
---

# Geopolitical Science Mapping

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

This skill coordinates multidimensional geopolitical analysis of scientific output operating under the **Workspace-First** principle over the `./corpus.parquet` file harvested in Stage 1.

## 1. Integrated Workspace Workflow (`./corpus.parquet`)

Rather than querying external APIs in isolation, this skill chains three analytical engines over the same `./corpus.parquet`:

### Step 1: International Collaboration Matrix, Salton Affinity, and Epistemological Sovereignty
Delegates to [`geopolitical-collaboration-analyst`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/geopolitical-collaboration-analyst/SKILL.md):
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/geopolitical-collaboration-analyst/scripts/geopolitical_collab_cli.py analyze-all \
  --input ./corpus.parquet \
  --anchor-country USA \
  --output-json ./reports/geopolitical_analysis.json \
  --html ./reports/geopolitical_dashboard.html \
  --lang en
```

### Step 2: Editorial Sovereignty Audit, 6 Open Access Pathways, and APC Expenditure (USD)
Delegates to [`open-access-monitor`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/SKILL.md):
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/scripts/open_access_monitor_cli.py breakdown \
  --input ./corpus.parquet \
  --output ./reports/oa_breakdown.json \
  --lang en

/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/scripts/open_access_monitor_cli.py apc-spending \
  --input ./corpus.parquet \
  --output ./reports/oa_apc_usd.json \
  --lang en
```

### Step 3: Alignment with the 17 Sustainable Development Goals (UN 2030 Agenda)
Delegates to [`sdg-impact-intelligence`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/sdg-impact-intelligence/SKILL.md):
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/sdg-impact-intelligence/scripts/sdg_impact_cli.py \
  --input ./corpus.parquet \
  --output-json ./reports/sdg_profile.json \
  --lang en
```

### Step 4: Country SOM Mapping (`tlachia-metrics-engine` $\to$ `som-methodological-expert`)
To project multidimensional country profiles onto the SOM:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py by-entity \
  --input ./corpus.parquet \
  --level country \
  --min-docs 2 \
  --output ./matrices/paises_som.parquet

/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/scripts/som_pipeline_cli.py \
  --input ./matrices/paises_som.parquet \
  --state-out ./reports/som_paises_state.json \
  --html-out ./reports/som_paises_dashboard.html
```
