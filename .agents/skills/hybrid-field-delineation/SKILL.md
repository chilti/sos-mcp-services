---
name: hybrid-field-delineation
description: Discipline-agnostic, Workspace-First (`./`) hybrid scientific field delineation pipeline (Phase 0->5): bilingual ~100% recall strategy with clean-room OpenAlex/WoS/Scopus/PubMed query transpilation & manual UI export links, 4-level deduplication (DOI/PMID/Title+Year/bilingual semantic), Open-Source Abstract Recovery Cascade (OpenAlex/Semantic Scholar/Europe PMC/PubMed), stratified S+/S- contrastive OOF calibration & RRF scoring, intrinsic-dimension UMAP(d_ID -> 2D) + multi-resolution Leiden 3-zone triage with Cluster-Aware Active Seeding, Agent-as-a-Judge Gray Zone adjudication + 1-hop Snowballing, and Horvitz-Thompson blind audit. Outputs standardized `./corpus.parquet` compatible with all TlachIA / KnoMap / SOM downstream skills, plus standalone English visual reports and an incremental HTML dashboard in `./reports/`. Respond in the user's language while generating English reports and figures by default.
metadata:
  python: ">=3.10"
  workspace_output: "./corpus.parquet"
---
# Hybrid Scientific Field Delineation

> **Language Rule:** Respond and explain in the user's language; generated HTML reports, Plotly/PNG figures, and PRISMA-S/GLOBAL manifests default to English.

End-to-end scientometric delineation skill that turns any user-defined scientific domain (`--topic-en` / `--topic-es`, arbitrary time window and geographic scope) into a clean, multi-layered **`./corpus.parquet`** ready for `tlachia-metrics-engine`, `bibliometric-network-analyst`, `topics-research-fronts-intelligence`, and the `SOM` triad.

## 1. Standardized Workspace Layout (`--workdir .`)

All artifacts use **relative workspace paths** inside `--workdir` (default: current directory `./`):

```text
./
├── delineation_config.yaml              # Project topic, time window, geography & thresholds
├── corpus.parquet                       # Canonical 27-column corpus (+ final_corpus_layer: STRICT_CORE | EXTENDED_INTERDISCIPLINARY)
├── corpus_conferences.parquet           # Separated conference proceedings & meeting abstracts
├── delineation/
│   ├── inputs/{wos,scopus,openalex,pubmed}/  # Optional manual clean-room exports dropped by user
│   ├── cache/                           # Persistent embedding & metadata caches
│   ├── fase0_estrategia/                # Topics, Bradford sources, term specificity audit & queries/{global,local}/
│   ├── fase1_corpus/                    # Multi-source union, 4-level dedup & embeddings
│   ├── fase2_scoring/                   # Stratified S+/S- seeds, 5-fold OOF metrics & RRF scores
│   ├── fase3_manifold/                  # UMAP(d_ID), Leiden partitions, cluster cards
│   ├── fase4_llm_snowball/              # Agent-as-a-Judge batch JSONLs + decisions + 1-hop snowball
│   └── fase5_corpus_final/              # Layered splits, Horvitz-Thompson blind audit CSV & key
└── reports/
    ├── fase0_visual_report.html .. fase5_visual_report.html
    ├── hybrid_delineation_dashboard.html  # Incremental Master Dashboard
    ├── fase3_manifold_zones.{html,png}    # UMAP(d_ID -> 2D) topological map
    └── GLOBAL_PRISMA_S_MANIFEST.md
```

## 2. Model & Host-Agent Defaults (Portable Across Agents)

