---
name: openalex-mexico-author-search
always-apply: true
description: Búsqueda y desambiguación de investigadoras e investigadores de México en ClickHouse local sobre las tablas materializadas rag.authors_seed_mexico (2.57M autores) y rag.academics_all, con filtros por nivel SNII, dependencia institucional y variantes de nombres hispanos.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex México Author Search

Habilidad especializada en la localización, desambiguación y recuperación de métricas de investigadoras e investigadores afiliados a instituciones de México en la base local de ClickHouse.

## Overview

Permite buscar perfiles académicos sobre el catálogo de más de 2.57 millones de autores relacionados con México (`rag.authors_seed_mexico`) y cruzar con datos del Sistema Nacional de Investigadoras e Investigadores (`rag.academics_all`), resolviendo automáticamente permutaciones de apellidos compuestos y caracteres diacríticos sin formular `JOIN`s.

## Dependencies

- **Entorno Python:** `/home/ambientesPy/revistaslatam`
- **Script CLI:** [`scripts/openalex_mexico_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-author-search/scripts/openalex_mexico_cli.py)
- **Base de datos:** ClickHouse local (base `rag`, tabla `authors_seed_mexico` y `academics_all`)

## CLI Interface

### 1. Búsqueda por Nombre o Apellidos
Genera automáticamente variantes con y sin guion y busca de forma insensible a mayúsculas:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py search-authors \
  --name "Rafael Torres Córdoba" \
  --limit 20 \
  --output /ruta/a/autores_encontrados.json
```

### 2. Filtrado por Institución y Dependencia
Filtra por universidad (ej. `UNAM`, `Cinvestav`, `UAM`) o entidad académica:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py search-authors \
  --name "Jiménez Andrade" \
  --institution "Universidad Nacional Autónoma de México" \
  --limit 10 \
  --output /ruta/a/autores_unam.json
```

### 3. Filtrado por Nivel SNII
Para consultas de personal académico adscrito al Padrón SNII:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py search-authors \
  --snii-level "III" \
  --institution "UNAM" \
  --limit 50 \
  --output /ruta/a/investigadores_snii3.json
```

## Workflow Steps

1. **Búsqueda Inicial:** Ejecutar `search-authors` con el nombre del investigador y volcar a archivo JSON.
2. **Identificación Canónica:** Extraer el `id` OpenAlex (`https://openalex.org/A...`) y el `orcid`.
3. **Paso a Publicaciones:** Utilizar el nombre o ID obtenido para alimentar la skill [`openalex-mexico-works-search`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-works-search/SKILL.md).

## References

- [Esquema de Tablas de Autores en ClickHouse](references/academics_all_schema.md)
- [Reglas de Permutación de Nombres Hispanos](references/hispanic_name_permutations.md)

## Common Mistakes & Edge Cases

- **No usar JOIN:** Jamás intente cruzar autores con tablas de artículos mediante SQL JOIN; extraiga primero los autores y luego filtre los trabajos por nombre o ROR.
- **Salida obligatoria:** Siempre especifique `--output` para mantener la memoria del agente limpia.
