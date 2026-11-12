# Technical Guide: NCBI E-utilities API (PubMed)
-----------------------------------------------

The National Library of Medicine (NLM / NCBI) provides programmatic access to PubMed through the E-utilities toolset.

## Core Endpoints

1. **`esearch.fcgi` (Search and PMID retrieval):**
   - URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`
   - Key parameters:
     - `db=pubmed`: Biomedical literature database.
     - `term=<query>`: Search terms using Entrez syntax (e.g., `asthma[Title/Abstract] AND Mexico[Affiliation]`).
     - `retmax=<n>`: Maximum number of PMIDs to retrieve (up to 10,000 in a single call).
     - `retstart=<offset>`: Pagination offset.
     - `retmode=json`: Structured JSON response.
     - `mindate=<YYYY>`, `maxdate=<YYYY>`, `datetype=pdat`: Chronological publication filter.

2. **`esummary.fcgi` (Document Metadata):**
   - URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi`
   - Parameters:
     - `db=pubmed`
     - `id=<pmid1,pmid2,...>`: Comma-separated list of identifiers (recommended batch size: 100 to 300).
     - `retmode=json`: Returns title, authors, date, journal (`fulljournalname`), DOI, and PMCID.

3. **`efetch.fcgi` (Full Content and Abstracts):**
   - URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`
   - Parameters:
     - `db=pubmed`
     - `id=<pmid1,pmid2,...>`
     - `retmode=xml`: Enables extracting full abstracts, detailed institutional affiliations for each author, and MeSH (*Medical Subject Headings*) terms.

## Key Field Tags in Entrez

- `[Title/Abstract]` or `[tiab]`: Search in title or abstract.
- `[Author]` or `[au]`: Author last name and initials (e.g., `Pardo A[Author]`).
- `[Affiliation]` or `[ad]`: Institution, university, hospital, or country (e.g., `National Autonomous University of Mexico[Affiliation]`, `Mexico[Affiliation]`).
- `[Journal]` or `[ta]`: Scientific journal.
- `[Mesh Terms]` or `[mesh]`: Controlled MeSH thematic descriptors.

## Access Policies and Rate Limiting

- **Without API Key:** Maximum 3 requests per second.
- **With API Key (`NCBI_API_KEY`):** Up to 10 requests per second.
- **Identification:** Passing `tool=knoMap-Harvester` and `email=<contact_email>` in the query string is recommended.
