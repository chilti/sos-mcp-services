---
name: knomap-unified-orchestrator
description: Orquestador integral del ecosistema KnoMap y TlachIA; coordina pipelines multi-fase bajo el principio Workspace-First ("De la Cosecha al SOM") desde la delimitación y cosecha de datos masivos hasta el cálculo de matrices de 35+ indicadores, detección de frentes, modelado topológico SOM y reportes.
---

# KnoMap Unified Orchestrator: La Cadena de Valor Completa ("De la Cosecha al SOM")

Esta skill actúa como el **director de orquesta maestro** cuando el usuario solicita un estudio cienciométrico o bibliométrico integral que abarca múltiples etapas del ecosistema.

## 1. Arquitectura de Encadenamiento en el Workspace (`./`)

Todas las skills del ecosistema se comunican a través de artefactos estandarizados en el directorio de trabajo del proyecto (`./`), evitando pasar estructuras masivas en memoria:

1. **Raíz del Workspace (`./corpus.parquet`):** Archivo maestro con las publicaciones cosechadas en esquema canónico.
2. **Subdirectorio `./matrices/`:** Matrices multidimensionales $[N \times D]$ (`.parquet` o `.csv`) con los **más de 35 indicadores** calculados por `tlachia-metrics-engine` (sin truncar columnas), listas para ser consumidas por la Tríada SOM.
3. **Subdirectorio `./networks/`:** Grafos y particiones modulares Leiden CPM (`.json`, `.gexf`).
4. **Subdirectorio `./reports/`:** Estados entrenados del SOM (`./reports/som_state.json`), diagnósticos de pares (`./reports/som_diagnosis.json`), frentes de investigación, leyes bibliométricas y dashboards interactivos HTML/PNG.

---

## 2. Protocolo de Orquestación en 4 Etapas

### Etapa 1: Delimitación Conceptual, Resolución de Identidades y Cosecha (`./corpus.parquet`)
1. **Delimitación del Campo:** Invocar `bibliometric-search-strategist` (`scripts/query_synthesizer.py`) para construir bloques conceptuales auditados bajo la directriz GLOBAL (ISSI) y transpilar a SQL ClickHouse (`clickhouse_query.sql`), WoS, Scopus y PubMed.
2. **Resolución de Entidades (si aplica a México):** Invocar `openalex-mexico-institutions`, `openalex-mexico-author-search` y `snii-identity-resolver`.
3. **Extracción del Corpus Canónico (`./corpus.parquet`):**
   - **Global (464.8M obras en `rag.works_flat`):** Usar `openalex-search-engineer` (`scripts/openalex_search_cli.py search-works --sql-file ./queries/clickhouse_query.sql --output ./corpus.parquet`) o `openalex-harvester`.
   - **Nacional México (1.65M obras en `rag.works_academic_all`):** Usar `openalex-mexico-works-search` (`openalex_mexico_cli.py search-works --output ./corpus.parquet`).
   - **Bases externas especializadas:** Usar `scopus-harvester`, `pubmed-harvester`, `arxiv-harvester`, `semantic-scholar-harvester`, o `deep-literature-researcher` (Snowballing).

### Etapa 2: Motores Analíticos y Construcción de Matrices (`./matrices/` y `./reports/`)
Todas las skills de Etapa 2 leen directamente `./corpus.parquet`:
1. **Motor de Indicadores Multidimensionales (`tlachia-metrics-engine`):**
   - Resumen global: `tlachia_metrics_cli.py calculate-summary --input ./corpus.parquet --output ./reports/summary_metrics.json`
   - Matriz por entidad para SOM Estático (35+ indicadores sin truncar):
     `tlachia_metrics_cli.py by-entity --input ./corpus.parquet --level institution --min-docs 2 --output ./matrices/indicadores_som.parquet`
   - Serie anual por entidad con Media Móvil Centrada (CMA) para SOM de Trayectorias:
     `tlachia_metrics_cli.py annual-series --input ./corpus.parquet --level institution --cma-window 3 --output ./matrices/series_cma_som.parquet`
   - Serie por periodos para SOM Longitudinal Warm-Start:
     `tlachia_metrics_cli.py period-series --input ./corpus.parquet --periods "2020-2022,2023-2026" --level institution --output ./matrices/periodos_som.parquet`
2. **Redes y Frentes de Investigación:**
   - Redes de coautoría, coocurrencia, acoplamiento y cocitación: `bibliometric-network-analyst` (`scripts/biblio_network_cli.py`).
   - Detección de Frentes (Leiden CPM sobre acoplamiento/cocitación/citas o Topics de OpenAlex) y Diagramas Aluviales Longitudinales (AMI): `topics-research-fronts-intelligence` (`build_bibliometric_fronts.py`, `track_longitudinal_lineages.py`).
3. **Leyes Clásicas, Geopolítica, Acceso Abierto y ODS:**
   - `classical-bibliometrics-laws` (`bibliometric_laws_cli.py`: Lotka, Bradford, Price, Crecimiento).
   - `geopolitical-collaboration-analyst` (`geopolitical_collab_cli.py`: Afinidad Salton, Soberanía Epistemológica).
   - `open-access-monitor` (`open_access_monitor_cli.py`: 6 vías OA y gasto APC USD observado vs arancel).
   - `sdg-impact-intelligence` (`sdg_impact_cli.py`: ODS 1–17).

### Etapa 3: Cartografía Neurocomputacional (Tríada SOM) y Visualización Ejecutiva
1. **Nota sobre Selección de Dimensiones:** Aunque existen 4 dimensiones cardinales clásicas (Volumen, Impacto de Citación, Excelencia Top 10%/1% y Colaboración/OA), el agente puede elegir **cualquier subconjunto de los 35+ indicadores** de `./matrices/*.parquet` mediante `--indicator-cols` según la pregunta de investigación.
2. **SOM Estático y Pares Comparables (`som-methodological-expert`):**
   - `scripts/som_pipeline_cli.py --input ./matrices/indicadores_som.parquet --state-out ./reports/som_state.json --html-out ./reports/som_dashboard.html --diagnosis-out ./reports/som_diagnosis.json`
3. **SOM de Trayectorias Continuas (`som-trajectory-mapping`):**
   - `scripts/som_trajectory_cli.py --input ./matrices/series_cma_som.parquet --top-entities 5 --html-out ./reports/som_trajectories.html --json-out ./reports/som_trajectories.json`
4. **SOM Longitudinal Warm-Start (`neural-longitudinal-mapping`):**
   - `scripts/neural_longitudinal_cli.py prepare` + `analyze` sobre `./matrices/periodos_som.parquet`.
5. **Visualizador Ejecutivo (`openalex-mexico-visualizer`):**
   - `openalex_mexico_viz_cli.py` para rankings, series duales, donas OA y cuadrículas ODS en `./reports/`.

### Etapa 4: Síntesis Documental
Integrar todos los hallazgos cuantitativos y enlaces a `./reports/` utilizando una de las 4 plantillas maestras:
- `template-articulo-cientifico-imryd`
- `template-informe-tecnico-institucional`
- `template-policy-brief-gobernanza`
- `template-radar-frentes-investigacion`
