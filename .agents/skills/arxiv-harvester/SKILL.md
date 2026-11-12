---
name: arxiv-harvester
description: Download and normalize scientific preprints from the arXiv Atom XML API into canonical tables (Parquet, JSON, CSV). Respond and label outputs in the user's language.
---

# arXiv Data Harvester

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Autonomous, standalone tool for harvesting scientific literature and preprints from the arXiv open repository (`https://export.arxiv.org/api/query`), strictly enforcing the 3-second courtesy rate-limit interval and normalizing records into the canonical tabular schema.

---

## Capabilities

- **Taxonomy-Based Search:** Thematic filtering by official arXiv subject categories (`cs.AI`, `stat.ML`, `physics.soc-ph`, etc.).
- **Identifier-Based Retrieval:** Direct download of curated lists of arXiv IDs.
- **Green Open Access Tagging:** Standardized tagging of preprints with authorship metadata and version links.
- **Canonical Format:** Parquet, JSON, or CSV files ready for network analysis and thematic descriptor extraction.

---

## CLI Interface

Execution environment:
```bash
python scripts/arxiv_harvest_cli.py [subcommand] [options]
```

### 1. Thematic search by category and keywords
```bash
python scripts/arxiv_harvest_cli.py search \
  --category "cs.AI" \
  --query "large language models" \
  --limit 50 \
  --output ./arxiv_llms.parquet
```

### 2. Retrieval by identifier list
```bash
python scripts/arxiv_harvest_cli.py fetch-by-ids \
  --id-list "2301.07041,2303.08774,2401.12345" \
  --output ./arxiv_selected.parquet
```

---

## Technical References
- [arXiv Categories Taxonomy](references/arxiv_categories_taxonomy.md)
- [arXiv API Query Syntax and Rules](references/arxiv_query_syntax.md)
