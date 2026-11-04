---
name: template-articulo-cientifico-imryd
description: >-
  Redacción de manuscritos científicos de investigación original o revisiones cienciométricas con estructura canónica IMRyD para someter a revistas Q1/Q2 en Cienciometría y Science of Science (estilo Polaritones / Especialización JoI). Opera bajo un protocolo en 2 etapas: I) Exploración empírica en el workspace mediante el menú completo de Agent Skills (delimitación, cosecha CERO JOINs, motor de 42+ indicadores, leyes clásicas, redes y frentes de investigación, revisión profunda de artículos núcleo, tríada SOM estática/trayectorias/longitudinal, geopolítica, especialización y OA/APC), y II) Curaduría científica para descartar técnicas sin señal y construir la narrativa del artículo únicamente con los resultados más sólidos y reveladores.
---

# Plantilla Maestra: Artículo Científico de Investigación Original / Revisión Cienciométrica (Formato IMRyD - Journal Q1)
### *Inspirada en el flujo de investigación humana del grupo LabSOM / C3-UNAM (ej. Sixty Years of Research on Polaritons, 2025; Specialization Indicators in Scientometrics, 2026; Neural Longitudinal & Trajectory Mapping, 2024–2025)*

Esta plantilla guía al agente para investigar y redactar un **MANUSCRITO CIENTÍFICO DE INVESTIGACIÓN ORIGINAL O REVISIÓN CIENCIOMÉTRICA** con estructura canónica **IMRyD** de grado publicable en revistas internacionales Q1/Q2 (*Journal of Informetrics*, *Scientometrics*, *Quantitative Science Studies*, *Research Evaluation*, *Engineering Reports*).

A diferencia de un formulario rígido, esta plantilla emula el **proceso real de investigación científica humana**: primero el investigador formula hipótesis, explora el corpus con un **menú amplio de técnicas analíticas** en su espacio de trabajo (*Fase de Laboratorio*), evalúa qué métodos arrojan estructura, ajuste estadístico o hallazgos reveladores, **descarta las técnicas que no aportan señal o rompen el hilo conductor**, y finalmente estructura el artículo alrededor de la **historia científica respaldada por la mejor evidencia empírica** (*Fase de Curaduría y Redacción*).

---

## Etapa I: Menú de Agent Skills para la Exploración Empírica (*Fase de Laboratorio*)

Para garantizar rigor metodológico, reproducibilidad y cero alucinaciones, el agente opera bajo el principio **Workspace-First** (`./corpus.parquet` $\to$ `./matrices/*.parquet` $\to$ `./reportes/`) delegando los cálculos en el siguiente **Menú de Agent Skills**:

### 1. Cimiento Obligatorio: Delimitación, Cosecha y Matrices Multidimensionales
*(Si `./corpus.parquet` y `./matrices/` ya existen en el workspace, el agente los reutiliza directamente sin re-descargar).*

- **Delimitación y Estrategia de Búsqueda:**
  * [`bibliometric-search-strategist`](../bibliometric-search-strategist/SKILL.md): Delimitación multi-etapa (Huang, Schiebel & Porter, 2011), auditoría bajo la directriz **GLOBAL (ISSI)** y transpilación a ClickHouse SQL (`rag.works_flat` para alcance mundial o `rag.works_academic_all` para México, con **CERO JOINs**) o sintaxis nativa WoS/Scopus/PubMed.
- **Cosecha de Corpus Hacia `./corpus.parquet`:**
  * [`openalex-search-engineer`](../openalex-search-engineer/SKILL.md): Extracción columnar desde ClickHouse global (`rag.works_flat`, 464M+ obras) con `referenced_works`, `all_country_codes`, `keywords` y métricas de impacto.
  * [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md): Orquestador nacional sobre `rag.works_academic_all` (1.65M obras de México).
  * Cosechadores externos opcionales: [`openalex-harvester`](../openalex-harvester/SKILL.md), [`scopus-harvester`](../scopus-harvester/SKILL.md), [`pubmed-harvester`](../pubmed-harvester/SKILL.md), [`arxiv-harvester`](../arxiv-harvester/SKILL.md), [`semantic-scholar-harvester`](../semantic-scholar-harvester/SKILL.md) o [`scientometrics-incites-expert`](../scientometrics-incites-expert/SKILL.md).
