---
name: infotlachia-scholar-intelligence
description: High-speed analytical access to the DuckDB database (analytics_cache.duckdb, 5.9 GB, 14 tables) to query precomputed metrics for SNII researchers, academic departments, Mexican universities, and the national landscape (FWCI, citations, APC USD, Gini). Respond and label outputs in the user's language.
dependencies:
  - python: ">=3.10"
  - script: "scripts/infotlachia_cli.py"
---

# Info TlachIA Scholar Intelligence

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Scientometric intelligence analytical module covering SNII-accredited researchers and university departments in Mexico using embedded DuckDB.

## Overview
Contains consolidated metrics for over 90,000 researchers and 3,000 institutions. Through DuckDB in read-only mode (`read_only=True`), it enables sub-10 ms analytical queries across time series, estimated APC expenditure, thematic Gini index, and placement in the excellence percentile (Top 10%).

## Dependencies
- **Python Environment:** Python 3.10+ (with required dependencies)
- DuckDB database: `/home/sinapsisai/data/analytics_cache.duckdb`
- Executable script: [`scripts/infotlachia_cli.py`](file://scripts/infotlachia_cli.py)

## Scripts & CLI Tools

### Researcher Profile (`query-researcher`)
Query the consolidated impact of a Mexican researcher:
```bash
python scripts/infotlachia_cli.py query-researcher \
  --name "Torres, Rafael" \
  --format markdown \
  --output /path/to/perfil_torres.md
```

### Faculty or Department Metrics (`query-entity`)
Analyze the scholarly output and APC expenditure of a university department or faculty:
```bash
python scripts/infotlachia_cli.py query-entity \
  --entity "Facultad de Ciencias" \
  --format json \
  --output /path/to/facultad_ciencias.json
```

### Institutional Overview (`query-institution`)
General benchmarking of an entire university or research institution:
```bash
python scripts/infotlachia_cli.py query-institution \
  --institution "UNIVERSIDAD NACIONAL AUTONOMA DE MEXICO" \
  --format markdown \
  --output /path/to/reporte_unam.md
```

### National Overview (`national-overview`)
Consolidated statistics for the Mexican scientific system:
```bash
python scripts/infotlachia_cli.py national-overview \
  --format markdown
```

### Safe SQL Queries (`sql-safe`)
Execute direct read-only `SELECT` statements across the 14 tables:
```bash
python scripts/infotlachia_cli.py sql-safe \
  --query "SELECT top_domain, count(*) FROM investigador_total GROUP BY top_domain ORDER BY count(*) DESC LIMIT 10" \
  --format markdown
```

## Workflow Steps
1. **Query Profile:** Run `query-researcher` to extract H-index, FWCI, and SNII status.
2. **Contextualize within Department:** Run `query-entity` to benchmark the researcher against their academic department or faculty.
3. **Formatted Report:** Use `--format markdown` (and `--lang es` if reporting in Spanish) to insert comparative tables directly into final agent reports.

## References
- [Dictionary of the 14 DuckDB Tables](references/duckdb_14tables_dictionary.md)
- [SNII Registry Structure and Knowledge Areas](references/snii_ranking_structure.md)

## Troubleshooting & Edge Cases
- **Multiple Researchers with the Same Name:** Name search uses partial matching (`ILIKE %name%`). When homonyms exist, the CLI returns up to 10 candidates ordered by document volume so the agent can filter by institution or ORCID.
- **SQL Query Safety:** The `sql-safe` subcommand blocks any statement containing `DROP`, `DELETE`, `UPDATE`, `INSERT`, or `ALTER`.
