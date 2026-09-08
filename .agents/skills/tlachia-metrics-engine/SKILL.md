---
name: tlachia-metrics-engine
description: Motor cienciométrico autónomo para el cálculo de más de 30 indicadores (FWCI, H-index, Top 10%, APC USD, 6 vías OA, Gini) y análisis temporal anual y longitudinal por periodos sobre tablas canónicas.
---

# TlachIA Metrics Engine

Motor analítico independiente para calcular la batería integral de indicadores cienciométricos, económicos y de ciencia abierta de TlachIA a partir de cualquier archivo tabular normalizado (`.parquet`, `.csv`, `.json`), sin requerir la interfaz web ni la base de datos central de TlachIA Metrics.

---

## Capacidades

- **Suite Consolidada de 30+ Indicadores:** Volumen, citas, H-index, i10, FWCI, percentiles, Top 10% y Top 1%.
- **Análisis Temporal Anual:** Generación de series temporales continuas año por año (`annual-series`) con cálculo de tasas de crecimiento anual ($\Delta \text{Docs}$, $\Delta \text{Citas}$).
- **Análisis Longitudinal por Periodos:** Evaluación por ventanas fijas (`--window 5` o `--window 10`), ventanas deslizantes (`--window 5 --step 1`), periodos específicos o último lustro (`--last-years 5`), con matrices longitudinales de entidades para SOM.
- **Monitoreo de Acceso Abierto:** Desglose de las 6 vías (Gold, Diamond, Hybrid, Green, Bronze, Closed).
- **Economía de la Publicación:** Gasto devengado en APC comercial en USD y cuantificación de ahorro por Acceso Abierto Diamante.
- **Agregación a 4 Niveles:** Desglose por investigador (`researcher`), departamento/institución (`institution`) o país (`country`).
- **Diversidad Temática de Gini:** Cuantificación del grado de concentración o dispersión del frente de investigación.

---

## Interfaz CLI

Entorno de ejecución:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py [subcomando] [opciones]
```

### 1. Resumen cienciométrico (con filtros temporales opcionales)
```bash
# Resumen global
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py calculate-summary \
  --corpus ./corpus.parquet \
  --output ./resumen_tlachia.md

# Resumen del último lustro (últimos 5 años)
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py calculate-summary \
  --corpus ./corpus.parquet \
  --last-years 5 \
  --output ./resumen_ultimo_lustro.md
```

### 2. Serie temporal anual año por año
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py annual-series \
  --corpus ./corpus.parquet \
  --year-from 2018 \
  --year-to 2024 \
  --output ./serie_anual.md
```

### 3. Análisis longitudinal por periodos consecutivos o ventanas
```bash
# Periodos consecutivos de 5 años
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py period-series \
  --corpus ./corpus.parquet \
  --window 5 \
  --output ./periodos_5anios.md

# Lista explícita de periodos para análisis decenal
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py period-series \
  --corpus ./corpus.parquet \
  --periods "2000-2009,2010-2019,2020-2024" \
  --output ./periodos_decenales.parquet

# Matriz longitudinal de investigadores por periodo (para mapeo SOM)
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py period-series \
  --corpus ./corpus.parquet \
  --window 5 \
  --level researcher \
  --output ./investigadores_longitudinal_som.parquet
```

### 4. Agregación transversal a nivel de investigadores
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py aggregate-by \
  --corpus ./corpus.parquet \
  --level researcher \
  --output ./autores_indicadores.parquet
```

### 5. Coeficiente de concentración de Gini temático
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py gini-diversity \
  --corpus ./corpus.parquet \
  --column keywords_plus
```

---

## Referencias Técnicas
- [Guía de Análisis Temporal y Longitudinal por Periodos](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/references/longitudinal_periods_guide.md)
- [Manual Matemático de Indicadores Cienciométricos TlachIA](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/references/tlachia_indicators_mathematical_handbook.md)
- [Modelo Económico de APC y Ahorro Diamante](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/references/apc_economic_model.md)
