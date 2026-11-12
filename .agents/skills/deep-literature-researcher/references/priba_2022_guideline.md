# PRIBA Reporting Guideline (Preferred Reporting Items for Bibliometric Analysis)

Based on: Koo, M., & Lin, S. C. (2022). *Preferred reporting items for bibliometric analysis (PRIBA): A proposal for reporting bibliometric reviews*. Journal of Medical Sciences, 42(3), 115-123.

---

## 1. Methodological Context

**PRIBA** was proposed by the scientometric community as a direct, formal adaptation of **PRISMA 2020** tailored to bibliometric reviews and science mapping.

Unlike traditional medical PRISMA (designed to evaluate clinical intervention biases and statistical meta-analysis), PRIBA reformulates items to audit the structural validity of studies based on bibliographic data:

---

## 2. Core Components of PRIBA

### A. Research Question and Unit of Analysis Definition
* Clear specification of the unit of analysis (authors, documents, journals, countries, institutions, or keywords/concepts).
* Declaration of the relational analysis type:
  * **Co-occurrence:** Term mapping and conceptual fronts.
  * **Co-authorship:** Social networks and institutional/geographical collaboration.
  * **Co-citation:** Foundational intellectual structure and invisible colleges.
  * **Bibliographic Coupling:** Active contemporary research fronts.
  * **Direct Citation:** Genealogical lineages of ideas.

### B. Delineation and Data Collection
* Exact query string with field tags and proximity operators.
* Record of access date and database version (OpenAlex, WoS, Scopus).
* Mapping of the quantitative flow: raw records retrieved $\to$ duplicates removed $\to$ included records with complete metadata.

### C. Normalization and Similarity Metrics
* Declaration of the relational normalization method:
  * **Association Strength** (Van Eck & Waltman, recommended for spatial clustering).
  * **Salton's Cosine** (suitable for international bilateral affinity).
  * **Jaccard Index** or **Equivalence Index**.
* Declaration of the counting method: **full counting** vs. **fractional counting**.

### D. Visualization, Algorithms, and Robustness
* Community partitioning algorithm (Leiden, Louvain, Infomap) and resolution parameters ($\gamma$).
* Software used and versions (VOSviewer, Bibliometrix, KnoMap, Python).
* Identification and discussion of linguistic coverage or database indexing biases.
