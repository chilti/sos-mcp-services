---
name: template-radar-frentes-investigacion
description: >-
  Cartografía cienciométrica de frentes de investigación emergentes, radar tecnológico, evolución temática y linajes aluviales AMI. Opera bajo un protocolo en 2 etapas: I) Exploración en el workspace mediante el menú de Agent Skills (detección multimodal de frentes por acoplamiento bibliográfico, co-citación, citación directa o Topics Macro/Meso/Micro; lectura de artículos núcleo; motor de 42+ indicadores; cinéticas de crecimiento; afinidad geopolítica; tríada SOM estática/trayectorias/longitudinal y alineación ODS), y II) Curaduría científica para seleccionar la representación de red y el subconjunto de técnicas que mejor revelen la estructura y evolución de los frentes.
---

# Plantilla Maestra: Reporte de Inteligencia Científica, Radar de Frentes de Investigación y Cartografía Topológica SOM
### *Inspirada en el mapeo multimodal de frentes de investigación, evolución temática y análisis SOM (estilo Polaritones / Topics & Research Fronts Intelligence)*

Esta plantilla guía la elaboración de un **REPORTE DE INTELIGENCIA CIENTÍFICA Y RADAR DE FRENTES DE INVESTIGACIÓN** de alto valor prospectivo para grupos de investigación, vicerrectorías, observatorios tecnológicos y agencias de financiamiento.

Siguiendo el principio de **exploración y curaduría humana**, la plantilla presenta al agente el **menú completo de Agent Skills** para explorar la estructura intelectual y temporal del campo en el workspace (`./corpus.parquet`), le permite **comparar distintas estrategias de detección de frentes** (acoplamiento bibliográfico, co-citación, citación directa, co-ocurrencia o taxonomías Topics Macro/Meso/Micro) y distintas configuraciones del **SOM**, y le instruye **descartar aquellas técnicas que produzcan particiones ruidosas o redundantes**, construyendo el reporte alrededor de los resultados con mayor poder explicativo y combinando la cartografía cuantitativa con la revisión sustantiva de los artículos núcleo de cada frente.

---

## Etapa I: Menú de Agent Skills para Exploración de Frentes (*Fase de Laboratorio*)

El agente opera bajo el principio **Workspace-First** (`./corpus.parquet` $\to$ `./matrices/*.parquet` $\to$ `./reportes/`) y dispone del siguiente menú de skills:

1. **Delimitación y Cosecha del Corpus (`./corpus.parquet`):**
   - [`bibliometric-search-strategist`](../bibliometric-search-strategist/SKILL.md): Delimitación de campo multi-etapa (Huang, Schiebel & Porter, 2011), auditoría GLOBAL (ISSI) y transpilación SQL a ClickHouse (`rag.works_flat` para estudios globales o `rag.works_academic_all` para estudios enfocados en México, con **CERO JOINs**).
   - [`openalex-search-engineer`](../openalex-search-engineer/SKILL.md) (global `rag.works_flat`), [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md) (nacional `rag.works_academic_all`), o cosechadores [`openalex-harvester`](../openalex-harvester/SKILL.md), [`scopus-harvester`](../scopus-harvester/SKILL.md), [`pubmed-harvester`](../pubmed-harvester/SKILL.md), [`arxiv-harvester`](../arxiv-harvester/SKILL.md).
2. **Detección Multimodal de Frentes y Linajes Longitudinales (Explorar y Comparar):**
   - [`topics-research-fronts-intelligence`](../topics-research-fronts-intelligence/SKILL.md) y [`research-fronts-detection-expert`](../research-fronts-detection-expert/SKILL.md):
     * Permite probar diferentes modalidades de red sobre `./corpus.parquet`: **acoplamiento bibliográfico** (óptimo para detectar frentes emergentes y activos), **co-citación** (óptimo para escuelas teóricas fundacionales), **citación directa** o **taxonomía nativa de OpenAlex Topics** (`domain` $\to$ `field` $\to$ `subfield` $\to$ `topic`).
     * Partición comunitaria mediante algoritmo **Leiden (CPM / Modularity)** y rastreo intertemporal mediante **Información Mutua Ajustada (AMI)** para clasificar eventos evolutivos (*Persistencia*, *Fusión/Merge*, *Escisión/Split*, *Génesis*) y generar diagramas aluviales interactivos (`alluvial_lineages.html`).
   - [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md): Redes de co-ocurrencia conceptual, coautoría y acoplamiento con normalización *Association Strength* (VOSviewer / Force Graph).
