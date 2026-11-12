---
name: semantic-scholar-harvester
description: Extract articles, abstracts, and citation graphs from the Semantic Scholar Graph API into canonical tables (Parquet, JSON, CSV). Respond and label outputs in the user's language.
---

# Semantic Scholar Data Harvester

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Autonomous, standalone tool for querying the Semantic Scholar knowledge graph (`https://api.semanticscholar.org/graph/v1`), downloading publications by keywords or author, and reconstructing direct citation subgraphs (incoming and outgoing).

---

## Capabilities

- **Broad Thematic Search:** Full-text search and year-range filtering without requiring a mandatory API key.
- **Citation Graph Construction:** Simultaneous download of incoming citations and outgoing bibliographic references for any paper.
- **Standardized Canonical Mapping:** Direct generation of Parquet, JSON, or CSV files ready for consumption by indicator and network engines.

---

## CLI Interface

Execution environment:
```bash
python scripts/s2_harvest_cli.py [subcommand] [options]
```

### 1. Thematic search
```bash
python scripts/s2_harvest_cli.py search-papers \
  --query "knowledge graphs science" \
  --year-from 2022 \
  --year-to 2024 \
  --limit 50 \
  --output ./s2_knowledge_graphs.parquet
```

### 2. Paper citation graph extraction
```bash
python scripts/s2_harvest_cli.py citation-graph \
  --paper-id "10.1038/s41586-020-2649-2" \
  --output ./paper_citation_subgraph.parquet
```

### 3. Author publications by S2 Author ID
```bash
python scripts/s2_harvest_cli.py author-papers \
  --author-id "1741101" \
  --limit 50 \
  --output ./author_papers.parquet
```

---

## Technical References
- [Semantic Scholar Graph API Fields and Structure](references/s2_graph_api_fields.md)
- [Influential Citations Concept](references/influential_citations_concept.md)
