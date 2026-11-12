# OpenAlex API Parameters and Filters

OpenAlex (`https://api.openalex.org`) provides open, indexed access to over 250 million scholarly works worldwide.

---

## 1. Filter Structure

Filters are combined using a comma-delimited string: `filter=field:value,field2:value2`.

### Core Filters by Entity

| Filter | Description | Syntax Example |
|---|---|---|
| `author.id` | Author OpenAlex identifier | `author.id:A5023888391` |
| `author.orcid` | Author ORCID (with or without https prefix) | `author.orcid:0000-0002-1825-0097` |
| `institutions.ror` | Institutional ROR identifier | `institutions.ror:012gw1n35` (UNAM) |
| `institutions.country_code` | ISO-3166-1 alpha-2 country code of the institution | `institutions.country_code:MX` |
| `primary_location.source.issn` | Source journal ISSN | `primary_location.source.issn:1386-4564` |
| `primary_topic.id` | Thematic cluster (Topic) identifier | `primary_topic.id:T10001` |
| `open_access.oa_status` | Open Access route | `open_access.oa_status:diamond` |
| `publication_year` | Publication year or range | `publication_year:2020-2024` |
| `from_publication_date` | Start date in YYYY-MM-DD format | `from_publication_date:2023-01-01` |
| `to_publication_date` | End date in YYYY-MM-DD format | `to_publication_date:2023-12-31` |
| `is_retracted` | Retracted works filter | `is_retracted:true` |

---

## 2. Efficient Cursor Pagination

For result sets exceeding 200 records, OpenAlex requires cursor pagination:
1. First request: `cursor=*`
2. The returned JSON includes the `next_cursor` key inside its `meta` block.
3. Subsequent requests: `cursor=<next_cursor>` until `next_cursor` is `null` or the requested limit is satisfied.

---

## 3. API Key and "Polite Pool"

- **With API Key (`OPENALEX_API_KEY`):** Added via the `api-key: <key>` header. Rate limit up to 10 req/s.
- **Without API Key (Polite Pool):** Added via the `User-Agent: KnoMap-Harvester/1.0 (mailto:your-email@domain.com)` header. Recommended rate limit: 5 req/s.
