# Plan Integral de Implementación: SOS MCP Services
**Proyecto:** `sos-mcp-services`  
**Ubicación:** `C:\Users\jlja\Documents\Proyectos\sos-mcp-services`  
**Autor:** Antigravity (Google DeepMind)  
**Fecha:** 22 de Agosto de 2026  
**Documento Fuente de Referencia:** `newLabSOM/docs/analisis_skills_mcp_knomap.md` (Secciones 1 a 6)  

---

## 1. Resumen Ejecutivo y Visión Arquitectónica

El proyecto **`sos-mcp-services`** centraliza y desacopla la suite de herramientas analíticas de cienciometría, bibliometría y topología neuronal de la UNAM en microservicios basados en el protocolo estándar **Model Context Protocol (MCP)**.

### Principio Rector: "Dual Hybrid Architecture"
1. **Herramientas para Humanos (Intactas):** Los dashboards en Streamlit, interfaces React de `knoMap`, APIs REST de `openalex-elastic-api` y entornos de visualización continúan funcionando como herramientas autónomas para visualización y streaming masivo de datos.
2. **Capacidades para Agentes (MCP):** Antigravity y otros agentes de IA consumen las funciones computacionales y consultas semánticas a través de servidores FastMCP modulares con respuestas estructuradas en JSON/Pydantic.
3. **Transporte Dual:**
   - **Desarrollo:** `stdio` (subproceso local directo, recarga instantánea, sin sobrecarga de red).
   - **Staging / Producción (`dinamica1`):** `HTTP/SSE` (contenedores Docker orquestados con `docker-compose`, permitiendo servicio multi-agente concurrente).

---

## 2. Mapa Completo de Servidores MCP y Herramientas (35 Tools / 9 Servidores)

