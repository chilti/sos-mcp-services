---
name: openalex-search-engineer
description: Experto en formulación de consultas sobre OpenAlex ClickHouse local (569M trabajos, 337M autores), tokenización, diacríticos y agregaciones analíticas.
---

# Skill: OpenAlex Search Engineer

## 1. Propósito y Activación
Esta skill se activa cuando se requiere buscar, filtrar o agregar información bibliográfica masiva sobre la base de datos local de OpenAlex en ClickHouse.

## 2. Protocolo de Búsqueda y Normalización
1. **Manejo de Nombres y Diacríticos:**
   - Para autores hispanos/iberoamericanos, utilizar búsqueda tokenizada insensible a mayúsculas/minúsculas y acentos (`positionCaseInsensitiveUTF8`).
   - Soportar variantes: "Torres Córdoba, Rafael" vs "Rafael Torres-Córdoba".
2. **Identificadores Canónicos:**
   - Normalizar identificadores removiendo prefijos de URI (`https://openalex.org/A...` -> `A...`).
   - Priorizar filtrado por ROR institucional (`03rzb4f20` para UNAM) y ORCID.
3. **Herramientas MCP a Invocar:**
   - `openalex-clickhouse-gateway -> openalex_search_authors`
   - `openalex-clickhouse-gateway -> openalex_search_works`
   - `openalex-clickhouse-gateway -> openalex_get_entity_by_id`
   - `openalex-clickhouse-gateway -> openalex_aggregate_group_by`

## 3. Heurísticas de Agregación
- Para tendencias temporales, agrupar por `publication_year`.
- Para acceso abierto, cruzar con `oa_status` (Gold, Diamond, Green, Hybrid, Bronze, Closed).
