---
name: openalex-harvester
description: Extract, cursor-paginate, and normalize scientific literature from OpenAlex into canonical tables (Parquet, JSON, CSV). Respond and label outputs in the user's language.
metadata:
  python: ">=3.10"
  script: "scripts/openalex_harvest_cli.py"
---
# OpenAlex Data Harvester

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Autonomous, standalone tool for bulk harvesting of scientific records from the OpenAlex API (`https://api.openalex.org` or local endpoints), supporting cursor pagination and mapping into the canonical tabular schema.

---

## Capabilities

- **Flexible Thematic Search:** Worldwide retrieval by keywords, titles, topics, and date ranges.
- **Author and Institutional Output:** Direct download by ORCID, OpenAlex Author ID, or institutional ROR.
- **Open Science Filters:** Segmentation by Open Access route (`gold`, `diamond`, `green`, `hybrid`, `closed`).
- **Canonical Schema Mapping:** Standardizes authors, affiliations, citations, FWCI, percentiles, APC, and references into a Parquet, JSON, or CSV file.

---

## Dependencies and Value Chain

- **Python Environment:** Python 3.10+ (with required dependencies)
- **CLI Script:** `scripts/openalex_harvest_cli.py`
- **Downstream Skills:**
  - [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Processes the canonical Parquet file to compute over 30 scientometric indicators.
  - [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md): Extracts co-authorship, bibliographic coupling, and term co-occurrence networks.
  - [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Receives the profile matrix computed from the corpus.
- **Differentiation from `openalex-mexico-clickhouse`:**
  - If the query is about **Mexico** (Mexican universities, SNII researchers, national output), use [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md), which queries the ultra-fast local ClickHouse cluster with embeddings and ZERO JOINs.
  - Use `openalex-harvester` when harvesting literature from **any country or topic worldwide** directly from the global OpenAlex API into canonical Parquet files.

---

## CLI Interface

Execution environment:

```bash
python scripts/openalex_harvest_cli.py [subcommand] [options]
```

### 1. Thematic or journal search

```bash
python scripts/openalex_harvest_cli.py fetch-works \
  --query "quantum computing" \
  --year-from 2020 \
  --year-to 2024 \
  --limit 100 \
  --output ./data/quantum_works.parquet
```

### 2. Author output by ORCID or ID

```bash
python scripts/openalex_harvest_cli.py fetch-author-works \
  --author-id "0000-0002-1825-0097" \
  --limit 200 \
  --output ./data/author_works.parquet
```

### 3. Institutional output by ROR

```bash
python scripts/openalex_harvest_cli.py fetch-institution-works \
  --ror "012gw1n35" \
  --year-from 2023 \
  --year-to 2024 \
  --limit 500 \
  --output ./data/unam_2023_2024.parquet
```

---

## Common Mistakes and Anti-Patterns (Avoid Frequent Pitfalls)

- ❌ **Anti-pattern 1: Harvesting literature via the public API that already resides in local ClickHouse**  
  Using `openalex-harvester` to download UNAM or Mexican papers over the external API with network latency.  
  **Solution:** For any research focused on Mexico, rely directly on `openalex-mexico-clickhouse` (1.65M local works with millisecond response times).
- ❌ **Anti-pattern 2: Using traditional page-number pagination for large volumes**  
  OpenAlex limits conventional page pagination to the first 10,000 records.  
  **Solution:** The CLI automatically uses cursor pagination (`cursor=*`) for exhaustive harvests.
- ❌ **Anti-pattern 3: Exporting large volumes to JSON instead of Parquet**  
  Generating massive JSON files for tens of thousands of papers.  
  **Solution:** Use `--output <path>.parquet`. The columnar Parquet format reduces disk size by up to 85% and preserves exact data types.
- ❌ **Anti-pattern 4: Violating File-Output First**  
  Attempting to process without specifying `--output`. The CLI always requires a structured destination file path.

---

## Technical References

- [OpenAlex API Parameters and Filters](references/openalex_api_parameters.md)
- [Cursor Pagination Guide](references/cursor_paging_guide.md)
