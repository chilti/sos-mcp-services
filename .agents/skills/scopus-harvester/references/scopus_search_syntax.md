# Scopus Advanced Search Syntax

The Scopus Search API accepts Boolean operators and specialized field codes defined by Elsevier.

---

## 1. Most Frequent Field Codes

| Code | Description | Example |
|---|---|---|
| `TITLE-ABS-KEY()` | Searches terms in title, abstract, and keywords | `TITLE-ABS-KEY("bibliometrics" OR "scientometrics")` |
| `AUTH()` | Author surname or name | `AUTH("Jimenez-Andrade")` |
| `AU-ID()` | Unique Scopus Author Identifier | `AU-ID(57200234567)` |
| `AFFIL()` | Institution or affiliation name | `AFFIL("Universidad Nacional Autonoma de Mexico")` |
| `AF-ID()` | Unique Scopus Affiliation Identifier | `AF-ID(60028190)` (UNAM) |
| `PUBYEAR` | Publication year | `PUBYEAR = 2024` or `PUBYEAR > 2020` |
| `EXACTSRCTITLE()` | Exact journal or source title | `EXACTSRCTITLE("Journal of Informetrics")` |
| `ISSN()` | Journal ISSN | `ISSN(1751-1577)` |
| `DOCTYPE()` | Document type (`ar` = article, `re` = review, `cp` = conference) | `DOCTYPE(ar)` |
| `SUBJAREA()` | ASJC subject area code | `SUBJAREA(COMP)` (Computer Science) |

---

## 2. Boolean and Proximity Operators

- `AND`, `OR`, `AND NOT` (must always be written in uppercase).
- Double quotes `""` for exact phrases: `TITLE-ABS-KEY("artificial intelligence")`.
- Parentheses to group expressions: `(AUTH("Gomez") OR AUTH("Perez")) AND PUBYEAR > 2022`.
