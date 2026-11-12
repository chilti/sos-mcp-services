---
name: scopus-harvester
description: Extract, paginate, and normalize scientific literature from the Elsevier Scopus API into canonical tables (Parquet, JSON, CSV). Respond and label outputs in the user's language.
---

# Scopus Data Harvester

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Autonomous, standalone tool for harvesting publications indexed in Elsevier Scopus via its official API (`https://api.elsevier.com/content/search/scopus`), standardizing records directly into the canonical tabular schema.

---

## Capabilities

- **Advanced Scopus Search:** Full support for Boolean syntax and field codes (`TITLE-ABS-KEY`, `AUTH`, `AFFIL`, `PUBYEAR`, etc.).
- **Author and Institution Profiles:** Extraction by Scopus Author ID (`AU-ID`) or Scopus Affiliation ID (`AF-ID`).
- **Network Resilience:** Automatic detection and backoff handling for quota rate limits (HTTP 429).
- **Reliable Raw Citations:** Normalizes cumulative citation counts (`citedby-count`) and metadata without making FWCI assumptions.

---

## CLI Interface

Execution environment:
```bash
python scripts/scopus_harvest_cli.py [subcommand] [options]
```

### 1. Thematic search
```bash
python scripts/scopus_harvest_cli.py search \
  --query 'TITLE-ABS-KEY("deep learning" AND "medical imaging")' \
  --year-from 2021 \
  --year-to 2024 \
  --limit 50 \
  --output ./scopus_deep_learning.parquet
```

### 2. Author publications by AU-ID
```bash
python scripts/scopus_harvest_cli.py author-profile \
  --author-id "57200234567" \
  --limit 100 \
  --output ./author_scopus.parquet
```

### 3. Institutional publications by AF-ID
```bash
python scripts/scopus_harvest_cli.py affil-works \
  --af-id "60028190" \
  --year-from 2023 \
  --year-to 2024 \
  --limit 100 \
  --output ./unam_scopus_2023.parquet
```

---

## Technical References
- [Scopus Advanced Search Syntax](references/scopus_search_syntax.md)
- [Elsevier Quota Policies and HTTP 429 Responses](references/elsevier_quota_policies.md)
