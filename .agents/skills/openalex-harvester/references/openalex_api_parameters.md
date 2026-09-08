# Parámetros y Filtros de la API de OpenAlex

OpenAlex (`https://api.openalex.org`) provee acceso abierto e indexado a más de 250 millones de obras científicas mundiales.

---

## 1. Estructura de Filtros

Los filtros se combinan mediante una cadena delimitada por comas: `filter=campo:valor,campo2:valor2`.

### Filtros Principales por Entidad

| Filtro | Descripción | Ejemplo de Sintaxis |
|---|---|---|
| `author.id` | Identificador OpenAlex del autor | `author.id:A5023888391` |
| `author.orcid` | ORCID del autor (con o sin prefijo https) | `author.orcid:0000-0002-1825-0097` |
| `institutions.ror` | Identificador ROR de la institución | `institutions.ror:012gw1n35` (UNAM) |
| `institutions.country_code` | Código ISO-3166-1 alpha-2 del país de la institución | `institutions.country_code:MX` |
| `primary_location.source.issn` | ISSN de la revista fuente | `primary_location.source.issn:1386-4564` |
| `primary_topic.id` | Identificador del clúster temático (Tópico) | `primary_topic.id:T10001` |
| `open_access.oa_status` | Modalidad de acceso abierto | `open_access.oa_status:diamond` |
| `publication_year` | Rango o año exacto de publicación | `publication_year:2020-2024` |
| `from_publication_date` | Fecha inicial en formato YYYY-MM-DD | `from_publication_date:2023-01-01` |
| `to_publication_date` | Fecha final en formato YYYY-MM-DD | `to_publication_date:2023-12-31` |
| `is_retracted` | Filtro de obras retractadas | `is_retracted:true` |

---

## 2. Paginación Eficiente mediante Cursor

Para conjuntos de más de 200 resultados, OpenAlex requiere paginación por cursor:
1. Primera llamada: `cursor=*`
2. El JSON retornado incluye en su bloque `meta` la clave `next_cursor`.
3. Siguientes llamadas: `cursor=<next_cursor>` hasta que `next_cursor` sea `null` o el límite se haya satisfecho.

---

## 3. Clave de API y "Polite Pool"

- **Con API Key (`OPENALEX_API_KEY`):** Se añade en la cabecera `api-key: <clave>`. Límite de hasta 10 req/s.
- **Sin API Key (Polite Pool):** Se añade la cabecera `User-Agent: KnoMap-Harvester/1.0 (mailto:tu-correo@dominio.com)`. Límite recomendado: 5 req/s.
