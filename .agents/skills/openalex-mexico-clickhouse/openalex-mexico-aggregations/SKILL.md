---
name: openalex-mexico-aggregations
description: "Calculation of aggregated metrics and scientometric rankings in ClickHouse (rag.works_academic_all): distribution across the 6 Open Access routes (Diamond vs Gold APC), commercial APC expenditure in USD, annual time series, thematic subfields, and RANKING of leading institutions and researchers in a topic ('top-entities') with volume, citations, and FWCI. Respond and label outputs in the user's language."
metadata:
  python: ">=3.10"
  script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex Mexico Aggregations

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Columnar aggregation engine for the quantitative evaluation of scientific production in Mexico at massive scale without transferring individual records.

## Overview

Calculates impact metrics and indicators, publishing expenditure, and publication models grouped by any scientometric dimension (year, OA route, subfield, discipline, or country), responding in milliseconds thanks to the ClickHouse MergeTree engine. Additionally, through the `top-entities` command, it directly identifies the institutions or researchers with the highest capacity in any topic.

## Dependencies

- **Python Environment:** Python 3.10+ (`clickhouse-connect`)
- **CLI Script:** `scripts/openalex_mexico_cli.py`
- **ClickHouse Table:** `rag.works_academic_all`

## CLI Interface

> [!IMPORTANT]
> Always save output files inside the current workspace in `./data/`, NEVER in `/tmp/`.

### 1. Breakdown of Open Access Routes and APC Expenditure
Quantifies the penetration of the 6 OA routes and calculates total commercial expenditure in USD:
```bash
python scripts/openalex_mexico_cli.py aggregate \
  --group-by "oa_status" \
  --filter "publication_year >= 2020" \
  --output ./data/acceso_abierto_mexico.json
```

### 2. Time Series of Production, Citations, and Impact Quality
Annual evolution of publications, percentage in the Top 10%, and mean FWCI:
```bash
python scripts/openalex_mexico_cli.py aggregate \
  --group-by "publication_year" \
  --filter "publication_year >= 2015 AND publication_year <= 2025" \
  --output ./data/tendencia_anual_mexico.json
```

### 3. Grouping by Disciplinary Subfield
Identifies the subfields with the highest publication volume and citation concentration:
```bash
python scripts/openalex_mexico_cli.py aggregate \
  --group-by "subfield" \
  --filter "publication_year >= 2020" \
  --output ./data/subcampos_mexico.json
```

### 4. Filtering by Specific Institution
Applies filters by university using native ClickHouse arrays:
```bash
python scripts/openalex_mexico_cli.py aggregate \
  --group-by "oa_status" \
  --filter "has(institution_rors, 'https://ror.org/01tmp8f25') AND publication_year >= 2022" \
  --output ./data/oa_unam_2022_2025.json
```

### 5. Distribution of Sustainable Development Goals (SDGs / ODS)
Groups and quantifies scientific production according to the 17 UN SDGs (2030 Agenda):
```bash
python scripts/openalex_mexico_cli.py aggregate \
  --group-by "sdgs" \
  --filter "publication_year >= 2020" \
  --output ./data/sdgs_mexico.json
```
*Supports 4 analytical levels:*
- **National:** Unfiltered to evaluate the entire corpus of Mexico (901K publications in SDGs).
- **Institutional:** Filtering by institutional ROR (e.g., `01tmp8f25` for UNAM) or by name in `institution_names`.
- **Researcher:** Filtering by canonical ID (`A...`) or name in `author_names` (`arrayExists(...)`).
- **Thematic:** Filtering by title or subfield (`ilike(title, '%...%')`).
*ClickHouse Technical Note:* Unnests both `sdgs` and `sdg_ids` via `ARRAY JOIN arrayDistinct(arrayConcat(sdgs, sdg_ids))`, guaranteeing full coverage of single-topic and multi-topic papers.

### 6. Ranking Leading Entities by Topic (`top-entities`)
Identifies with a single command which **authors** or **institutions** have the highest scientific capacity (volume, citations, FWCI, and percentage in the global Top 10%) in a strategic topic (e.g., lithium, solar cells, graphene):

**For Leading Institutions:**
```bash
python scripts/openalex_mexico_cli.py top-entities \
  --query "lithium" \
  --by "institutions" \
  --limit 10 \
  --output ./data/top_instituciones_litio.json
```

**For Leading Researchers (with name and ORCID resolution):**
```bash
python scripts/openalex_mexico_cli.py top-entities \
  --query "lithium" \
  --by "authors" \
  --limit 10 \
  --output ./data/top_investigadores_litio.json
```

## Structured Output

Each grouped record automatically returns:
- `dimension`: Value of the grouped category (e.g., `diamond`, `2024`, etc.).
- `total_works`: Absolute publication count.
- `total_citations`: Cumulative global citations.
- `avg_fwci`: Average Field-Weighted Citation Impact.
- `pct_top_10`: Percentage of articles in the world's top 10% most cited.
- `total_apc_paid_usd`: Sum of estimated commercial expenditure on APC charges (USD).

## Mandatory Protocol for Broad Umbrella Topics (AI, Nanotechnology, Biotechnology)

When the user's query refers to a broad umbrella area or discipline (e.g., *"Artificial Intelligence"*, *"Biotechnology"*, *"Renewable Energy"*), **NEVER run `top-entities` directly with the general term**. Strictly follow this 2-phase procedure for local models with bounded context windows:

### Phase 1: Taxonomic Discovery in ClickHouse (Data-Driven Taxonomy)
Run the aggregation grouping by topics to discover which actual specialties have scientific production in Mexico:
```bash
python scripts/openalex_mexico_cli.py aggregate \
  --group-by "topics_hierarchy" \
  --filter "subfield = 'Artificial Intelligence'" \
  --output ./data/especialidades_ia.json
```
Inspect the top output results to identify the 3 to 5 dominant topics (e.g., *Metaheuristic Optimization*, *Neural Networks*, *Natural Language Processing*, *Fuzzy Logic*).

### Phase 2: Capacity Evaluation by Specific Specialty
Using the real topics discovered in Phase 1, run `top-entities` for each concrete specialty:
```bash
python scripts/openalex_mexico_cli.py top-entities \
  --query "Natural Language Processing" \
  --by "authors" \
  --limit 5 \
  --output ./data/top_nlp_autores.json
```

## References

- [Metrics Dictionary and APC Economic Model](references/metrics_and_apc_dictionary.md)

## Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Formulating JOINs in aggregation statements**  
  Attempting to join `rag.works_academic_all` with other tables. ClickHouse rejects unoptimized JOIN queries.  
  **Solution:** Filter strictly on the columns and native arrays of the materialized table (`has(institution_rors, '...')`).
- ❌ **Anti-pattern 2: Querying umbrella topics in a single step**  
  Searching for "Artificial Intelligence" directly as a topic. In Mexico, production is fragmented across specific specialties.  
  **Solution:** Decompose first by grouping by `topics_hierarchy` filtered by `subfield = 'Artificial Intelligence'`, identify the dominant topics, and then query with `top-entities`.
- ❌ **Anti-pattern 3: Violating File-Output First (Storing in `/tmp/`)**  
  Saving results in volatile operating system directories.  
  **Solution:** Always save in `./data/` or in `scratch/` of the current workspace.
- ❌ **Anti-pattern 4: Dumping full reports into the chat context**  
  Reading and printing the entire JSON of hundreds of lines.  
  **Solution:** Read only the top records or the executive summary to keep token consumption below 500.
