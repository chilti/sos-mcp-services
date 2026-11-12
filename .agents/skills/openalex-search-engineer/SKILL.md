---
name: openalex-search-engineer
description: Formulate searches, aggregations, and analytical queries on the local OpenAlex database in ClickHouse (569M works, 337M authors) with diacritic normalization and Hispanic name variant handling. Respond and label outputs in the user's language.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/openalex_search_cli.py"
---

# OpenAlex Search Engineer

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Specialist in formulating high-performance queries over the massive local OpenAlex dump in ClickHouse, applying diacritic-insensitive tokenization and safe ZERO-JOIN retrieval.

## Overview
ClickHouse locally hosts over 569 million scientific publications. This module implements the batch search interface for autonomous agents, automatically generating Hispanic name permutations and dumping results to JSON/Parquet/CSV files to avoid saturating the conversation context.

## Dependencies
- Python environment: `/home/ambientesPy/revistaslatam`
- Data engine: Local ClickHouse (database `openalex` / `rag`)
- Executable script: [`scripts/openalex_search_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-search-engineer/scripts/openalex_search_cli.py)

## Scripts & CLI Tools

### Author Search with Permutations (`search-authors`)
Searches for authors by automatically testing compound surname variations:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_search_cli.py search-authors \
  --name "Rafael Torres Córdoba" \
  --limit 20 \
  --output /path/to/found_authors.json
```

### Publication Search (`search-works`)
Retrieves scientific articles by applying filters on materialized tables:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_search_cli.py search-works \
  --query "quantum computing" \
  --year-min 2020 \
  --year-max 2025 \
  --limit 500 \
  --output /path/to/quantum_articles.json
```

### Analytical Aggregations (`aggregate`)
Computes counts and cumulative citations grouped by year, type, or Open Access status:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_search_cli.py aggregate \
  --entity-type works \
  --group-by publication_year \
  --output /path/to/annual_trend.json
```

## Workflow Steps
1. **Identify Entity:** Use `search-authors` to obtain the canonical ID (`A...`) or ORCID.
2. **Extract Works:** Use `search-works` passing the `author_id` or `institution_ror`.
3. **Pass to Downstream Modules:** Save the JSON/Parquet for normalization with [`bibliometric-entity-normalizer`](file:///home/labsom/knomap/engine/skills/bibliometric-entity-normalizer/SKILL.md) or research front modeling with [`research-fronts-citation-network`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/research-fronts-citation-network/SKILL.md).

## References
- [ClickHouse OpenAlex Table Schema](references/clickhouse_openalex_schema.md)
- [Hispanic Name Permutations](references/hispanic_name_permutations.md)

## Troubleshooting & Edge Cases
- **Strict ZERO-JOIN Rule:** Direct `JOIN` statements are strictly prohibited. To cross-reference authors and institutions, filter by ROR directly in `authors` or use pre-joined materialized tables (`works_academic_all`).
- **Memory Limits:** Results are written to disk via `--output` to keep the agent's context window clean.