- **Cálculo de la Batería Completa de Indicadores (Sin Truncar Columnas):**
  * [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Calcula el resumen global (`summary`) y genera en `./matrices/` las matrices de **46 columnas (42 indicadores numéricos + 4 metadatos)** por país, institución, autor, fuente o topic (`by-entity`), series anuales suavizadas con Media Móvil Centrada (`annual-series --cma-window 3`) y ventanas por periodos (`period-series`).
  * [`bibliometric-eda-profiler`](../bibliometric-eda-profiler/SKILL.md): Perfilado exploratorio, índices H/G/M y dispersión.

### 2. Menú de Familias Analíticas Exploratorias (Seleccionar, Probar y Evaluar)

El agente cuenta con 5 familias de técnicas para explorar sus preguntas de investigación ($RQ_1, RQ_2, \dots$):

| Familia Analítica | Agent Skills Disponibles | Qué Permite Explorar y Probar en el Laboratorio |
| :--- | :--- | :--- |
| **Familia A: Dinámica Temporal y Leyes Clásicas** | [`classical-bibliometrics-laws`](../classical-bibliometrics-laws/SKILL.md) | Ajuste exponencial vs. logístico de Price ($R^2$, tasa $\alpha$, tiempo de duplicación $t_d$), detección de puntos de inflexión/quiebres estructurales ($\tau$), ley de productividad de Lotka (full vs. fractional counting, prueba KS), zonas de Bradford e Índice de Price de obsolescencia. |
| **Familia B: Estructura Intelectual, Redes y Frentes de Investigación** | [`topics-research-fronts-intelligence`](../topics-research-fronts-intelligence/SKILL.md), [`research-fronts-detection-expert`](../research-fronts-detection-expert/SKILL.md), [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md) | Comparar **acoplamiento bibliográfico** (frentes emergentes recientes), **co-citación** (bases intelectuales), **citación directa** o **co-ocurrencia conceptual** con partición Leiden (CPM/Modularity). Rastrear la evolución longitudinal y eventos aluviales AMI (persistencia, fusión, escisión, génesis) por ventanas temporales o niveles Macro/Meso/Micro. |
| **Familia C: Revisión Profunda de Literatura y Artículos Núcleo (*Core Papers*)** | [`deep-literature-researcher`](../deep-literature-researcher/SKILL.md), [`graphrag-scientific-intelligence`](../graphrag-scientific-intelligence/SKILL.md) | *Citation Snowballing* con filtro de densidad de Glänzel ($k \ge 2$) para el estado del arte, y **lectura sustantiva de los artículos más citados/centrales de cada frente detectado** en `./corpus.parquet` para explicar los hallazgos científicos reales de cada comunidad (estilo Sección 6 del artículo de *Polaritons*). |
| **Familia D: Cartografía Neurocomputacional SOM (Las 3 Variantes LabSOM)** | [`som-methodological-expert`](../som-methodological-expert/SKILL.md), [`som-trajectory-mapping`](../som-trajectory-mapping/SKILL.md), [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md), [`semantic-manifold-expert`](../semantic-manifold-expert/SKILL.md) | 1) **SOM Estático:** Perfiles multidimensionales de países, instituciones o frentes sobre cualquier subconjunto de los 42 indicadores (`--indicator-cols`), U-Matrix, Mapas de Componentes y meta-clustering de Vesanto optimizado por Silhouette ($s^*$).<br>2) **SOM de Trayectorias:** Evolución temporal continua suavizada con CMA y splines cúbicos ($\le 5$ entidades focales o perfil global).<br>3) **SOM Longitudinal Warm-Start:** Deriva sináptica ($\Delta W$) y rotación intertemporal entre periodos. |
| **Familia E: Geopolítica, Especialización, Vías OA/APC y ODS (Modulares)** | [`geopolitical-collaboration-analyst`](../geopolitical-collaboration-analyst/SKILL.md), [`open-access-monitor`](../open-access-monitor/SKILL.md), [`sdg-impact-intelligence`](../sdg-impact-intelligence/SKILL.md), [`journal-editorial-intelligence`](../journal-editorial-intelligence/SKILL.md) | Afinidad bilateral (Coseno de Salton $S_{ij}$), liderazgo autoral, indicadores de especialización ($AI$, $\text{F-measure}$, $DShareC$ y $CShareD$), auditoría de las 6 vías de Acceso Abierto y gasto APC (USD), y alineación con los ODS 1–17. |