- **Local Model First (`--judge-mode local_llm`, default):** Phase 4 defaults to evaluating `ZONA_GRIS` (`INCLUDE_CORE`, `INCLUDE_PERIPHERY`, `EXCLUDE`) with the user's configured local/OpenAI-compatible LLM (`LM_STUDIO_URL`, default `http://localhost:1234/v1` via `delineation_config.yaml`). Users without a local LLM server can pass `--judge-mode agent` so Phase 4 prepares compact cluster-coherent `batch_*.jsonl` packages for adjudication by the active host agent (Antigravity, Claude, Codex).
- **Local-First Embeddings (`--embed-backend auto`):** Phase 1 uses the configured HTTP embedding server (`embedding_base_url` / `LM_STUDIO_URL`) with `Authorization: Bearer <LLM_API_KEY>`, then locally cached `sentence-transformers` models (`local_files_only=True`), and finally an offline SVD-TFIDF dense fallback.
- **OpenAlex Budget Economy & Zero-ClickHouse Default:**
  - Phase 0 audits term specificity **locally in memory** over the downloaded Pearl-Growing sample (`0` extra `/works` calls; pass `--online-term-audit` only if desired).
  - Phase 0 generates **both** cursor-paginated `openalex_api_broad.json` (`~$0.10–$0.20` USD) **and** `openalex_web_manual.txt` (1-click OpenAlex Web UI URLs + copy-paste queries for free CSV download).
  - ClickHouse local snapshots remain strictly opt-in (`--openalex-cleanroom snapshot` when `CLICKHOUSE_HOST` is configured).

## 3. Execution Sequence (Phase 0 -> Phase 5)

Run scripts from `scripts/` pointing `--workdir .` to the user's project workspace:

### Phase 0: Config Initialization & Clean-Room Strategy
```bash
python scripts/00_build_strategy.py \
  --workdir . \
  --topic-en "Solar Perovskite Cells" \
  --topic-es "Celdas solares de perovskita" \
  --year-from 2014 --year-to 2025 \
  --country "" \
  --biomedical false
```
*(If no local LLM endpoint is active at `LM_STUDIO_URL`, `--llm-mode agent` emits JSON prompts in `./delineation/fase0_estrategia/agent_prompts/` so the host agent supplies the initial facets/topic labels directly.)*

### Phase 1: Multi-Source Clean-Room Harvest, Open Abstract Cascade & 4-Level Dedup
Drop any manual exports from Web of Science (`*.txt`), Scopus (`*.csv`), or OpenAlex Web UI (`*.csv`) into `./delineation/inputs/{wos,scopus,openalex}/`, then run:
```bash
python scripts/01_ingest_enrich.py --workdir . --openalex-cleanroom api
# Or if using manual OpenAlex Web CSV exports in ./delineation/inputs/openalex/:
python scripts/01_ingest_enrich.py --workdir . --openalex-cleanroom manual
```

### Phase 2: Co-Constructed S+/S- Seeds, 5-Fold OOF Calibration & RRF(k=60)
```bash
python scripts/02_seeds_rrf.py --workdir .
```

### Phase 3: UMAP(d_ID -> 2D) Manifold, Multi-Resolution Leiden & 3-Zone Triage
```bash
python scripts/03_manifold_leiden.py --workdir .
```

### Phase 4: Local-LLM / Agent-as-a-Judge Gray Zone Triage & 1-Hop Snowballing
Default (`--judge-mode local_llm`, uses `llm_base_url` + `llm_model`):
```bash
python scripts/04_judge_snowball.py --workdir .
```
Or host-agent batch mode when no local LLM server is available:
```bash
python scripts/04_judge_snowball.py --workdir . --judge-mode agent
# Evaluate batch_*.jsonl -> delineation/fase4_llm_snowball/cache_llm_gris.jsonl, then:
python scripts/04_judge_snowball.py --workdir . --judge-mode agent --finalize
```

### Phase 5: Canonical Export (`./corpus.parquet`), Horvitz-Thompson Audit & Reports
```bash
python scripts/05_audit_and_canonicalize.py --workdir .
```
Downstream `sos-mcp-services` skills can then consume `./corpus.parquet` immediately (and optionally filter by `final_corpus_layer == 'STRICT_CORE'` vs. full peer-reviewed `STRICT_CORE + EXTENDED_INTERDISCIPLINARY`).

## 4. Technical Reference
- [Methodology, Canonical Schema Bridge & OpenAlex Budget Design](references/methodology_and_schema.md)
