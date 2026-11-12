# Data Schema: Authors and Researchers of Mexico in ClickHouse

## 1. Table `rag.authors_seed_mexico` (2,572,943 records)
Unified catalog of authors associated with Mexico in OpenAlex with full JSON metadata:
- `id` (String): Canonical URI (`https://openalex.org/A...`).
- `display_name` (String): Primary reported name.
- `orcid` (String): Normalized ORCID link.
- `raw_data` (String JSON): Complete OpenAlex object containing:
  - `works_count` (Int): Total publication output of the author.
  - `cited_by_count` (Int): Total cumulative citations.
  - `summary_stats.h_index` (Int): Calculated h-index.
  - `last_known_institutions` (Array): Most recent affiliated institution with ROR.
  - `topics` (Array): Thematic areas and specialization subfields.

## 2. Table `rag.academics_all` (431,697 records)
Academic registry with resolution of institutional departments and SNII levels:
- `id` (String): Canonical identifier.
- `name` (String): Full name.
- `institution` (String): Affiliated institution.
- `dependency` (String): Faculty, center, or institute (e.g., `Facultad de Medicina`).
- `subdependency` (String): Internal department or division.
- `snii_level` (String): Official SNII level (`Candidato`, `I`, `II`, `III`, `Emérito`).
- `paper_count` (UInt32): Number of publications.
- `citation_count` (UInt32): Number of citations.
