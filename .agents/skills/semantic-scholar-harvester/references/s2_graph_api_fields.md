# Semantic Scholar Graph API Fields and Structure

The Semantic Scholar Graph API (`https://api.semanticscholar.org/graph/v1`) structures scientific literature through interconnected nodes of papers, authors, and citations.

---

## 1. Key Paper Fields (`/paper`)

| Field | Type | Description |
|---|---|---|
| `paperId` | String | Unique SHA-1 paper identifier in Semantic Scholar |
| `title` | String | Work title |
| `abstract` | String | Text abstract |
| `year` | Integer | Publication year |
| `venue` | String | Short venue or conference name |
| `publicationVenue` | Object | Journal metadata (ISSN, type, full name) |
| `citationCount` | Integer | Total count of received citations |
| `influentialCitationCount` | Integer | Citations deemed influential according to S2's heuristic model |
| `fieldsOfStudy` | Array[str] | General disciplinary areas (Computer Science, Medicine, etc.) |
| `s2FieldsOfStudy` | Array[obj] | Hierarchical taxonomy with specialized categories |
| `openAccessPdf` | Object | Direct link to the Open Access PDF file |
| `externalIds` | Object | Dictionary of external identifiers (`DOI`, `ArXiv`, `PubMed`) |
| `authors` | Array[obj] | List of authors with `authorId`, `name`, `affiliations` |
| `citations` | Array[obj] | Papers citing this work (incoming) |
| `references` | Array[obj] | Papers cited in the bibliography (outgoing) |

---

## 2. Rate Limiting

- **Anonymous mode:** 1 request per second (the client automatically enforces a 1.0 s pause).
- **With `S2_API_KEY`:** Up to 10 requests per second (0.2 s pause).