---

## Etapa II: Protocolo de Curaduría Científica y Descarte (*De los Datos a la Historia del Paper*)

En la investigación científica real, **no todos los análisis explorados terminan en el artículo publicado**. Antes de redactar el manuscrito, el agente debe evaluar los resultados obtenidos en la Etapa I y aplicar las siguientes **Reglas de Selección y Descarte**:

1. **Criterio de Hilo Conductor (*Storytelling Científico*):**
   - Definir cuál es la tesis central y el arco narrativo del artículo respaldado por la evidencia más fuerte (ej. *¿la emergencia de un nuevo polo hegemónico como China en Polaritones? ¿la bifurcación de un frente teórico hacia aplicaciones de ingeniería? ¿una paradoja entre volumen e impacto normalizado revelada por el SOM?*).
   - Seleccionar únicamente entre **3 y 5 bloques analíticos principales** que se conecten orgánicamente para responder a las preguntas de investigación ($RQ_1 \dots RQ_k$).

2. **Criterio de Competencia Metodológica y Calidad de Señal (Probar y Descartar):**
   - **En Frentes y Redes:** Si se probaron varias redes (ej. acoplamiento bibliográfico vs. co-citación vs. co-ocurrencia), conservar para el cuerpo del artículo aquella que ofrezca mayor modularidad ($Q$), clusters temáticamente nítidos y mejor resolución histórica, descartando las redes ruidosas o redundantes.
   - **En la Selección de Indicadores y Variantes del SOM:**
     * El agente dispone de 42 indicadores numéricos en `./matrices/`. En lugar de usar una lista fija a ciegas, debe elegir las dimensiones que tengan sentido teórico para la pregunta (ej. incluyendo *Global Share* $CShareD$ y *National Share* $DShareC$, FWCI, % Top 10%, % Colaboración Internacional, índice G/M o vía Diamante) y verificar que generen una partición con buen coeficiente **Silhouette ($s^*$)** y gradientes interpretables en los Mapas de Componentes.
     * Elegir la variante SOM que mejor responda al diseño del estudio: **SOM Estático** (para radiografía transversal de perfiles), **SOM de Trayectorias CMA+Splines** (cuando las series anuales tienen horizonte suficiente para trazar órbitas suaves de $\le 5$ actores líderes) y/o **SOM Longitudinal Warm-Start** (cuando se contrastan ventanas plurianuales discretas). Si una variante no aporta información nueva respecto a la otra, se descarta del texto principal.
   - **En Leyes Bibliométricas Clásicas:** Si el horizonte temporal es muy corto (ej. 3–5 años) y el ajuste logístico o el Índice de Price no son informativos, o si Bradford/Lotka son tangenciales al foco temático del estudio, reportar únicamente la cinética de crecimiento relevante y descartar los ajustes que no aporten valor analítico.
   - **En Módulos Especializados (OA/APC, ODS, Geopolítica):** Incluir secciones o tablas de Acceso Abierto/APC o de ODS **sólo si** forman parte de los objetivos del estudio o si la exploración reveló un hallazgo empírico relevante (ej. una asimetría marcada entre vía Verde/arXiv y vía Gold APC, o una fuerte concentración en un ODS específico). Nunca meter con calzador subsecciones desconectadas de la tesis central.

