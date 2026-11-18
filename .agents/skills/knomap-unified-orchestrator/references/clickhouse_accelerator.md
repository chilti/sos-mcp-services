# Optional Local Accelerator: OpenAlex ClickHouse Snapshot (`Fast-Path`)

All skills and master templates in the KnoMap / TlachIA ecosystem are **fully autonomous and portable**: by default they harvest directly from the official OpenAlex REST API (`openalex-harvester`) and operate **Workspace-First** over `./corpus.parquet`.

However, when the user works inside an environment with access to the **local OpenAlex ClickHouse snapshot**, the workflow automatically enriches and accelerates execution without modifying the scientific provenance (OpenAlex) reported in manuscripts.

---

## 1. Two-Tier Execution Policy (`Portable Default` vs. `ClickHouse Fast-Path`)

| Stage / Task | Tier 1: Autonomous Default (No ClickHouse Required) | Tier 2: Optional Local ClickHouse Accelerator (When Configured) |
|---|---|---|
| **Field Delineation (`bibliometric-search-strategist`)** | Produces OpenAlex API boolean/filter queries (`openalex_query.txt`), WoS, Scopus, PubMed, and GLOBAL audit. | Also emits ZERO-JOIN ClickHouse SQL (`clickhouse_query.sql`) when `CLICKHOUSE_HOST` is set or `--include-clickhouse` is passed. |
| **Global Corpus Harvesting (`./corpus.parquet`)** | [`openalex-harvester`](../../openalex-harvester/SKILL.md) cursor-paginated REST extraction into `./corpus.parquet`. | [`openalex-search-engineer`](../../openalex-search-engineer/SKILL.md) columnar extraction over `rag.works_flat` (`464M+`–`569M` works, **ZERO JOINs**). |
| **Mexican National / SNII Studies** | [`openalex-harvester`](../../openalex-harvester/SKILL.md) filtered by country `MX` / ROR. | [`openalex-mexico-clickhouse`](../../openalex-mexico-clickhouse/SKILL.md) over `rag.works_academic_all` (`1.65M` Mexican works + SNII registry + 768d Nomic semantic search). |
| **Citation Snowballing (`deep-literature-researcher`)** | Resolves seeds and backward/forward citations via OpenAlex REST API (`api.openalex.org/works`). | Queries `CLICKHOUSE_HOST` (`CLICKHOUSE_TABLE`, default `rag.works_flat`) first when `CLICKHOUSE_HOST` is explicitly configured, falling back to OpenAlex API for missing IDs. |
| **Research Fronts Fallback (`topics-research-fronts-intelligence`)** | Primary: reads `./corpus.parquet` directly; Standalone fallback: queries OpenAlex API (`api.openalex.org/works`). | Standalone fallback uses ClickHouse `rag.works_flat` only when `CLICKHOUSE_HOST` (or `--ch-host`) is explicitly provided and reachable; otherwise uses OpenAlex API seamlessly. |

---

## 2. Capabilities Unlocked Only by the Local ClickHouse Snapshot

When available (`CLICKHOUSE_HOST` set in environment and optional accelerator skills active), the snapshot adds four distinct advantages:

1. **Massive Extraction Without HTTP Rate Limits:** Harvests `50,000–500,000+` works with full `referenced_works`, `all_country_codes`, `keywords`, and `fwci` in seconds instead of batched cursor HTTP requests.
2. **Exact Background Denominators ($AI$, $\text{F-measure}$, $DShareC$, $CShareD$):** Computes exact world, national, or subfield totals directly in SQL (`count()`) so specialization indices (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2026) do not require downloading the entire OpenAlex universe.
3. **Bilingual Semantic Search (768d Nomic Vectors) & SNII Linkage:** Enables conceptual retrieval beyond exact keywords and authoritative disambiguation against Mexico's official SNII researcher registry.
4. **Corpus-Scale Retrospective Reference Resolution:** Speeds up co-citation and citation snowballing over pre-indexed `referenced_works` arrays under the strict **ZERO JOINs** rule.

---

## 3. Environment Activation (Opt-In)

External users do not need to set any ClickHouse variables; scripts automatically default to OpenAlex REST API. Internal users with cluster access enable the fast-path by configuring:

```bash
export CLICKHOUSE_HOST="<your-clickhouse-host>"
export CLICKHOUSE_PORT="8124"
export CLICKHOUSE_USER="<user>"
export CLICKHOUSE_PASSWORD="<password>"
export CLICKHOUSE_DATABASE="rag"
```

> **Manuscript Provenance Rule:** Even when harvested via ClickHouse, cite the scholarly index as **OpenAlex** (specifying the snapshot cutoff date and exact search query) in the article prose; reserve ClickHouse connection parameters strictly for technical reproducibility appendices or logs.

