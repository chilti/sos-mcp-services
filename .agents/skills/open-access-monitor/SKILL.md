---
name: open-access-monitor
description: Monitoreo analítico de las 6 vías de Acceso Abierto (Diamante, Dorada APC, Híbrida, Bronce, Verde, Cerrada), cálculo de gasto comercial estimado en APC (USD) y análisis de tendencias de transición.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/open_access_monitor_cli.py"
---

# Open Access Monitor

Módulo cienciométrico especializado en la clasificación y cuantificación de las 6 vías canónicas de Acceso Abierto (Open Access), soberanía científica y estimación de costos de publicación comercial por APC.

## Overview

El módulo permite auditar colecciones documentales (Parquet, CSV o JSON) para identificar la penetración del acceso abierto, contrastar modelos no comerciales (Diamante) frente a modelos comerciales de mercado (Gold APC, Híbridas) y modelar la transición temporal de las publicaciones.

## Dependencies

- Entorno Python: `/home/ambientesPy/revistaslatam`
- Script ejecutable: [`scripts/open_access_monitor_cli.py`](file:///home/jlja/.gemini/config/skills/open-access-monitor/scripts/open_access_monitor_cli.py)

## Interfaz CLI

### 1. Desglose por Vías de Acceso Abierto (`breakdown`)
Calcula la distribución absoluta y porcentual en las 6 vías:
```bash
/home/ambientesPy/revistaslatam/bin/python /home/jlja/.gemini/config/skills/open-access-monitor/scripts/open_access_monitor_cli.py breakdown \
  --input /ruta/al/corpus.parquet \
  --output /ruta/a/oa_breakdown.json
```

### 2. Estimación de Gasto Comercial en APC (`apc-spending`)
Calcula el gasto monetario en USD derivado de artículos en revistas doradas e híbridas:
```bash
/home/ambientesPy/revistaslatam/bin/python /home/jlja/.gemini/config/skills/open-access-monitor/scripts/open_access_monitor_cli.py apc-spending \
  --input /ruta/al/corpus.parquet \
  --gold-apc-usd 2200 \
  --hybrid-apc-usd 3200 \
  --output /ruta/a/apc_spending.json
```

### 3. Tendencias de Transición Anual (`transition-trend`)
Analiza la serie cronológica anual de adopción de Acceso Abierto:
```bash
/home/ambientesPy/revistaslatam/bin/python /home/jlja/.gemini/config/skills/open-access-monitor/scripts/open_access_monitor_cli.py transition-trend \
  --input /ruta/al/corpus.parquet \
  --output /ruta/a/oa_trend.json
```
