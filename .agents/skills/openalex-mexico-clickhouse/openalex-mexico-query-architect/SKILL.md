---
name: openalex-mexico-query-architect
description: Asesor técnico y validador de consultas ClickHouse sobre el corpus científico de México, asegurando la regla estricta de CERO JOINs, uso de funciones de arrays nativos (has, arrayExists) y optimización columnar sobre rag.works_academic_all.
metadata:
  python: "/home/ambientesPy/revistaslatam"
  script: "shared_scripts/openalex_mexico_cli.py"
---

# OpenAlex México Query Architect

Consultor metodológico y de seguridad para la formulación de consultas analíticas de alto rendimiento sobre las tablas materializadas de México en ClickHouse.

## Overview

ClickHouse aloja más de 1.65 millones de registros detallados para México en `rag.works_academic_all` y 2.57 millones de autores en `rag.authors_seed_mexico`. Esta habilidad actúa como el guardián de rendimiento y buenas prácticas de ingeniería de datos, verificando que el agente nunca formule sentencias con `JOIN` que degraden la infraestructura.

## Dependencies

- **Entorno Python:** `/home/ambientesPy/revistaslatam`
- **Script CLI:** `shared_scripts/openalex_mexico_cli.py`
- **Tablas ClickHouse:** `rag.works_academic_all`, `rag.authors_seed_mexico`

## Regla de Oro: Prohibición Estricta de JOINs

> [!CAUTION]
> En la infraestructura analítica de la UNAM, **queda terminantemente prohibido formular sentencias con `JOIN` directo** en ClickHouse sin autorización previa. 
> Cualquier consulta que contenga la palabra clave `JOIN` será interceptada y rechazada automáticamente por el motor de validación.

## ¿Por qué no se necesitan JOINs en la producción de México?

La base de datos `rag` cuenta con una arquitectura columnar totalmente desnormalizada donde cada trabajo en `rag.works_academic_all` ya incluye:
1. **Autores:** `author_names` (Array de nombres completos).
2. **Afiliaciones:** `institution_names` y `institution_rors` (Arrays de nombres y códigos ROR).
3. **Temas y Clasificaciones:** `topic`, `subfield`, `field`, `domain`, `primary_topic_id`.
4. **Métricas de Impacto:** `fwci`, `percentile`, `is_top_10`, `is_top_1`.
5. **Acceso Abierto y Costos:** `oa_status`, `is_oa`, `apc_paid_usd`, `apc_list_usd`.
6. **Objetivos de Desarrollo:** `sdg_ids`, `sdgs`.

## Patrones de Consulta Seguros (Equivalentes a JOINs)

### 1. Filtrar trabajos por institución
En lugar de: `SELECT * FROM works w JOIN institutions i ON ... WHERE i.ror = '...'`  
**Utilizar:**
```sql
SELECT title, publication_year, cited_by_count
FROM rag.works_academic_all
WHERE has(institution_rors, 'https://ror.org/01tmp8f25')
```

### 2. Filtrar trabajos por autor
En lugar de: `SELECT * FROM works w JOIN authors a ON ... WHERE a.name = '...'`  
**Utilizar:**
```sql
SELECT title, publication_year, cited_by_count
FROM rag.works_academic_all
WHERE arrayExists(x -> positionCaseInsensitiveUTF8(x, 'Torres Córdoba') > 0, author_names)
```

### 3. Agregaciones directas sin cruces
```sql
SELECT oa_status, count(*) as total, round(sum(apc_paid_usd), 2) as gasto_usd
FROM rag.works_academic_all
WHERE publication_year >= 2020
GROUP BY oa_status
```

## Validación Previa de Consultas
Para comprobar si una sentencia SQL cumple con las directivas de seguridad antes de ejecutarla:
```bash
/home/ambientesPy/revistaslatam/bin/python shared_scripts/openalex_mexico_cli.py validate-query \
  --query "SELECT * FROM rag.works_academic_all WHERE publication_year = 2024" \
  --output /ruta/a/reporte_validacion.json
```

## Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Formular consultas con sentencia `JOIN`**  
  Intentar enlazar tablas como si fuese una base de datos relacional tradicional (MySQL o PostgreSQL). ClickHouse MergeTree es columnar y el clúster rechaza consultas con JOIN sin optimización de memoria.  
  **Solución:** Consultar las columnas de arrays nativas pre-materializadas (`has(institution_rors, '...')`).
- ❌ **Anti-patrón 2: Consultas sin LIMIT o sin volcado a archivo (Violación de File-Output First)**  
  Lanzar sentencias `SELECT *` abiertas que intentan retornar cientos de miles de registros a la consola.  
  **Solución:** Especificar siempre un `--limit` explícito y dirigir la salida con `--output`.
- ❌ **Anti-patrón 3: Comparaciones de cadenas case-sensitive sin diacríticos**  
  Usar `WHERE author = 'Jose Lopez'` perdiendo miles de registros por acentuación o mayúsculas.  
  **Solución:** Usar `positionCaseInsensitiveUTF8(x, '...') > 0`.

## References

- [Catálogo de Patrones de Consulta Seguros para México](references/no_joins_mexico_patterns.md)
