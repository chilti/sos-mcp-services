# Semantic Search Architecture with Vector Embeddings (OpenAlex Mexico)

## Models and Tables in ClickHouse

### 1. Embedding Model
- **Model:** `text-embedding-nomic-ai-nomic-embed-text-v2-moe`
- **Vector dimension:** 768 dimensions (`Float32`).
- **Local server:** LM Studio (`http://127.0.0.1:1234/v1` on host / `http://172.17.0.1:1234/v1` in Docker).
- **Inference latency:** < 100 ms per query.

### 2. Pre-indexed Vector Tables in ClickHouse
1. **`rag.works_academic_all`**:
   - Total works indexed with `embedding_nomic` (768d): **1,372,261 publications**.
   - Distance function: `cosineDistance(embedding_nomic, query_vector)`.
   - Semantic similarity metric: `1.0 - cosineDistance`.
   - Vector scan time: ~0.3 to 1.2 seconds over 1.37M vectors without requiring an external GPU.

2. **`rag.academics_all`**:
   - Total researchers indexed with `embedding_nomic` (768d): **9,118 key profiles**.
   - Total researchers with `embedding_fastrp` (128d): **431,697 profiles**.
   - Scan time: ~50 ms.

### 3. Disambiguation of Domestic vs. Foreign Authors
When retrieving scientific articles in international collaboration:
- The original record may include foreign co-authors (e.g., UNAM co-authorship with Harvard, Oxford, Shenyang).
- The analytical engine batch-cross-references identifiers against `rag.authors_seed_mexico` (without performing JOINs).
- It automatically classifies authors into:
  - `mexican_affiliated_authors`: With verified affiliation to Mexican institutions.
  - `international_collaborators`: Co-authors from foreign institutions.
