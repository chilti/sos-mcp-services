---
name: openalex-search-engineer
description: Formulación de búsquedas, agregaciones y consultas analíticas sobre la base de datos local de OpenAlex en ClickHouse (569M trabajos, 337M autores) con normalización de diacríticos y variantes de nombres hispanos.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/openalex_search_cli.py"
---

# OpenAlex Search Engineer

Especialista en la formulación de consultas de alto rendimiento sobre el volcado masivo de OpenAlex en ClickHouse local, aplicando tokenización insensible a diacríticos y recuperación segura sin JOINs.

## Overview
ClickHouse aloja localmente más de 569 millones de publicaciones científicas. Este módulo implementa la interfaz de búsqueda por lotes para agentes autónomos, generando variantes automáticas de nombres hispanos y volcando los resultados en archivos JSON para evitar saturar el contexto de la conversación.

## Dependencies
- Entorno Python: `/home/ambientesPy/revistaslatam`
- Motor de datos: ClickHouse local (base de datos `openalex`)
- Script ejecutable: [`scripts/openalex_search_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-search-engineer/scripts/openalex_search_cli.py)

## Scripts & CLI Tools

### Búsqueda de Autores con Permutaciones (`search-authors`)
Busca autores probando automáticamente variantes de apellidos compuestos:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_search_cli.py search-authors \
  --name "Rafael Torres Córdoba" \
  --limit 20 \
  --output /ruta/a/autores_encontrados.json
```

### Búsqueda de Publicaciones (`search-works`)
Recupera artículos científicos aplicando filtros sobre tablas materializadas:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_search_cli.py search-works \
  --query "quantum computing" \
  --year-min 2020 \
  --year-max 2025 \
  --limit 500 \
  --output /ruta/a/articulos_quantum.json
```

### Agrupaciones Analíticas (`aggregate`)
Calcula conteos y citas acumuladas agrupadas por año, tipo o acceso abierto:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_search_cli.py aggregate \
  --entity-type works \
  --group-by publication_year \
  --output /ruta/a/tendencia_anual.json
```

## Workflow Steps
1. **Identificar Entidad:** Usar `search-authors` para obtener el ID canónico (`A...`) u ORCID.
2. **Extraer Trabajos:** Usar `search-works` pasando el `author_id` o `institution_ror`.
3. **Paso a Siguientes Módulos:** Guardar el JSON para normalización con [`bibliometric-entity-normalizer`](file:///home/labsom/knomap/engine/skills/bibliometric-entity-normalizer/SKILL.md) o modelado de frentes con [`research-fronts-citation-network`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/research-fronts-citation-network/SKILL.md).

## References
- [Esquema de Tablas en ClickHouse](references/clickhouse_openalex_schema.md)
- [Permutaciones de Nombres Hispanos](references/hispanic_name_permutations.md)

## Troubleshooting & Edge Cases
- **Regla Estricta sin JOINs:** Queda prohibido formular `JOIN`s directos. Para cruzar autores e instituciones, filtrar por ROR directamente en `authors` o usar tablas materializadas (`works_academic_all`).
- **Límites de Memoria:** Los resultados se escriben en disco mediante `--output` para mantener la memoria del agente despejada.
