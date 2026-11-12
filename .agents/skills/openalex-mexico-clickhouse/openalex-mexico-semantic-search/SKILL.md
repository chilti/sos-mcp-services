---
name: openalex-mexico-semantic-search
description: "Semantic and conceptual search of scientific publications and researchers in Mexico using 768-dimensional nomic vector embeddings in ClickHouse (rag.works_academic_all and rag.academics_all), with automatic disambiguation of domestic authors vs. international collaborators. Respond and label outputs in the user's language."
metadata:
  python: ">=3.10"
  script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex Mexico Semantic Search

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Semantic search based on 768-dimensional vector embeddings (`text-embedding-nomic-ai-nomic-embed-text-v2-moe`) and cosine similarity in ClickHouse over Mexico's scientific corpus.

## Overview

Unlike lexical searches based on exact text matching, this skill enables:
1. **Discovering conceptually related works:** Even if the title does not contain the exact words or is written in English/Spanish (e.g., `"materiales catódicos para baterías de litio"` or `"cathode materials for lithium batteries"` retrieves lithium cuprates and electrochemical models).
2. **Identifying specialist researcher profiles:** Vector search across the critical mass of researchers in Mexico (`rag.academics_all`).
3. **Disambiguating international co-authorship:** Automatically separates researchers affiliated with Mexican institutions (`mexican_affiliated_authors`) from foreign collaborators (`international_collaborators`) in the results, while resolving OpenAlex IDs into human-readable names.
4. **Strict adherence to ZERO JOINs:** All vector retrieval and metadata enrichment runs in sub-seconds via direct columnar scanning and `WHERE id IN (...)`.

## Dependencies

- **Python Environment:** Python 3.10+ (`clickhouse-connect`)
- **CLI Script:** [`scripts/openalex_mexico_cli.py`](scripts/openalex_mexico_cli.py)
- **Embeddings Server:** Local LM Studio (`http://127.0.0.1:1234/v1` on host / `http://172.17.0.1:1234/v1` in Docker container)
- **ClickHouse Tables:** `rag.works_academic_all` (1.37M publications with `embedding_nomic`), `rag.academics_all` (9.1K profiles with `embedding_nomic`), `rag.authors_seed_mexico` (2.57M authors).

## CLI Interface

### 1. Semantic Search of Publications
Retrieves articles conceptually related to a topic in natural language (Spanish or English):
```bash
python scripts/openalex_mexico_cli.py semantic-search \
  --query "materiales catódicos para baterías de litio" \
  --target works \
  --limit 20 \
  --output ./data/articulos_semanticos_litio.json
```

Combinable optional filters:
- `--year-min 2020` / `--year-max 2025`
- `--oa-status diamond` (or `gold`, `hybrid`, etc.)
- `--is-top-10 true`
- `--institution-name "Universidad Nacional Autónoma de México"`

### 2. Semantic Search of Specialist Researchers
Discovers researchers in Mexico whose thematic profile vectorially matches a discipline or problem:
```bash
python scripts/openalex_mexico_cli.py semantic-search \
  --query "procesamiento de lenguaje natural y modelos de lenguaje" \
  --target authors \
  --limit 15 \
  --output ./data/expertos_pln_mexico.json
```

### 3. Interpretation of Authors and Co-authorship
In the JSON results returned for each publication:
- `authors_disambiguated.mexican_affiliated_authors`: Contains authors who hold formal affiliation or publication history in Mexican institutions (UNAM, IPN, UAM, Cinvestav, etc.).
- `authors_disambiguated.international_collaborators`: Contains co-authors affiliated with foreign universities who collaborated on the study.
- `cosine_distance`: Measures angular distance (lower value = higher conceptual closeness).
- `semantic_similarity`: Normalized measure between 0.0 and 1.0 (`1.0 - cosine_distance`).

## Guidelines for the Agent (LLM)

1. **When the user asks about complex concepts or open-ended questions:** Use `semantic-search` instead of a strict keyword matching search (`search-works`).
2. **When mentioning Mexican researchers from a paper:** Always inspect `mexican_affiliated_authors` to report national specialists and avoid attributing Mexican affiliation to international co-authors.
3. **For quantitative global rankings by publication volume in a topic:** Complement with `top-entities --by authors` from the [`openalex-mexico-aggregations`](../openalex-mexico-aggregations/SKILL.md) skill.

## References

- [Semantic Search Architecture with Vector Embeddings](references/semantic_search_embeddings.md)

## Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Treating foreign co-authors as Mexican researchers**  
  In a medical physics article with 30 authors from 10 countries and 1 author from UNAM, listing all 30 as national researchers.  
  **Solution:** Always inspect the structured field `authors_disambiguated.mexican_affiliated_authors`.
- ❌ **Anti-pattern 2: Using lexical search for broad interdisciplinary concepts**  
  Attempting to cover `"regenerative agriculture and climate change"` with dozens of `LIKE '%...%'` filters.  
  **Solution:** Use `semantic-search --query "..."` leveraging the 768d nomic embeddings precomputed in ClickHouse.
- ❌ **Anti-pattern 3: Violating File-Output First**  
  Omitting `--output`, causing the JSON with abstracts and partial vectors to dump to the terminal.  
  **Solution:** Always write the result to a structured file (`--output ./data/articulos_semanticos.json`).
