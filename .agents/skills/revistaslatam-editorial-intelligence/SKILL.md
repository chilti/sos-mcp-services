---
name: revistaslatam-editorial-intelligence
description: Comprehensive dictionary and reference for Revistas Latam (Ibero-American Journal Catalog, editorial evaluation, DOAJ/SciELO/Redalyc/Latindex 2.0 indexing checklist, Diamond Open Access, and multilingualism). Respond and label outputs in the user's language.
---

# Skill: Revistas Latam Editorial Intelligence

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Scope and Ibero-American Editorial Evaluation
Activated for scientometric assessments of scientific journals, Diamond Open Access policies (\$0 APC), indexing status, and international visibility across Latin America, the Caribbean, Spain, and Portugal.

---

## 2. Indicators and Indexing Checklist
1. **Diamond Open Access vs. Commercial APC:**
   * Monitoring full zero-fee access (no charges to authors or readers) versus the commercial APC model.
2. **International and Regional Indexing Matrix:**
   * Global indexes: Scopus (SJR, CiteScore, Quartiles Q1–Q4), Web of Science (JCR, ESCI).
   * Regional quality indexes: DOAJ (Directory of Open Access Journals with DOAJ Seal), SciELO (Scientific Electronic Library Online), Redalyc (Network of Scientific Journals from Latin America and the Caribbean), Latindex Catalog 2.0 (compliance with 38 editorial quality criteria), Dialnet, MIAR, AmeliCA.
3. **Internationalization and Editorial Quality Metrics:**
   * Editorial endogamy: Percentage of authors and peer reviewers external to the publishing institution.
   * Internationalization of the Editorial Board and contributing authors.
   * Editorial workflow: Average peer-review turnaround days, acceptance/rejection rate, and publication periodicity.
4. **Multilingualism and Self-Archiving Policies:**
   * Distribution of articles by language (Spanish, Portuguese, English).
   * Self-archiving and copyright policies registered in Sherpa Romeo and Diadorim (Green, Blue, Yellow policies, etc.).

---

## 3. Data Sources and Microservice
* `revistaslatam-mcp` (Port 8013): Editorial query and journal metadata microservice.
* `pipeline_revistaslatam/`: Local databases of journals, publishers, and indexing cross-references.
