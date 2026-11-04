---
name: template-informe-tecnico-institucional
description: >-
  Elaboración de informes técnicos de evaluación institucional cienciométrica de máxima autoridad (estilo Instituto de Neurobiología / INB UNAM, ICN, INCan). Opera bajo un protocolo en 2 etapas: I) Exploración empírica en el workspace mediante el menú de Agent Skills (identidad ROR y dependencias, cosecha global/nacional, benchmarking con instituciones homólogas especializadas, motor de 42+ indicadores sin truncar, censo SNII, redes de colaboración, evolución temática, auditoría OA/APC y tríada SOM estática/trayectorias/longitudinal), y II) Curaduría científica para descartar análisis sin señal y estructurar el informe con las dimensiones e indicadores de mayor valor diagnóstico.
---

# Plantilla Maestra: Informe Técnico de Evaluación Institucional, Benchmarking con Pares y Diagnóstico Multidimensional SOM
### *Inspirada en los reportes cienciométricos del C3-UNAM / LabSOM para dependencias e institutos de investigación (Instituto de Neurobiología / INB, ICN, INCan)*

Esta plantilla guía la elaboración de un **INFORME TÉCNICO DE EVALUACIÓN INSTITUCIONAL** de máxima autoridad para rectorías, direcciones de institutos, consejos técnicos y comités de política científica.

Integra el **marco neurocomputacional de análisis multidimensional de perfiles de desempeño basado en Mapas Autoorganizados de Kohonen (SOM)** (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor-García et al., 2017; Jiménez-Andrade et al., 2024, 2025, 2026) para superar el reduccionismo de los rankings unidimensionales (*pesar y sumar*), evaluando a la institución **frente a instituciones homólogas especializadas y pares legítimos** (como en el estudio comparativo del INB con centros de neurociencias nacionales e internacionales).

---

## Etapa I: Menú de Agent Skills para la Exploración Institucional (*Fase de Laboratorio*)

El agente opera bajo el principio **Workspace-First** (`./corpus.parquet` $\to$ `./matrices/*.parquet` $\to$ `./reportes/`) y dispone del siguiente **Menú de Agent Skills** para explorar las distintas dimensiones de la institución evaluada:

1. **Identidad Institucional, Cosecha y Universo de Comparación (`./corpus.parquet`):**
   - [`openalex-mexico-institutions`](../openalex-mexico-institutions/SKILL.md) y [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md): Resolución del código canónico **ROR** (ej. UNAM `https://ror.org/01tmp8f25`, Cinvestav `https://ror.org/05cb51e40`) y aislamiento de dependencias o campus (ej. *Instituto de Neurobiología*, *Instituto de Ciencias Nucleares*) mediante filtrado insensible a mayúsculas y diacríticos en `institution_names` sobre `rag.works_academic_all` (CERO JOINs).
   - [`openalex-search-engineer`](../openalex-search-engineer/SKILL.md) (`rag.works_flat`) y [`scientometrics-incites-expert`](../scientometrics-incites-expert/SKILL.md): Extracción de producción e indicadores de **instituciones homólogas internacionales o nacionales especializadas en el mismo dominio y de escala comparable** (estilo Sección 2 del *Informe del INB 2022*).
