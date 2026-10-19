---
name: openalex-mexico-aggregations
description: Agregaciones analíticas instantáneas sobre la producción científica de México en ClickHouse (rag.works_academic_all), calculando distribución por vías de acceso abierto (Diamond vs Gold APC), gasto comercial en APC en USD, publicaciones de élite Top 10% mundial, FWCI promedio y series cronológicas.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex México Aggregations

Motor de agregación columnar para la evaluación cuantitativa de la producción científica en México a escala masiva sin transferir registros individuales.

## Overview

Calcula métricas e indicadores de impacto, gasto editorial y modelos de publicación agrupados por cualquier dimensión cienciométrica (año, vía OA, subcampo, disciplina o país), respondiendo en milisegundos gracias al motor MergeTree de ClickHouse.

## Dependencies

- **Entorno Python:** `/home/ambientesPy/revistaslatam`
- **Script CLI:** [`scripts/openalex_mexico_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-aggregations/scripts/openalex_mexico_cli.py)
- **Tabla ClickHouse:** `rag.works_academic_all`

## CLI Interface

### 1. Desglose de Vías de Acceso Abierto y Gasto en APC
Cuantifica la penetración de las 6 vías y calcula el gasto comercial total en USD:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "oa_status" \
  --filter "publication_year >= 2020" \
  --output /ruta/a/acceso_abierto_mexico.json
```

### 2. Serie Temporal de Producción, Citas y Calidad de Impacto
Evolución anual de publicaciones, porcentaje en el Top 10% y FWCI medio:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "publication_year" \
  --filter "publication_year >= 2015 AND publication_year <= 2025" \
  --output /ruta/a/tendencia_anual_mexico.json
```

### 3. Agrupación por Subcampo Disciplinar
Identifica los subcampos con mayor volumen de publicaciones y concentración de citas:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "subfield" \
  --filter "publication_year >= 2020" \
  --output /ruta/a/subcampos_mexico.json
```

### 4. Filtrado por Institución Específica
Aplica filtros por universidad usando los arrays nativos de ClickHouse:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "oa_status" \
  --filter "has(institution_rors, 'https://ror.org/01tmp8f25') AND publication_year >= 2022" \
  --output /ruta/a/oa_unam_2022_2025.json
```

### 5. Ranking de Entidades Líderes por Tema (`top-entities`)
Identifica con un solo comando qué **autores** o **instituciones** tienen la mayor capacidad científica (volumen, citas, FWCI y porcentaje en el Top 10% mundial) en un tema estratégico (ej. litio, celdas solares, grafeno):

**Para Instituciones líderes:**
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py top-entities \
  --query "lithium" \
  --by "institutions" \
  --limit 10 \
  --output /ruta/a/top_instituciones_litio.json
```

**Para Investigadores líderes (con resolución de nombres y ORCID):**
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py top-entities \
  --query "lithium" \
  --by "authors" \
  --limit 10 \
  --output /ruta/a/top_investigadores_litio.json
```

## Salida Estructurada

Cada registro agrupado devuelve de forma automática:
- `dimension`: Valor de la categoría agrupada (ej. `diamond`, `2024`, etc.).
- `total_works`: Conteo absoluto de publicaciones.
- `total_citations`: Citas acumuladas globales.
- `avg_fwci`: Promedio del impacto normalizado por campo.
- `pct_top_10`: Porcentaje de artículos en el 10% más citado del mundo.
- `total_apc_paid_usd`: Suma del gasto comercial estimado en cargos APC (USD).

## Protocolo Obligatorio para Temas Generales (IA, Nanotecnología, Biotecnología)

Cuando la consulta del usuario se refiera a un área sombrilla o disciplina amplia (ej. *"Inteligencia Artificial"*, *"Biotecnología"*, *"Energías Renovables"*), **NUNCA ejecutes `top-entities` directamente con el término general**. Sigue estrictamente este procedimiento en 2 fases para modelos locales con ventanas acotadas:

### Fase 1: Descubrimiento Taxonómico en ClickHouse (Data-Driven Taxonomy)
Ejecuta la agregación agrupando por tópicos para descubrir cuáles son las especialidades reales con producción científica en México:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "topic" \
  --filter "subfield = 'Artificial Intelligence'" \
  --output /ruta/a/especialidades_ia.json
```
Inspecciona los primeros resultados de salida para identificar los 3 a 5 tópicos dominantes (ej. *Metaheuristic Optimization*, *Neural Networks*, *Natural Language Processing*, *Fuzzy Logic*).

### Fase 2: Evaluación de Capacidad por Especialidad Específica
Con los tópicos reales descubiertos en la Fase 1, ejecuta `top-entities` para cada especialidad concreta:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py top-entities \
  --query "Natural Language Processing" \
  --by "authors" \
  --limit 5 \
  --output /ruta/a/top_nlp_autores.json
```

## References

- [Diccionario de Métricas y Modelo Económico APC](references/metrics_and_apc_dictionary.md)

## Common Mistakes & Edge Cases

- **Regla Anti-JOIN:** No intente concatenar con sentencias JOIN en el parámetro `--filter`. Los filtros deben basarse estrictamente en las columnas y arrays de `rag.works_academic_all`.
- **Temas Sombrilla:** No busque "Inteligencia Artificial" en un solo paso; descomponga primero con la Fase 1 para no pasar por alto nichos de investigación nacionales.
- **Ventana de Contexto en Modelos Locales:** El CLI siempre genera su salida en disco (`--output`). Lea únicamente los primeros registros para mantener el consumo de tokens por debajo de 500.

