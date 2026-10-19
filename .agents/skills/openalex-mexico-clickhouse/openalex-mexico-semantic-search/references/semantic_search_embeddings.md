# Arquitectura de Búsqueda Semántica con Embeddings Vectoriales (OpenAlex México)

## Modelos y Tablas en ClickHouse

### 1. Modelo de Embeddings
- **Modelo:** `text-embedding-nomic-ai-nomic-embed-text-v2-moe`
- **Dimensión vectorial:** 768 dimensiones (Float32).
- **Servidor local:** LM Studio (`http://127.0.0.1:1234/v1` en host / `http://172.17.0.1:1234/v1` en Docker).
- **Latencia de inferencia:** < 100 ms por consulta.

### 2. Tablas Vectoriales Preindexadas en ClickHouse
1. **`rag.works_academic_all`**:
   - Total de trabajos indexados con `embedding_nomic` (768d): **1,372,261 publicaciones**.
   - Función de distancia: `cosineDistance(embedding_nomic, query_vector)`.
   - Métrica de similitud semántica: `1.0 - cosineDistance`.
   - Tiempo de escaneo vectorial: ~0.3 a 1.2 segundos sobre 1.37M de vectores sin necesidad de GPU externa.

2. **`rag.academics_all`**:
   - Total de investigadoras/es indexados con `embedding_nomic` (768d): **9,118 perfiles clave**.
   - Total de investigadoras/es con `embedding_fastrp` (128d): **431,697 perfiles**.
   - Tiempo de escaneo: ~50 ms.

### 3. Desambiguación de Autores Nacionales vs Extranjeros
Al recuperar artículos científicos en colaboración internacional:
- El registro original puede incluir coautores extranjeros (ej. coautoría UNAM con Harvard, Oxford, Shenyang).
- El motor analítico cruza por lotes los identificadores contra `rag.authors_seed_mexico` (sin hacer JOINs).
- Clasifica automáticamente a los autores en:
  - `mexican_affiliated_authors`: Con adscripción verificada a instituciones mexicanas.
  - `international_collaborators`: Coautores de instituciones externas.
