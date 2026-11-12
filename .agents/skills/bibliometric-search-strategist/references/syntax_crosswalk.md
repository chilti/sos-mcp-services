# Bibliographic Syntax Matrix and Operator Crosswalk

Comprehensive syntax comparison for transpilation across Web of Science, Scopus, PubMed, and ClickHouse (`rag.works_academic_all`).

---

## 1. Boolean Operator and Special Character Mapping

| Function | Web of Science | Scopus | PubMed | ClickHouse SQL |
|---|---|---|---|---|
| **Logical AND** | `AND` | `AND` | `AND` | `AND` |
| **Logical OR** | `OR` | `OR` | `OR` | `OR` |
| **Logical NOT** | `NOT` | `AND NOT` | `NOT` | `AND NOT` |
| **Grouping** | `( ... )` | `( ... )` | `( ... )` | `( ... )` |
| **Exact phrase** | `"phrase"` | `"phrase"` or `{phrase}` | `"phrase"` | `positionCaseInsensitiveUTF8(col, 'phrase') > 0` |
| **Right truncation** | `term*` | `term*` | `term*` | `ilike(col, '%term%')` or regex |
| **Single-char wildcard** | `?` (exactly 1) | `?` (exactly 1) | N/A | `_` in LIKE |
| **Zero-or-one wildcard** | `$` (0 or 1 char) | N/A | N/A | regex `col ~ '...'` |
| **Any-order proximity** | `term1 NEAR/n term2` | `term1 W/n term2` | N/A (`"term1 term2"~n`) | Logical combination / distance |
| **Strict-order proximity** | N/A | `term1 PRE/n term2` | N/A | Regex with `\w+` spacer |

---

## 2. Field Codes by Database

### Web of Science (Core Collection)
- `TS=`: Topic (Title, Abstract, Author Keywords, Keywords Plus).
- `TI=`: Title.
- `AB=`: Abstract.
- `AK=`: Author Keywords.
- `KP=`: Keywords Plus.
- `AU=`: Authors.
- `AI=`: ResearcherID or ORCID.
- `OG=`: Organization Enhanced.
- `WC=`: Web of Science Category.
- `DT=`: Document Type (`Article`, `Review`, `Proceedings Paper`, `Editorial Material`, etc.).
- `PY=`: Year Published (`PY=2020-2024`).
- `IS=`: ISSN / eISSN.
- `DO=`: Digital Object Identifier (DOI).

### Scopus (Elsevier)
- `TITLE-ABS-KEY( )`: Combined Title, Abstract, and Keywords.
- `TITLE( )`: Document Title.
- `ABS( )`: Abstract.
- `KEY( )`: Keywords (author and indexed).
- `AUTHKEY( )`: Author keywords only.
- `INDEXTERMS( )`: Indexed keywords (Emtree, MeSH, Ei thesaurus).
- `AUTH( )`: Author surname and initials.
- `AF-ID( )`: Scopus Affiliation ID.
- `AFFIL( )`: Free-text affiliation.
- `SUBJAREA( )`: ASJC subject area code (`COMP`, `MEDI`, `ENGI`, etc.).
- `DOCTYPE( )`: Document type (`ar` = Article, `re` = Review, `cp` = Conference Paper).
- `PUBYEAR =` / `PUBYEAR >` / `PUBYEAR <`: Publication year filter.

### PubMed (NCBI / NLM)
- `[tiab]`: Title and Abstract.
- `[ti]`: Title.
- `[ab]`: Abstract.
- `[ot]`: Other Term (Author Keywords).
- `[mesh]`: Medical Subject Headings (with automatic hierarchy explosion).
- `[mesh:noexp]`: MeSH without hierarchical explosion.
- `[majr]`: MeSH Major Topic (primary focus of the study).
- `[pt]`: Publication Type (`journal article`, `review`, `clinical trial`, `meta-analysis`).
- `[ad]`: Affiliation.
- `[dp]`: Date of Publication (`2020/01/01:2024/12/31[dp]`).
- `[lang]`: Language (`eng[lang]`, `spa[lang]`).

### ClickHouse OpenAlex (`rag.works_academic_all`)
- **Inviolable rule:** Zero JOINs.
- **Core fields:**
  - `id`: Canonical OpenAlex Work ID (`https://openalex.org/W...`).
  - `doi`: Normalized DOI identifier.
  - `title`: Work title (UTF-8 string).
  - `publication_year`: Publication year (UInt16).
  - `type`: Canonical document type (`article`, `review`, `book-chapter`, `dataset`, etc.).
  - `concepts`: Array(String) of OpenAlex v2 concepts.
  - `topics`: Array(String) of Topics v5.0.
  - `author_names`: Array(String) of full author names.
  - `institutions`: Array(String) of affiliated institution names.
  - `institutions_country_codes`: Array(String) of ISO-2 country codes (`MX`, `US`, `ES`).
  - `oa_status`: Canonical Open Access route (`diamond`, `gold`, `green`, `hybrid`, `bronze`, `closed`).
  - `is_oa`: Boolean (1 if Open Access).
  - `cited_by_count`: Cumulative received citations.
  - `fwci`: Field-Weighted Citation Impact.
  - `has_embedding`: 1 if 768-dimensional vector is computed.
