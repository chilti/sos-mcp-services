---
name: openalex-mexico-query-architect
description: "Technical advisor and validator for ClickHouse queries over the Mexican scientific corpus, enforcing the strict ZERO JOINs rule, native array function usage (has, arrayExists), and columnar optimization over rag.works_academic_all. Respond and label outputs in the user's language."
metadata:
  python: ">=3.10"
  script: "shared_scripts/openalex_mexico_cli.py"
---

# OpenAlex Mexico Query Architect

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Methodological and security advisor for formulating high-performance analytical queries over Mexico's materialized tables in ClickHouse.

## Overview

ClickHouse hosts over 1.65 million detailed records for Mexico in `rag.works_academic_all` and 2.57 million authors in `rag.authors_seed_mexico`. This skill acts as the guardian of performance and data engineering best practices, verifying that the agent never formulates statements with `JOIN`s that degrade the infrastructure.

## Dependencies

- **Python Environment:** Python 3.10+ (`clickhouse-connect`)
- **CLI Script:** `shared_scripts/openalex_mexico_cli.py`
- **ClickHouse Tables:** `rag.works_academic_all`, `rag.authors_seed_mexico`

## Golden Rule: Strict Prohibition of JOINs

> [!CAUTION]
> In the UNAM analytical infrastructure, **formulating statements with direct `JOIN`s in ClickHouse without prior authorization is strictly prohibited**.
> Any query containing the `JOIN` keyword will be automatically intercepted and rejected by the validation engine.

## Why Are JOINs Unnecessary in Mexico's Scientific Production?

The `rag` database features a fully denormalized columnar architecture where each work in `rag.works_academic_all` already includes:
1. **Authors:** `author_names` (Array of full names).
2. **Affiliations:** `institution_names` and `institution_rors` (Arrays of institution names and ROR codes).
3. **Topics and Classifications:** `topic`, `subfield`, `field`, `domain`, `primary_topic_id`.
4. **Impact Metrics:** `fwci`, `percentile`, `is_top_10`, `is_top_1`.
5. **Open Access and Costs:** `oa_status`, `is_oa`, `apc_paid_usd`, `apc_list_usd`.
6. **Sustainable Development Goals:** `sdg_ids`, `sdgs`.

## Safe Query Patterns (JOIN Equivalents)

### 1. Filter works by institution
Instead of: `SELECT * FROM works w JOIN institutions i ON ... WHERE i.ror = '...'`  
**Use:**
```sql
SELECT title, publication_year, cited_by_count
FROM rag.works_academic_all
WHERE has(institution_rors, 'https://ror.org/01tmp8f25')
```

### 2. Filter works by author
Instead of: `SELECT * FROM works w JOIN authors a ON ... WHERE a.name = '...'`  
**Use:**
```sql
SELECT title, publication_year, cited_by_count
FROM rag.works_academic_all
WHERE arrayExists(x -> positionCaseInsensitiveUTF8(x, 'Torres Córdoba') > 0, author_names)
```

### 3. Direct aggregations without joins
```sql
SELECT oa_status, count(*) as total, round(sum(apc_paid_usd), 2) as gasto_usd
FROM rag.works_academic_all
WHERE publication_year >= 2020
GROUP BY oa_status
```

## Pre-Validation of Queries
To verify whether an SQL statement complies with security directives before executing it:
```bash
python shared_scripts/openalex_mexico_cli.py validate-query \
  --query "SELECT * FROM rag.works_academic_all WHERE publication_year = 2024" \
  --output ./data/reporte_validacion.json
```

## Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Formulating queries with a `JOIN` statement**  
  Attempting to link tables as if it were a traditional relational database (MySQL or PostgreSQL). ClickHouse MergeTree is columnar, and the cluster rejects unoptimized JOIN queries to protect memory.  
  **Solution:** Query the pre-materialized native array columns (`has(institution_rors, '...')`).
- ❌ **Anti-pattern 2: Queries without LIMIT or without file output (Violating File-Output First)**  
  Running open-ended `SELECT *` statements that attempt to return hundreds of thousands of records to the console.  
  **Solution:** Always specify an explicit `--limit` and direct output with `--output`.
- ❌ **Anti-pattern 3: Case-sensitive string comparisons without diacritics**  
  Using `WHERE author = 'Jose Lopez'`, losing thousands of records due to accents or capitalization.  
  **Solution:** Use `positionCaseInsensitiveUTF8(x, '...') > 0`.

## References

- [Safe Query Patterns Catalog for Mexico](references/no_joins_mexico_patterns.md)