3. **Registro Transparente en la Bitácora de Exploración (`./reportes/exploration_log.md`):**
   - Antes de redactar el artículo, guardar o actualizar `./reportes/exploration_log.md` resumiendo brevemente: (a) qué técnicas del menú se ejecutaron, (b) cuáles se seleccionaron para el cuerpo del manuscrito por su solidez empírica, y (c) cuáles se descartaron o enviaron al Material Suplementario y por qué.

---

## Disponibilidad de Datos y Reglas Anti-Fabricación (Inviolables)

**Tablas y columnas reales en ClickHouse (`rag.works_flat` para alcance mundial con 464.8M obras y `rag.works_academic_all` para producción de México con 1.65M obras)**: `publication_year`, `cited_by_count`, `is_oa`, `oa_status` (`closed`, `green`, `diamond`, `gold`, `bronze`, `hybrid`), `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `keywords`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `is_doaj_journal`, `is_core_journal`, `referenced_works`.

1. **Diseño de Tablas sin Columnas Vacías (`N/D`):** Construir las tablas del artículo **únicamente con las columnas de indicadores que fueron efectivamente calculadas y contienen datos reales en el workspace**. No incluir columnas enteras rellenas con `N/D` (como cuartiles JCR/Scimago, colaboración industrial o tasas de primer autor cuando no se extrajeron de `raw_data`). Si un indicador no disponible en el esquema es relevante conceptualmente, mencionarlo brevemente en las limitaciones metodológicas.
2. **Número de autores e hiperautoría:** Usar `length(author_names)`. Aplicar el desglose por regímenes de autoría ($\le 20$ vs. $> 20$ autores) cuando el campo estudiado presente hiperautoría real (*Big Science*); no forzar una tabla tripartita vacía si la totalidad o casi totalidad del corpus tiene $\le 20$ autores.
3. **APC:** Usar `apc_paid_usd` (observado) y `apc_list_usd` (precio de lista) o la estimación auditada de `open-access-monitor`, indicando siempre cuál se reporta.
4. **Indicadores de Especialización ($AI$, $\text{F-measure}$, $DShareC$ y $CShareD$):** Siguiendo a Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet (2026, *Journal of Informetrics*), distinguir rigurosamente entre **priorización interna de un dominio dentro de una entidad ($DShareC$, *National/Institutional Share*)** y **participación de la entidad en el total mundial del dominio ($CShareD$, *Global Share*)**, recordando que en la comparación entre países dentro de un dominio fijo el $AI$ es equivalente en rango a $DShareC$ y la $\text{F-measure}$ opera como proxy de $CShareD$, mientras que al comparar dominios dentro de un mismo país el patrón se invierte.
5. **Coseno de Salton:** Verificar $S_{ij} = C_{ij}/\sqrt{C_i C_j}$ a partir de los conteos de coautoría ($C_{ij}$, $C_i$, $C_j$).
6. **Cálculo de Matrices y Entrenamiento SOM:** Generar siempre primero `./matrices/*.parquet` con `tlachia_metrics_cli.py` (46 columnas sin truncar) y entrenar el SOM con `som_pipeline_cli.py`, `som_trajectory_cli.py` o `neural_longitudinal_cli.py` persistiendo `./reportes/som_state.json` y `./reportes/som_dashboard.html`.

---

## Reglas Editoriales Estrictas

- **LENGUAJE MODERADO Y SOBRIO (PROHIBICIÓN ABSOLUTA DE SUPERLATIVOS):** Emplear un estilo rigurosamente académico, neutro y fundamentado en evidencia empírica. Queda prohibido el uso de adjetivos hiperbólicos (*"revolucionario"*, *"sin precedentes"*, *"extraordinario"*, *"espectacular"*, *"abrumador"*, *"pionero"*, *"asombroso"*).
- **ZERO-SCAFFOLDING LEAKAGE:** El manuscrito debe leerse como un artículo científico formal sometido a arbitraje por pares. No mencionar nombres de scripts internos, comandos CLI, prompts ni entornos de chat en el cuerpo del artículo (reservar los nombres de scripts para la sección de Disponibilidad de Datos y Código y Material Suplementario).
- **INTEGRACIÓN CIENCIOMETRÍA + CONTENIDO SUSTANTIVO DEL CAMPO:** Especialmente al analizar los frentes de investigación (estilo *Polaritons*, Ruiz-Sánchez et al., 2025), no limitarse a listar números de clusters: **discutir qué problemas científicos, métodos o descubrimientos abordan los artículos seminales y más citados de cada frente**.

---

# Estructura Modular del Manuscrito IMRyD (Adaptar Subsecciones a los Hallazgos Seleccionados)

# [Título Formal, Descriptivo e Informativo en Español y/o Inglés]

> ## RESUMEN / ABSTRACT
> Presentar un resumen fluido (o estructurado en *Objetivo, Metodología, Resultados y Conclusiones*) que sintetice el problema científico estudiado, el corpus analizado, la combinación específica de técnicas seleccionadas tras la curaduría (ej. redes de acoplamiento bibliográfico, revisión de literatura y mapeo multidimensional SOM) y los hallazgos cuantitativos y sustantivos principales.
>
> **Palabras clave / Keywords:** (5 a 7 términos canónicos en orden alfabético).

---

## 1. INTRODUCCIÓN Y ANTECEDENTES DEL DOMINIO
- **1.1. Fenomenología e Importancia Científica del Campo Estudiado:**
  * Explicar el origen, los hitos conceptuales o tecnológicos del tema analizado (ej. desde las predicciones teóricas fundacionales hasta las aplicaciones contemporáneas) y por qué su estructura actual requiere una cartografía cienciométrica y computacional.
- **1.2. Estado del Arte (Background) y Brecha Analítica:**
  * Síntesis crítica de estudios bibliométricos o revisiones previas sobre el tema o áreas afines (apoyándose en una tabla comparativa de estudios previos cuando aporte claridad).
  * Articulación explícita de las preguntas de investigación ($RQ_1, RQ_2, \dots$) y del aporte diferencial del estudio.

---

## 2. MATERIALES Y MÉTODO (DATA SOURCES, INDICATORS & WORKFLOW)
- **2.1. Fuentes de Datos, Estrategia de Búsqueda y Criterios de Selección (Directriz GLOBAL - ISSI):**
  * Declarar la base de datos utilizada (OpenAlex / ClickHouse `rag.works_flat` o `rag.works_academic_all`, Web of Science, Scopus, InCites), fecha exacta de corte, ecuación de búsqueda empleada, ventana temporal, tipos documentales incluidos y tamaño final del corpus depurado ($N$).
  * Incluir un **Diagrama de Flujo Metodológico (Mermaid)** que ilustre las etapas reales aplicadas en el estudio (Recolección y filtrado del corpus $\to$ Indicadores calculados $\to$ Flujos analíticos seleccionados: ej. Flujo LabSOM y Flujo de Redes/Frentes).
- **2.2. Indicadores Cienciométricos Seleccionados:**
  * Definir formalmente y con su formulación matemática **únicamente los indicadores utilizados en los análisis que superaron la fase de curaduría** (ej. productividad, tasas de crecimiento, FWCI/CNCI, % Top 10%, % Top 1%, *Global Share* $CShareD$, *National/Institutional Share* $DShareC$, Índice de Actividad $AI$, $\text{F-measure}$, índices H/G/M, % Colaboración Internacional, vías de Acceso Abierto o Coseno de Salton).
- **2.3. Procesamiento de Datos, Redes y Modelado Neurocomputacional SOM:**
  * Explicar con rigor técnico las metodologías empleadas en los resultados seleccionados:
    - *Si se incluye análisis cinético/leyes:* formulación de los modelos ajustados.
    - *Si se incluye análisis de redes y frentes de investigación:* tipo de red seleccionada (ej. acoplamiento bibliográfico, co-citación o co-ocurrencia), normalización (*Association Strength* o Coseno de Salton), algoritmo de partición (Leiden CPM/Modularity), parámetro de resolución ($\gamma$) y método de rastreo longitudinal (ventanas temporales o linajes aluviales AMI).
    - *Si se incluye Cartografía SOM (Estática, Trayectorias CMA+Splines y/o Longitudinal Warm-Start):* formulación del espacio vectorial $\mathbb{R}^D$, topología hexagonal, dimensionamiento espectral SVD ($\sigma_1/\sigma_2$), U-Matrix, Mapas de Componentes divergentes (Verde-Amarillo-Rojo), meta-clustering de Vesanto & Alhoniemi optimizado con Silhouette ($s^*$) y, en su caso, suavizado con Medias Móviles Centradas e interpolación con splines cúbicos paramétricos (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2025; Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet, 2024; Villaseñor-García et al., 2017).

---

## 3. RESULTADOS (ESTRUCTURADOS SEGÚN LOS MÓDULOS SELECCIONADOS EN LA CURADURÍA)
*(El agente organiza las secciones o subsecciones de Resultados siguiendo el orden lógico de su narrativa científica, activando únicamente los módulos respaldados por hallazgos sólidos en `./reportes/`):*

- **Módulo A — Evolución de la Producción, Cinética de Crecimiento y Perfil Global:**
  * Análisis de las etapas históricas del campo, tasas de crecimiento ($\alpha$), tiempos de duplicación ($t_d$), puntos de inflexión y evolución de la colaboración o del impacto global.
- **Módulo B — Perfiles Multidimensionales de Desempeño y Evolución en el SOM (Países / Instituciones / Actores):**
  * Caracterización de las entidades más productivas en el SOM estático (clusters, fortalezas en zonas rojas vs. áreas deprimidas en zonas verdes, diagnóstico de pares comparables y paradojas como FWCI vs. Percentil o $DShareC$ vs. $CShareD$).
  * Análisis de la evolución temporal mediante el **SOM de Trayectorias** (órbitas de las $\le 5$ entidades líderes o trayectoria global) y/o el **SOM Longitudinal Warm-Start** (deriva sináptica $\Delta W$, convergencia, divergencia y núcleo persistente).
- **Módulo C — Evolución Temática y Estructura de Redes (Macro, Meso y Micro / Co-ocurrencia / Geopolítica):**
  * Distribución y evolución de áreas temáticas, subcampos o Topics a lo largo del tiempo, y/o estructura de las redes de colaboración internacional (Coseno de Salton, bloques geopolíticos).
- **Módulo D — Frentes de Investigación: Cartografía Bibliométrica + Revisión Sustantiva de Literatura:**
  * Identificación de los frentes de investigación activos y su genealogía longitudinal (transiciones aluviales AMI o evolución por periodos).
  * **Análisis sustantivo de cada frente (Sello LabSOM / Polaritones):** Para cada frente principal o etapa temporal, integrar las métricas del cluster con la discusión científica de sus trabajos fundacionales y de mayor impacto presentes en el corpus, explicando los aportes teóricos, metodológicos o experimentales que definen a cada comunidad.
- **Módulo E (Opcional / Condicional) — Economía Política del Acceso Abierto, APC u ODS:**
  * Incluir cuando revele hallazgos empíricos relevantes para la pregunta de investigación (ej. transición hacia preprints/vía Verde, concentración del gasto APC en USD o contribución a los ODS de la Agenda 2030).

---

## 4. DISCUSIÓN E IMPLICACIONES
- Síntesis integradora que conecte los hallazgos macro, meso y micro del estudio con la literatura previa y las preguntas de investigación ($RQ_1 \dots RQ_k$).
- Discusión de las tensiones estructurales, dinámicas de especialización o retos metodológicos y tecnológicos del campo estudiado.
- **Limitaciones del Estudio:** Cobertura de la base de datos utilizada, alcances del recorte temporal o de los filtros léxicos/toponímicos aplicados.

---

## 5. CONCLUSIONES
- Recapitulación precisa y concisa de las contribuciones empíricas y metodológicas del trabajo, y líneas abiertas para investigaciones futuras.

---

## REFERENCIAS BIBLIOGRÁFICAS
*(Incluir todas las referencias disciplinares citadas del corpus junto con las referencias metodológicas efectivamente utilizadas en el artículo, en formato APA 7ª edición o el estilo de la revista).*

**Referencias Metodológicas Base del Grupo y Clásicas (Citar las que correspondan a las técnicas aplicadas):**
1. **Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025).** Redes neuronales autoorganizadas y mapeos de la ciencia. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 271–292). UNAM, IIBI. ISBN-e: 978-607-642-193-2.
2. **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 293–313). UNAM, IIBI.
3. **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2026).** Specialization indicators in scientometrics: Understanding the Activity Index and the F-measure through their underlying components. *Journal of Informetrics*, 20, 101880. https://doi.org/10.1016/j.joi.2026.101880
4. **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** Neural longitudinal mapping of multidimensional performance profiles of Latin American universities. *Iberoamerican Journal of Science Measurement and Communication*, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92
5. **Ruiz-Sánchez, R., Arencibia-Jorge, R., Jiménez-Andrade, J. L., Tagüeña, J., Carrillo-Calvet, H., & Rubo, Y. G. (2025).** Sixty years of research on polaritons: A scientometric review. *Engineering Reports*, 7, e70045. https://doi.org/10.1002/eng2.70045
6. **Villaseñor-García, E. A., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2017).** Multiparametric characterization of scientometric performance profiles assisted by neural networks: A study of Mexican higher education institutions. *Scientometrics*, 110(1), 77–104. https://doi.org/10.1007/s11192-016-2166-0
7. **Vesanto, J., & Alhoniemi, E. (2000).** Clustering of the Self-Organizing Map. *IEEE Transactions on Neural Networks*, 11(3), 586–600.
8. **Perianes-Rodriguez, A., Waltman, L., & van Eck, N. J. (2016).** Constructing bibliometric networks: A comparison between full and fractional counting. *Journal of Informetrics*, 10(4), 1178–1195.
9. **Traag, V. A., Waltman, L., & van Eck, N. J. (2019).** From Louvain to Leiden: guaranteeing well-connected communities. *Scientific Reports*, 9(1), 5233.
10. **Huang, C., Schiebel, E., & Porter, A. L. (2011).** A multi-stage approach to mapping emerging technologies: the case of DNA sequencing technology. *Scientometrics*, 87(2), 241–260.
11. **Hicks, D., Wouters, P., Waltman, L., de Rijcke, S., & Rafols, I. (2015).** Bibliometrics: The Leiden Manifesto for research metrics. *Nature*, 520(7548), 429–431.

---

## DECLARACIONES DE DISPONIBILIDAD DE DATOS, CÓDIGO Y MATERIAL SUPLEMENTARIO
- **Data & Code Availability Statement:** Especificar la fuente primaria de datos, fecha de corte y los artefactos reproducibles generados en el workspace (`./corpus.parquet`, `./matrices/*.parquet`, `./reportes/som_state.json`, dashboards interactivos HTML y `./reportes/exploration_log.md`).
- **Índice de Material Suplementario:** Listar en una tabla los datasets, estados neuronales, figuras interactivas HTML (`som_dashboard.html`, `som_trajectories.html`, `alluvial_lineages.html`, redes) y la bitácora de exploración con las técnicas adicionales evaluadas.
