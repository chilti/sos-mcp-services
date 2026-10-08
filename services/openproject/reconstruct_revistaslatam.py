import requests
import json
from services.openproject.tools.client import OpenProjectClient

client = OpenProjectClient()
PROJECT_ID = 3

print("Iniciando reconstrucción histórica de Revistas LATAM en OpenProject...")

# 1. Definición de Versiones / Fases Históricas
versions_data = [
    {
        "name": "v1.0 - Fundación y Precómputo Paralelo",
        "description": "Fase inicial: Arquitectura base, extracción de OpenAlex Snapshot, colector PostgreSQL y precómputo paralelo de indicadores de impacto.",
        "startDate": "2026-01-30",
        "endDate": "2026-02-27",
        "status": "closed"
    },
    {
        "name": "v1.2 - Migración ClickHouse y Despliegue UNAM",
        "description": "Fase de aceleración: Migración al snapshot local en ClickHouse (569M obras), auditoría de indicadores de excelencia y primer despliegue en dinamica1.",
        "startDate": "2026-03-01",
        "endDate": "2026-04-23",
        "status": "closed"
    },
    {
        "name": "v2.0 - Plan RevistasLATAM 2.0: Métricas y UMAP",
        "description": "Fase de transformación: Formulación del Plan RevistasLATAM 2.0, leyes bibliométricas clásicas, índices H/G/M, Acceso Abierto Diamante y cartografía UMAP 2D.",
        "startDate": "2026-08-22",
        "endDate": "2026-08-31",
        "status": "closed"
    },
    {
        "name": "v2.1 - Autenticación ORCID y Dossier Hub",
        "description": "Fase de integración y gobierno: Autenticación federada ORCID OAuth 2.0, compilador de Dossier Hub para IA, compresión Gzip y routers modulares FastAPI.",
        "startDate": "2026-09-01",
        "endDate": "2026-09-08",
        "status": "closed"
    },
    {
        "name": "v2.2 - i18n Trilingüe y Zenodo Release",
        "description": "Fase de internacionalización y madurez: Localización ES/PT/EN, matriz de coautoría país-país, WebGL GPU a 60 FPS, SuiteBar TlachIA y release Zenodo con DOI.",
        "startDate": "2026-09-09",
        "endDate": "2026-09-29",
        "status": "closed"
    },
    {
        "name": "v2.3 - Ecosistema de Agentes de IA y MCP",
        "description": "Fase de gobernanza autónoma: Servidores MCP en sos-mcp-services, despliegue All-in-One de OpenProject y reconstrucción automatizada del roadmap.",
        "startDate": "2026-10-01",
        "endDate": "2026-10-06",
        "status": "open"
    }
]

# Crear o recuperar versiones
existing_versions = client.get(f"/api/v3/projects/{PROJECT_ID}/versions").get("_embedded", {}).get("elements", [])
ver_map = {v["name"]: v["id"] for v in existing_versions}

for v in versions_data:
    if v["name"] not in ver_map:
        payload = {
            "name": v["name"],
            "description": {"format": "markdown", "raw": v["description"]},
            "startDate": v["startDate"],
            "status": v["status"],
            "_links": {
                "definingProject": {"href": f"/api/v3/projects/{PROJECT_ID}"}
            }
        }
        res = client.post("/api/v3/versions", payload)
        ver_map[v["name"]] = res.get("id")
        print(f"  + Versión creada: {v['name']} (ID {res.get('id')})")
    else:
        print(f"  = Versión existente: {v['name']} (ID {ver_map[v['name']]})")