El monorepo agrupa los 9 servidores definidos en `analisis_skills_mcp_knomap.md` en 6 microservicios autónomos:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       HEXÁGONO DE MICROSERVICIOS MCP (UNAM)                                      │
├──────────────────┬──────────────────┬─────────────────┬──────────────────┬─────────────────┬─────────────────────┤
│ 1. knoMap Suite  │ 2. SinapsisAI    │ 3. PLmetrix     │ 4. RevistasLATAM │ 5. Topics       │ 6. OpenAlex Gateway │
│ (Puertos 8001)   │ (Puerto 8002)    │ (Puerto 8003)   │ (Puerto 8004)    │ (Puerto 8005)   │ (Puerto 8006)       │
├──────────────────┼──────────────────┼─────────────────┼──────────────────┼─────────────────┼─────────────────────┤
│ • SOM Engine     │ • Cypher Graph   │ • Ley de Lotka  │ • FWCI Journals  │ • Fronts v5     │ • Token Search      │
│ • Bibliometrics  │ • Qdrant Vectors │ • Ley Bradford  │ • Benchmarking   │ • Evolution AMI │ • Works by Query    │
│ • InCites Bench. │ • Padrón SNII    │ • Ley de Zipf   │ • Diamond vs Gold│ • Geopolitics   │ • Entity by ID      │
│ • Semantic UMAP  │ • Desambiguación │ • Índice Price  │ • Multilingual   │ • OA Transition │ • Group By SQL      │
│                  │ • Researcher Prof│ • Growth Models │ • DOAJ / SciELO  │ • SDG UN Impact │   Aggregations      │
└──────────────────┴──────────────────┴─────────────────┴──────────────────┴─────────────────┴─────────────────────┘
```

---

### Detalle de Servidores y Herramientas a Implementar

#### Servidor 1: `openalex-clickhouse-gateway` (`services/openalex`)
*Gateway de búsqueda semántica y filtrado sobre la base local OpenAlex en ClickHouse (569M works).*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 1.1 | `openalex_search_authors` | `search_query`, `orcid`, `institution_ror`, `limit` | Búsqueda tokenizada e insensible a acentos/diacríticos de autores con filtros de filiación. |
| 1.2 | `openalex_search_works` | `search_query`, `author_id`, `institution_ror`, `topic_id`, `from_publication_date`, `to_publication_date`, `is_oa`, `limit` | Búsqueda de publicaciones científicas por título, tópico, autor, revista o fechas. |
| 1.3 | `openalex_get_entity_by_id` | `entity_type` (works/authors/institutions/sources/topics/funders), `identifier` | Recupera el objeto normalizado completo dado su OpenAlex ID, DOI, ORCID o ROR. |
| 1.4 | `openalex_aggregate_group_by` | `entity_type`, `filter_param`, `group_by_field` (publication_year, oa_status, primary_topic.id, country_code) | Agregaciones analíticas y conteos agrupados ultra-rápidos en ClickHouse. |

---

#### Servidor 2: `knomap-som-engine` (`services/knomap/tools/som_tools.py`)
*Entrenamiento neuronal no supervisado, topología hexagonal y agrupamiento.*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 2.1 | `suggest_grid_size` | `data` (Matriz N x D) | Calcula el tamaño óptimo de la malla (Big SOM 10N vs Small SOM 5sqrt(N)) y el aspect ratio SVD. |
| 2.2 | `train_som` | `data`, `labels`, `rows`, `cols`, `method` (batch/basic), `init` (pca/linear/random), `iterations`, `clustering_algorithm`, `n_clusters` | Entrena mapa auto-organizado retornando U-Matrix, pesos, BMUs, errores de cuantización y coordenadas. |
| 2.3 | `evaluate_som_clusters` | `weights`, `max_k` | Evalúa Silhouette, Davies-Bouldin y Calinski-Harabasz para encontrar el K óptimo sobre pesos neuronales. |
| 2.4 | `recluster_som` | `weights`, `algorithm` (kmeans/dbscan/agglomerative), `n_clusters` | Recalcula etiquetas de clusters neuronales instantáneamente sin re-entrenar la red. |

---

#### Servidor 3: `knomap-bibliometrics` (`services/knomap/tools/bibliometrics_tools.py`)
*Ingesta de archivos bibliográficos y extracción de redes relacionales VOSviewer.*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 3.1 | `parse_bibliographic_file` | `filepath`, `network_type` (co-occurrence/co-authorship/co-citation/coupling/bipartite), `custom_tag`, `max_terms`, `min_cooccurrence`, `counting_method`, `thesaurus_filepath` | Procesa exportaciones (WoS, Scopus, PubMed, OpenAlex) y genera redes en formato VOSviewer/Pajek. |
| 3.2 | `detect_louvain_communities` | `vosviewer_json`, `resolution`, `min_cluster_size` | Detección de comunidades de Louvain con control de resolución modular. |

---

#### Servidor 4: `knomap-incites-explorer` (`services/knomap/tools/incites_tools.py`)
*Benchmarking cienciométrico institucional (Clarivate InCites) y análisis longitudinal.*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 4.1 | `inspect_incites_package` | `package_path` | Inspecciona archivo ZIP o directorio InCites y extrae el inventario de unidades y esquemas. |
| 4.2 | `get_incites_unit_matrix` | `session_dir`, `unit_name`, `use_recent_5years`, `selected_indicators`, `filter_indicator`, `filter_min_threshold`, `limit_top_n` | Extrae el perfil multidimensional de una unidad aplicando normalización y filtros de umbral. |
| 4.3 | `get_incites_temporal_evolution` | `session_dir`, `unit_name`, `entities`, `indicators`, `smoothing` (raw/ecma3/ecma5) | Extrae la matriz de series de tiempo multivariadas (PathSOM) con suavizado exponencial. |
| 4.4 | `compute_strategic_growth_matrix` | `session_dir`, `unit_name`, `indicator`, `entities` | Matriz CAGR % vs Volumen actual clasificando en cuadrantes estratégicos (Stars, Leaders, Giants). |

---

#### Servidor 5: `knomap-semantic-pipeline` (`services/knomap/tools/semantic_tools.py`)
*Espacio latente de publicaciones, embeddings y geometría de variedades no lineales.*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 5.1 | `generate_document_embeddings` | `filepath`, `model_name` (nomic-embed-text/specter2) | Genera embeddings densos combinando Título, Resumen, Keywords y MeSH. |
| 5.2 | `estimate_intrinsic_dimension` | `embeddings`, `mode` (ceiling/manual), `algorithm` (MLE) | Estima la dimensión intrínseca con MLE local (Estrategia Techo de Información al percentil 95). |
| 5.3 | `reduce_semantic_dimension` | `embeddings`, `target_dimension` | Comprime embeddings al espacio intrínseco o a 2D preservando topología no lineal (UMAP). |
| 5.4 | `cluster_semantic_documents` | `reduced_data`, `records`, `num_levels` | Agrupa documentos en clusters jerárquicos con descriptores TF-IDF adaptativos. |

---

#### Servidor 6: `sinapsisai-graphrag-engine` (`services/sinapsisai`)
*Grafo de conocimiento Neo4j, búsqueda semántica Qdrant y padrón oficial SNII.*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 6.1 | `query_knowledge_graph_cypher` | `cypher_query` | Ejecuta consultas Cypher sobre el grafo Neo4j (autores, papers, afiliaciones UNAM, tópicos, ODS). |
| 6.2 | `search_scientific_papers_semantic` | `query`, `limit`, `entity_context` | Búsqueda vectorial densa en Qdrant con traducción automática y contexto institucional. |
| 6.3 | `get_researcher_profile` | `name_fragment` | Perfil académico integral (afiliación, producción histórica, citas, tópicos, coautores, SNII, ORCID). |
| 6.4 | `get_entity_statistics` | `entity_name` | Estadísticas cienciométricas agregadas para una entidad académica o dependencia. |
| 6.5 | `resolve_snii_identity` | `fullname`, `institution`, `dependency` | Resuelve y desambigua identidad de investigadores contra el padrón oficial SNII y ORCID. |

---

#### Servidor 7: `topics-research-fronts-engine` (`services/topics`)
*Detección longitudinal de frentes de investigación v5.0, geopolítica y taxonomía.*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 7.1 | `detect_research_fronts_multimodal` | `subfield_name`, `year_start`, `year_end`, `modality` (structural/semantic/topological/all) | Pipeline multimodal para frentes de investigación (Leiden/Salton, SPECTER2/HDBSCAN, FastRP). |
| 7.2 | `track_front_evolution_longitudinal` | `subfield_name` | Rastrea evolución temporal de frentes entre ventanas deslizantes con Jaccard y consistencia AMI. |
| 7.3 | `get_geopolitical_collaboration_matrix` | `subfield_name`, `target_country` (default: MX) | Matriz de coautorías internacionales por pares de países, red PyVis y coropletas. |
| 7.4 | `get_open_access_transition_data` | `subfield_name` | Evolución y desglose porcentual de las 6 vías de Acceso Abierto (Gold, Diamond, Green, Hybrid, Bronze, Closed). |
| 7.5 | `get_sdg_impact_matrix` | `subfield_name` | Matriz de alineación con los 17 Objetivos de Desarrollo Sostenible (ODS de la ONU). |

---

#### Servidor 8: `plmetrix-laws-engine` (`services/plmetrix`)
*Modelado matemático de leyes bibliométricas clásicas y fases de crecimiento.*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 8.1 | `analyze_lotka_law` | `data` (distribución autor-artículo) | Ajusta Ley de Productividad de Lotka (An = A1 / n^c), exponente c, R^2 y prueba Kolmogorov-Smirnov. |
| 8.2 | `analyze_bradford_law` | `data` (artículos por revista) | Calcula Ley de Dispersión de Bradford en 3 zonas, multiplicador k y extrae revistas del núcleo Core. |
| 8.3 | `analyze_price_index` | `text` o `references_years` | Calcula el Índice de Inmediatez de Price (% de referencias en los últimos 5 años). |
| 8.4 | `analyze_scientific_growth_phases` | `data` (series temporales anuales) | Ajusta modelos exponencial y logístico clasificando la fase de madurez del campo científico. |

---

#### Servidor 9: `revistaslatam-journals-engine` (`services/revistaslatam`)
*Benchmarking editorial, Acceso Abierto Diamante y evaluación de revistas científicas.*

| # | Herramienta | Parámetros Principales | Descripción |
|---|---|---|---|
| 9.1 | `get_journal_impact_profile` | `journal_issn_or_name` | Perfil cienciométrico de revista (FWCI promedio, percentiles normalizados, % Top 10%, indexación). |
| 9.2 | `compare_journals_benchmarking` | `journal_identifiers` (lista de ISSNs o nombres) | Comparación simultánea de revistas en impacto normalizado, volumen, internacionalización y vía OA. |
| 9.3 | `analyze_country_editorial_landscape` | `country_code` (default: MX) | Análisis del ecosistema editorial nacional: Acceso Abierto Diamante vs Gold y diversidad lingüística (ES/PT/EN). |

---

## 3. Catálogo Consolidado de Skills de Antigravity (`.agents/skills/`)

Para que el agente ejecute workflows complejos orquestando múltiples servidores MCP, se contemplan las **11 Skills** de conocimiento metodológico:

| # | Skill | Directorio | Propósito |
|---|---|---|---|
| 1 | `openalex-search-engineer` | `.agents/skills/openalex-search-engineer/` | Formulación óptima de queries tokenizadas sobre OpenAlex ClickHouse local. |
| 2 | `som-methodological-expert` | `.agents/skills/som-methodological-expert/` | Selección de topología, tamaño de malla, épocas e interpretación de U-Matrix. |
| 3 | `scientometrics-incites-expert` | `.agents/skills/scientometrics-incites-expert/` | Protocolos de benchmarking institucional Clarivate InCites y trayectorias PathSOM. |
| 4 | `bibliometric-network-analyst` | `.agents/skills/bibliometric-network-analyst/` | Ingesta de formatos WoS/Scopus y particionamiento de comunidades Louvain. |
| 5 | `semantic-manifold-expert` | `.agents/skills/semantic-manifold-expert/` | Estimación de dimensión intrínseca (MLE) y compresión semántica UMAP. |
| 6 | `graphrag-scientific-intelligence` | `.agents/skills/graphrag-scientific-intelligence/` | Consultas híbridas GraphRAG cruzando Neo4j, Qdrant y padrón SNII. |
| 7 | `research-fronts-detection-expert`| `.agents/skills/research-fronts-detection-expert/` | Detección multimodal de frentes (Leiden Salton >= 0.1, SPECTER2 HDBSCAN). |
| 8 | `geopolitical-science-mapping` | `.agents/skills/geopolitical-science-mapping/` | Cartografía de colaboración científica internacional y alineación con ODS. |
| 9 | `classical-bibliometrics-laws` | `.agents/skills/classical-bibliometrics-laws/` | Modelado y validación de leyes de Lotka, Bradford, Zipf y Price. |
| 10 | `journal-editorial-intelligence` | `.agents/skills/journal-editorial-intelligence/` | Evaluación de calidad editorial, indexación DOAJ/SciELO y vía Diamante. |
| 11 | `knomap-unified-orchestrator` | `.agents/skills/knomap-unified-orchestrator/` | Orquestación end-to-end multi-proyecto desde datos crudos hasta mapas SOM y reportes. |

---

## 4. Estructura de Archivos del Monorepo `sos-mcp-services`

```
C:\Users\jlja\Documents\Proyectos\sos-mcp-services\
├── README.md                          # Guía técnica
├── docker-compose.yml                  # Orquestación de los 6 microservicios
├── requirements.txt                   # Dependencias globales de Python
├── .env.example                       # Variables de entorno
├── mcp_config.local.json               # Configuración stdio para Antigravity IDE (dev)
├── mcp_config.remote.json              # Configuración HTTP/SSE para Antigravity IDE (prod)
│
├── docs/
│   └── plan_implementacion_sos_mcp.md # Este plan maestro
│
├── shared/                            # Módulos transversales
│   ├── __init__.py
│   ├── config.py                      # Variables de entorno y DB settings
│   ├── clickhouse.py                  # Cliente y pool de ClickHouse
│   └── models.py                      # Pydantic models compartidos
│
└── services/                          # Microservicios con endpoints MCP
    ├── knomap/                        # knoMap Suite (Puerto 8001)
    │   ├── Dockerfile, requirements.txt, mcp_server.py
    │   └── tools/
    │       ├── som_tools.py           # Tools 2.1 - 2.4 (SOM Engine)
    │       ├── bibliometrics_tools.py # Tools 3.1 - 3.2 (Bibliometrics & VOS)
    │       ├── incites_tools.py       # Tools 4.1 - 4.4 (InCites Explorer)
    │       └── semantic_tools.py      # Tools 5.1 - 5.4 (Semantic UMAP)
    │
    ├── sinapsisai/                    # SinapsisAI / RAGs (Puerto 8002)
    │   ├── Dockerfile, requirements.txt, mcp_server.py
    │   └── tools/
    │       ├── snii_tools.py          # Tools 6.3, 6.5 (Padrón SNII & Perfiles)
    │       └── graph_tools.py         # Tools 6.1, 6.2, 6.4 (Cypher & Qdrant)
    │
    ├── plmetrix/                      # PLmetrix (Puerto 8003)
    │   ├── Dockerfile, requirements.txt, mcp_server.py
    │   └── tools/
    │       └── laws_tools.py          # Tools 8.1 - 8.4 (Leyes y Fases de Crecimiento)
    │
    ├── revistaslatam/                 # RevistasLATAM (Puerto 8004)
    │   ├── Dockerfile, requirements.txt, mcp_server.py
    │   └── tools/
    │       └── journals_tools.py      # Tools 9.1 - 9.3 (Benchmarking e Impacto Editorial)
    │
    ├── topics/                        # Topics (Puerto 8005)
    │   ├── Dockerfile, requirements.txt, mcp_server.py
    │   └── tools/
    │       ├── fronts_tools.py        # Tools 7.1 - 7.2 (Research Fronts v5)
    │       └── geopolitics_tools.py   # Tools 7.3 - 7.5 (Geopolítica, OA, ODS)
    │
    └── openalex/                      # OpenAlex Gateway (Puerto 8006)
        ├── Dockerfile, requirements.txt, mcp_server.py
        └── tools/
            ├── search_tools.py        # Tools 1.1 - 1.2 (Búsquedas Difusas)
            └── entity_tools.py        # Tools 1.3 - 1.4 (Entidades y Agregaciones SQL)
