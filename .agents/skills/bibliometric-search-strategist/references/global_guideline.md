# Application Guide to the GLOBAL (ISSI) Checklist

Based on: International Society for Scientometrics and Informetrics (ISSI) / ScholCommLab (Sugimoto, C. R., Larivière, V., Haustein, S., Vanderbilt, et al., 2023–2024). *GLOBAL: Guidance List for repOrting Bibliometric AnaLyses*.

---

## 1. Foundations and Need in Scientometrics

Unlike medical systematic reviews (designed under PRISMA to evaluate individual clinical trials and pharmacological meta-analyses), scientometric and bibliometric studies analyze **macroscopic structures of science**, collaboration dynamics, citation lineages, and research fronts.

The **GLOBAL** guideline emerged from the consensus of the international scientometrics academic community to overcome the reproducibility crisis in bibliometric studies, establishing an explicit standard for reporting how a corpus is delineated, how data are cleaned, and how network algorithms are parameterized.

---

## 2. The 7 Domains of the GLOBAL Checklist

### Domain 1: Theoretical Rationale and Research Questions
- **Problem Delineation:** Epistemological justification of the field or topic under study.
- **Scientometric Scope:** Clear specification of whether the study is evaluative (performance indicators), relational (science mapping of networks), or longitudinal (temporal trajectories).

### Domain 2: Information Sources and Temporal Snapshot
- **Selected Databases:** Explicitly declare the queried platforms (OpenAlex, Web of Science Core Collection, Scopus, PubMed, Dimensions).
- **Snapshot and Query Date:** Exact date and time zone of data extraction. Because databases such as OpenAlex, Scopus, and WoS update citations and indexing daily, the exact timestamp is indispensable for replicability.
- **Edition and Subscription:** Exact indexes queried (e.g., SCIE, SSCI, AHCI, ESCI in WoS) to prevent discrepancies caused by differing institutional subscriptions.

### Domain 3: Corpus Delineation (Field Delineation)
- **Complete Search String:** Publish the literal, exact syntax used in each database, including field tags (`TS=`, `TITLE-ABS-KEY()`, `[tiab]`).
- **Delineation Approach:** Indicate whether delineation was purely lexical (keywords/Boolean operators), citation-based (bibliographic coupling, co-citation clusters), or hybrid (lexical core + network expansion).
- **Term Justification:** Procedure for selecting keywords (MeSH/Emtree thesauri, Topics, or iterative *Pearl Growing*).
- **Document and Temporal Limits:** Explicit justification of the publication year range (`PY`) and included document types (`DT=Article/Review`).

### Domain 4: Data Cleaning and Entity Disambiguation
- **Deduplication:** Cross-database duplicate detection protocol (DOI normalization, title/year matching).
- **Author Disambiguation:** Algorithms or persistent identifiers used to resolve homonyms (ORCID, OpenAlex Author IDs, Scopus Author ID).
- **Institutional Harmonization:** Normalization of organizational variants via controlled vocabularies (ROR codes, university sub-units).
- **Keyword Thesaurus:** Merging of synonyms, lemmas, and acronyms, and removal of stopwords or generic methodological terms.

### Domain 5: Selected Indicators and Metrics
- **Performance Indicators:** Publication volume ($P$), total citations ($C$), citations per paper ($C/P$), field-normalized citations (FWCI / CNCI), excellence decile (Top 10%).
- **Relational Indicators:** Full counting vs. fractional counting (*fractional counting*, Perianes-Rodriguez et al., 2016) for co-authorship and bibliographic coupling.
- **Similarity Normalization:** Specification of the association function used: *Association Strength* (Van Eck & Waltman), Salton's Cosine, Jaccard, or Equivalence Index.

### Domain 6: Algorithms, Software, and Parameters
- **Software Tools:** Exact names and versions of tools used (VOSviewer, Bibliometrix in R, KnoMap, SciMAT, Gephi, Python NetworkX).
- **Minimum Thresholds:** Minimum occurrence frequency for nodes (keywords $\ge n$, minimum citations $\ge c$).
- **Clustering Algorithm and Resolution:** Community partitioning algorithm (Leiden, Louvain, Infomap) and modular resolution parameter ($\gamma$).

### Domain 7: Open Science and Data/Code Availability
- **Data Availability:** Public repository (Zenodo, OSF, Figshare, GitHub) hosting the canonical metadata file (Parquet, CSV, RIS).
- **Reproducibility Scripts:** Documented source code with fixed seeds (`random_state=42`) so any researcher can regenerate the networks and tables.
