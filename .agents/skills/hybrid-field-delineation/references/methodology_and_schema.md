# Hybrid Field Delineation — Methodology, Canonical Bridge & Budget Design

## 1. Seven-Stage Architecture (Modes A / B)

1. **Phase 0 (`00_build_strategy.py`):** Decomposes any user topic (`--topic-en`, `--topic-es`) into discovery facets, queries OpenAlex `/topics` and Bradford `/sources` without `domain_name` cutoffs, pulls MeSH descriptors when `is_biomedical: true`, performs bilingual differential Pearl Growing (`Log-Odds` Dirichlet), enforces short-acronym proximity rules ($\le 3$ characters $\rightarrow$ `COUPLE_PROXIMITY`) and wildcard safety ($\ge 4$ stem chars), and compiles synchronized queries for **OpenAlex Web UI (manual 1-click links)**, **OpenAlex REST API (`cursor=*`)**, **PubMed**, **Scopus**, **Web of Science**, and optional **ClickHouse SQL (`ZERO JOINs`)**.
2. **Phase 1 (`01_ingest_enrich.py`):** Harvests and normalizes multi-database clean-room inputs (`WoS`, `Scopus`, `PubMed`, `OpenAlex API/manual/snapshot`), applies geographic anti-false-positive disambiguation (when a country filter is configured), recovers missing abstracts via an **Open-Source Recovery Cascade** (Semantic Scholar Graph Batch API `400 DOIs/POST` + Europe PMC/OpenAlex DOI fallback), computes `1024d` (or local `sentence-transformers`) semantic embeddings with SHA-1 caching, and runs **4-level hybrid deduplication** (`DOI -> PMID -> Title+Year -> Bilingual Semantic Cosine >= 0.95`).
3. **Phase 2 (`02_seeds_rrf.py`):** Co-constructs stratified positive (`S+`) and hard-negative (`S-`) seed pools from structural signals (`topic_tier` including MeSH/Source mapping, free title/body hits, homonym flags), runs 5-fold OOF calibration (`PR-AUC`, `ROC-AUC`, `FPR@Rec90`, `Abstract vs. No-Abstract Gap`), and computes continuous TF-IDF tie-broken `RRF(k=60)` fusion.
4. **Phase 3 (`03_manifold_leiden.py`):** Estimates intrinsic dimension `d_ID` via `TwoNN` + Levina-Bickel `MLE_p95`, projects `UMAP(d_ID, cosine)`, hierarchically projects `UMAP(d_ID -> 2D)` for 1:1 visual alignment, optimizes multi-gamma `Leiden` partitioning (`0%` orphans), performs **2-Pass Cluster-Aware Active Seeding** for under-seeded communities (`ns < 5`), and rescues high-margin lexical outliers from `RED ZONE` back to `GRAY ZONE`.
5. **Phase 4 (`04_judge_snowball.py`):** Evaluates `100%` of `GRAY ZONE` works via Host-Agent (`--judge-mode agent`, default) or local LLM (`--judge-mode local_llm`) enriched with Top-3 Green Zone semantic neighbors, runs Cohen's $\kappa$ calibration check when human pilot annotations exist, and applies 1-hop citation snowballing ($k \ge 2$ Green links + positive margin).
6. **Phase 5 (`05_audit_and_canonicalize.py`):** Separates conference proceedings/abstracts (`./corpus_conferences.parquet`), removes retracted/paratext records, infers missing `language` and scientific `domain` deterministically (`0` blind domains), generates stratified Horvitz-Thompson blind audit packages (`n=360`), and exports canonical **`./corpus.parquet`** matching `shared/canonical_schema.py` (`CANONICAL_COLUMNS`) plus provenance layers (`final_corpus_layer`).

## 2. Canonical Bridge (`./corpus.parquet`)

Downstream skills in `sos-mcp-services` (`tlachia-metrics-engine`, `bibliometric-network-analyst`, `topics-research-fronts-intelligence`, `classical-bibliometrics-laws`, `open-access-monitor`, `sdg-impact-intelligence`, `som-*`) read `./corpus.parquet` expecting the 27 columns defined in `shared/canonical_schema.py`:

| Canonical Column | Populated From Delineation Corpus | Notes |
|---|---|---|
| `id` | `oa_id` (or `work_uid` fallback) | Normalized `W...` or UID |
| `doi`, `pmid`, `pmcid` | `doi_norm`, `pmid_norm`, `pmcid` | Normalized identifiers |
| `title`, `abstract` | `title`, `abstract_final` | Post open-cascade recovery |
| `publication_year` | `publication_year` (`Int64`) | Year filter applied |
| `journal_name` | `source_venue` | Source / journal display name |
| `cited_by_count`, `fwci`, `is_oa`, `oa_status`, `apc_paid_usd` | Respective numeric/bool fields | Type-cast to canonical pandas dtypes |
| `author_names`, `countries`, `keywords`, `topics`, `references` | Parsed lists (`list[str]`) | Converted from delimited strings/arrays |
| `source_harvester` | `sources_list` | e.g., `oa_cleanroom_api|pubmed_broad|wos_cleanroom` |
| *Extra Audit Columns* | `final_corpus_layer`, `zona_triaje`, `margin_score`, `rrf_score`, `domain`, `field`, `subfield`, `language`, `doc_type_norm` | Preserved for stratified filtering downstream |
