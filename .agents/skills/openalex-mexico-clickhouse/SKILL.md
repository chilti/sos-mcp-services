---
name: openalex-mexico-clickhouse
description: >-
  Master analytical engine and orchestrator for Mexico's scientific production in ClickHouse (1.65M works in rag.works_academic_all, 2.57M authors in rag.authors_seed_mexico, 456K institutions in rag.institutions_seed_mexico). Orchestrates Open Access aggregations (Diamond vs Gold APC), USD expenditure, author search and disambiguation with the SNII registry, ROR institutional catalog, 768d nomic semantic vector search, and interactive visualization, under the strict ZERO JOINs rule and File-Output First principle. Respond and label outputs in the user's language.
metadata:
  python: ">=3.10"
  script: "shared_scripts/openalex_mexico_cli.py"
---

# OpenAlex Mexico ClickHouse: National Analytical Engine and Orchestrator

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Overview and Purpose

This skill acts as the **central orchestrator** for querying, extracting, and analyzing Mexican scientific production hosted in the UNAM ClickHouse cluster.

The `rag` database hosts the complete universe of research from Mexico structured in massive denormalized columnar tables:
* **`rag.works_academic_all` (~1.65 million records):** Works with Mexican affiliation, including normalized impact metrics (FWCI, percentile, Top 10%, Top 1%), Open Access typology (6 OA routes, paid and list APC in USD), Sustainable Development Goals (SDGs 1–17), thematic taxonomy (Domain, Field, Subfield, Topic), and 768-dimensional `nomic` vector embeddings.
* **`rag.authors_seed_mexico` (~2.57 million records):** Catalog of authors with production in Mexico, citation metrics, h-index, and Hispanic name variants.
* **`rag.academics_all` (~431 thousand records):** Researchers cross-referenced with the Official SNII Registry, validity status, and institutional affiliation.
* **`rag.institutions_seed_mexico` (~456 thousand records):** National institutional catalog with ROR identifiers, name variants, and acronyms (UNAM, IPN, UAM, Cinvestav, etc.).

---

## 2. Dependencies and Value Chain

* **Execution Environment:** `python` with `clickhouse-connect` library.
* **Canonical CLI Script:** `shared_scripts/openalex_mexico_cli.py` (multi-command engine with built-in security validation).
* **Connection Parameters:** ClickHouse server configured via environment variables (`CLICKHOUSE_HOST=10.90.0.87`, `CLICKHOUSE_PORT=8124`, `CLICKHOUSE_DATABASE=rag`).
* **Specialized Skills in the Suite:**
  * [`openalex-mexico-query-architect`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-query-architect/SKILL.md): Safe SQL statement validator and advisor.
  * [`openalex-mexico-aggregations`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-aggregations/SKILL.md): OA route aggregations, APC USD expenditure, and time series.
  * [`openalex-mexico-works-search`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-works-search/SKILL.md): Publication extraction via complex filters.
  * [`openalex-mexico-author-search`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-author-search/SKILL.md): Researcher disambiguation and SNII level lookup.
  * [`openalex-mexico-institutions`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-institutions/SKILL.md): ROR mapping and institutional catalog.
  * [`openalex-mexico-semantic-search`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-semantic-search/SKILL.md): Vector semantic search (768d nomic embeddings).
  * [`openalex-mexico-visualizer`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-visualizer/SKILL.md): Interactive Plotly dashboards and PyVis networks.

---

## 3. Golden Rule: Strict Prohibition of JOINs

> [!CAUTION]
> In the UNAM analytical infrastructure, **formulating statements with direct `JOIN`s in ClickHouse is strictly prohibited**.
> Any query containing the `JOIN` keyword will be automatically intercepted and rejected with an error by `openalex_mexico_cli.py`.

### Why Are JOINs Unnecessary?
Because the `rag.works_academic_all` table is already completely denormalized at the document level. Instead of joining tables:
* **To filter by institution:** Use `has(institution_rors, 'https://ror.org/01tmp8f25')`.
* **To filter by author:** Use `arrayExists(x -> positionCaseInsensitiveUTF8(x, 'Apellido Nombre') > 0, author_names)`.
* **For thematic classifications:** Filter directly on the `domain`, `field`, `subfield`, or `topic` columns.

