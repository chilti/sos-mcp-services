---
name: openalex-mexico-author-search
description: Búsqueda y desambiguación de investigadoras e investigadores de México en ClickHouse local sobre las tablas materializadas rag.authors_seed_mexico (2.57M autores) y rag.academics_all, con filtros por nivel SNII, dependencia institucional y variantes de nombres hispanos.
metadata:
  python: ">=3.10"
  script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex México Author Search

Habilidad especializada en la localización, desambiguación y recuperación de métricas de investigadoras e investigadores afiliados a instituciones de México en la base local de ClickHouse.

## Overview

Permite buscar perfiles académicos sobre el catálogo de más de 2.57 millones de autores relacionados con México (`rag.authors_seed_mexico`) y cruzar con datos del Sistema Nacional de Investigadoras e Investigadores (`rag.academics_all`), resolviendo automáticamente permutaciones de apellidos compuestos y caracteres diacríticos sin formular `JOIN`s.

## Dependencies

- **Entorno Python:** Python 3.10+ (`clickhouse-connect`)
- **Script CLI:** [`scripts/openalex_mexico_cli.py`](scripts/openalex_mexico_cli.py)
- **Base de datos:** ClickHouse local (base `rag`, tabla `authors_seed_mexico` y `academics_all`)

## CLI Interface

### 1. Búsqueda por Nombre o Apellidos
Genera automáticamente variantes con y sin guion y busca de forma insensible a mayúsculas:
```bash
python scripts/openalex_mexico_cli.py search-authors \
  --name "Rafael Torres Córdoba" \
  --limit 20 \
  --output /ruta/a/autores_encontrados.json
```

### 2. Filtrado por Institución y Dependencia
Filtra por universidad (ej. `UNAM`, `Cinvestav`, `UAM`) o entidad académica:
```bash
python scripts/openalex_mexico_cli.py search-authors \
  --name "Jiménez Andrade" \
  --institution "Universidad Nacional Autónoma de México" \
  --limit 10 \
  --output /ruta/a/autores_unam.json
```

### 3. Filtrado por Nivel SNII
Para consultas de personal académico adscrito al Padrón SNII:
```bash
python scripts/openalex_mexico_cli.py search-authors \
  --snii-level "III" \
  --institution "UNAM" \
  --limit 50 \
  --output /ruta/a/investigadores_snii3.json
```

## Workflow Steps

1. **Búsqueda Inicial:** Ejecutar `search-authors` con el nombre del investigador y volcar a archivo JSON.
2. **Identificación Canónica:** Extraer el `id` OpenAlex (`https://openalex.org/A...`) y el `orcid`.
3. **Paso a Publicaciones:** Utilizar el nombre o ID obtenido para alimentar la skill [`openalex-mexico-works-search`](../openalex-mexico-works-search/SKILL.md).

## References

- [Esquema de Tablas de Autores en ClickHouse](references/academics_all_schema.md)
- [Reglas de Permutación de Nombres Hispanos](references/hispanic_name_permutations.md)

## Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Búsqueda con cadenas exactas sin contemplar diacríticos hispanos**  
  Buscar `"Rafael Torres Cordoba"` sin acento en una consulta SQL directa sensible a mayúsculas.  
  **Solución:** Usar el subcomando `search-authors` del CLI, que genera permutaciones fonéticas y normaliza diacríticos automáticamente.
- ❌ **Anti-patrón 2: Formular JOINs entre autores y artículos**  
  Intentar cruzar `rag.authors_seed_mexico` con `rag.works_academic_all` mediante SQL JOIN.  
  **Solución:** Extraer primero el autor para obtener su ID u ORCID, y luego filtrar `rag.works_academic_all` mediante arrays nativos.
- ❌ **Anti-patrón 3: Consultas sin límite explícito**  
  Buscar un apellido común (e.g. `"Hernández"`, `"González"`) sin `--limit`, devolviendo miles de homónimos.  
  **Solución:** Acotar siempre con `--limit 10` o `--limit 20` y refinar filtrando por `--institution`.
- ❌ **Anti-patrón 4: Violación de File-Output First**  
  Omitir `--output` y volcar listas masivas de autores en la consola.  
  **Solución:** Guardar siempre en archivo estructurado (`--output ./data/autores.json`).
