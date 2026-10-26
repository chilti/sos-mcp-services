---
name: openalex-mexico-aggregations
description: "Cálculo de métricas agregadas y rankings cienciométricos en ClickHouse (rag.works_academic_all): distribución de las 6 vías de acceso abierto (Diamond vs Gold APC), gasto comercial en APC en USD, series temporales anuales, subcampos temáticos y RANKING de instituciones e investigadoras/es líderes en un tema ('top-entities') con volumen, citas y FWCI."
metadata:
  python: "/home/ambientesPy/revistaslatam"
  script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex México Aggregations

Motor de agregación columnar para la evaluación cuantitativa de la producción científica en México a escala masiva sin transferir registros individuales.

## Overview

Calcula métricas e indicadores de impacto, gasto editorial y modelos de publicación agrupados por cualquier dimensión cienciométrica (año, vía OA, subcampo, disciplina o país), respondiendo en milisegundos gracias al motor MergeTree de ClickHouse. Además, mediante el comando `top-entities`, identifica de forma directa las instituciones o personas investigadoras con mayor capacidad en cualquier tema.

## Dependencies

- **Entorno Python:** `/home/ambientesPy/revistaslatam`
- **Script CLI:** `scripts/openalex_mexico_cli.py`
- **Tabla ClickHouse:** `rag.works_academic_all`

## CLI Interface

> [!IMPORTANT]
> Guarda siempre los archivos de salida dentro del workspace actual en `./data/`, NUNCA en `/tmp/`.

### 1. Desglose de Vías de Acceso Abierto y Gasto en APC
Cuantifica la penetración de las 6 vías y calcula el gasto comercial total en USD:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "oa_status" \
  --filter "publication_year >= 2020" \
  --output ./data/acceso_abierto_mexico.json
```

### 2. Serie Temporal de Producción, Citas y Calidad de Impacto
Evolución anual de publicaciones, porcentaje en el Top 10% y FWCI medio:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "publication_year" \
  --filter "publication_year >= 2015 AND publication_year <= 2025" \
  --output ./data/tendencia_anual_mexico.json
```

### 3. Agrupación por Subcampo Disciplinar
Identifica los subcampos con mayor volumen de publicaciones y concentración de citas:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "subfield" \
  --filter "publication_year >= 2020" \
  --output ./data/subcampos_mexico.json
```

### 4. Filtrado por Institución Específica
Aplica filtros por universidad usando los arrays nativos de ClickHouse:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "oa_status" \
  --filter "has(institution_rors, 'https://ror.org/01tmp8f25') AND publication_year >= 2022" \
  --output ./data/oa_unam_2022_2025.json
```

### 5. Distribución de Objetivos de Desarrollo Sostenible (ODS / SDGs)
Agrupa y cuantifica la producción científica según los 17 ODS de la ONU (Agenda 2030):
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py aggregate \
  --group-by "sdgs" \
  --filter "publication_year >= 2020" \
  --output ./data/sdgs_mexico.json
```
*Soporta 4 niveles analíticos:*
- **Nacional:** Sin filtro para evaluar todo el corpus de México (901K publicaciones en ODS).
- **Institucional:** Filtrando por ROR institucional (ej. `01tmp8f25` para la UNAM) o por nombre en `institution_names`.
- **Investigador:** Filtrando por ID canónico (`A...`) o nombre en `author_names` (`arrayExists(...)`).
- **Temático:** Filtrando por título o subcampo (`ilike(title, '%...%')`).
*Nota técnica ClickHouse:* Desanida tanto `sdgs` como `sdg_ids` mediante `ARRAY JOIN arrayDistinct(arrayConcat(sdgs, sdg_ids))` garantizando cobertura completa de artículos individuales y multitemáticos.

### 6. Ranking de Entidades Líderes por Tema (`top-entities`)
Identifica con un solo comando qué **autores** o **instituciones** tienen la mayor capacidad científica (volumen, citas, FWCI y porcentaje en el Top 10% mundial) en un tema estratégico (ej. litio, celdas solares, grafeno):

**Para Instituciones líderes:**
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py top-entities \
  --query "lithium" \
  --by "institutions" \
  --limit 10 \
  --output ./data/top_instituciones_litio.json
```

**Para Investigadores líderes (con resolución de nombres y ORCID):**
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py top-entities \
  --query "lithium" \
  --by "authors" \
  --limit 10 \
  --output ./data/top_investigadores_litio.json
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
  --output ./data/especialidades_ia.json
```
Inspecciona los primeros resultados de salida para identificar los 3 a 5 tópicos dominantes (ej. *Metaheuristic Optimization*, *Neural Networks*, *Natural Language Processing*, *Fuzzy Logic*).

### Fase 2: Evaluación de Capacidad por Especialidad Específica
Con los tópicos reales descubiertos en la Fase 1, ejecuta `top-entities` para cada especialidad concreta:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py top-entities \
  --query "Natural Language Processing" \
  --by "authors" \
  --limit 5 \
  --output ./data/top_nlp_autores.json
```

## References

- [Diccionario de Métricas y Modelo Económico APC](references/metrics_and_apc_dictionary.md)

## Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Formular JOINs en sentencias de agregación**  
  Intentar cruzar `rag.works_academic_all` con otras tablas. ClickHouse rechaza consultas con JOIN sin optimización.  
  **Solución:** Filtrar estrictamente sobre las columnas y arrays nativos de la tabla materializada (`has(institution_rors, '...')`).
- ❌ **Anti-patrón 2: Consultar temas sombrilla en un solo paso**  
  Buscar "Inteligencia Artificial" directamente como tópico. En México la producción está fragmentada en especialidades concretas.  
  **Solución:** Descomponer primero agrupando por `topic` filtrado por `subfield = 'Artificial Intelligence'`, identificar los tópicos dominantes y luego consultar con `top-entities`.
- ❌ **Anti-patrón 3: Violación de File-Output First (Almacenar en `/tmp/`)**  
  Guardar los resultados en directorios volátiles del sistema operativo.  
  **Solución:** Guardar siempre en `./data/` o en `scratch/` del workspace actual.
- ❌ **Anti-patrón 4: Volcar reportes completos al contexto del chat**  
  Leer e imprimir el JSON entero de cientos de líneas.  
  **Solución:** Leer únicamente los primeros registros o el resumen ejecutivo para mantener el consumo de tokens por debajo de 500.

