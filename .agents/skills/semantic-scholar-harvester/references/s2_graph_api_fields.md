# Campos y Estructura de Semantic Scholar Graph API

La API Graph de Semantic Scholar (`https://api.semanticscholar.org/graph/v1`) estructura la literatura científica mediante nodos interconectados de artículos, autores y citas.

---

## 1. Campos Clave de Artículos (`/paper`)

| Campo | Tipo | Descripción |
|---|---|---|
| `paperId` | String | SHA-1 unívoco del artículo en Semantic Scholar |
| `title` | String | Título del trabajo |
| `abstract` | String | Resumen textual |
| `year` | Integer | Año de publicación |
| `venue` | String | Nombre corto o conferencia del medio |
| `publicationVenue` | Objeto | Metadatos de la revista (ISSN, tipo, nombre completo) |
| `citationCount` | Integer | Conteo total de citas recibidas |
| `influentialCitationCount` | Integer | Citas consideradas influyentes según el modelo heurístico de S2 |
| `fieldsOfStudy` | Array[str] | Áreas disciplinarias generales (Computer Science, Medicine, etc.) |
| `s2FieldsOfStudy` | Array[obj] | Taxonomía jerárquica con categorías especializadas |
| `openAccessPdf` | Objeto | Enlace directo al archivo PDF de acceso abierto |
| `externalIds` | Objeto | Diccionario de identificadores externos (`DOI`, `ArXiv`, `PubMed`) |
| `authors` | Array[obj] | Lista de autores con `authorId`, `name`, `affiliations` |
| `citations` | Array[obj] | Artículos que citan a este trabajo (entrantes) |
| `references` | Array[obj] | Artículos citados en la bibliografía (salientes) |

---

## 2. Límites de Tasa (Rate Limiting)

- **Modo anónimo:** 1 solicitud por segundo (el cliente aplica automáticamente una pausa de 1.0 s).
- **Con clave `S2_API_KEY`:** Hasta 10 solicitudes por segundo (pausa de 0.2 s).
