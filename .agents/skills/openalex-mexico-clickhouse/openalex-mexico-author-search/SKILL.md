---
name: openalex-mexico-author-search
description: "Search and disambiguation of Mexican researchers in local ClickHouse over the materialized tables rag.authors_seed_mexico (2.57M authors) and rag.academics_all, with filters by SNII level, institutional department, and Hispanic name variants. Respond and label outputs in the user's language."
metadata:
  python: ">=3.10"
  script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex Mexico Author Search

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Specialized skill for locating, disambiguating, and retrieving metrics of researchers affiliated with Mexican institutions in the local ClickHouse database.

## Overview

Enables searching academic profiles across the catalog of over 2.57 million authors linked to Mexico (`rag.authors_seed_mexico`) and cross-referencing with data from the National System of Researchers (`rag.academics_all`), automatically resolving compound surname permutations and diacritical marks without formulating `JOIN`s.

## Dependencies

- **Python Environment:** Python 3.10+ (`clickhouse-connect`)
- **CLI Script:** [`scripts/openalex_mexico_cli.py`](scripts/openalex_mexico_cli.py)
- **Database:** Local ClickHouse (`rag` database, `authors_seed_mexico` and `academics_all` tables)

## CLI Interface

### 1. Search by Given Name or Surnames
Automatically generates hyphenated and unhyphenated variants and performs case-insensitive searches:
```bash
python scripts/openalex_mexico_cli.py search-authors \
  --name "Rafael Torres Córdoba" \
  --limit 20 \
  --output ./data/autores_encontrados.json
```

### 2. Filtering by Institution and Academic Department
Filters by university (e.g., `UNAM`, `Cinvestav`, `UAM`) or academic entity:
```bash
python scripts/openalex_mexico_cli.py search-authors \
  --name "Jiménez Andrade" \
  --institution "Universidad Nacional Autónoma de México" \
  --limit 10 \
  --output ./data/autores_unam.json
```

### 3. Filtering by SNII Level
For queries regarding academic staff registered in the Official SNII Registry:
```bash
python scripts/openalex_mexico_cli.py search-authors \
  --snii-level "III" \
  --institution "UNAM" \
  --limit 50 \
  --output ./data/investigadores_snii3.json
```

## Workflow Steps

1. **Initial Search:** Run `search-authors` with the researcher's name and write the output to a JSON file.
2. **Canonical Identification:** Extract the OpenAlex `id` (`https://openalex.org/A...`) and `orcid`.
3. **Proceed to Publications:** Use the obtained name or ID to feed the [`openalex-mexico-works-search`](../openalex-mexico-works-search/SKILL.md) skill.

## References

- [Author Tables Schema in ClickHouse](references/academics_all_schema.md)
- [Hispanic Name Permutation Rules](references/hispanic_name_permutations.md)

## Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Searching with exact strings without accounting for Hispanic diacritics**  
  Searching for `"Rafael Torres Cordoba"` without an accent in a direct, case-sensitive SQL query.  
  **Solution:** Use the `search-authors` CLI subcommand, which generates phonetic permutations and normalizes diacritics automatically.
- ❌ **Anti-pattern 2: Formulating JOINs between authors and articles**  
  Attempting to join `rag.authors_seed_mexico` with `rag.works_academic_all` via SQL JOIN.  
  **Solution:** First extract the author to obtain their ID or ORCID, and then filter `rag.works_academic_all` using native arrays.
- ❌ **Anti-pattern 3: Queries without an explicit limit**  
  Searching for a common surname (e.g., `"Hernández"`, `"González"`) without `--limit`, returning thousands of homonyms.  
  **Solution:** Always bound with `--limit 10` or `--limit 20` and refine by filtering with `--institution`.
- ❌ **Anti-pattern 4: Violating File-Output First**  
  Omitting `--output` and dumping massive author lists to the console.  
  **Solution:** Always save to a structured file (`--output ./data/autores.json`).
