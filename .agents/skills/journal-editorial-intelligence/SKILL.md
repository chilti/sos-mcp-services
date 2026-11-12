---
name: journal-editorial-intelligence
description: Scientometric evaluation of scientific journals (sources), Bradford concentration zones, Diamond Open Access vs commercial APCs, institutional endogamy, DOAJ/SciELO/Latindex 2.0 indexing, and multidimensional journal profiling on the SOM. Respond and label outputs in the user's language.
---

# Journal Editorial Intelligence

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

This skill orchestrates editorial and scientometric analysis of scientific journals by combining local corpus analysis (`./corpus.parquet`) with specialized Ibero-American editorial evaluation engines (`revistaslatam-editorial-intelligence` and `revistaslatam-indicators-engine`).

## 1. Workspace Operational Workflow (`./corpus.parquet`)

### A. Bradford Zone Demarcation (Core vs. Peripheral Journals)
Use `classical-bibliometrics-laws` on `./corpus.parquet`:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/classical-bibliometrics-laws/scripts/bibliometric_laws_cli.py bradford \
  --input ./corpus.parquet \
  --output ./reports/bradford_zones.json
```

### B. Multidimensional Journal Matrix (`--level source`) and SOM Projection
Use `tlachia-metrics-engine` to compute the 35+ indicators per journal (`source`) without truncating columns and project them via `som-methodological-expert`:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py by-entity \
  --input ./corpus.parquet \
  --level source \
  --min-docs 2 \
  --output ./matrices/revistas_som.parquet

/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/scripts/som_pipeline_cli.py \
  --input ./matrices/revistas_som.parquet \
  --state-out ./reports/som_revistas_state.json \
  --html-out ./reports/som_revistas_dashboard.html
```

### C. Ibero-American Editorial Audit (Latindex 2.0, DOAJ, SciELO, Endogamy)
When evaluating specific Latin American or Ibero-American journals, delegate to:
- [`revistaslatam-editorial-intelligence`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-editorial-intelligence/SKILL.md)
- [`revistaslatam-indicators-engine`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/SKILL.md)
