# Guía Práctica de Invocación de Skills (`sos-mcp-services`)

> **Cobertura:** Las **39 Skills** del ecosistema en [`.agents/skills/`](../.agents/skills/)  
> **Enfoque:** Cómo pedirle al agente que ejecute cada skill, qué *slash command* combinar en Antigravity y **dos prompts listos para copiar y pegar** por skill (**Uso básico** y **Uso exhaustivo**).

---

## 1. Cómo invocar las skills y combinarlas con *Slash Commands*

En Antigravity, los *slash commands* no ejecutan scripts por sí solos, sino que **configuran la estrategia de razonamiento, profundidad o flujo de trabajo del agente** mientras invocas explícitamente una o varias skills por su nombre (entre comillas invertidas, p. ej. `` `openalex-harvester` ``).

### Guía rápida de *Slash Commands*

| Slash command | Cuándo usarlo con las skills | Efecto práctico en el flujo |
|---|---|---|
| *(sin slash command)* | Tareas puntuales de una sola skill | Ejecución directa de una extracción, métrica o gráfica específica. |
| `/plan` | Estudios nuevos antes de descargar datos | Diseña la estrategia multi-etapa (GLOBAL/Huang & Porter), valida archivos de entrada y ordena dependencias antes de ejecutar. |
| `/boost` | Análisis complejos, frentes, redes, SOM y revisión profunda | Activa razonamiento profundo, comparación de técnicas en competencia y verificación rigurosa sin atajos. |
| `/goal` | Tuberías largas de principio a fin (plantillas `template-*` u orquestación) | Mantiene al agente trabajando de forma autónoma hasta entregar figuras, tablas, manuscrito `.md`, `.docx` y `.pdf`. |
| `/grill-me` | Antes de iniciar un estudio o definir preguntas de investigación | Entrevista interactiva previa para cerrar alcance, periodo, idioma (`--lang es`/`--lang en`), entidades foco y criterios de inclusión. |
| `/browser` | Después de generar tableros HTML interactivos | Lanza el subagente de navegador para abrir e inspeccionar visualmente artefactos Plotly, VOSviewer o KnoMap Force Graph. |
| `/schedule` | Vigilancia periódica de literatura o preprints | Programa cosechas recurrentes (p. ej., cada lunes) con `openalex-harvester` o `arxiv-harvester`. |
| `/teamwork` | Estudios masivos (`template-estudio-cienciometrico-exhaustivo`) o Etapa I paralela en `template-articulo-cientifico-imryd` | Coordina un enjambre (`swarm`) de agentes en paralelo con propiedad de archivos disjunta (`./evidence_vault/` o `./lab_exploration/`), tanto en 4 Olas completas como acotado a 3–4 familias de un artículo. |
| `/compact` | Sesiones largas tras múltiples corridas | Libera ventana de contexto resumiendo resultados ya persistidos en `./corpus.parquet` y `./matrices/`. |

### Principios operativos del ecosistema

1. **Workspace-First (`./corpus.parquet` → `./matrices/` → `./reportes/`):** Las skills leen y escriben archivos columnares en tu carpeta de trabajo para no saturar la memoria del chat.
2. **Arquitectura Autónoma OpenAlex-First + Acelerador Opcional ClickHouse:** Todas las skills de cosecha y análisis funcionan de manera autónoma vía APIs públicas o archivos locales; si tu entorno define `CLICKHOUSE_HOST`, las skills habilitadas activan automáticamente la vía rápida local sin *JOINs* (ver [`clickhouse_accelerator.md`](../.agents/skills/bibliometric-search-strategist/references/clickhouse_accelerator.md)).
3. **Idioma (`--lang`):** Las salidas de CLI usan inglés por defecto (`--lang en`); cuando interactúes en español y quieras etiquetas de gráficas y reportes en español, indícalo en el prompt o solicita `--lang es`.

---

## 2. Índice General de las 39 Skills

