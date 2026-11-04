---
name: journal-editorial-intelligence
description: Evaluación cienciométrica de revistas científicas (fuentes/sources), concentración de Bradford, Acceso Abierto Diamante vs APC comercial, endogamia institucional, indización DOAJ/SciELO/Latindex 2.0 y perfilado multidimensional de revistas en el SOM.
---

# Journal Editorial Intelligence

Esta skill articula el análisis editorial y cienciométrico de revistas científicas combinando el análisis del corpus local (`./corpus.parquet`) con los motores especializados de evaluación editorial iberoamericana (`revistaslatam-editorial-intelligence` y `revistaslatam-indicators-engine`).

## 1. Flujo de Trabajo sobre el Workspace (`./corpus.parquet`)

### A. Demarcación de Zonas de Bradford (Revistas Núcleo vs Periferia)
Utiliza `classical-bibliometrics-laws` sobre `./corpus.parquet`:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/classical-bibliometrics-laws/scripts/bibliometric_laws_cli.py bradford \
  --input ./corpus.parquet \
  --output ./reports/bradford_zones.json
```

### B. Matriz Multidimensional de Revistas (`--level source`) y Proyección en el SOM
Utiliza `tlachia-metrics-engine` para calcular los 35+ indicadores por revista (`source`) sin truncar columnas y proyectarlos en `som-methodological-expert`:
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

### C. Auditoría Editorial Iberoamericana (Latindex 2.0, DOAJ, SciELO, Endogamia)
Cuando se evalúan revistas latinoamericanas específicas, delegar en:
- [`revistaslatam-editorial-intelligence`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-editorial-intelligence/SKILL.md)
- [`revistaslatam-indicators-engine`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/revistaslatam-indicators-engine/SKILL.md)
