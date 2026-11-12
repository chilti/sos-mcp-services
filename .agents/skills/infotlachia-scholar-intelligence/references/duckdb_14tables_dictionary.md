# Table Dictionary for `analytics_cache.duckdb`

The Info TlachIA analytical data warehouse is managed in DuckDB (`analytics_cache.duckdb`, 5.9 GB) for ultra-low-latency queries ($< 10\text{ms}$).

---

## 1. The 14 Consolidated Tables

| Table | Records | Analysis Level | Key Columns |
|---|---|---|---|
| `investigador_total` | 90,000 | Researcher (Consolidated) | `academic_name`, `is_snii`, `num_documents`, `citations`, `fwci_avg`, `pct_top_10`, `h_index`, `apc_paid_usd` |
| `investigador_annual` | 409,000 | Researcher $\times$ Year | Annual time series of output and impact per author |
| `investigador_recent` | 43,000 | Researcher (Last 3 years) | Recent impact dynamics and moving-window citations |
| `institucion_total` | 3,000 | Institution and Department | Cumulative totals per university and faculty/department |
| `institucion_annual` | 63,000 | Institution $\times$ Year | Institutional annual time series |
| `papers_profesor` | 1,250,000 | Documents per Researcher | `academic_name`, `doi`, `title`, `year`, `citations`, `topics` |
| `papers_institucion` | 4,220,000 | Documents per Institution | Documents indexed per university |
| `topics_investigador` | 377,000 | Researcher Topics | Thematic breakdown of authors |
| `topics_institucion` | 223,000 | Institutional Topics | Thematic specialization per faculty/department |
| `keywords_investigador`| 3,730,000 | Author Keywords | Frequent keywords per researcher |
| `keywords_institucion` | 1,110,000 | Institutional Keywords | Keywords per academic department |
| `thematic_evolution_investigador` | 819,000 | Topic Evolution (Author) | Temporal migration of topics per author |
| `thematic_evolution_institucion` | 949,000 | Topic Evolution (Inst) | Institutional thematic trajectory |
| `umap_investigadores` | 18,700 | 2D/3D Coordinates | Topological positioning of SNII researchers |

---

## 2. Canonical Filtering Columns

* `db_level`: `'NATIONAL'`, `'INSTITUTION'`, `'ENTITY'`, `'RESEARCHER'`.
* `db_institution_name`: Canonical institution name (e.g. `'UNIVERSIDAD NACIONAL AUTONOMA DE MEXICO (UNAM)'`).
* `db_entity_name`: Name of the faculty, school, or research institute (e.g. `'FACULTAD DE CIENCIAS'`).
* `db_academic_name`: Normalized researcher name (`'APELLIDO PATERNO MATERNO, NOMBRES'`).
