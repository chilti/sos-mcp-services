---
name: infotlachia-scholar-intelligence
description: Acceso analítico de alta velocidad a la base DuckDB (analytics_cache.duckdb, 5.9 GB, 14 tablas) para consultar métricas precalculadas de investigadores SNII, dependencias académicas, universidades mexicanas y panorama nacional (FWCI, citas, APC USD, Gini).
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/infotlachia_cli.py"
---

# Info TlachIA Scholar Intelligence

Módulo analítico de inteligencia cienciométrica sobre investigadores acreditados en el SNII y dependencias universitarias de México utilizando DuckDB embebido.

## Overview
Contiene métricas consolidadas sobre más de 90,000 investigadores y 3,000 instituciones. A través de DuckDB en modo solo lectura (`read_only=True`), permite consultas analíticas de latencia inferior a 10 ms sobre series temporales, gasto estimado en APC, índice de Gini temático y colocación en el percentil de excelencia (Top 10%).

## Dependencies
- Entorno Python: `/home/ambientesPy/revistaslatam`
- Base de datos DuckDB: `/home/sinapsisai/data/analytics_cache.duckdb`
- Script ejecutable: [`scripts/infotlachia_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/infotlachia-scholar-intelligence/scripts/infotlachia_cli.py)

## Scripts & CLI Tools

### Perfil de Investigador (`query-researcher`)
Consulta el impacto consolidado de un científico mexicano:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/infotlachia_cli.py query-researcher \
  --name "Torres, Rafael" \
  --format markdown \
  --output /ruta/a/perfil_torres.md
```

### Métricas de Facultad o Dependencia (`query-entity`)
Analiza la producción y gasto de una dependencia universitaria:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/infotlachia_cli.py query-entity \
  --entity "Facultad de Ciencias" \
  --format json \
  --output /ruta/a/facultad_ciencias.json
```

### Panorama Institucional (`query-institution`)
Benchmarking general de una universidad completa:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/infotlachia_cli.py query-institution \
  --institution "UNIVERSIDAD NACIONAL AUTONOMA DE MEXICO" \
  --format markdown \
  --output /ruta/a/reporte_unam.md
```

### Panorama Nacional (`national-overview`)
Estadísticas consolidadas del sistema científico mexicano:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/infotlachia_cli.py national-overview \
  --format markdown
```

### Consultas SQL Seguras (`sql-safe`)
Ejecución de sentencias SELECT directas de solo lectura sobre las 14 tablas:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/infotlachia_cli.py sql-safe \
  --query "SELECT top_domain, count(*) FROM investigador_total GROUP BY top_domain ORDER BY count(*) DESC LIMIT 10" \
  --format markdown
```

## Workflow Steps
1. **Consultar Perfil:** Ejecutar `query-researcher` para extraer H-index, FWCI y estatus SNII.
2. **Contextualizar en Dependencia:** Ejecutar `query-entity` para contrastar al investigador con su comunidad académica.
3. **Reporte Formateado:** Usar `--format markdown` para insertar tablas comparativas directamente en los informes finales del agente.

## References
- [Diccionario de las 14 Tablas de DuckDB](references/duckdb_14tables_dictionary.md)
- [Estructura y Áreas del Padrón SNII](references/snii_ranking_structure.md)

## Troubleshooting & Edge Cases
- **Múltiples Investigadores con Mismo Nombre:** La búsqueda por nombre utiliza coincidencia parcial `ILIKE %nombre%`. Si hay homónimos, el CLI retorna hasta 10 candidatos ordenados por volumen de documentos para que el agente filtre por institución u ORCID.
- **Seguridad en Consultas SQL:** El subcomando `sql-safe` bloquea cualquier sentencia que contenga `DROP`, `DELETE`, `UPDATE`, `INSERT` o `ALTER`.
