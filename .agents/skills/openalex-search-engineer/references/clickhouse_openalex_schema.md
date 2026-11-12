# Local ClickHouse OpenAlex Table Schema

OpenAlex has a complete dump materialized locally in ClickHouse containing 569 million works and 337 million authors.

---

## 1. Core Tables

| Table | Approx. Records | Description and Optimal Use |
|---|---|---|
| `openalex.works_flat` | 569,000,000 | Global catalog of all scholarly publications worldwide |
| `openalex.works_academic_all` | 1,652,927 | Publications with authors affiliated with institutions in Mexico |
| `openalex.authors` | 337,000,000 | Normalized authors with ORCID, metrics, and canonical affiliation |
| `openalex.institutions` | 110,000 | Universities and research centers with ROR identifier |
| `openalex.sources` | 250,000 | Journals, repositories, and publishers |
| `openalex.topics` | 4,500 | Hierarchical topics from the OpenAlex Topics v5.0 model |

---

## 2. Strict Rule: Prohibition of Direct JOINs

Due to the massive size of the tables ($> 500\text{M}$ records), **do not formulate queries with direct `JOIN` clauses in ClickHouse without prior authorization**.
* For queries on authors in Mexico $\to$ Query the materialized table `works_academic_all` directly.
* For text searches on authors $\to$ Use `positionCaseInsensitiveUTF8(display_name, 'term') > 0` on `authors`.