1. **Cosecha de Literatura y Textos Completos (6):** [`arxiv-harvester`](#21-arxiv-harvester) · [`open-access-pdf-downloader`](#22-open-access-pdf-downloader) · [`openalex-harvester`](#23-openalex-harvester) · [`pubmed-harvester`](#24-pubmed-harvester) · [`scopus-harvester`](#25-scopus-harvester) · [`semantic-scholar-harvester`](#26-semantic-scholar-harvester)
2. **Delimitación, Búsqueda y Motores ClickHouse / México (5):** [`bibliometric-search-strategist`](#31-bibliometric-search-strategist) · [`infotlachia-scholar-intelligence`](#32-infotlachia-scholar-intelligence) · [`openalex-mexico-clickhouse`](#33-openalex-mexico-clickhouse) · [`openalex-search-engineer`](#34-openalex-search-engineer) · [`snii-identity-resolver`](#35-snii-identity-resolver)
3. **Métricas, Leyes Clásicas y Paquetes Externos (5):** [`bibliometrix-guide`](#41-bibliometrix-guide) · [`classical-bibliometrics-laws`](#42-classical-bibliometrics-laws) · [`scientometrics-incites-expert`](#43-scientometrics-incites-expert) · [`tlachia-metrics-engine`](#44-tlachia-metrics-engine) · [`tlachia-metrics-handler`](#45-tlachia-metrics-handler)
4. **Redes, Frentes de Investigación y Revisión Profunda (4):** [`bibliometric-network-analyst`](#51-bibliometric-network-analyst) · [`deep-literature-researcher`](#52-deep-literature-researcher) · [`research-fronts-detection-expert`](#53-research-fronts-detection-expert) · [`topics-research-fronts-intelligence`](#54-topics-research-fronts-intelligence)
5. **Cartografía Topológica SOM y Variedades Semánticas (5):** [`knomap-project-resumer`](#61-knomap-project-resumer) · [`neural-longitudinal-mapping`](#62-neural-longitudinal-mapping) · [`semantic-manifold-expert`](#63-semantic-manifold-expert) · [`som-methodological-expert`](#64-som-methodological-expert) · [`som-trajectory-mapping`](#65-som-trajectory-mapping)
6. **Geopolítica, Ciencia Abierta, ODS y GraphRAG (5):** [`geopolitical-collaboration-analyst`](#71-geopolitical-collaboration-analyst) · [`geopolitical-science-mapping`](#72-geopolitical-science-mapping) · [`graphrag-scientific-intelligence`](#73-graphrag-scientific-intelligence) · [`open-access-monitor`](#74-open-access-monitor) · [`sdg-impact-intelligence`](#75-sdg-impact-intelligence)
7. **Inteligencia Editorial y Revistas Iberoamericanas (3):** [`journal-editorial-intelligence`](#81-journal-editorial-intelligence) · [`revistaslatam-editorial-intelligence`](#82-revistaslatam-editorial-intelligence) · [`revistaslatam-indicators-engine`](#83-revistaslatam-indicators-engine)
8. **Orquestación Maestra y Plantillas de Estudios Completos (6):** [`knomap-unified-orchestrator`](#91-knomap-unified-orchestrator) · [`template-articulo-cientifico-imryd`](#92-template-articulo-cientifico-imryd) · [`template-estudio-cienciometrico-exhaustivo`](#96-template-estudio-cienciometrico-exhaustivo) · [`template-informe-tecnico-institucional`](#93-template-informe-tecnico-institucional) · [`template-policy-brief-gobernanza`](#94-template-policy-brief-gobernanza) · [`template-radar-frentes-investigacion`](#95-template-radar-frentes-investigacion)

---

## Grupo 1 · Cosecha de Literatura y Textos Completos

### 2.1 `arxiv-harvester`
* **Definición:** [`SKILL.md`](../.agents/skills/arxiv-harvester/SKILL.md) · **Script:** `arxiv_harvest_cli.py` (`search`, `fetch-by-ids`) · **Slash command recomendado:** Ninguno (puntual) o `/schedule` (vigilancia).
* **Uso básico:**
  ```markdown
  Usa la skill `arxiv-harvester` para descargar los 50 preprints más recientes de arXiv en la categoría `cs.AI` sobre "causal reasoning" y guárdalos en `./arxiv_causal.parquet` con etiquetas en español (`--lang es`).
  ```
* **Uso exhaustivo:**
  ```markdown
  /schedule Todos los lunes a las 08:00 ejecuta la skill `arxiv-harvester`:
  1. Usa `search` en categorías `cs.CL`, `cs.LG` y `stat.ML` con `--query "counterfactual reasoning OR structural causal model"` y `--limit 200`, guardando en `./corpora/arxiv_raw.parquet`.
  2. Si ya tengo una lista de IDs semilla en `./arxiv_ids.txt`, ejecuta también `fetch-by-ids` (`--id-list`) y fusiona sin duplicados.
  3. Exporta una copia tabular en `.csv` y `.json` y repórtame los títulos nuevos de la última semana.
  ```

### 2.2 `open-access-pdf-downloader`
* **Definición:** [`SKILL.md`](../.agents/skills/open-access-pdf-downloader/SKILL.md) · **Script:** `download_oa_pdfs.py` · **Slash command recomendado:** Ninguno o `/teamwork`.
* **Uso básico:**
  ```markdown
  Usa la skill `open-access-pdf-downloader` para descargar los PDFs en Acceso Abierto de esta lista de DOIs (`10.1109/JPROC.2021.3058954`, `10.48550/arxiv.2305.00050`) en `./pdf_cache/` y extrae su texto plano con `--extract-text`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta `open-access-pdf-downloader` sobre los candidatos priorizados en `./snowball_candidates.csv`:
  1. Usa `--input ./snowball_candidates.csv`, `--output ./revision_fulltext/`, `--limit 30`, `--delay 1.0`, `--timeout 25` y `--extract-text` (`--lang es`).
  2. Verifica encabezados binarios `%PDF-`, aplica la cascada de resolución (OpenAlex `best_oa_location`, arXiv, PMC y repositorios institucionales).
  3. Genera `download_manifest.json`, `download_manifest.csv` y `download_report.md` con el desglose PRISMA de exitosos, paywalled y fallidos.
  ```

### 2.3 `openalex-harvester`
* **Definición:** [`SKILL.md`](../.agents/skills/openalex-harvester/SKILL.md) · **Script:** `openalex_harvest_cli.py` (`fetch-works`, `fetch-author-works`, `fetch-institution-works`) · **Slash command recomendado:** `/plan` o directo.
* **Uso básico:**
  ```markdown
  Usa la skill `openalex-harvester` (`fetch-works`) para descargar hasta 500 artículos de OpenAlex sobre `"federated learning privacy"` entre `--year-from 2020` y `--year-to 2026` y guárdalos en `./corpus.parquet`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /plan Ejecuta una cosecha canónica completa vía API de OpenAlex con `openalex-harvester`:
  1. Corre `fetch-works` usando la consulta booleana validada en `./queries/openalex_query.txt` con paginación por cursor, `--year-from 2015`, `--year-to 2026`, `--limit 5000` y `--output ./corpus.parquet` (conservando `referenced_works`, `all_country_codes`, `keywords`, vías OA, APCs y FWCI).
  2. Descarga aparte la producción de la institución ROR `https://ror.org/01tmp8f25` (UNAM) con `fetch-institution-works` en `./unam_corpus.parquet` y audita el conteo por año y tasa de Open Access (`--lang es`).
  ```

### 2.4 `pubmed-harvester`
* **Definición:** [`SKILL.md`](../.agents/skills/pubmed-harvester/SKILL.md) · **Script:** `pubmed_harvest_cli.py` (`fetch-works`, `fetch-author-works`) · **Slash command recomendado:** Ninguno o `/plan`.
* **Uso básico:**
  ```markdown
  Usa `pubmed-harvester` (`fetch-works`) para extraer de NCBI PubMed hasta 300 registros sobre `"gut microbiota depression"` desde 2020 y guárdalos en `./pubmed_corpus.parquet`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta `pubmed-harvester` en modo completo:
  1. Descarga con `fetch-works` la ecuación MeSH en `./queries/pubmed_query.txt` filtrando `--year-from 2018 --year-to 2026 --affiliation "Mexico" --limit 2000 --output ./data/pubmed_mx.parquet`.
  2. Complementa con `fetch-author-works` para el investigador indicado, normaliza autores/DOIs/PMIDs al esquema canónico Parquet/CSV y respeta el *rate limit* de NCBI (`--lang es`).
  ```

### 2.5 `scopus-harvester`
* **Definición:** [`SKILL.md`](../.agents/skills/scopus-harvester/SKILL.md) · **Script:** `scopus_harvest_cli.py` (`search`, `author-profile`, `affil-works`) · **Slash command recomendado:** Ninguno o `/plan` *(requiere `SCOPUS_API_KEY` / `--api-key`)*.
* **Uso básico:**
  ```markdown
  Usa `scopus-harvester` (`search`) con mi API key de Elsevier en la variable de entorno para buscar `"digital twin manufacturing"` (`--year-from 2021 --limit 200`) y exportar `./scopus_corpus.parquet`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta `scopus-harvester` sobre Scopus API (`--lang es`):
  1. Con `search`, ejecuta la sintaxis de `./queries/scopus_query.txt` (`--year-from 2016 --year-to 2026 --limit 2000 --output ./data/scopus_works.parquet`).
  2. Extrae el perfil del autor con `author-profile --author-id <ID>` y la producción institucional con `affil-works --af-id <AF_ID>` para cruzar DOIs con `./corpus.parquet`.
  ```

### 2.6 `semantic-scholar-harvester`
* **Definición:** [`SKILL.md`](../.agents/skills/semantic-scholar-harvester/SKILL.md) · **Script:** `s2_harvest_cli.py` (`search-papers`, `citation-graph`, `author-papers`) · **Slash command recomendado:** Ninguno o `/boost`.
* **Uso básico:**
  ```markdown
  Usa `semantic-scholar-harvester` (`search-papers`) para buscar los 100 artículos más relevantes sobre `"mechanistic interpretability transformers"` con sus abstracts y guárdalos en `./s2_papers.parquet`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Enriquece mi estudio con `semantic-scholar-harvester` (`--lang es`):
  1. Ejecuta `search-papers` con `--query "sparse autoencoders causal circuits" --year-from 2022 --year-to 2026 --limit 300 --output ./data/s2_circuits.parquet`.
  2. Para los 5 artículos semilla (`--paper-id`), ejecuta `citation-graph` para extraer citas entrantes, referencias salientes y contextos de citación en `./data/s2_graph.json`, y extrae la obra reciente de autores clave con `author-papers --author-id <ID>`.
  ```

---

## Grupo 2 · Delimitación, Búsqueda y Motores ClickHouse / México

### 3.1 `bibliometric-search-strategist`
* **Definición:** [`SKILL.md`](../.agents/skills/bibliometric-search-strategist/SKILL.md) · **Script:** `query_synthesizer.py` · **Slash command recomendado:** `/plan` o `/grill-me`.
* **Uso básico:**
  ```markdown
  /plan Usa la skill `bibliometric-search-strategist` para construir una estrategia de búsqueda por bloques conceptuales sobre "IA generativa en educación superior" y transpílala a OpenAlex API (`openalex_query.txt`), Scopus, WoS y PubMed.
  ```
* **Uso exhaustivo:**
  ```markdown
  /plan Usa `bibliometric-search-strategist` siguiendo el protocolo multi-etapa de Huang & Porter y la directriz GLOBAL (ISSI):
  1. Toma mis 10 artículos semilla en `./seeds.csv`, realiza *Pearl Growing* para extraer bloques conceptuales (`blocks`) y valida términos con `query_synthesizer.py --action validate` evitando comodines peligrosos.
  2. Configura `./search_config.json` y ejecuta `--action transpile` (añadiendo `--include-clickhouse` solo si `CLICKHOUSE_HOST` está activo) generando `openalex_query.txt`, `wos_query.txt`, `scopus_query.txt`, `pubmed_query.txt` y `global_audit.md` en `./queries/`.
  3. Mide el *Golden Standard Recall* contra las semillas y documenta falsos positivos/negativos antes de cosechar.
  ```

### 3.2 `infotlachia-scholar-intelligence`
* **Definición:** [`SKILL.md`](../.agents/skills/infotlachia-scholar-intelligence/SKILL.md) · **Script:** `infotlachia_cli.py` (`query-researcher`, `query-entity`, `query-institution`, `national-overview`, `sql-safe`) · **Slash command recomendado:** Ninguno *(requiere acceso local a `analytics_cache.duckdb`)*.
* **Uso básico:**
  ```markdown
  Usa `infotlachia-scholar-intelligence` (`query-institution`) para consultar los indicadores precalculados de la UNAM en `analytics_cache.duckdb` y exporta el resumen a `./unam_infotlachia.json`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Usa `infotlachia-scholar-intelligence` (`--lang es`) sobre `analytics_cache.duckdb`:
  1. Obtén el panorama nacional de referencia con `national-overview` en `./reportes/panorama_mx.json`.
  2. Consulta la dependencia con `query-entity --entity "Instituto de Neurobiología"` y el perfil de investigadoras/es SNII con `query-researcher --name "<Nombre>" --limit 20`.
  3. Ejecuta una consulta agregada segura en solo lectura con `sql-safe` comparando FWCI, gasto APC USD, Top 10% y Gini frente a 3 centros pares.
  ```

### 3.3 `openalex-mexico-clickhouse`
* **Definición:** [`SKILL.md`](../.agents/skills/openalex-mexico-clickhouse/SKILL.md) · **Script:** `shared_scripts/openalex_mexico_cli.py` (requiere acceso ClickHouse México `rag.works_academic_all`) · **Slash command recomendado:** `/plan` o `/goal`.
* **Uso básico:**
  ```markdown
  Usa `openalex-mexico-clickhouse` para obtener la producción científica de México en "energía solar" entre 2020 y 2025, con distribución por institución y vías de Acceso Abierto (sin JOINs en ClickHouse).
  ```
* **Uso exhaustivo:**
  ```markdown
  /goal Ejecuta con `openalex-mexico-clickhouse` un estudio nacional completo sobre `rag.works_academic_all` respetando estrictamente la regla de **CERO JOINs**:
  1. Resuelve los códigos ROR y sedes de UNAM, IPN, Cinvestav y UAM; extrae el corpus filtrado a `./corpus_mx.parquet`.
  2. Calcula agregaciones de las 6 vías de Acceso Abierto (Diamante vs. Gold APC), gasto en APC USD, percentiles Top 10%/1% y cruce con el padrón SNII vigente.
  3. Si hay embeddings 768d Nomic disponibles, realiza búsqueda semántica híbrida y genera tableros Plotly interactivos y tarjetas PNG (200/300 DPI) en `./reportes/`.
  ```

### 3.4 `openalex-search-engineer`
* **Definición:** [`SKILL.md`](../.agents/skills/openalex-search-engineer/SKILL.md) · **Script:** `openalex_search_cli.py` (`search-authors`, `search-works`, `get-entity`, `aggregate`) · **Slash command recomendado:** Ninguno o `/plan` *(requiere ClickHouse `rag.works_flat` cuando `CLICKHOUSE_HOST` está configurado)*.
* **Uso básico:**
  ```markdown
  Usa `openalex-search-engineer` (`search-works`) para extraer en ClickHouse (`rag.works_flat`, sin JOINs) los trabajos globales de 2020–2026 con `"quantum error correction"` en título/keywords y guárdalos en `./corpus.parquet`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Usa `openalex-search-engineer` (`--lang es`) sobre el snapshot local de ClickHouse respetando CERO JOINs y funciones nativas de arreglos:
  1. Ejecuta `search-authors --name "<Apellidos>" --institution-ror "<ROR>"` probando permutaciones de apellidos hispanos y normalización diacrítica.
  2. Lanza `aggregate` sobre `--topic-id` / `--country` / `--year-min 2015 --year-max 2026` para obtener el **denominador exacto mundial** (necesario para calcular índices de especialización $AI$ / $CShareD$).
  3. Extrae el corpus completo mediante `search-works --sql-file ./queries/clickhouse_query.sql --limit 50000 --output ./corpus.parquet`.
  ```

### 3.5 `snii-identity-resolver`
* **Definición:** [`SKILL.md`](../.agents/skills/snii-identity-resolver/SKILL.md) · **Script:** `snii_resolver_cli.py` (`resolve`, `profile`) · **Slash command recomendado:** Ninguno.
* **Uso básico:**
  ```markdown
  Usa `snii-identity-resolver` (`resolve`) para verificar el nivel SNII 2025, área del conocimiento, vigencia, ORCID y Scopus ID de los autores listados en `./claustro.csv`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta `snii-identity-resolver` (`--lang es`) para desambiguar el claustro académico completo de la dependencia:
  1. Corre `resolve` cruzando `--name`, `--institution` y `--dependency` para resolver homónimos y variantes de apellidos compuestos en el Padrón SNII 2025.
  2. Genera el perfil consolidado con `profile` en `./matrices/snii_resolved.json`, desglosando distribución por nivel (Candidato, I, II, III, Emérito), áreas del conocimiento y cobertura de identificadores persistentes (`ORCID` / `OpenAlex`).
  ```

---

## Grupo 3 · Métricas, Leyes Clásicas y Paquetes Externos

### 4.1 `bibliometrix-guide`
* **Definición:** [`SKILL.md`](../.agents/skills/bibliometrix-guide/SKILL.md) · **Scripts:** `bibliometrix_cli.py` (`summary`, `callon-map`, `convert`, `generate-script`, `run`) y `bibliometrix_runner.R` · **Slash command recomendado:** `/boost` *(requiere R + paquete `bibliometrix`)*.
* **Uso básico:**
  ```markdown
  Usa `bibliometrix-guide` (`callon-map`) sobre `./corpus.parquet` tomando `--field DE --top-terms 50` para construir el diagrama estratégico de Callon (Centralidad vs. Densidad) y guardar la gráfica en `./reportes/callon_map.png`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Ejecuta un análisis completo con el paquete canónico R `bibliometrix` mediante `bibliometrix-guide` (`--lang es`):
  1. Convierte e ingesta el corpus con `convert` / `summary` validando campos `DE`, `ID`, `CR` y `AU`.
  2. Calcula el mapa temático de Callon (`callon-map --top-terms 60 --min-freq 5`) para aislar temas motores, básicos, emergentes/declinantes y de nicho.
  3. Genera con `generate-script --analysis thematic` un script reproducible `.R` de evolución temática longitudinal por periodos y ejecútalo con `run`, guardando salidas y figuras en `./reportes/bibliometrix/`.
  ```

### 4.2 `classical-bibliometrics-laws`
* **Definición:** [`SKILL.md`](../.agents/skills/classical-bibliometrics-laws/SKILL.md) · **Script:** `bibliometric_laws_cli.py` (`lotka`, `bradford`, `price-index`, `growth-phase`) · **Slash command recomendado:** `/boost`.
* **Uso básico:**
  ```markdown
  Usa `classical-bibliometrics-laws` (`growth-phase` y `lotka`) sobre `./corpus.parquet` para ajustar el crecimiento de publicaciones y la productividad autoral, guardando gráficas en español en `./reportes/`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Aplica las cuatro leyes bibliométricas clásicas con `classical-bibliometrics-laws` sobre `./corpus.parquet` (`--lang es`, `--dpi 300`):
  1. `growth-phase`: ajusta crecimiento exponencial vs. logístico (reportando $R^2$, tasa $\alpha$, tiempo de duplicación $t_d$ y punto de inflexión $\tau$, excluyendo años calendario incompletos si distorsionan la saturación).
  2. `lotka`: compara conteo completo (`--counting full`) vs. fraccional con prueba Kolmogorov-Smirnov ($D_{\max}$ vs. $D_{\text{crit}}$) exportando `lotka_distribution_es.png` y HTML Plotly.
  3. `bradford` (formulación continua de Egghe) para identificar zonas nucleares de revistas y `price-index` para medir obsolescencia/vida media de las referencias.
  ```

### 4.3 `scientometrics-incites-expert`
* **Definición:** [`SKILL.md`](../.agents/skills/scientometrics-incites-expert/SKILL.md) · **Script:** `incites_cli.py` (`inspect`, `unit-matrix`, `trend`, `growth-matrix`) · **Slash command recomendado:** `/plan` o `/boost`.
* **Uso básico:**
  ```markdown
  Usa `scientometrics-incites-expert` (`inspect`) para auditar el archivo exportado de Clarivate InCites en `./datos_incites/` e identificar unidades, periodos e indicadores disponibles.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Procesa mi exportación de Clarivate InCites con `scientometrics-incites-expert` (`--lang es`):
  1. Corre `inspect` sobre `./incites_export/` para inventariar organizaciones, categorías WoS, áreas ESI, ODS y fuentes.
  2. Extrae matrices multidimensionales por ventanas con `unit-matrix --unit Organizations --recent-5years --min-threshold 20` listas para entrenar el SOM estático.
  3. Genera series anuales longitudinales con `trend --smoothing cma` para PathSOM y construye la matriz estratégica de crecimiento con `growth-matrix` (CAGR % vs. volumen) con figuras a `--dpi 300` en `./reportes/`.
  ```

### 4.4 `tlachia-metrics-engine`
* **Definición:** [`SKILL.md`](../.agents/skills/tlachia-metrics-engine/SKILL.md) · **Script:** `tlachia_metrics_cli.py` (`calculate-summary`, `summary`, `annual-series`, `period-series`, `aggregate-by`, `by-entity`, `gini-diversity`) · **Slash command recomendado:** Ninguno o `/plan`.
* **Uso básico:**
  ```markdown
  Usa `tlachia-metrics-engine` sobre `./corpus.parquet` para calcular el resumen global (`summary`) y la matriz completa de entidades por país (`by-entity --level country --min-docs 5`) en `./matrices/`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta la batería completa sin truncar dimensiones con `tlachia-metrics-engine` (`--corpus ./corpus.parquet --lang es`):
  1. Genera `summary` en `./reportes/summary_metrics.json` y `.md`.
  2. Construye matrices completas de 46 columnas (42 indicadores + 4 metadatos) con `by-entity` para `--level country`, `--level institution` (`--min-docs 3`), `--level author` (`--top 100`) y `--level source` en `./matrices/`.
  3. Calcula series anuales suavizadas con `annual-series --cma-window 3`, ventanas multianuales con `period-series --window 3 --step 3` y concentración/diversidad con `gini-diversity`.
  ```

### 4.5 `tlachia-metrics-handler`
* **Definición:** [`SKILL.md`](../.agents/skills/tlachia-metrics-handler/SKILL.md) · **Script:** `tlachia_handler_cli.py` (`inspect`, `unit-matrix`, `trend`, `works-meta`) · **Slash command recomendado:** Ninguno.
* **Uso básico:**
  ```markdown
  Usa `tlachia-metrics-handler` (`inspect`) para revisar el contenido del paquete `./export_tlachia_metrics.zip` y listar las unidades e indicadores disponibles.
  ```
* **Uso exhaustivo:**
  ```markdown
  Desempaqueta y prepara datos desde `./export_tlachia_metrics.zip` con `tlachia-metrics-handler` (`--lang es`):
  1. Ejecuta `inspect` para validar unidades (`Locations`, `Organizations`, `Sources`, `Topics`).
  2. Extrae con `unit-matrix --unit Organizations --min-docs 10 --period-mode window` la matriz de indicadores lista para SOM en `./matrices/org_matrix.parquet` y las series temporales con `trend --smoothing cma`.
  3. Recupera con `works-meta` la tabla canónica de documentos en `./corpus.parquet` para análisis de redes.
  ```

---

## Grupo 4 · Redes, Frentes de Investigación y Revisión Profunda

### 5.1 `bibliometric-network-analyst`
* **Definición:** [`SKILL.md`](../.agents/skills/bibliometric-network-analyst/SKILL.md) · **Script:** `biblio_network_cli.py` (`build-network`, `render-knomap`, `render-vosviewer`, `export-som-matrix`, `sequential-networks`, `period-networks`, `detect-communities`, `calculate-centralities`, `export-graph`) · **Slash command recomendado:** `/boost` + `/browser`.
* **Uso básico:**
  ```markdown
  Usa `bibliometric-network-analyst` (`build-network` + `render-vosviewer`) sobre `./corpus.parquet` para generar la red de co-ocurrencia de palabras clave (`--unit keywords --min-freq 5`) y exporta `./reportes/network_keywords.html`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Construye y analiza redes multimodales con `bibliometric-network-analyst` sobre `./corpus.parquet` (`--lang es`):
  1. Genera redes con normalización `--normalization association` y partición Leiden (`detect-communities`) + `calculate-centralities` para `--network-type coauthorship --unit countries`, `cooccurrence --unit keywords` y `coupling --unit works`.
  2. Renderiza ambos visores interactivos con `render-knomap` y `render-vosviewer`, además de exportar la matriz topológica al SOM mediante `export-som-matrix` y redes temporales mediante `period-networks`.
  3. Abre las redes HTML con `/browser` para comprobar etiquetas, clusters y nodos centrales.
  ```

### 5.2 `deep-literature-researcher`
* **Definición:** [`SKILL.md`](../.agents/skills/deep-literature-researcher/SKILL.md) · **Script:** `citation_snowball.py` · **Slash command recomendado:** `/boost`.
* **Uso básico:**
  ```markdown
  Usa `deep-literature-researcher` (`citation_snowball.py --mode both --top-citations 25 --lang es`) partiendo de los DOIs semilla `10.1109/JPROC.2021.3058954` y `10.52202/075280-1353`, y genera la matriz de síntesis en `./revision_literatura/`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Ejecuta una revisión profunda completa con `deep-literature-researcher` (`--lang es`):
  1. Formaliza criterios de inclusión/exclusión (`PCC`) y corre `citation_snowball.py --mode both --min-cocitations 2 --top-citations 35 --download-oa-pdfs --fulltext-limit 20 --extract-text --output ./revision_literatura/sintesis/`.
  2. Inspecciona los textos completos en `sintesis/text/` para llenar la **Matriz Canónica de Síntesis** (registrando `N/A` si un dato no consta, nunca inventando cifras), capturando limitaciones y trabajo futuro declarado por los autores.
  3. Redacta el **borrador narrativo extenso del Estado del Arte** (`literature_review_draft.md`, compilado también a `.docx` y `.pdf`) en prosa temática continua, con sección explícita que separe el **trabajo futuro señalado por los autores** frente a los **caminos no explorados valorados por el agente**, y verifica 1:1 todas las referencias en OpenAlex.
  ```

### 5.3 `research-fronts-detection-expert`
* **Definición:** [`SKILL.md`](../.agents/skills/research-fronts-detection-expert/SKILL.md) · **Script:** Delega ejecución a `topics-research-fronts-intelligence` · **Slash command recomendado:** `/boost`.
* **Uso básico:**
  ```markdown
  Usa `research-fronts-detection-expert` sobre `./corpus.parquet` para comparar qué representación de red (acoplamiento bibliográfico vs. co-citación) revela con mayor claridad los frentes actuales de mi corpus.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Aplica la metodología multimodal de `research-fronts-detection-expert` sobre `./corpus.parquet`:
  1. Evalúa experimentalmente en paralelo acoplamiento bibliográfico (frentes emergentes recientes), co-citación (bases intelectuales fundacionales) y OpenAlex Topics usando partición Leiden CPM.
  2. Compara densidad de aristas, modularidad, coherencia semántica y tamaño de clústeres para decidir y justificar qué método modela mejor la estructura del campo y qué variantes deben descartarse en el reporte final.
  ```

### 5.4 `topics-research-fronts-intelligence`
* **Definición:** [`SKILL.md`](../.agents/skills/topics-research-fronts-intelligence/SKILL.md) · **Scripts:** `build_bibliometric_fronts.py` y `track_longitudinal_lineages.py` · **Slash command recomendado:** `/boost` + `/browser`.
* **Uso básico:**
  ```markdown
  Usa `topics-research-fronts-intelligence` (`build_bibliometric_fronts.py --input-file ./corpus.parquet --method coupling --similarity-metric salton --algorithm leiden --lang es`) para detectar los frentes activos y exportar `./reportes/fronts_summary.csv`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Ejecuta el rastreo completo de frentes y genealogía temporal con `topics-research-fronts-intelligence` (`--lang es`):
  1. Corre `build_bibliometric_fronts.py` sobre `./corpus.parquet` (o vía API de OpenAlex con `--query` si es *standalone*, usando ClickHouse solo si `CLICKHOUSE_HOST` está configurado) con `--method coupling --similarity-metric salton --algorithm leiden --partition-type cpm --min-cluster-size 5`.
  2. Ejecuta `track_longitudinal_lineages.py` sobre `works_with_fronts.parquet` (`--window-width 3 --step-size 1 --persistence-threshold 0.15`) para calcular Información Mutua Ajustada (AMI), detectar eventos evolutivos (`Persistence`, `Split`, `Merge`, `Genesis`) y generar `./reportes/alluvial_lineages.html`.
  ```

---

## Grupo 5 · Cartografía Topológica SOM y Variedades Semánticas

### 6.1 `knomap-project-resumer`
* **Definición:** [`SKILL.md`](../.agents/skills/knomap-project-resumer/SKILL.md) · **Script:** `knomap_resume_cli.py` (`inspect`, `extract-workspace`, `update-knomap`, `create-knomap`) · **Slash command recomendado:** `/plan`.
* **Uso básico:**
  ```markdown
  Usa `knomap-project-resumer` (`inspect` y `extract-workspace`) para abrir `./mi_proyecto.knoMap`, reconstruir matrices/artefactos en `./workspace/` y resumir los mapas e historial del asistente previos.
  ```
* **Uso exhaustivo:**
  ```markdown
  /plan Reanuda y empaqueta mi investigación con `knomap-project-resumer` (`--lang es`):
  1. Inspecciona `./proyecto_base.knoMap` con `inspect` y extrae todos los módulos científicos, cachés y figuras al workspace con `extract-workspace --workspace-dir ./ws_knomap/`.
  2. Tras recalcular el SOM y redactar notas analíticas en `./notas_som.md`, actualiza el paquete con `update-knomap --add-note-title "Diagnóstico Big SOM" --add-note-file ./notas_som.md --add-html-artifact ./reportes/som_dashboard.html --som-state-file ./reportes/som_state.json --output ./proyecto_actualizado.knoMap` (o usa `create-knomap` si partes desde cero).
  ```

### 6.2 `neural-longitudinal-mapping`
* **Definición:** [`SKILL.md`](../.agents/skills/neural-longitudinal-mapping/SKILL.md) · **Script:** `neural_longitudinal_cli.py` (`prepare`, `train`, `plot`, `analyze`, `report`) · **Slash command recomendado:** `/goal` o `/boost`.
* **Uso básico:**
  ```markdown
  Usa `neural-longitudinal-mapping` (`prepare`, `train`, `plot`, `analyze`, `report`) sobre `./matrices/instituciones_periodos.parquet` para modelar el encadenamiento *Warm-Start* entre 2016–2020 y 2021–2025 (`--lang es`).
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Ejecuta el flujo intertemporal *Warm-Start* completo con `neural-longitudinal-mapping` (`--lang es`):
  1. Prepara las matrices con `prepare --input ./corpus.parquet --entity-col institution --period-col year --periods "2015-2019,2020-2022,2023-2025"`.
  2. Entrena el SOM encadenado aplicando la heurística **Big SOM** (`10·N` neuronas con relación espectral SVD; p. ej. `--rows 22 --cols 34 --base-epochs 500 --refine-epochs 250`).
  3. Genera figuras bilingües a 300 DPI con `plot`, cuantifica deriva sináptica ($\Delta W$), rotación de cohortes y dinámicas Macro/Meso/Micro con `analyze`, y exporta el informe en `report` (`./reportes/longitudinal_som_report.md`).
  ```

### 6.3 `semantic-manifold-expert`
* **Definición:** [`SKILL.md`](../.agents/skills/semantic-manifold-expert/SKILL.md) · **Script:** `semantic_manifold_cli.py` · **Slash command recomendado:** `/boost`.
* **Uso básico:**
  ```markdown
  Usa `semantic-manifold-expert` sobre `./matrices/by_institution.parquet` para estimar la dimensión intrínseca local (MLE al percentil 95 y TwoNN) y generar la proyección UMAP en `./reportes/` (`--lang es`).
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Audita la geometría no lineal de mi espacio de indicadores o embeddings con `semantic-manifold-expert`:
  1. Ejecuta `semantic_manifold_cli.py --input ./matrices/instituciones_som.parquet --output ./reportes/manifold_analysis.json --plot-dir ./reportes/ --dpi 300 --lang es`.
  2. Interpreta la relación entre dimensión extrínseca ($D$ indicadores), dimensión intrínseca estimada (MLE p95 y TwoNN) y separación topológica en `manifold_umap_es.png`, justificando cuántas variables independientes gobiernan realmente el desempeño del sistema.
  ```

### 6.4 `som-methodological-expert`
* **Definición:** [`SKILL.md`](../.agents/skills/som-methodological-expert/SKILL.md) · **Script:** `som_pipeline_cli.py` · **Slash command recomendado:** `/boost` + `/browser`.
* **Uso básico:**
  ```markdown
  Usa `som-methodological-expert` para entrenar un **Big SOM** (`--grid-type big`, `--norm divmax`) sobre `./matrices/by_institution.parquet`, evaluar $K=2\dots 15$ y generar el diagnóstico en `./reportes/som_dashboard.html` (`--lang es`).
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Ejecuta el modelado neurocomputacional estático bajo el principio Full Evidence-First con `som-methodological-expert`:
  1. Corre `som_pipeline_cli.py --input ./matrices/instituciones.parquet --entity-col entity --norm divmax --grid-type big --max-k 15 --cluster-strategy global_max --iterations 200 --dpi 300 --lang es` (usando todos los indicadores numéricos o una selección explícita con `--indicator-cols`).
  2. Inspecciona `som_cluster_eval.csv` y `som_cluster_eval_es.png`; si el máximo global es $K=2$, re-clusteriza sin reentrenar sobre el siguiente máximo local con `--recluster-from ./reportes/som_state.json --cluster-strategy local_max_gt2 --min-clusters 3`.
  3. Reporta QE, TE, relación espectral SVD, estadísticas por clúster (`som_cluster_profiles.csv`), perfiles singulares y paradojas métricas.
  ```

### 6.5 `som-trajectory-mapping`
* **Definición:** [`SKILL.md`](../.agents/skills/som-trajectory-mapping/SKILL.md) · **Script:** `som_trajectory_cli.py` · **Slash command recomendado:** `/goal` o `/boost`.
* **Uso básico:**
  ```markdown
  Usa `som-trajectory-mapping` sobre `./matrices/countries_annual.parquet` con `--norm divmax --cma-window 3 --grid-type big --top-entities 5` para trazar las trayectorias temporales de los 5 países líderes (`--lang es`).
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Modela las trayectorias continuas en el espacio de estados SOM con `som-trajectory-mapping`:
  1. Corre `som_trajectory_cli.py --input ./matrices/by_country_annual.parquet --entity-col entity --time-col year --norm divmax --entities "USA,CHN,DEU,GBR,CHE" --cma-window 3 --grid-type big --max-k 15 --cluster-strategy global_max --dpi 300 --lang es --state-out ./reportes/som_trajectory_state.json --html-out ./reportes/som_trajectories.html --json-out ./reportes/som_trajectories.json --png-es ./reportes/som_trajectories_es.png`.
  2. Si conviene refinar $K$ sin reentrenar, usa `--recluster-from ./reportes/som_trajectory_state.json --cluster-strategy local_max_gt2`.
  3. Diagnostica puntos de inflexión, QE/TE, fases de maduración e inversión de desempeño apoyado en las curvas interpoladas con splines cúbicos y `*_cluster_profiles.csv`.
  ```

---

## Grupo 6 · Geopolítica, Ciencia Abierta, ODS y GraphRAG

### 7.1 `geopolitical-collaboration-analyst`
* **Definición:** [`SKILL.md`](../.agents/skills/geopolitical-collaboration-analyst/SKILL.md) · **Script:** `geopolitical_collab_cli.py` (`country-matrix`, `dashboard`, `regional-benchmark`, `scientific-leadership`, `analyze-all`) · **Slash command recomendado:** Ninguno o `/browser`.
* **Uso básico:**
  ```markdown
  Usa `geopolitical-collaboration-analyst` (`analyze-all`) sobre `./corpus.parquet` con país ancla `--anchor-country MEX` y genera el tablero interactivo en `./reportes/geopolitical_dashboard.html` (`--lang es`).
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta un análisis geopolítico completo con `geopolitical-collaboration-analyst` (`--lang es`):
  1. Corre `analyze-all --input ./corpus.parquet --anchor-country MEX --top-n 25 --html ./reportes/geopolitical_dashboard.html --output ./reportes/geopolitical_analysis.json`.
  2. Complementa con `regional-benchmark` comparando bloques (Iberoamérica, Sur Global, OCDE, BRICS, UE) y `scientific-leadership` para auditar soberanía epistemológica (tasas de primer autor y autor de correspondencia) y afinidad bilateral por Coseno de Salton e índice de Jaccard.
  ```

### 7.2 `geopolitical-science-mapping`
* **Definición:** [`SKILL.md`](../.agents/skills/geopolitical-science-mapping/SKILL.md) · **Script:** Orquesta `geopolitical-collaboration-analyst`, `open-access-monitor` y `sdg-impact-intelligence` · **Slash command recomendado:** `/plan` o `/goal`.
* **Uso básico:**
  ```markdown
  Usa `geopolitical-science-mapping` sobre `./corpus.parquet` para entregar un diagnóstico integrado de colaboración internacional ISO-3, vías de Acceso Abierto y alineación con los ODS.
  ```
* **Uso exhaustivo:**
  ```markdown
  /goal Ejecuta el pipeline tridimensional de `geopolitical-science-mapping` sobre `./corpus.parquet` (`--lang es`):
  1. Modela la red geopolítica ISO-3166-1 alpha-3, bloques regionales, afinidad de Salton y liderazgo autoral.
  2. Cruza los países y bloques líderes con sus rutas de Acceso Abierto / gasto en APC (USD) y con su contribución diferenciada a los 17 ODS de la Agenda 2030.
  3. Consolida hallazgos y tableros HTML en `./reportes/`.
  ```

### 7.3 `graphrag-scientific-intelligence`
* **Definición:** [`SKILL.md`](../.agents/skills/graphrag-scientific-intelligence/SKILL.md) · **Script:** Orquestación sobre servicios semánticos 768d, grafos y padrón SNII *(requiere infraestructura local de embeddings/grafo/ClickHouse)* · **Slash command recomendado:** `/boost`.
* **Uso básico:**
  ```markdown
  Usa `graphrag-scientific-intelligence` para localizar investigadores activos en México sobre "agroecología y resiliencia hídrica" combinando búsqueda semántica 768d y verificación en el padrón SNII.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Realiza una consulta híbrida GraphRAG completa con `graphrag-scientific-intelligence`:
  1. Recupera publicaciones y perfiles conceptualmente afines en español e inglés mediante similitud coseno en embeddings Nomic 768d (sin depender de palabras clave literales).
  2. Expande la red de coautoría y citación de los actores centrales para identificar colegios invisibles y puentes interinstitucionales.
  3. Valida adscripción institucional, ROR y nivel SNII 2025 vigente de cada investigador detectado, entregando un informe estructurado con evidencia trazable.
  ```

### 7.4 `open-access-monitor`
* **Definición:** [`SKILL.md`](../.agents/skills/open-access-monitor/SKILL.md) · **Script:** `open_access_monitor_cli.py` (`breakdown`, `apc-spending`, `apc`, `transition-trend`) · **Slash command recomendado:** Ninguno o `/browser`.
* **Uso básico:**
  ```markdown
  Usa `open-access-monitor` (`breakdown`) sobre `./corpus.parquet` para cuantificar las 6 vías de Acceso Abierto y generar la gráfica en español en `./reportes/oa_distribution_es.png`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta la auditoría financiera y longitudinal de Ciencia Abierta con `open-access-monitor` (`--lang es`, `--dpi 300`):
  1. Corre `breakdown --input ./corpus.parquet --output ./reportes/oa_breakdown.json --plot-es ./reportes/oa_distribution_es.png --plotly-html ./reportes/oa_distribution.html`.
  2. Estima el gasto pagado y de lista en APC comercial con `apc-spending` (`--output ./reportes/oa_apc_usd.json`), desglosando ahorro institucional por publicación Diamante ($0 APC).
  3. Modela la evolución temporal anual con `transition-trend` para detectar desplazamiento entre rutas Verde, Gold, Híbrida y Diamante.
  ```

### 7.5 `sdg-impact-intelligence`
* **Definición:** [`SKILL.md`](../.agents/skills/sdg-impact-intelligence/SKILL.md) · **Script:** `sdg_impact_cli.py` · **Slash command recomendado:** Ninguno o `/browser`.
* **Uso básico:**
  ```markdown
  Usa `sdg-impact-intelligence` sobre `./corpus.parquet` para mapear la contribución del corpus a los 17 Objetivos de Desarrollo Sostenible y guardar `./reportes/sdg_impact_report.md` y `sdg_grid_es.png`.
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta el diagnóstico integral de alineación con la Agenda 2030 mediante `sdg-impact-intelligence`:
  1. Corre `sdg_impact_cli.py --input ./corpus.parquet --title "Contribución a los ODS" --dpi 300 --lang es --output-html ./reportes/sdg_impact_dashboard.html --output-png-es ./reportes/sdg_grid_es.png --output-png-en ./reportes/sdg_grid_en.png --output-json ./reportes/sdg_impact_summary.json --output-md ./reportes/sdg_impact_report.md`.
  2. Contrasta qué ODS combinan alto volumen con mayor FWCI y porcentaje de Acceso Abierto Diamante, e inspecciona el tablero HTML con `/browser`.
  ```

---

## Grupo 7 · Inteligencia Editorial y Revistas Iberoamericanas

### 8.1 `journal-editorial-intelligence`
* **Definición:** [`SKILL.md`](../.agents/skills/journal-editorial-intelligence/SKILL.md) · **Script:** Orquesta `classical-bibliometrics-laws`, `open-access-monitor`, `revistaslatam-indicators-engine` y `som-methodological-expert` · **Slash command recomendado:** `/plan` o `/boost`.
* **Uso básico:**
  ```markdown
  Usa `journal-editorial-intelligence` sobre `./corpus.parquet` para identificar las revistas núcleo (zonas de Bradford), sus rutas de Acceso Abierto y posibles señales de endogamia editorial.
  ```
* **Uso exhaustivo:**
  ```markdown
  /boost Realiza una evaluación editorial multidimensional de fuentes científicas con `journal-editorial-intelligence`:
  1. Delimita zonas de concentración de Bradford sobre `./corpus.parquet` y audita la proporción entre revistas Diamante, DOAJ/SciELO/Latindex 2.0 y revistas comerciales con APC.
  2. Calcula endogamia institucional, balance multilingüe y matriz completa de indicadores por revista (`by-entity --level source`).
  3. Entrena un SOM estático de fuentes para tipificar perfiles editoriales comparables (revistas diamante regionales vs. megajournals comerciales vs. revistas de nicho de alto FWCI).
  ```

### 8.2 `revistaslatam-editorial-intelligence`
* **Definición:** [`SKILL.md`](../.agents/skills/revistaslatam-editorial-intelligence/SKILL.md) · **Script:** Skill normativa/diccionario técnico (se apoya en `revistaslatam-indicators-engine`) · **Slash command recomendado:** `/grill-me` o `/plan`.
* **Uso básico:**
  ```markdown
  Usa `revistaslatam-editorial-intelligence` para revisar qué criterios de indización de Latindex Catálogo 2.0, DOAJ y SciELO debe cumplir una revista universitaria iberoamericana en Acceso Abierto Diamante.
  ```
* **Uso exhaustivo:**
  ```markdown
  /plan Activa `revistaslatam-editorial-intelligence` como marco auditor para evaluar nuestra revista académica:
  1. Mapea las 38 características editoriales de Latindex Catálogo 2.0, requisitos de preservación digital, licencias Creative Commons, políticas sin cobro de APC ($0) y estándares de multilingüismo.
  2. Cruza el catálogo conceptual con los metadatos reales de la revista y delega los cálculos empíricos a `revistaslatam-indicators-engine` para emitir un plan de mejora editorial priorizado.
  ```

### 8.3 `revistaslatam-indicators-engine`
* **Definición:** [`SKILL.md`](../.agents/skills/revistaslatam-indicators-engine/SKILL.md) · **Script:** `revistaslatam_indicators_cli.py` (`journal-profile`, `editorial-endogamy`, `multilingual-balance`, `latindex-audit`) · **Slash command recomendado:** Ninguno o `/boost`.
* **Uso básico:**
  ```markdown
  Usa `revistaslatam-indicators-engine` (`journal-profile` y `editorial-endogamy`) sobre `./corpus.parquet` para evaluar la revista `"Revista Mexicana de Biodiversidad"` frente a su institución anfitriona UNAM.
  ```
* **Uso exhaustivo:**
  ```markdown
  Ejecuta la auditoría cuantitativa editorial completa con `revistaslatam-indicators-engine` (`--lang es`):
  1. Calcula `journal-profile --corpus ./corpus.parquet --journal-name "<Nombre Revista>" --output ./reportes/journal_profile.json`.
  2. Mide endogamia institucional y nacional con `editorial-endogamy --host-institution "<Institución>" --host-country MEX`.
  3. Evalúa diversidad lingüística con `multilingual-balance` y ejecuta `latindex-audit --metadata ./revista_meta.json` sobre los 38 criterios de Latindex 2.0 generando el dictamen técnico final.
  ```

---

## Grupo 8 · Orquestación Maestra y Plantillas de Estudios Completos

### 9.1 `knomap-unified-orchestrator`
* **Definición:** [`SKILL.md`](../.agents/skills/knomap-unified-orchestrator/SKILL.md) · **Script:** Coordina el pipeline completo (`bibliometric-search-strategist` → `openalex-harvester` / ClickHouse opt-in → `tlachia-metrics-engine` → Redes/SOM → Reporte) · **Slash command recomendado:** `/goal`.
* **Uso básico:**
  ```markdown
  /goal Usa `knomap-unified-orchestrator` para ejecutar la cadena completa "De la Cosecha al SOM" sobre "computación cuántica topológica" (2018–2026): cosecha vía OpenAlex, calcula matrices de indicadores, detecta frentes y entrena el Big SOM en `./`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /goal Orquesta un flujo completo de principio a fin con `knomap-unified-orchestrator` bajo el principio Workspace-First:
  1. Delimita y cosecha `./corpus.parquet` mediante `bibliometric-search-strategist` y `openalex-harvester` (activando `clickhouse_accelerator.md` solo si `CLICKHOUSE_HOST` está configurado).
  2. Calcula todas las matrices de 46 columnas en `./matrices/` con `tlachia-metrics-engine`, leyes clásicas, análisis geopolítico, OA/APC, frentes Leiden + aluviales AMI y la tríada **Big SOM** (estático, trayectorias CMA-3 y longitudinal Warm-Start).
  3. Emite `./reportes/exploration_log.md`, figuras PNG a 300 DPI, tableros HTML e integra todo en un reporte final compilado a `.md`, `.docx` y `.pdf` con referencias verificadas 1:1 en OpenAlex.
  ```

### 9.2 `template-articulo-cientifico-imryd`
* **Definición:** [`SKILL.md`](../.agents/skills/template-articulo-cientifico-imryd/SKILL.md) · **Protocolo:** Exploración empírica acotada por $RQ$ en laboratorio (Etapa I, secuencial o `/teamwork` en 3–4 ramas) + curaduría científica hacia 3–5 bloques y redacción IMRaD/IMRyD Q1/Q2 (Etapa II–III) · **Slash command recomendado:** `/goal` (secuencial) o `/teamwork` (para paralelizar las familias candidatas de la Etapa I).
* **Uso básico:**
  ```markdown
  /goal Usa la plantilla `template-articulo-cientifico-imryd` sobre mi corpus `./corpus.parquet` para ejecutar la exploración cienciométrica acotada a mis preguntas de investigación y redactar un manuscrito IMRyD en español listo para revista Q1/Q2, exportado en `.md`, `.docx` y `.pdf`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /teamwork Ejecuta la plantilla `template-articulo-cientifico-imryd` en modo enjambre acotado (sin convertirlo en auditoría de las 39 skills) para el tema `"<Tema científico>"` (2015–2026) con salidas en español (`--lang es`):
  1. **Barrera inicial y Etapa I (Laboratorio paralelo en `./lab_exploration/`):** Delimita según GLOBAL (ISSI), cosecha vía `openalex-harvester` en `./corpus.parquet`, calcula matrices completas de 46 columnas en `./matrices/` para 2–3 escalas ligadas a mis $RQ$ (con `min_docs >= 3-5`) y lanza hasta 4 *workers* en paralelo sobre las familias pertinentes (leyes clásicas, redes en competencia + aluviales AMI, revisión de textos clave + PDFs OA con `deep-literature-researcher` y tríada **Big SOM `--norm divmax --grid-type big --max-k 15`** auditando `QE`/`TE` y máximos locales $K>2$). Consolida la evidencia en `./reportes/exploration_scorecard.csv` y `exploration_log.md`.
  2. **Etapa II–III (Curaduría, Verificación y Manuscrito):** Poda hacia 3–5 bloques con mayor señal, redacta el artículo en estilo *Polaritons / JoI* integrando en Discusión el trabajo futuro de autores vs. caminos no explorados, tablas sin `N/D`, figuras PNG a 300 DPI embebidas, verificación 1:1 de cada referencia contra OpenAlex y compilación final a `./reportes/manuscrito.docx` y `./reportes/manuscrito.pdf`.
  ```

### 9.3 `template-informe-tecnico-institucional`
* **Definición:** [`SKILL.md`](../.agents/skills/template-informe-tecnico-institucional/SKILL.md) · **Protocolo:** Evaluación cienciométrica institucional + benchmarking con pares especializados (estilo INB/ICN/INCan UNAM) · **Slash command recomendado:** `/goal`.
* **Uso básico:**
  ```markdown
  /goal Usa `template-informe-tecnico-institucional` para elaborar un informe técnico institucional del Centro/Instituto `<Nombre>` (ROR `<ROR>`, 2015–2025) comparándolo contra 4 pares especializados y compílalo en `.md`, `.docx` y `.pdf`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /goal Ejecuta el protocolo completo de `template-informe-tecnico-institucional`:
  1. Aísla la dependencia por ROR/afiliación vía `openalex-harvester` (o acelerador ClickHouse / `snii-identity-resolver` si está disponible) y cosecha el *benchmark* de instituciones pares nacionales e internacionales.
  2. Calcula la batería completa de 42+ indicadores sin truncamiento, auditoría OA/APC (USD), censo SNII, redes de colaboración interna/externa, evolución temática y Big SOM comparativo de departamentos e instituciones.
  3. Selecciona en Etapa II los hallazgos más diagnósticos, redacta el informe con tablas numeradas, figuras 300 DPI embebidas, referencias verificadas 1:1 en OpenAlex y exportación verificada a `.docx` y `.pdf`.
  ```

### 9.4 `template-policy-brief-gobernanza`
* **Definición:** [`SKILL.md`](../.agents/skills/template-policy-brief-gobernanza/SKILL.md) · **Protocolo:** Síntesis ejecutiva de 2 a 4 páginas para rectoría, ministerios/SECIHTI y agencias financiadoras · **Slash command recomendado:** `/goal`.
* **Uso básico:**
  ```markdown
  /goal Usa `template-policy-brief-gobernanza` para producir un *Policy Brief* ejecutivo de 3 páginas sobre "Publicación en Acceso Abierto Diamante vs. gasto en APCs en universidades mexicanas" en `.md`, `.docx` y `.pdf`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /goal Aplica el protocolo de 2 etapas de `template-policy-brief-gobernanza`:
  1. **Etapa I:** Ejecuta sobre `./corpus.parquet` (o cosecha `openalex-harvester` / acelerador ClickHouse SNII opt-in) métricas de las 6 vías OA, gasto observado/lista en APC (USD), especialización temática ($AI$, $\text{F-measure}$), alineación ODS 1–17 y Big SOM estratégico.
  2. **Etapa II (Curaduría ejecutiva):** Destila estrictamente los **3 a 4 hallazgos empíricos más contundentes**, formula recomendaciones accionables con métricas de seguimiento, inserta gráficas ejecutivas (300 DPI) y tablas sin `N/D`, verifica referencias en OpenAlex y compila la versión final lista para impresión en `.docx` y `.pdf`.
  ```

### 9.5 `template-radar-frentes-investigacion`
* **Definición:** [`SKILL.md`](../.agents/skills/template-radar-frentes-investigacion/SKILL.md) · **Protocolo:** Radar tecnológico y cartografía evolutiva de frentes de investigación · **Slash command recomendado:** `/boost` + `/goal`.
* **Uso básico:**
  ```markdown
  /goal Usa `template-radar-frentes-investigacion` para mapear los frentes emergentes en "baterías de estado sólido de sodio" (2018–2026), su evolución aluvial y sus artículos nucleares en `.md`, `.docx` y `.pdf`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /goal Ejecuta el estudio completo de radar científico con `template-radar-frentes-investigacion`:
  1. **Etapa I:** Delimita el dominio con `bibliometric-search-strategist`, cosecha `./corpus.parquet`, compara detecciones en competencia (`coupling` vs. `cocitation` vs. `topics`) con Leiden CPM, rastrea linajes temporales AMI (`alluvial_lineages.html`), inspecciona a texto completo los artículos centrales con `deep-literature-researcher`, evalúa cinética de crecimiento ($\alpha$, $t_d$), geopolítica, ODS y entrena Big SOM estático y de trayectorias por frente.
  2. **Etapa II:** Selecciona la representación de red más informativa (descartando las fragmentadas en `exploration_log.md`), redacta el radar estratégico con fichas de madurez/emergencia por frente, figuras PNG a 300 DPI, tablas numeradas y referencias 1:1 verificadas en OpenAlex, compilando finalmente a `.docx` y `.pdf`.
  ```

### 9.6 `template-estudio-cienciometrico-exhaustivo`
* **Definición:** [`SKILL.md`](../.agents/skills/template-estudio-cienciometrico-exhaustivo/SKILL.md) · **Protocolo:** Estudio maestro de espectro completo con *Capability & Scope Gate* (`skills_execution_matrix.csv`), bóveda de evidencia inmutable (`./evidence_vault/`, *Full Evidence-First*), análisis multiescala (países, instituciones, fuentes, autores, tópicos) y orquestación en enjambre de 4 Olas · **Slash command recomendado:** `/teamwork` (enjambre nativo `swarm`, ideal para estudios de alta escala) o `/goal` (ejecución secuencial autónoma).
* **Uso básico:**
  ```markdown
  /goal Usa la plantilla `template-estudio-cienciometrico-exhaustivo` sobre `./corpus.parquet` para ejecutar de punta a punta la auditoría completa del ecosistema (leyes clásicas, redes y frentes, geopolítica, OA/APC, ODS, calidad editorial, variedad semántica y tríada Big SOM multiescala), registrando qué skills aplican en `skills_execution_matrix.csv` y compilando el tratado final en `./reportes/estudio_exhaustivo.{md,docx,pdf}`.
  ```
* **Uso exhaustivo:**
  ```markdown
  /teamwork Coordina un enjambre (`swarm`) siguiendo estrictamente `template-estudio-cienciometrico-exhaustivo` para el dominio `"<Tema / Entidad / País>"` (2015–2026) con salidas en español (`--lang es`):
  1. **Fase 0 (Triage):** Verifica precondiciones y masa crítica por escala, genera `./evidence_vault/00_triage/skills_execution_matrix.csv` y cosecha `./corpus.parquet` mediante `bibliometric-search-strategist` + `openalex-harvester` (más `pubmed-harvester` / `arxiv-harvester` / `semantic-scholar-harvester` si aplica).
  2. **Olas 1–3 en paralelo con propiedad de archivos disjunta:** Lanza workers en `./evidence_vault/` para leyes clásicas y motor de 46+ indicadores (`tlachia-metrics-engine` / `classical-bibliometrics-laws` / `bibliometrix-guide`), redes y frentes con evaluación multi-resolución y revisión de artículos nucleares (`bibliometric-network-analyst` / `topics-research-fronts-intelligence` / `deep-literature-researcher`), dimensiones geopolíticas/OA/ODS/editoriales (`geopolitical-science-mapping` / `journal-editorial-intelligence`), y cartografía multiescala (`semantic-manifold-expert` + tríada **Big SOM** `--norm divmax --max-k 15` para países, instituciones, revistas y períodos).
  3. **Ola 4 (Curaduría e Integración):** Consolida `./evidence_vault/04_synthesis/diagnostic_scorecard.csv`, selecciona las escalas con mayor poder discriminante (QE/TE, Silhouette $> K=2$, $Q$ modular, AMI), redacta el informe integral con trazabilidad `run_manifest.json`, auditoría 1:1 en OpenAlex y compila a `./reportes/estudio_exhaustivo.{md,docx,pdf}`.
  ```