# 2. Definición exhaustiva de paquetes de trabajo basados en commits y documentación
work_packages_data = [
    # --- FASE 1: v1.0 ---
    {
        "subject": "Inicialización y Arquitectura Base del Ecosistema Revistas LATAM",
        "version": "v1.0 - Fundación y Precómputo Paralelo",
        "type_id": 5, # Épico
        "status_id": 12, # Cerrado
        "start_date": "2026-01-30",
        "due_date": "2026-02-02",
        "estimated_time": "PT16H",
        "percentage_done": 100,
        "description": """### Resumen
Establecimiento del repositorio base, definición de la estructura modular y arquitectura híbrida para análisis cienciométrico sobre revistas científicas de América Latina.

### Componentes y Commits Clave
- Commit inicial: `0d9b2cc Initial commit: Revistas LATAM v1.0`
- Configuración de dependencias base de análisis de datos y procesamiento numérico.
- Definición de directorios para ingesta, pipeline y caché analítico."""
    },
    {
        "subject": "Motor de Precómputo Paralelo y Resiliencia ante Cuotas OpenAlex",
        "version": "v1.0 - Fundación y Precómputo Paralelo",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-01-31",
        "due_date": "2026-02-04",
        "estimated_time": "PT24H",
        "percentage_done": 100,
        "description": """### Resumen
Implementación de procesamiento multi-hilo para calcular indicadores a gran escala y manejo inteligente de interrupciones en la API de OpenAlex con reanudación por puntos de control (checkpoints).

### Commits Clave
- `93350ec Nuvo script de precómputo de los indicadores y capacidad de reanudar descarga de openalex despues de superar el limite`
- `ff8bbb3 Add optimized parallel metrics precomputation script`
- Módulo: `pipeline_revistaslatam/precompute_metrics_parallel.py`"""
    },
    {
        "subject": "Colector de Datos PostgreSQL y Prevención de Desbordamiento de Memoria (Anti-OOM)",
        "version": "v1.0 - Fundación y Precómputo Paralelo",
        "type_id": 1, # Tarea
        "status_id": 12,
        "start_date": "2026-02-09",
        "due_date": "2026-02-11",
        "estimated_time": "PT20H",
        "percentage_done": 100,
        "description": """### Resumen
Optimización del colector de datos desde bases relacionales masivas hacia disco para evitar errores de memoria (Out-of-Memory) en lotes de millones de registros.

### Commits Clave
- `84e9534 feat: Add PostgreSQL data collector and indexing metrics improvements`
- `0425afd Optimized PostgreSQL data collection pipeline to prevent OOM errors and adding DuckDB consolidation script`
- Documentación: `docs/DATA_COLLECTOR_FIXES.md` y `docs/POSTGRES_COLLECTOR_README.md`"""
    },
    {
        "subject": "Normalización de Métricas de Impacto: FWCI y Percentiles de Excelencia",
        "version": "v1.0 - Fundación y Precómputo Paralelo",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-02-12",
        "due_date": "2026-02-16",
        "estimated_time": "PT28H",
        "percentage_done": 100,
        "description": """### Resumen
Modelado del impacto ponderado por campo (Field-Weighted Citation Impact - FWCI) y estratificación de obras en percentiles de excelencia (Top 1%, Top 5% y Top 10%).

### Commits Clave
- `ce95b57 Organize project layout, fix metrics (FWCI/percentiles), add Sunburst via API enrichment`
- `f65919a Refine top percentile calculation logic`
- `bfdf2b5 Add script to update Postgres works table with FWCI metrics`
- Guía metodológica: `docs/METRICS_CALCULATION_GUIDE.md`"""
    },
    {
        "subject": "Taxonomía Temática Sunburst 4 Niveles y Consolidación Parquet con PyArrow",
        "version": "v1.0 - Fundación y Precómputo Paralelo",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-02-12",
        "due_date": "2026-02-20",
        "estimated_time": "PT22H",
        "percentage_done": 100,
        "description": """### Resumen
Enriquecimiento jerárquico en 4 niveles (Dominio, Campo, Subcampo y Tópico) mediante la API Polite Pool de OpenAlex y almacenamiento columnar particionado con PyArrow.

### Commits Clave
- `ce95b57 Organize project layout, fix metrics (FWCI/percentiles), add Sunburst via API enrichment`
- `f96b031 Replace DuckDB with PyArrow for consolidation`
- `1272786 Add file consolidation step to run_pipeline.py`"""
    },

    # --- FASE 2: v1.2 ---
    {
        "subject": "Análisis Temporal y Evolución de Perfiles Temáticos por Revista",
        "version": "v1.2 - Migración ClickHouse y Despliegue UNAM",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-03-09",
        "due_date": "2026-03-25",
        "estimated_time": "PT30H",
        "percentage_done": 100,
        "description": """### Resumen
Seguimiento temporal del perfil disciplinar de las revistas y modelado de transiciones temáticas interanuales.

### Commits Clave
- `9390299 Evolución del perfil temático`
- Ingesta de trayectorias de especialización disciplinar."""
    },
    {
        "subject": "Migración al Snapshot Masivo Local en ClickHouse (569M Trabajos)",
        "version": "v1.2 - Migración ClickHouse y Despliegue UNAM",
        "type_id": 5, # Épico
        "status_id": 12,
        "start_date": "2026-04-12",
        "due_date": "2026-04-14",
        "estimated_time": "PT32H",
        "percentage_done": 100,
        "description": """### Resumen
Migración de la ingesta hacia ClickHouse local (569M trabajos, 337M autores) en el Centro de Ciencias de la Complejidad (C3 UNAM), logrando procesar 7,490 revistas y 3.63M artículos en minutos.

### Commits Clave
- `14e9534 extracción desde clickhouse`
- Reducción drástica de dependencia de descargas HTTP externas."""
    },
    {
        "subject": "Auditoría y Conciliación de Indicadores de Excelencia Científica",
        "version": "v1.2 - Migración ClickHouse y Despliegue UNAM",
        "type_id": 1, # Tarea
        "status_id": 12,
        "start_date": "2026-04-14",
        "due_date": "2026-04-15",
        "estimated_time": "PT18H",
        "percentage_done": 100,
        "description": """### Resumen
Verificación exhaustiva de discrepancias en conteos de citas, soporte de tipos documentales mixtos (artículos vs conferencias) y deduplicación por identificador canónico.

### Commits Clave
- `8549ca3 Script para verificar indicadores de excelencia clickhouse`
- `8926049 Fix: excellence indicators discrepancy, included conferences and mixed JSON path support`
- `8569ca3 Fix: deduplicate works by ID in verify script to match dashboard logic`"""
    },
    {
        "subject": "Despliegue Oficial en Servidor Principal UNAM (dinamica1)",
        "version": "v1.2 - Migración ClickHouse y Despliegue UNAM",
        "type_id": 2, # Hito
        "status_id": 12,
        "start_date": "2026-04-16",
        "due_date": "2026-04-16",
        "estimated_time": "PT8H",
        "percentage_done": 100,
        "description": """### Resumen
Puesta en producción del portal web y APIs en la infraestructura de la Facultad de Ciencias de la UNAM.

### URLs
- Servidor Principal: https://dinamica1.fciencias.unam.mx/revistaslatam/
- Servidor Espejo: https://dinamica10.fciencias.unam.mx/revistaslatam/
- Commit: `a649ca3 docs: add deployment URLs for principal and mirror servers to README`"""
    },
    {
        "subject": "Analítica Institucional y Segmentación por Tipología de Entidad",
        "version": "v1.2 - Migración ClickHouse y Despliegue UNAM",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-04-20",
        "due_date": "2026-04-23",
        "estimated_time": "PT26H",
        "percentage_done": 100,
        "description": """### Resumen
Agregación cienciométrica por tipología de instituciones editoras (Universidades públicas/privadas, Institutos de Investigación, Hospitales y Organismos Gubernamentales).

### Commits Clave
- `7e930f7 feat: Integración de analítica institucional, optimización ClickHouse y refactorización UI dashboard_tema.py`
- `94ca0ec dashboard para area temática. Tipo de instituciones agregado`"""
    },

    # --- FASE 3: v2.0 ---
    {
        "subject": "Formulación del Plan Estratégico RevistasLATAM 2.0",
        "version": "v2.0 - Plan RevistasLATAM 2.0: Métricas y UMAP",
        "type_id": 2, # Hito
        "start_date": "2026-08-22",
        "due_date": "2026-08-24",
        "status_id": 12,
        "estimated_time": "PT16H",
        "percentage_done": 100,
        "description": """### Resumen
Aprobación del documento rector de la versión 2.0 estableciendo la transición de un dashboard a una plataforma de inteligencia cienciométrica integral para América Latina.

### Artefacto
- Documento: `docs/plan_revistaslatam_2.0.md`
- Reutilización metodológica de PLmetrix, newLabSOM, Topics y TlachIA."""
    },
    {
        "subject": "Modelado de Leyes Bibliométricas Clásicas e Índices H, G y M por Revista",
        "version": "v2.0 - Plan RevistasLATAM 2.0: Métricas y UMAP",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-08-24",
        "due_date": "2026-08-28",
        "estimated_time": "PT32H",
        "percentage_done": 100,
        "description": """### Resumen
Cálculo automatizado de la Ley de Lotka, Núcleos de Bradford, Ley de Zipf e Índice de Price, junto a los índices de impacto H, G y M (H temporal normalizado por antigüedad).

### Módulos
- `src/performance_metrics.py` (MetricsAccumulator)
- Modelado de distribución de citas y grado de madurez editorial."""
    },
    {
        "subject": "Cartografía Semántica Topológica UMAP 2D con Embeddings Nomic",
        "version": "v2.0 - Plan RevistasLATAM 2.0: Métricas y UMAP",
        "type_id": 5, # Épico
        "status_id": 12,
        "start_date": "2026-08-28",
        "due_date": "2026-08-31",
        "estimated_time": "PT40H",
        "percentage_done": 100,
        "description": """### Resumen
Proyección en variedades semánticas bidimensionales de más de 7,400 revistas utilizando embeddings neuronales de última generación (Nomic Embed Text v2) y estimación de frontera por Envolturas Convexas (Convex Hulls).

### Commits Clave
- `484b588 feat: integrar panel consolidado de Indicadores de Desempeño`
- `a6d8206 feat(regional): add ThematicEvolutionTable, AnnualDataTable, and fix regional/country/journal UMAP trajectories`
- Script: `pipeline_revistaslatam/calculate_umap.py`"""
    },
    {
        "subject": "Panel de Desempeño Longitudinal por Periodos (0-2026 vs 2021-2025)",
        "version": "v2.0 - Plan RevistasLATAM 2.0: Métricas y UMAP",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-08-31",
        "due_date": "2026-08-31",
        "estimated_time": "PT20H",
        "percentage_done": 100,
        "description": """### Resumen
Diseño de la interfaz y lógica de comparación entre el acumulado histórico completo (0-2026) frente a la ventana quinquenal reciente (2021-2025) para capturar el dinamismo reciente de la ciencia regional.

### Commits Clave
- `484b588 feat: integrar panel consolidado de Indicadores de Desempeño por periodo (0-2026 vs 2021-2025)`
- `8b91200 feat(country): add full metrics breakdown for impact, open science, language distribution, and recent period 2021-2025`"""
    },
    {
        "subject": "Monitoreo de Soberanía Editorial y Acceso Abierto Diamante vs Gold",
        "version": "v2.0 - Plan RevistasLATAM 2.0: Métricas y UMAP",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-08-31",
        "due_date": "2026-08-31",
        "estimated_time": "PT24H",
        "percentage_done": 100,
        "description": """### Resumen
Cuantificación de las vías de acceso abierto (Diamante, Dorada comercial, Híbrida, Verde, Bronce y Cerrada) y estimación de los costos comerciales evitados (Ahorro en APC en USD) por el ecosistema público latinoamericano.

### Commits Clave
- `465c897 feat(country): add Open Access and Language distribution pie charts with period selector`
- `267f095 feat(country): add Country Thematic Profiles (Domain/Field/Subfield) and Country Thematic Evolution`"""
    },

    # --- FASE 4: v2.1 ---
    {
        "subject": "Autenticación Federada ORCID OAuth 2.0 y Panel de Administración",
        "version": "v2.1 - Autenticación ORCID y Dossier Hub",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-09-01",
        "due_date": "2026-09-02",
        "estimated_time": "PT20H",
        "percentage_done": 100,
        "description": """### Resumen
Integración del protocolo ORCID OAuth 2.0 para inicio de sesión único (SSO) de investigadores, control de acceso basado en roles y panel administrativo.

### Commits Clave
- `dd2ea3d feat(auth): add ORCID OAuth 2.0, Admin management panel, architecture docs and protected exports`
- `726aa47 fix(auth): fix recursion in requireAuth and persist dossier items in localStorage`
- Router: `api/routers/auth.py`"""
    },
    {
        "subject": "Dossier Hub Interactivo y Compilador Contextual para IA",
        "version": "v2.1 - Autenticación ORCID y Dossier Hub",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-09-01",
        "due_date": "2026-09-03",
        "estimated_time": "PT24H",
        "percentage_done": 100,
        "description": """### Resumen
Herramienta de canasta analítica (Dossier Hub) que permite al usuario seleccionar tablas, KPIs y gráficos para exportar reportes ejecutivos o transferir contexto a agentes de IA.

### Commits Clave
- `50675c3 feat: actualizar PageDossierExpander con nuevos indicadores y soporte de exportación OpenAlex`
- `a4b6190 refactor(ui): remove individual top Dossier buttons and consolidate into bottom multi-select expander`
- Componente: `frontend/src/components/PageDossierExpander.jsx`"""
    },
    {
        "subject": "Pipeline de Clustering HDBSCAN en Espacio Latente 5D",
        "version": "v2.1 - Autenticación ORCID y Dossier Hub",
        "type_id": 1, # Tarea
        "status_id": 12,
        "start_date": "2026-09-01",
        "due_date": "2026-09-03",
        "estimated_time": "PT16H",
        "percentage_done": 100,
        "description": """### Resumen
Optimización del agrupamiento jerárquico basado en densidad (HDBSCAN) sobre el espacio latente pentadimensional para etiquetar linajes temáticos sin sesgo manual.

### Commits Clave
- `e6b0d40 fix(pipeline): enable Nomic MoE embeddings and parallel HDBSCAN in 5D latent space`
- `71c2e2f feat: optimizaciones cienciometricas, pipeline de proyeccion UMAP HDBSCAN GPU y soporte multilingue i18n`"""
    },
    {
        "subject": "Arquitectura de Routers Modulares y Conexión DuckDB en FastAPI",
        "version": "v2.1 - Autenticación ORCID y Dossier Hub",
        "type_id": 1, # Tarea
        "status_id": 12,
        "start_date": "2026-09-07",
        "due_date": "2026-09-08",
        "estimated_time": "PT18H",
        "percentage_done": 100,
        "description": """### Resumen
Refactorización de la API monolítica hacia routers desacoplados (`regional.py`, `countries.py`, `journals.py`, `networks.py`, `maps.py`) con pool de lectura columnar en DuckDB.

### Commits Clave
- `c103fdf fix(api,i18n): ajustes en routers regionales, traducciones i18n y precomputo paralelo de metricas`
- Arquitectura: `docs/ARQUITECTURA_REVISTASLATAM.md`"""
    },

    # --- FASE 5: v2.2 ---
    {
        "subject": "Publicación Científica Oficial y Registro DOI en Zenodo",
        "version": "v2.2 - i18n Trilingüe y Zenodo Release",
        "type_id": 2, # Hito
        "status_id": 12,
        "start_date": "2026-09-09",
        "due_date": "2026-09-09",
        "estimated_time": "PT12H",
        "percentage_done": 100,
        "description": """### Resumen
Publicación formal del software científico en el repositorio de la Unión Europea Zenodo con asignación de Identificador de Objeto Digital (DOI) persistente.

### Metadatos
- **DOI**: 10.5281/zenodo.22679773
- **Tag**: `v2.0.0`
- **Archivos**: `CITATION.cff` y `.zenodo.json`
- Commits: `2abc5b0`, `578c6eb`, `c7b286f`"""
    },
    {
        "subject": "Sistema de Internacionalización Trilingüe Reactivo (ES 🇲🇽 / PT 🇧🇷 / EN 🇺🇸)",
        "version": "v2.2 - i18n Trilingüe y Zenodo Release",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-09-09",
        "due_date": "2026-09-12",
        "estimated_time": "PT36H",
        "percentage_done": 100,
        "description": """### Resumen
Localización trilingüe integral de la plataforma (Español, Portugués e Inglés) con conmutación en tiempo real en encabezados, gráficos Plotly, tablas, tooltips y descargas.

### Commits Clave
- `c7ebc1d feat(i18n): sincronizacion trilingue completa (es/en/pt), correccion TDZ en CountryPage e importacion useMemo en JournalPage`
- `6fe736b docs: actualizar README con soporte i18n, dependencias de ClickHouse y seccion Acerca de`
- Módulo: `frontend/src/i18n/`"""
    },
    {
        "subject": "Perfiles de Radar Multidimensional 6D por País y Revista",
        "version": "v2.2 - i18n Trilingüe y Zenodo Release",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-09-17",
        "due_date": "2026-09-18",
        "estimated_time": "PT20H",
        "percentage_done": 100,
        "description": """### Resumen
Visualización de balance y madurez de revistas y países en un gráfico de radar en 6 dimensiones normalizadas (Impacto, Cobertura, Colaboración, Acceso Abierto, Soberanía y Citación).

### Commits Clave
- `45993ae feat(topics, radar): optimizar extraccion vectorial de topicos en pipeline y agregar perfiles de radar multidimensional por pais`"""
    },
    {
        "subject": "Matriz de Coautoría Internacional País-País (Connection Map Global)",
        "version": "v2.2 - i18n Trilingüe y Zenodo Release",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-09-18",
        "due_date": "2026-09-20",
        "estimated_time": "PT26H",
        "percentage_done": 100,
        "description": """### Resumen
Visualización cartográfica y arcos de flujo de coautoría científica entre países latinoamericanos y sus contrapartes en Europa, Norteamérica y el Sur Global.

### Commits Clave
- `3e03800 feat(networks): implementar Matriz de Coautoría País-País (Connection Map Global) en vistas Revista y País`"""
    },
    {
        "subject": "Renderizado WebGL GPU de Alta Densidad a 60 FPS con Escalamiento P98",
        "version": "v2.2 - i18n Trilingüe y Zenodo Release",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-09-18",
        "due_date": "2026-09-21",
        "estimated_time": "PT28H",
        "percentage_done": 100,
        "description": """### Resumen
Motor gráfico sobre lienzo WebGL para renderizado fluido de 100,000+ esferas en mapas semánticos, con calibración dinámica de radios mediante percentil P98 y raíz cuadrada.

### Commits Clave
- `8a4d5a0 feat(maps): implementar escalamiento dinamico de tamano de circulos con percentil P98 y raiz cuadrada estilo SinapsisAI`
- `45ca4d6 fix(maps): calibrar rango de tamaño de circulos a 1.8px-4.5px evitando saturacion y oclusion`
- `ce86c7a feat(maps): habilitar WebGL por defecto en vistas de Revista y Pais con fondo regional y aspect ratio 1:1`"""
    },
    {
        "subject": "Integración de la SuiteBar Obsidian Glass del Ecosistema TlachIA",
        "version": "v2.2 - i18n Trilingüe y Zenodo Release",
        "type_id": 1, # Tarea
        "status_id": 12,
        "start_date": "2026-09-29",
        "due_date": "2026-09-29",
        "estimated_time": "PT12H",
        "percentage_done": 100,
        "description": """### Resumen
Integración de la barra superior unificada con estilo Obsidian Glass que conecta visualmente Revistas LATAM con KnoMap, SinapsisAI, Info TlachIA y PLmetrix.

### Commits Clave
- `8ba0fb8 feat(ecosystem): integrar barra superior Obsidian Glass del Ecosistema Cientifico TlachIA`
- `edc414d fix(symlink): hacer SuiteBar 100% autonoma dentro de frontend para evitar errores EPERM en discos montados`"""
    },

    # --- FASE 6: v2.3 ---
    {
        "subject": "Servidor MCP sos_revistaslatam para Consulta de Perfiles Cienciométricos",
        "version": "v2.3 - Ecosistema de Agentes de IA y MCP",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-10-01",
        "due_date": "2026-10-04",
        "estimated_time": "PT24H",
        "percentage_done": 100,
        "description": """### Resumen
Exposición de capacidades cienciométricas de Revistas LATAM para agentes de inteligencia artificial mediante el Model Context Protocol (FastMCP/Stdio).

### Ubicación
- `/mnt/expansion/desplegados/sos-mcp-services/services/revistaslatam/mcp_server.py`
- Herramientas: consulta de perfiles de revistas, indicadores de impacto, endogamia y benchmarking."""
    },
    {
        "subject": "Despliegue de OpenProject All-in-One con Soporte Nginx SSL",
        "version": "v2.3 - Ecosistema de Agentes de IA y MCP",
        "type_id": 1, # Tarea
        "status_id": 12,
        "start_date": "2026-10-06",
        "due_date": "2026-10-06",
        "estimated_time": "PT12H",
        "percentage_done": 100,
        "description": """### Resumen
Instalación y endurecimiento de OpenProject v17 mediante Docker Compose, volúmenes de almacenamiento ext4 y proxy inverso seguro en Nginx bajo el subdirectorio /openproject con TLSv1.3 y WebSockets.

### Ubicación
- `/mnt/expansion/desplegados/openproject/`
- https://dinamica1.fciencias.unam.mx/openproject/"""
    },
    {
        "subject": "Pasarela MCP sos_openproject para Gestión Autónoma de Proyectos",
        "version": "v2.3 - Ecosistema de Agentes de IA y MCP",
        "type_id": 4, # Función
        "status_id": 12,
        "start_date": "2026-10-06",
        "due_date": "2026-10-06",
        "estimated_time": "PT16H",
        "percentage_done": 100,
        "description": """### Resumen
Construcción del servidor MCP sos_openproject con 11 herramientas para la administración de proyectos, tareas, hitos y bitácoras vía API REST v3 de OpenProject.

### Ubicación
- `/mnt/expansion/desplegados/sos-mcp-services/services/openproject/mcp_server.py`
- Registrado en `mcp_config.linux.json` y configuración global de Antigravity."""
    },
    {
        "subject": "Reconstrucción Histórica del Ciclo de Vida y Roadmap de Revistas LATAM",
        "version": "v2.3 - Ecosistema de Agentes de IA y MCP",
        "type_id": 2, # Hito
        "status_id": 12,
        "start_date": "2026-10-06",
        "due_date": "2026-10-06",
        "estimated_time": "PT10H",
        "percentage_done": 100,
        "description": """### Resumen
Sincronización histórica automatizada de los 250 commits, planes de implementación (v1.0 a v2.3), artefactos de arquitectura y publicaciones científicas dentro de OpenProject."""
    }
]

print(f"\nIniciando creación de {len(work_packages_data)} paquetes de trabajo...")

created_count = 0
for wp in work_packages_data:
    v_id = ver_map.get(wp["version"])
    payload = {
        "subject": wp["subject"],
        "description": {"format": "markdown", "raw": wp["description"]},
        "startDate": wp["start_date"],
        "dueDate": wp["due_date"],
        "estimatedTime": wp.get("estimated_time"),
        "percentageDone": wp.get("percentage_done", 100),
        "_links": {
            "project": {"href": f"/api/v3/projects/{PROJECT_ID}"},
            "type": {"href": f"/api/v3/types/{wp['type_id']}"},
            "status": {"href": f"/api/v3/statuses/{wp['status_id']}"}
        }
    }
    if v_id:
        payload["_links"]["version"] = {"href": f"/api/v3/versions/{v_id}"}

    res = client.post("/api/v3/work_packages", payload)
    created_count += 1
    print(f"  [{created_count}/{len(work_packages_data)}] Tarea #{res.get('id')} creada: {wp['subject']} ({wp['start_date']} -> {wp['due_date']})")

print(f"\n¡Reconstrucción completada exitosamente! Se crearon {len(versions_data)} versiones y {created_count} paquetes de trabajo en OpenProject.")
