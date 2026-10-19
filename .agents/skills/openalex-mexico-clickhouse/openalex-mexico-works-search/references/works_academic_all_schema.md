# Esquema de rag.works_academic_all (~1,652,927 filas)

Tabla analítica central de la producción científica en México en ClickHouse.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String | URI canónica (`https://openalex.org/W...`) |
| `title` | String | Título del artículo o publicación |
| `doi` | String | Enlace DOI resuelto |
| `publication_year` | Int32 | Año de publicación |
| `cited_by_count` | Int64 | Citas acumuladas globales |
| `is_oa` | String | Indicador booleano de acceso abierto (`"1"` o `"0"`) |
| `oa_status` | String | Vía canónica: `diamond`, `gold`, `hybrid`, `bronze`, `green`, `closed` |
| `fwci` | Float32 | Field-Weighted Citation Impact normalizado por categoría |
| `percentile` | Float32 | Percentil global de citación en su disciplina |
| `is_top_10` | UInt8 | Indicador binario si pertenece al decil superior mundial |
| `is_top_1` | UInt8 | Indicador binario si pertenece al 1% de élite mundial |
| `apc_paid_usd` | Float64 | Costo estimado de APC pagado a la editorial comercial en USD |
| `apc_list_usd` | Float64 | Tarifa oficial de lista de APC reportada |
| `author_names` | Array(String) | Lista de coautoras/es |
| `institution_names`| Array(String) | Nombres de instituciones de adscripción |
| `institution_rors` | Array(String) | URIs ROR de las instituciones |
| `topic` | String | Nombre del tópico OpenAlex Topics v5.0 |
| `subfield` | String | Subcampo cienciométrico |
| `field` | String | Campo general |
| `domain` | String | Gran área del conocimiento |
| `sdg_ids` | Array(String) | Identificadores de Objetivos de Desarrollo Sostenible |
| `sdgs` | Array(String) | Nombres de los ODS alineados |
| `all_country_codes`| Array(String) | Países participantes en la coautoría |
