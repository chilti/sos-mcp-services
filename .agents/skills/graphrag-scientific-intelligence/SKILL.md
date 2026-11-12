---
name: graphrag-scientific-intelligence
description: Hybrid GraphRAG queries combining 768-dimensional dense vector semantic search (Nomic), co-authorship/citation network exploration, and official SNII Registry verification. Respond and label outputs in the user's language.
---

# GraphRAG Scientific Intelligence

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

This skill orchestrates hybrid **GraphRAG** queries (knowledge graph and dense vector retrieval-augmented generation) across the ecosystem's scientific infrastructure.

## 1. Ecosystem Operational Workflow (Workspace-First)

1. **Dense Vector Semantic Retrieval (768d Nomic):**
   - Delegate to `openalex-mexico-semantic-search` (`openalex_mexico_cli.py semantic-search`) to retrieve scholarly works and researcher profiles via conceptual cosine similarity without relying on exact lexical matching.
2. **Identity Resolution and SNII Registry Verification:**
   - Delegate to `snii-identity-resolver` (`snii_resolver_cli.py`) and `openalex-mexico-author-search` to link each author node with their official SNII level, ORCID, and institutional ROR.
3. **Relational Subgraph Construction in the Workspace:**
   - Once the retrieved corpus is exported to `./corpus.parquet`, delegate to `bibliometric-network-analyst` (`biblio_network_cli.py`) and `topics-research-fronts-intelligence` (`build_bibliometric_fronts.py`) to extract the Leiden community structure, betweenness centralities, and structural bridges across research groups.
