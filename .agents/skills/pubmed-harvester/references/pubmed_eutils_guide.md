# Guía Técnica: API NCBI E-utilities (PubMed)
-----------------------------------------------

La National Library of Medicine (NLM / NCBI) provee acceso programático a PubMed a través del conjunto de herramientas E-utilities.

## Endpoints Principales

1. **`esearch.fcgi` (Búsqueda y obtención de PMIDs):**
   - URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`
   - Parámetros clave:
     - `db=pubmed`: Base de datos de literatura biomédica.
     - `term=<query>`: Términos de búsqueda con sintaxis Entrez (ej. `asthma[Title/Abstract] AND Mexico[Affiliation]`).
     - `retmax=<n>`: Número máximo de PMIDs a recuperar (hasta 10,000 en un solo llamado).
     - `retstart=<offset>`: Desplazamiento para paginación.
     - `retmode=json`: Respuesta estructurada en JSON.
     - `mindate=<YYYY>`, `maxdate=<YYYY>`, `datetype=pdat`: Filtro cronológico de publicación.

2. **`esummary.fcgi` (Metadatos Documentales):**
   - URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi`
   - Parámetros:
     - `db=pubmed`
     - `id=<pmid1,pmid2,...>`: Lista de identificadores separados por comas (lotes recomendados de 100 a 300).
     - `retmode=json`: Entrega título, autores, fecha, revista (`fulljournalname`), DOI y PMCID.

3. **`efetch.fcgi` (Contenido Completo y Abstracts):**
   - URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`
   - Parámetros:
     - `db=pubmed`
     - `id=<pmid1,pmid2,...>`
     - `retmode=xml`: Permite extraer abstracts completos, afiliaciones institucionales detalladas de cada autor y términos MeSH (*Medical Subject Headings*).

## Filtros de Campo Clave en Entrez

- `[Title/Abstract]` o `[tiab]`: Búsqueda en título o resumen.
- `[Author]` o `[au]`: Apellido e iniciales del autor (ej. `Pardo A[Author]`).
- `[Affiliation]` o `[ad]`: Institución, universidad, hospital o país (ej. `National Autonomous University of Mexico[Affiliation]`, `Mexico[Affiliation]`).
- `[Journal]` o `[ta]`: Revista científica.
- `[Mesh Terms]` o `[mesh]`: Descriptores temáticos controlados MeSH.

## Políticas de Acceso y Límites de Tasa (Rate Limiting)

- **Sin API Key:** Máximo 3 peticiones por segundo.
- **Con API Key (`NCBI_API_KEY`):** Hasta 10 peticiones por segundo.
- **Identificación:** Se recomienda enviar `tool=knoMap-Harvester` y `email=<correo_contacto>` en la query string.
