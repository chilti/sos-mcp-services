---
name: openalex-mexico-works-search
always-apply: true
description: Recuperación y extracción de publicaciones científicas de México sobre la tabla materializada rag.works_academic_all (1.65M de trabajos), filtrando por institución ROR, autor, rango de años, vía de acceso abierto (Diamond, Gold, Hybrid) y percentiles de impacto Top 10% y Top 1%.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex México Works Search

Recuperación granular de artículos, actas y capítulos de la producción científica vinculada a México almacenados en la tabla materializada `rag.works_academic_all`.

## Overview

Permite consultar los 1,652,927 trabajos de México con indicadores cienciométricos enriquecidos (FWCI, percentiles, Top 10%, APC pagado, vías de acceso abierto y ODS), aplicando filtros optimizados sin necesidad de formular cruces relacionales.

## Dependencies

- **Entorno Python:** `/home/ambientesPy/revistaslatam`
- **Script CLI:** [`scripts/openalex_mexico_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-works-search/scripts/openalex_mexico_cli.py)
- **Tabla ClickHouse:** `rag.works_academic_all`

## CLI Interface

### 1. Búsqueda por Institución (ROR) y Rango Temporal
Recupera la producción de una institución (ej. UNAM: `01tmp8f25`, Cinvestav: `04yeehy64`) en un periodo definido:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py search-works \
  --institution-ror "01tmp8f25" \
  --year-min 2023 \
  --year-max 2025 \
  --limit 200 \
  --output /ruta/a/produccion_unam_reciente.json
```

### 2. Búsqueda de Publicaciones de Élite (Top 10% / Top 1%)
Filtra artículos en el decil superior de impacto mundial:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py search-works \
  --is-top-10 true \
  --year-min 2020 \
  --limit 100 \
  --output /ruta/a/articulos_top10_mexico.json
```

### 3. Filtrado por Acceso Abierto Diamante vs Doradas
Para análisis de soberanía editorial y vías no comerciales:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py search-works \
  --oa-status "diamond" \
  --year-min 2024 \
  --limit 100 \
  --output /ruta/a/articulos_diamante_2024.json
```

### 4. Búsqueda por Tópico o Término
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py search-works \
  --query "quantum dots" \
  --topic "Nanotechnology" \
  --limit 50 \
  --output /ruta/a/nanotecnologia_mexico.json
```

## Workflow Steps

1. **Definir Filtros:** Seleccionar institución, año, tipo de acceso o nivel de impacto.
2. **Ejecutar Búsqueda:** Correr `search-works` enviando la salida a JSON.
3. **Flujos Posteriores:**
   - Para cálculo de indicadores agregados: usar [`openalex-mexico-aggregations`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-aggregations/SKILL.md).
   - Para modelado en redes: alimentar [`bibliometric-network-analyst`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/scientometrics-network/bibliometric-network-analyst/SKILL.md).

## References

- [Diccionario de Campos de rag.works_academic_all](references/works_academic_all_schema.md)

## Common Mistakes & Edge Cases

- **Formato del ROR:** Puede pasar el ROR en formato corto (`01tmp8f25`) o URI completa (`https://ror.org/01tmp8f25`), el script resuelve ambas automáticamente.
- **Volumen de Datos:** Para descargas masivas de más de 5,000 registros, aumente el `--limit` de forma prudente para evitar sobrecargar la memoria local.
