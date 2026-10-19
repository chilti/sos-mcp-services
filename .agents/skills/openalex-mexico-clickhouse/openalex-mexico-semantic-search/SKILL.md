---
name: openalex-mexico-semantic-search
description: Búsqueda semántica y conceptual de publicaciones científicas e investigadoras/es en México usando embeddings vectoriales nomic de 768 dimensiones en ClickHouse (rag.works_academic_all y rag.academics_all), con desambiguación automática de autores nacionales frente a colaboradores internacionales.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex México Semantic Search

Búsqueda semántica basada en embeddings vectoriales de 768 dimensiones (`text-embedding-nomic-ai-nomic-embed-text-v2-moe`) y similitud coseno en ClickHouse sobre el acervo científico de México.

## Overview

A diferencia de las búsquedas léxicas por coincidencia exacta de texto, esta skill permite:
1. **Descubrir trabajos conceptualmente afines:** Aunque el título no contenga las palabras exactas o esté redactado en inglés/español (ej. "materiales catódicos para baterías de litio" encuentra cupratos de litio y modelos electroquímicos).
2. **Identificar perfiles de investigadores especialistas:** Búsqueda vectorial sobre la masa crítica de investigadores en México (`rag.academics_all`).
3. **Desambiguar coautoría internacional:** Separa automáticamente en los resultados a las investigadoras y los investigadores adscritos a instituciones de México (`mexican_affiliated_authors`) de los colaboradores extranjeros (`international_collaborators`), resolviendo además los IDs de OpenAlex a nombres legibles.
4. **Respeto estricto a CERO JOINs:** Toda la recuperación vectorial y enriquecimiento de metadatos se ejecuta en subsegundos mediante escaneo columnar directo y `WHERE id IN (...)`.

## Dependencies

- **Entorno Python:** `/home/ambientesPy/revistaslatam`
- **Script CLI:** [`scripts/openalex_mexico_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-semantic-search/scripts/openalex_mexico_cli.py)
- **Servidor de Embeddings:** LM Studio local (`http://127.0.0.1:1234/v1` en host / `http://172.17.0.1:1234/v1` en contenedor Docker)
- **Tablas ClickHouse:** `rag.works_academic_all` (1.37M publicaciones con `embedding_nomic`), `rag.academics_all` (9.1K perfiles con `embedding_nomic`), `rag.authors_seed_mexico` (2.57M autores).

## CLI Interface

### 1. Búsqueda Semántica de Publicaciones
Recupera artículos conceptualmente afines a una temática en lenguaje natural (español o inglés):
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py semantic-search \
  --query "materiales catódicos para baterías de litio" \
  --target works \
  --limit 20 \
  --output /ruta/a/articulos_semanticos_litio.json
```

Filtros opcionales combinables:
- `--year-min 2020` / `--year-max 2025`
- `--oa-status diamond` (o gold, hybrid, etc.)
- `--is-top-10 true`
- `--institution-name "Universidad Nacional Autónoma de México"`

### 2. Búsqueda Semántica de Investigadores Especialistas
Descubre investigadores de México cuyo perfil temático coincide vectorialmente con una disciplina o problema:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_mexico_cli.py semantic-search \
  --query "procesamiento de lenguaje natural y modelos de lenguaje" \
  --target authors \
  --limit 15 \
  --output /ruta/a/expertos_pln_mexico.json
```

### 3. Interpretación de Autores y Coautoría
En los resultados en formato JSON devueltos para cada publicación:
- `authors_disambiguated.mexican_affiliated_authors`: Contiene a los autores que poseen adscripción formal o historial en instituciones mexicanas (UNAM, IPN, UAM, Cinvestav, etc.).
- `authors_disambiguated.international_collaborators`: Contiene a los coautores adscritos a universidades extranjeras que colaboraron en el estudio.
- `cosine_distance`: Mide la distancia angular (menor valor = mayor cercanía conceptual).
- `semantic_similarity`: Medida normalizada entre 0.0 y 1.0 (`1.0 - cosine_distance`).

## Directrices para el Agente (LLM)

1. **Cuando el usuario pregunte por conceptos complejos o preguntas abiertas:** Usa `semantic-search` en lugar de una búsqueda por coincidencia estricta de palabras clave (`search-works`).
2. **Cuando menciones investigadores de México a partir de un paper:** Revisa siempre `mexican_affiliated_authors` para reportar a los especialistas nacionales y no atribuir la afiliación mexicana a coautores internacionales.
3. **Para rankings cuantitativos globales por volumen de publicaciones en un tema:** Complementa con `top-entities --by authors` de la skill [`openalex-mexico-aggregations`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-aggregations/SKILL.md).