```

---

## 5. Fases de Ejecución

1. **Fase 1: Gateway OpenAlex & Shared Pool (`services/openalex`)**  
   - Conectar cliente ClickHouse local (`shared/clickhouse.py`).
   - Implementar las 4 herramientas de búsqueda y agregación (1.1 - 1.4).

2. **Fase 2: Modelos Matemáticos PLmetrix (`services/plmetrix`)**  
   - Importar funciones de ajuste de `PLmetrix-Lab-2.0/backend/app/` (Lotka, Bradford, Price, Crecimiento).
   - Implementar herramientas 8.1 - 8.4 con validación Pydantic.

3. **Fase 3: Inteligencia Editorial RevistasLATAM (`services/revistaslatam`)**  
   - Importar métricas de `revistaslatam/src/performance_metrics.py`.
   - Implementar herramientas 9.1 - 9.3 (Impacto FWCI, Comparación, Panorama OA país).

4. **Fase 4: Padrón SNII y GraphRAG SinapsisAI (`services/sinapsisai`)**  
   - Importar consultas Neo4j y Qdrant de `Proyectos/RAGs`.
   - Implementar herramientas 6.1 - 6.5 (Cypher, Búsqueda vectorial, Perfil SNII, Desambiguación).

5. **Fase 5: Frentes de Investigación Topics (`services/topics`)**  
   - Importar pipeline multimodal v5 de `Proyectos/Topics`.
   - Implementar herramientas 7.1 - 7.5 (Leiden/Salton, Evolución longitudinal, Geopolítica, ODS).

6. **Fase 6: Suite Topológica knoMap (`services/knomap`)**  
   - Importar algoritmos SOM y de reducción de `newLabSOM`.
   - Implementar herramientas 2.1 - 2.4 (SOM), 3.1 - 3.2 (VOSviewer), 4.1 - 4.4 (InCites), 5.1 - 5.4 (UMAP Semántico).

---

## 6. Despliegue en `dinamica1` y Consumo Multi-Agente

Para desplegar en el servidor central `dinamica1`:
1. Clonar el repositorio en `dinamica1`:
   ```bash
   git clone https://github.com/tu-usuario/sos-mcp-services.git
   cd sos-mcp-services
   ```
2. Configurar variables de producción en `.env` (apuntando a ClickHouse, Neo4j y Qdrant locales en `dinamica1`).
3. Levantar con Docker:
   ```bash
   docker-compose up -d --build
   ```
4. Cualquier agente de Antigravity (en laptops o servidores de investigación) se conecta de forma remota configurando su `mcp_config.json`:
   ```json
   {
     "mcpServers": {
       "openalex_mcp": { "url": "http://dinamica1.fciencias.unam.mx:8006/sse" },
       "plmetrix_mcp": { "url": "http://dinamica1.fciencias.unam.mx:8003/sse" },
       "sinapsisai_mcp": { "url": "http://dinamica1.fciencias.unam.mx:8002/sse" },
       "topics_mcp": { "url": "http://dinamica1.fciencias.unam.mx:8005/sse" },
       "revistaslatam_mcp": { "url": "http://dinamica1.fciencias.unam.mx:8004/sse" },
       "knomap_mcp": { "url": "http://dinamica1.fciencias.unam.mx:8001/sse" }
     }
   }
   ```
