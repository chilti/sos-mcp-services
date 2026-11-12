---
name: openalex-mexico-works-search
description: "Retrieval and extraction of Mexican scientific publications over the materialized table rag.works_academic_all (1.65M works), filtering by institution ROR, author, year range, Open Access route (Diamond, Gold, Hybrid), and Top 10% and Top 1% impact percentiles. Respond and label outputs in the user's language."
metadata:
  python: ">=3.10"
  script: "scripts/openalex_mexico_cli.py"
---
# OpenAlex Mexico Works Search

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Granular retrieval of articles, proceedings, and book chapters from scientific production linked to Mexico stored in the `rag.works_academic_all` materialized table.

## Overview

Enables querying the 1,652,927 works from Mexico with enriched scientometric indicators (FWCI, percentiles, Top 10%, paid APC, Open Access routes, and SDGs), applying optimized filters without needing relational joins.

## Dependencies

- **Python Environment:** Python 3.10+ (`clickhouse-connect`)
- **CLI Script:** [`scripts/openalex_mexico_cli.py`](scripts/openalex_mexico_cli.py)
- **ClickHouse Table:** `rag.works_academic_all`

## CLI Interface

### 1. Search by Institution (ROR) and Time Range

Retrieves the production of an institution (e.g., UNAM: `01tmp8f25`, Cinvestav: `04yeehy64`) within a defined period:

```bash
python scripts/openalex_mexico_cli.py search-works \
  --institution-ror "01tmp8f25" \
  --year-min 2023 \
  --year-max 2025 \
  --limit 200 \
  --output ./data/produccion_unam_reciente.json
```

### 2. Search for Elite Publications (Top 10% / Top 1%)

Filters articles in the top decile of global impact:

```bash
python scripts/openalex_mexico_cli.py search-works \
  --is-top-10 true \
  --year-min 2020 \
  --limit 100 \
  --output ./data/articulos_top10_mexico.json
```

### 3. Filtering by Diamond vs. Gold Open Access

For analyses of publishing sovereignty and non-commercial routes:

```bash
python scripts/openalex_mexico_cli.py search-works \
  --oa-status "diamond" \
  --year-min 2024 \
  --limit 100 \
  --output ./data/articulos_diamante_2024.json
```

### 4. Search by Topic or Keyword

```bash
python scripts/openalex_mexico_cli.py search-works \
  --query "quantum dots" \
  --topic "Nanotechnology" \
  --limit 50 \
  --output ./data/nanotecnologia_mexico.json
```

## Workflow Steps

1. **Define Filters:** Select institution, year range, Open Access route, or impact level.
2. **Execute Search:** Run `search-works` outputting to a JSON, CSV, or Parquet file.
3. **Downstream Workflows:**
   - For aggregated indicator calculations: use [`openalex-mexico-aggregations`](../openalex-mexico-aggregations/SKILL.md).
   - For network modeling: feed into [`bibliometric-network-analyst`](../../bibliometric-network-analyst/SKILL.md).

## References

- [Field Dictionary of rag.works_academic_all](references/works_academic_all_schema.md)

## Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Exhaustive search without bounding by year or ROR**  
  Running open-text searches over 1.65M records without delineating a time window.  
  **Solution:** Specify `--year-min` and `--year-max`, or filter by `--institution-ror`.
- ❌ **Anti-pattern 2: Confusion over ROR code format**  
  Assuming only the short alphanumeric ID or only the full URI is accepted.  
  **Solution:** The CLI accepts both the short format (`01tmp8f25`) and the full URI (`https://ror.org/01tmp8f25`) interchangeably, resolving both transparently.
- ❌ **Anti-pattern 3: Massive downloads without pagination or a prudent limit**  
  Attempting to download 50,000 records in a single command without verifying the impact on local memory.  
  **Solution:** Increase `--limit` incrementally (e.g., 500 $\rightarrow$ 1,000 $\rightarrow$ 2,500).
- ❌ **Anti-pattern 4: Violating File-Output First**  
  Omitting the `--output` flag, causing the CLI to fail or dump thousands of articles with abstracts and metadata to the terminal.  
  **Solution:** Always specify `--output ./data/publicaciones.json`.