2. **Motor de 42+ Indicadores Multidimensionales (Sin Truncar Columnas):**
   - [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Genera en `./matrices/` la matriz completa de **46 columnas (42 indicadores numéricos + 4 metadatos)** para la institución, sus pares comparables, sus investigadores o sus áreas temáticas (`by-entity`), así como la serie anual suavizada con Media Móvil Centrada (`annual-series --cma-window 3`) y la evolución por periodos (`period-series`).
3. **Menú de Módulos Analíticos Exploratorios (Probar y Seleccionar según la Naturaleza de la Institución):**
   - **Módulo de Hiperautoría y Capacidad Autónoma:** Desglose de la producción según `length(author_names)` ($\le 20$ autores vs. mega-consorcios $> 20$ autores) cuando el instituto participe en colaboraciones de *Big Science* (ej. física de altas energías en ICN, genómica o astronomía).
   - **Módulo de Evolución Temática y Especialización ($AI$, $\text{F-measure}$, $DShareC$, $CShareD$):** [`topics-research-fronts-intelligence`](../topics-research-fronts-intelligence/SKILL.md) y análisis de categorías/subcampos para identificar las etapas de desarrollo temático del instituto, su priorización interna ($DShareC$) y su peso en el contexto nacional/mundial ($CShareD$) (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2026).
   - **Módulo de Redes de Colaboración Institucional e Internacional:** [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md) y [`geopolitical-collaboration-analyst`](../geopolitical-collaboration-analyst/SKILL.md) para mapear las redes de coautoría intramuros, nacionales e internacionales.
   - **Módulo de Cartografía Multidimensional SOM (Las 3 Variantes LabSOM):**
     * [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Posicionamiento del instituto frente a su universo de instituciones homólogas en el SOM estático, eligiendo los indicadores con mayor poder diagnóstico (`--indicator-cols`), U-Matrix, Mapas de Componentes y clusters de pares comparables.
     * [`som-trajectory-mapping`](../som-trajectory-mapping/SKILL.md) y [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md): Evolución histórica del perfil de desempeño del propio instituto a través de los años (trayectoria continua CMA+Splines, como en la Sección 5 del *Informe del INB*) o entre gestiones/periodos (Warm-Start $\Delta W$).
   - **Módulo de Claustro Académico y Padrón SNII:** [`snii-identity-resolver`](../snii-identity-resolver/SKILL.md), [`openalex-mexico-author-search`](../openalex-mexico-author-search/SKILL.md) e [`infotlachia-scholar-intelligence`](../infotlachia-scholar-intelligence/SKILL.md) (distribución por niveles Candidato a Emérito, concentración de Lotka y relevo generacional).
   - **Módulo de Acceso Abierto, Costos APC, Revistas y ODS:** [`open-access-monitor`](../open-access-monitor/SKILL.md) (6 vías OA y gasto APC en USD), [`journal-editorial-intelligence`](../journal-editorial-intelligence/SKILL.md), [`sdg-impact-intelligence`](../sdg-impact-intelligence/SKILL.md) y [`openalex-mexico-visualizer`](../openalex-mexico-visualizer/SKILL.md).

---

## Etapa II: Criterios de Curaduría y Descarte en Informes Institucionales

Cada institución tiene una vocación, escala y problemática distinta (no es igual evaluar un instituto de física nuclear con mega-consorcios del CERN que un instituto de neurobiología o uno de investigaciones sociales). El agente debe aplicar estas reglas antes de redactar:

1. **Adaptación a la Vocación de la Dependencia (Probar y Descartar):**
   - **Filtro de Hiperautoría ($\le 20$ vs. $> 20$ autores):** Si al explorar `./corpus.parquet` se observa que los artículos con $> 20$ autores representan una fracción significativa o distorsionan el FWCI institucional, el análisis tripartito se convierte en un eje central del informe. Si en cambio $\ge 98\%$ de la producción tiene $\le 20$ autores, **no se fuerza una sección ni tabla artificial de mega-consorcios**: basta con consignar el dato en una línea metodológica y dedicar el espacio a la evolución temática y al benchmarking con pares.
   - **Selección de Dimensiones en el SOM:** Explorar en `./matrices/` qué combinación de indicadores refleja mejor tanto las fortalezas como las áreas de oportunidad de la dependencia frente a sus homólogas (ej. volumen, FWCI, % Top 10%, % colaboración internacional, índice H/G, vía Diamante o especialización) verificando el coeficiente Silhouette ($s^*$).
   - **Evolución del Perfil Propio vs. Comparación con Pares:** Siguiendo el modelo del *Informe del INB*, combinar cuando los datos lo permitan: (a) el mapa SOM comparativo frente a instituciones homólogas, y (b) el mapa SOM de la trayectoria evolutiva de la propia institución a lo largo de sus años o periodos.
2. **Cero Columnas Vacías (`N/D`) en las Tablas:**
   - Construir todas las tablas del informe **exclusivamente con los indicadores calculados con datos reales**. Si un indicador (como tasa de primer autor desde `raw_data` o padrón SNII cuando se evalúa una entidad extranjera) no está presente en los datos del workspace, omitir esa columna de la tabla en vez de llenarla con `N/D`.
3. **Bitácora de Exploración (`./reportes/exploration_log.md`):**
   - Documentar en `./reportes/exploration_log.md` los análisis realizados en el workspace y la justificación de las dimensiones seleccionadas para el informe.

---

## Disponibilidad de Datos, Reglas Anti-Fabricación y Reglas Editoriales

1. **Tablas y columnas reales en ClickHouse (`rag.works_academic_all` y `rag.works_flat`):** `publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `keywords`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `is_doaj_journal`, `is_core_journal`, `referenced_works`.
2. **Desambiguación de dependencias universitarias:** El ROR identifica a la institución matriz (ej. UNAM). Para aislar una dependencia o instituto, filtrar por `institution_names` e indicar explícitamente en la nota metodológica el alcance del filtro toponímico.
3. **Lenguaje ejecutivo sobrio y cero filtración de andamiaje (*Zero-Scaffolding Leakage*):** Prohibición absoluta de adjetivos hiperbólicos (*"espectacular"*, *"revolucionario"*, *"sin precedentes"*). No mencionar prompts ni herramientas de chat en el cuerpo del informe.

---

# Estructura Modular del Informe Técnico Institucional (Adaptar a los Hallazgos Seleccionados)

# [Título Oficial: Evaluación Cienciométrica, Evolución Temática y Diagnóstico Multidimensional SOM de [Nombre de la Institución / Dependencia], Periodo [Año_i – Año_f]]

## 1. RESUMEN EJECUTIVO Y DIAGNÓSTICO SITUACIONAL
- **1.1. Contexto Institucional y Síntesis de Posicionamiento:**
  * Misión de la dependencia, volumen histórico y reciente de producción, impacto normalizado (FWCI), inserción en el decil superior (Top 10%) y principales fortalezas y tensiones estructurales detectadas.
- **1.2. Tabla 1: Indicadores Clave de Desempeño Institucional (Semáforo Diagnóstico):**
  * Presentar los indicadores efectivamente calculados para la institución contrastados con su referencia (media de la universidad matriz, media nacional o mundial, o pares homólogos) y su estado diagnóstico (🟢 Óptimo / Fortaleza, 🟡 Alerta preventiva, 🔴 Área de atención prioritaria).

---

## 2. MATERIALES, MÉTODO Y TRAZABILIDAD (DIRECTRIZ GLOBAL - ISSI)
- **2.1. Fuentes de Información y Delimitación de la Producción Institucional:**
  * Bases de datos utilizadas (`rag.works_academic_all`, `rag.works_flat`, InCites/WoS/Scopus, Padrón SNII), identificador ROR, criterios de desambiguación de la dependencia, fecha de corte y métodos de conteo (completo vs. fraccional; y desglose de hiperautoría cuando aplique).
- **2.2. Indicadores y Metodología Neurocomputacional SOM:**
  * Definición de los indicadores seleccionados tras la exploración y explicación del modelado de perfiles multidimensionales y trayectorias con redes autoorganizadas de Kohonen (SOM).

---

## 3. DINÁMICA DE LA PRODUCCIÓN CIENTÍFICA Y ESTUDIO COMPARATIVO CON INSTITUCIONES HOMÓLOGAS
- **3.1. Evolución Histórica de la Productividad y Visibilidad:**
  * Análisis de las etapas de crecimiento de la dependencia y su participación porcentual respecto a la institución matriz, al país y a la región (incluyendo, cuando sea pertinente por la disciplina, la comparativa entre producción autónoma $\le 20$ autores y consorcios $> 20$ autores).
- **3.2. Benchmarking con Instituciones Especializadas Homólogas:**
  * Comparación del desempeño en volumen, impacto normalizado (FWCI), excelencia (% Top 10% / Top 1%) y colaboración frente a instituciones nacionales e internacionales de vocación y escala similares.

---

## 4. EVOLUCIÓN TEMÁTICA, FRENTES DE INVESTIGACIÓN Y REDES DE COLABORACIÓN
- **4.1. Especialización y Evolución Temática ($DShareC$, $CShareD$, $AI$, $\text{F-measure}$ y Frentes):**
  * Distribución de la producción en áreas, subcampos y frentes de investigación activos; identificación de las líneas consolidadas y de los temas emergentes a lo largo del tiempo.
- **4.2. Estructura de la Colaboración Científica:**
  * Redes de coautoría con otras dependencias, instituciones nacionales y socios internacionales (`network_institutions.html` / `geopolitical_dashboard.html`).

---

## 5. PERFIL MULTIDIMENSIONAL DE DESEMPEÑO Y EVOLUCIÓN EN EL SOM (KOHONEN)
- **5.1. Posicionamiento Frente a Pares Comparables en la Tríada LabSOM:**
  * Análisis sobre la **U-Matrix**, **Mapas de Componentes** (Verde-Amarillo-Rojo) y **Meta-clustering de Vesanto** ($K^*$ óptimo por Silhouette $s^*$), identificando el cluster de pares legítimos de la institución, sus fortalezas cardinales (zonas rojas) y sus vulnerabilidades relativas (zonas verdes).
- **5.2. Tabla de Clusters y Evolución Temporal del Perfil Institucional (Trayectoria SOM / Longitudinal):**
  * Tabla de caracterización de los clusters en el SOM y análisis de la trayectoria evolutiva de la propia institución a través de las ventanas temporales estudiadas (`som_dashboard.html`, `som_trajectories.html` y/o `longitudinal_som_report.md`).

---

## 6. DIMENSIONES DE GOBERNANZA: CLAUSTRO ACADÉMICO, ACCESO ABIERTO Y COSTOS APC (SEGÚN APLICABILIDAD)
*(Incluir y desarrollar con profundidad las subsecciones respaldadas por los datos del estudio):*
- **6.1. Estructura del Claustro, Productividad Autoral y Padrón SNII:**
  * Composición por niveles del SNII, distribución de productividad de los investigadores y diagnóstico de relevo generacional.
- **6.2. Auditoría de las 6 Vías de Acceso Abierto y Costos de Publicación en APC (USD):**
  * Tabla y análisis de la distribución en las 6 vías OA (`diamond`, `gold`, `hybrid`, `green`, `bronze`, `closed`), gasto observado/estimado en cuotas APC comerciales (USD) y oportunidades de ahorro mediante vía Diamante y repositorios verdes.

---

## 7. CONSIDERACIONES FINALES Y MATRIZ DE RECOMENDACIONES ESTRATÉGICAS (1, 3 Y 5 AÑOS)
- Síntesis integradora de hallazgos y **Tabla de Recomendaciones Accionables** para los órganos de dirección y cuerpos colegiados (Corto plazo: 1 año; Mediano plazo: 3 años; Largo plazo: 5 años) con indicadores verificables.

---

## ANEXOS, REFERENCIAS Y MATERIAL SUPLEMENTARIO AUDITABLE
- **Referencias Metodológicas:** Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge (2025); Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet (2025, 2026); Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet (2024); Villaseñor-García et al. (2017); Vesanto & Alhoniemi (2000); Hicks et al. (2015).
- **Catálogo de Artefactos en el Workspace:** Enlaces a `./corpus.parquet`, `./matrices/*.parquet`, dashboards interactivos HTML en `./reportes/` y bitácora `./reportes/exploration_log.md`.
