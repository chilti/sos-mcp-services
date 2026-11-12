---
name: pubmed-harvester
description: Extract, paginate, and normalize biomedical and clinical literature from the official PubMed API (NCBI E-utilities) into the canonical tabular schema (Parquet, JSON, CSV). Respond and label outputs in the user's language.
---

# PubMed Data Harvester

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Autonomous, standalone tool for harvesting publications indexed in the National Library of Medicine (NLM / PubMed) via E-utilities (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils`), automatically standardizing records into the `sos-mcp-services` suite's canonical tabular schema.

---

## Capabilities

- **Advanced Entrez Search:** Full support for MeSH terms, `[Title/Abstract]` and `[Affiliation]` fields, and date filters.
- **Author and Clinical Output:** Extraction by author name (`[Author]`) cross-referenced with affiliation (`[Affiliation]`).
- **PMC Open Access Detection:** Automatic classification of works with full text available in PubMed Central (`pmcid`).
- **Canonical Schema:** Standardizes authors, cross-identifiers (`pmid`, `doi`, `pmcid`), journal, dates, and Open Access route.

---

## CLI Interface

Execution environment:
```bash
python scripts/pubmed_harvest_cli.py [subcommand] [options]
```

### 1. Thematic and Affiliation Search
```bash
python scripts/pubmed_harvest_cli.py fetch-works \
  --query "idiopathic pulmonary fibrosis" \
  --affiliation "Mexico" \
  --year-from 2020 \
  --year-to 2026 \
  --limit 50 \
  --output ./ipf_mexico.parquet
```

### 2. Author Output by Name
```bash
python scripts/pubmed_harvest_cli.py fetch-author-works \
  --author "Pardo Annie" \
  --affiliation "UNAM" \
  --limit 100 \
  --output ./annie_pardo_pubmed.parquet
```

---

## Technical References
- [E-utilities Technical Guide](references/pubmed_eutils_guide.md)
