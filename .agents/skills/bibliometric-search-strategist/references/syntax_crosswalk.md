# Matriz de Sintaxis y Crosswalk de Operadores Bibliográficos

Comparativa exhaustiva de sintaxis para transpilación entre Web of Science, Scopus, PubMed y ClickHouse (`rag.works_academic_all`).

---

## 1. Mapeo de Operadores Booleanos y de Caracteres Especiales

| Función | Web of Science | Scopus | PubMed | ClickHouse SQL |
|---|---|---|---|---|
| **Y lógico** | `AND` | `AND` | `AND` | `AND` |
| **O lógico** | `OR` | `OR` | `OR` | `OR` |
| **No lógico** | `NOT` | `AND NOT` | `NOT` | `AND NOT` |
| **Agrupación** | `( ... )` | `( ... )` | `( ... )` | `( ... )` |
| **Frase exacta** | `"phrase"` | `"phrase"` o `{phrase}` | `"phrase"` | `positionCaseInsensitiveUTF8(col, 'phrase') > 0` |
| **Truncamiento derecho** | `term*` | `term*` | `term*` | `ilike(col, '%term%')` o regex |
| **Comodín un caracter** | `?` (exactamente 1) | `?` (exactamente 1) | N/A | `_` en LIKE |
| **Comodín cero o uno** | `$` (0 o 1 caracter) | N/A | N/A | regex `col ~ '...'` |
| **Proximidad cualquier orden** | `term1 NEAR/n term2` | `term1 W/n term2` | N/A (`"term1 term2"~n`) | Combinación lógica / distance |
| **Proximidad orden estricto** | N/A | `term1 PRE/n term2` | N/A | Regex con espaciador `\w+` |

---

## 2. Códigos de Campos por Base de Datos

### Web of Science (Core Collection)
- `TS=`: Topic (Título, Abstract, Author Keywords, Keywords Plus).
- `TI=`: Title.
- `AB=`: Abstract.
- `AK=`: Author Keywords.
- `KP=`: Keywords Plus.
- `AU=`: Authors.
- `AI=`: ResearcherID o ORCID.
- `OG=`: Organization Enhanced.
- `WC=`: Web of Science Category.
- `DT=`: Document Type (`Article`, `Review`, `Proceedings Paper`, `Editorial Material`, etc.).
- `PY=`: Year Published (`PY=2020-2024`).
- `IS=`: ISSN / eISSN.
- `DO=`: Digital Object Identifier (DOI).

### Scopus (Elsevier)
- `TITLE-ABS-KEY( )`: Título, Abstract y Palabras clave combinadas.
- `TITLE( )`: Título del documento.
- `ABS( )`: Resumen.
- `KEY( )`: Palabras clave (autor e indexadas).
- `AUTHKEY( )`: Únicamente palabras clave de autor.
- `INDEXTERMS( )`: Palabras clave indexadas (Emtree, MeSH, Ei thesaurus).
- `AUTH( )`: Apellido e inicial del autor.
- `AF-ID( )`: Affiliation ID de Scopus.
- `AFFIL( )`: Texto libre de afiliación.
- `SUBJAREA( )`: Código de área temática ASJC (`COMP`, `MEDI`, `ENGI`, etc.).
- `DOCTYPE( )`: Tipo de documento (`ar` = Article, `re` = Review, `cp` = Conference Paper).
- `PUBYEAR =` / `PUBYEAR >` / `PUBYEAR <`: Filtro de año de publicación.

### PubMed (NCBI / NLM)
- `[tiab]`: Title and Abstract.
- `[ti]`: Title.
- `[ab]`: Abstract.
- `[ot]`: Other Term (Author Keywords).
- `[mesh]`: Medical Subject Headings (con jerarquía / explode automático).
- `[mesh:noexp]`: MeSH sin expansión jerárquica.
- `[majr]`: MeSH Major Topic (foco principal del estudio).
- `[pt]`: Publication Type (`journal article`, `review`, `clinical trial`, `meta-analysis`).
- `[ad]`: Affiliation.
- `[dp]`: Date of Publication (`2020/01/01:2024/12/31[dp]`).
- `[lang]`: Language (`eng[lang]`, `spa[lang]`).

### ClickHouse OpenAlex (`rag.works_academic_all`)
- **Regla inviolable:** Cero JOINs.
- **Campos principales:**
  - `id`: OpenAlex Work ID canónico (`https://openalex.org/W...`).
  - `doi`: Identificador DOI normalizado.
  - `title`: Título del trabajo (cadena UTF-8).
  - `publication_year`: Año (UInt16).
  - `type`: Tipo canónico (`article`, `review`, `book-chapter`, `dataset`, etc.).
  - `concepts`: Array(String) con conceptos de OpenAlex v2.
  - `topics`: Array(String) con Topics v5.0.
  - `author_names`: Array(String) con nombres completos de autoras y autores.
  - `institutions`: Array(String) con nombres de instituciones de afiliación.
  - `institutions_country_codes`: Array(String) códigos ISO-2 (`MX`, `US`, `ES`).
  - `oa_status`: Vía canónica de Acceso Abierto (`diamond`, `gold`, `green`, `hybrid`, `bronze`, `closed`).
  - `is_oa`: Booleano (1 si tiene acceso abierto).
  - `cited_by_count`: Citas recibidas acumuladas.
  - `fwci`: Field-Weighted Citation Impact.
  - `has_embedding`: 1 si tiene vector de 768 dimensiones calculado.