---

## 4. Canonical CLI Subcommands (File-Output First)

All commands must be executed specifying a mandatory `--output <path>` and explicit limits (pass `--lang es` if Spanish output messages/instructions are desired; defaults to `--lang en`):

### 1. Scientometric Aggregations (`aggregate`)
```bash
python shared_scripts/openalex_mexico_cli.py aggregate \
  --group-by "oa_status" \
  --filter "publication_year >= 2020" \
  --output ./data/acceso_abierto_mexico.json
```

### 2. Scientific Publication Search (`search-works`)
```bash
python shared_scripts/openalex_mexico_cli.py search-works \
  --query "artificial intelligence in education" \
  --year-min 2020 --year-max 2025 \
  --is-top-10 true \
  --limit 100 \
  --output ./data/ia_educacion_top10.json
```

### 3. Researcher Search and Disambiguation (`search-authors`)
```bash
python shared_scripts/openalex_mexico_cli.py search-authors \
  --name "Gorbea Portal" \
  --institution "UNAM" \
  --limit 10 \
  --output ./data/investigador_desambiguado.json
```

### 4. Ranking Leading Entities in a Topic (`top-entities`)
```bash
python shared_scripts/openalex_mexico_cli.py top-entities \
  --query "Vaccines" \
  --by "institutions" \
  --limit 20 \
  --output ./data/top_instituciones_vacunas.json
```

### 5. Vector Semantic Search (`semantic-search`)
```bash
python shared_scripts/openalex_mexico_cli.py semantic-search \
  --query "soberanía alimentaria y maíces nativos" \
  --target works \
  --limit 50 \
  --output ./data/busqueda_semantica_maiz.json
```

### 6. SQL Query Validation (`validate-query`)
```bash
python shared_scripts/openalex_mexico_cli.py validate-query \
  --query "SELECT title, publication_year FROM rag.works_academic_all WHERE has(institution_rors, 'https://ror.org/01tmp8f25') LIMIT 10" \
  --output ./data/reporte_validacion.json
```

---

## 5. Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Formulating queries with `JOIN` statements**  
  Attempting to join `rag.works_academic_all` with `rag.authors_seed_mexico` using `JOIN`. The ClickHouse engine degrades performance, and `openalex_mexico_cli.py` aborts execution with a `ValueError`.  
  **Solution:** Query the pre-materialized native array columns (`author_names`, `institution_rors`).
- ❌ **Anti-pattern 2: `SELECT *` queries without `--limit` or `--output`**  
  Attempting to extract hundreds of thousands of rows without pagination or limits, saturating server memory and the console.  
  **Solution:** Always specify a deliberate `--limit` (e.g., 50, 100) and write to a structured file via `--output`.
- ❌ **Anti-pattern 3: Case-sensitive or diacritic-naive name searches**  
  Using `author_name = 'Jose Lopez'` or `LIKE '%Lopez%'`. Omitting accents or capitalization variations misses up to 60% of records in Hispanic names.  
  **Solution:** Use `positionCaseInsensitiveUTF8(x, 'López') > 0` or the `search-authors` subcommand, which normalizes diacritics automatically.
- ❌ **Anti-pattern 4: Counting international co-authors as Mexican researchers**  
  Assuming that all authors of a Mexican paper belong to domestic institutions. A multi-center paper may have 20 foreign co-authors and 1 Mexican author.  
  **Solution:** Disambiguate authors using `rag.academics_all` or by filtering authors linked to Mexican RORs.
- ❌ **Anti-pattern 5: Violating File-Output First (Storing in `/tmp/`)**  
  Saving results in global operating system temporary directories that may be deleted or inaccessible.  
  **Solution:** Always save results inside the current workspace (`./data/` or in the artifact's `scratch/` folder).

---

## 6. Technical References

- [OpenAlex Mexico CLI Engine](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/shared_scripts/openalex_mexico_cli.py)
- [Query Architect (ZERO JOINs Guardian)](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-query-architect/SKILL.md)
- [Aggregations Engine](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-aggregations/SKILL.md)
- [Canonical Scientific Skills Design Standard](file:///mnt/expansion/desplegados/sos-mcp-services/docs/estandar_diseno_skills_cientificas.md)
