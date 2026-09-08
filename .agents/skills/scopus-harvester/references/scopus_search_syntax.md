# Sintaxis de Búsqueda Avanzada de Scopus

La API de Scopus Search acepta operadores booleanos y códigos de campo especializados definidos por Elsevier.

---

## 1. Códigos de Campo Más Frecuentes

| Código | Descripción | Ejemplo |
|---|---|---|
| `TITLE-ABS-KEY()` | Busca términos en título, resumen y palabras clave | `TITLE-ABS-KEY("bibliometrics" OR "scientometrics")` |
| `AUTH()` | Apellido o nombre del autor | `AUTH("Jimenez-Andrade")` |
| `AU-ID()` | Identificador unívoco del autor en Scopus | `AU-ID(57200234567)` |
| `AFFIL()` | Nombre de la institución o afiliación | `AFFIL("Universidad Nacional Autonoma de Mexico")` |
| `AF-ID()` | Identificador unívoco de afiliación en Scopus | `AF-ID(60028190)` (UNAM) |
| `PUBYEAR` | Año de publicación | `PUBYEAR = 2024` o `PUBYEAR > 2020` |
| `EXACTSRCTITLE()` | Título exacto de la revista o fuente | `EXACTSRCTITLE("Journal of Informetrics")` |
| `ISSN()` | ISSN de la revista | `ISSN(1751-1577)` |
| `DOCTYPE()` | Tipo documental (`ar` = article, `re` = review, `cp` = conference) | `DOCTYPE(ar)` |
| `SUBJAREA()` | Código de área temática ASJC | `SUBJAREA(COMP)` (Computer Science) |

---

## 2. Operadores Booleanos y de Proximidad

- `AND`, `OR`, `AND NOT` (deben escribirse siempre en mayúsculas).
- Comillas dobles `""` para frases exactas: `TITLE-ABS-KEY("artificial intelligence")`.
- Paréntesis para agrupar expresiones: `(AUTH("Gomez") OR AUTH("Perez")) AND PUBYEAR > 2022`.
