---
name: geopolitical-science-mapping
description: Cartografía geopolítica de la ciencia, redes de coautoría internacional ISO-3166-1 alpha-3, afinidad bilateral de Salton, soberanía epistemológica, monitoreo de Acceso Abierto y alineación con ODS. Orquesta geopolitical-collaboration-analyst, open-access-monitor y sdg-impact-intelligence sobre ./corpus.parquet.
---

# Geopolitical Science Mapping

Esta skill coordina el análisis geopolítico multidimensional de la producción científica operando bajo el principio **Workspace-First** sobre el archivo `./corpus.parquet` descargado en la Etapa 1.

## 1. Flujo Integrado en el Workspace (`./corpus.parquet`)

En lugar de consultar APIs externas de forma aislada, esta skill encadena tres motores analíticos sobre el mismo `./corpus.parquet`:

### Paso 1: Matriz de Colaboración Internacional, Afinidad de Salton y Soberanía Epistemológica
Delega en [`geopolitical-collaboration-analyst`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/geopolitical-collaboration-analyst/SKILL.md):
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/geopolitical-collaboration-analyst/scripts/geopolitical_collab_cli.py dashboard \
  --input ./corpus.parquet \
  --anchor-country USA \
  --output ./reports/geopolitical_analysis.json \
  --html-output ./reports/geopolitical_dashboard.html
```

### Paso 2: Auditoría de Soberanía Editorial, 6 Vías de Acceso Abierto y Fuga en APC (USD)
Delega en [`open-access-monitor`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/SKILL.md):
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/scripts/open_access_monitor_cli.py breakdown \
  --input ./corpus.parquet \
  --output ./reports/oa_breakdown.json

/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/scripts/open_access_monitor_cli.py apc \
  --input ./corpus.parquet \
  --output ./reports/oa_apc_usd.json
```

### Paso 3: Alineación con los 17 Objetivos de Desarrollo Sostenible (Agenda 2030 ONU)
Delega en [`sdg-impact-intelligence`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/sdg-impact-intelligence/SKILL.md):
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/sdg-impact-intelligence/scripts/sdg_impact_cli.py profile \
  --input ./corpus.parquet \
  --output ./reports/sdg_profile.json
```

### Paso 4: Cartografía SOM de Países (`tlachia-metrics-engine` $\to$ `som-methodological-expert`)
Para proyectar los perfiles multidimensionales de los países colaboradores en el SOM:
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