3. **Inspección Sustantiva de Artículos Seminales y Núcleo (*Core Papers* por Frente):**
   - [`deep-literature-researcher`](../deep-literature-researcher/SKILL.md) y lectura directa de `./reportes/corpus_with_fronts.parquet`: Identificar los artículos de mayor impacto, centralidad o densidad ($k \ge 2$, Glänzel et al., 2009) dentro de cada frente detectado para sintetizar qué problemas científicos, arquitecturas o fenómenos investiga realmente cada cluster.
4. **Motor de Indicadores Multidimensionales y Cartografía SOM (Estático, Trayectorias y Longitudinal):**
   - [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Genera en `./matrices/` los **42+ indicadores sin truncar columnas** agregados por frente/topic, institución o país (`by-entity`), series anuales con CMA (`annual-series --cma-window 3`) y ventanas por periodos (`period-series`).
   - [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Proyección topológica SOM de los frentes, Topics o países/instituciones líderes eligiendo el subconjunto de indicadores más informativo (`--indicator-cols`), U-Matrix, Mapas de Componentes y meta-clustering de Vesanto con Silhouette ($s^*$).
   - [`som-trajectory-mapping`](../som-trajectory-mapping/SKILL.md) y [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md): Evolución temporal de los frentes o actores líderes mediante órbitas con splines cúbicos ($\le 5$ entidades) o encadenamiento intertemporal Warm-Start ($\Delta W$).
5. **Módulos Complementarios de Cinética, Geopolítica, Acceso Abierto y ODS:**
   - [`classical-bibliometrics-laws`](../classical-bibliometrics-laws/SKILL.md): Cinética de crecimiento exponencial/logístico de Price ($\alpha, t_d$), Lotka, Bradford e Índice de Price.
   - [`geopolitical-collaboration-analyst`](../geopolitical-collaboration-analyst/SKILL.md): Matriz de colaboración internacional (Coseno de Salton $S_{ij}$) y liderazgo por país/bloque.
   - [`open-access-monitor`](../open-access-monitor/SKILL.md), [`sdg-impact-intelligence`](../sdg-impact-intelligence/SKILL.md) y [`openalex-mexico-visualizer`](../openalex-mexico-visualizer/SKILL.md).

---

## Etapa II: Criterios de Curaduría y Selección de Técnicas

Antes de redactar el reporte, el agente evalúa los artefactos generados en `./reportes/` y aplica las siguientes reglas:

1. **Elección del Método Ganador de Detección de Frentes:**
   - Si el agente probó acoplamiento bibliográfico, co-citación y/o agrupación por Topics de OpenAlex, debe evaluar cuál partición presenta mejor modularidad ($Q$), cobertura no trivial del corpus y diferenciación temática clara. La técnica con mejor señal encabeza el reporte; si ambas se complementan (como en el estudio de *Polaritons*, donde la evolución Macro/Meso/Micro de Topics se complementa con los frentes de acoplamiento bibliográfico), se articulan en secciones sucesivas.
2. **Selección de Dimensiones y Variante del SOM:**
   - Escoger de `./matrices/` los indicadores que mejor discriminen la naturaleza de los frentes o actores (ej. volumen, FWCI, % Top 10%, citas/doc, índice H/G, % colaboración internacional, año promedio/recencia o vía OA) verificando el coeficiente Silhouette ($s^*$).
   - Si el horizonte temporal o el tamaño de muestra por ventana no justifica las 3 variantes SOM al mismo tiempo, conservar la variante (Estática, Trayectorias o Longitudinal Warm-Start) que muestre con mayor nitidez la diferenciación y maduración de los frentes.
3. **Módulos Condicionales (ODS, APC, Geopolítica, Leyes):**
   - Incluir análisis de ODS (`sdg-impact-intelligence`) o de costos APC (`open-access-monitor`) únicamente cuando exista señal empírica relevante en el corpus o sea parte del encargo del usuario. Nunca rellenar tablas con ceros o `N/D` por cumplir un formato fijo.
4. **Bitácora de Exploración (`./reportes/exploration_log.md`):**
   - Registrar en `./reportes/exploration_log.md` qué métodos y parámetros se probaron y por qué se eligieron los que integran el reporte final.

---

## Disponibilidad de Datos y Reglas Anti-Fabricación

1. **Tablas reales en ClickHouse (`rag.works_flat` mundial y `rag.works_academic_all` México):** Usar únicamente columnas verificadas (`publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `keywords`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `referenced_works`).
2. **Tablas adaptadas a indicadores reales:** Diseñar las columnas de cada tabla con las métricas efectivamente calculadas en `./matrices/` y `./reportes/`. Prohibido imprimir columnas vacías con `N/D`.
3. **Indicadores de Especialización ($AI$, $\text{F-measure}$, $DShareC$, $CShareD$):** Aplicar los criterios de contexto analítico de Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet (2026, *Journal of Informetrics*).
4. **Lenguaje sobrio y cero filtración de andamiaje (*Zero-Scaffolding Leakage*):** Prohibición absoluta de superlativos (*"revolucionario"*, *"sin precedentes"*, *"espectacular"*). No mencionar comandos CLI ni prompts en la narrativa principal.

---

# Estructura Modular del Reporte de Radar de Frentes

# [Título del Reporte: Radar Cienciométrico, Evolución de Frentes de Investigación y Cartografía Topológica SOM en [Dominio / Tema], [Año_i – Año_f]]

## 1. RESUMEN EJECUTIVO Y PANORAMA DEL DOMINIO
- **1.1. Diagnóstico Global y Trazabilidad Metodológica (Directriz GLOBAL - ISSI):**
  * Síntesis de la magnitud del corpus ($N$ documentos, citas, FWCI, % Top 10%, ritmo de crecimiento anual y tiempo de duplicación $t_d$), declarando la fuente de datos (`rag.works_flat` / `rag.works_academic_all` / otras), fecha de corte, estrategia de delimitación y método de detección de frentes seleccionado tras la fase exploratoria.
- **1.2. Tabla 1: Cuadrante de Frentes de Investigación Identificados:**
  * Presentar los frentes principales detectados con sus métricas reales calculadas (ej. ID del Frente, Denominación Temática, Volumen de Documentos, Citas Totales / Citas por Doc, FWCI o Impacto, Año Medio / Fase de Madurez y Términos o Autores/Instituciones Núcleo).

---

## 2. ARQUITECTURA TAXONÓMICA Y REDES CONCEPTUALES DEL CAMPO
- **2.1. Convergencia Disciplinar (Macro / Meso / Micro):**
  * Distribución de la producción en dominios, campos, subcampos y topics, complementada con un diagrama **Mermaid** de la arquitectura temática real del corpus.
- **2.2. Estructura de la Red de Conocimiento:**
  * Análisis de la red de acoplamiento bibliográfico, co-citación o co-ocurrencia de conceptos (`network_keywords.html`, `fronts_summary.csv`), destacando los puentes interdisciplinarios y la cohesión modular ($Q$).

---

## 3. ANÁLISIS PROFUNDO DE LOS FRENTES DE INVESTIGACIÓN Y LINAJES LONGITUDINALES (AMI)
- **3.1. Caracterización Sustantiva de Cada Frente Activo (Cienciometría + Revisión de Literatura):**
  * Para cada uno de los frentes principales identificados en la Tabla 1, presentar una subsección analítica que explique:
    1. *El problema científico o tecnológico central que resuelve el frente.*
    2. *Los hallazgos, metodologías o arquitecturas propuestas en sus artículos núcleo más citados/centrales dentro del corpus.*
    3. *Su perfil de impacto, velocidad de crecimiento e instituciones/países líderes.*
- **3.2. Dinámica Evolutiva y Linajes Aluviales (AMI):**
  * Análisis de las transiciones intertemporales entre ventanas (`alluvial_lineages.html`, `alluvial_events.csv`): qué frentes muestran **Persistencia** (hilo conductor consolidado), cuáles experimentaron **Escisión (*Split*)** hacia nuevas sublíneas especializadas, cuáles surgieron por **Fusión (*Merge*)** de comunidades previas y cuáles representan **Génesis** recientes.

---

## 4. CARTOGRAFÍA TOPOLÓGICA MULTIDIMENSIONAL CON REDES SOM (KOHONEN)
- **4.1. Posicionamiento Multidimensional en la Tríada LabSOM:**
  * Interpretación de la **U-Matrix**, **Mapas de Componentes** (en las dimensiones seleccionadas de las 42 disponibles) y **Meta-clustering de Vesanto** ($K^*$ óptimo por Silhouette $s^*$), clasificando los frentes, países o instituciones líderes sin el reduccionismo de rankings escalares.
- **4.2. Tabla de Clusters en el SOM y Evolución Temporal (Trayectorias CMA+Splines y/o Longitudinal Warm-Start):**
  * Presentar la tabla de caracterización de los clusters del SOM (Fortalezas en zonas rojas, vulnerabilidades en zonas verdes y miembros representativos) y discutir la evolución dinámica observada en las trayectorias (`som_trajectories.html`) o en el mapeo longitudinal (`longitudinal_som_report.md`).

---

## 5. DINÁMICA GEOPOLÍTICA, ESPECIALIZACIÓN Y DIMENSIONES COMPLEMENTARIAS (SEGÚN SEÑAL EMPÍRICA)
*(Incluir las subsecciones que hayan arrojado hallazgos significativos durante la exploración):*
- **5.1. Geopolítica de la Colaboración y Especialización ($CShareD$, $DShareC$, Salton):**
  * Polos nacionales e institucionales líderes, corredores bilaterales de mayor afinidad de Salton (`geopolitical_dashboard.html`) y patrones de especialización temática.
- **5.2. (Condicional) Canales de Publicación, Vías de Acceso Abierto / APC y Alineación con ODS:**
  * Distribución por vías de Acceso Abierto (ej. peso de preprints/vía Verde vs. Gold APC y vía Diamante) y/o contribución a los Objetivos de Desarrollo Sostenible cuando exista señal relevante en el corpus.

---

## 6. CONCLUSIONES E IMPLICACIONES PROSPECTIVAS (ROADMAP)
- Identificación de oportunidades de investigación de frontera (frentes con alta aceleración o alto impacto emergente y nichos abiertos a la colaboración) y hoja de ruta estratégica a corto y mediano plazo.

---

## ANEXOS, REFERENCIAS Y MATERIAL SUPLEMENTARIO AUDITABLE
- **Referencias Bibliográficas:** Trabajos seminales del corpus discutidos en la Sección 3 y referencias metodológicas (Carrillo-Calvet et al., 2025; Jiménez-Andrade et al., 2024, 2025, 2026; Ruiz-Sánchez et al., 2025; Villaseñor-García et al., 2017; Traag et al., 2019; Huang et al., 2011).
- **Catálogo de Artefactos en el Workspace:** Tabla con enlaces a `./corpus.parquet`, `./matrices/*.parquet`, `./reportes/fronts_summary.csv`, `./reportes/alluvial_lineages.html`, `./reportes/som_dashboard.html`, `./reportes/som_trajectories.html` y `./reportes/exploration_log.md`.
