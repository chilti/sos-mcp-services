# Schema of rag.works_academic_all (~1,652,927 rows)

Central analytical table of scientific production in Mexico in ClickHouse.

| Field | Type | Description |
|---|---|---|
| `id` | String | Canonical URI (`https://openalex.org/W...`) |
| `title` | String | Article or publication title |
| `doi` | String | Resolved DOI link |
| `publication_year` | Int32 | Publication year |
| `cited_by_count` | Int64 | Cumulative global citations |
| `is_oa` | String | Boolean Open Access indicator (`"1"` or `"0"`) |
| `oa_status` | String | Canonical OA route: `diamond`, `gold`, `hybrid`, `bronze`, `green`, `closed` |
| `fwci` | Float32 | Field-Weighted Citation Impact normalized by category |
| `percentile` | Float32 | Global citation percentile within its discipline |
| `is_top_10` | UInt8 | Binary indicator for membership in the global top 10% decile |
| `is_top_1` | UInt8 | Binary indicator for membership in the global top 1% elite |
| `apc_paid_usd` | Float64 | Estimated APC cost paid to commercial publishers in USD |
| `apc_list_usd` | Float64 | Official reported list-price APC in USD |
| `author_names` | Array(String) | List of co-authors |
| `institution_names`| Array(String) | Names of affiliated institutions |
| `institution_rors` | Array(String) | Institutional ROR URIs |
| `topic` | String | OpenAlex Topics v5.0 topic name |
| `subfield` | String | Scientometric subfield |
| `field` | String | General field |
| `domain` | String | Broad knowledge domain |
| `sdg_ids` | Array(String) | Sustainable Development Goal identifiers |
| `sdgs` | Array(String) | Aligned SDG names |
| `all_country_codes`| Array(String) | Participating countries in co-authorship |
