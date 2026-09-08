# Esquema de Tablas OpenAlex en ClickHouse Local

OpenAlex cuenta con un volcado completo materializado localmente en ClickHouse conteniendo 569 millones de trabajos y 337 millones de autores.

---

## 1. Tablas Principales

| Tabla | Registros Aprox. | Descripción y Uso Óptimo |
|---|---|---|
| `openalex.works_flat` | 569,000,000 | Catálogo global de todas las publicaciones científicas mundiales |
| `openalex.works_academic_all` | 1,652,927 | Publicaciones con autores adscritos a instituciones de México |
| `openalex.authors` | 337,000,000 | Autores normalizados con ORCID, métricas y afiliación canónica |
| `openalex.institutions` | 110,000 | Universidades y centros con identificador ROR |
| `openalex.sources` | 250,000 | Revistas, repositorios y editoriales |
| `openalex.topics` | 4,500 | Tópicos jerárquicos del modelo OpenAlex Topics v5.0 |

---

## 2. Regla Estricta: Prohibición de JOINs Directos

Debido al volumen de las tablas ($> 500\text{M}$ de registros), **no se deben formular sentencias con `JOIN` directo en ClickHouse sin autorización previa**.
* Para consultas sobre autores en México $\to$ Consultar directamente la tabla materializada `works_academic_all`.
* Para búsquedas de texto en autores $\to$ Usar `positionCaseInsensitiveUTF8(display_name, 'termino') > 0` sobre `authors`.
