---
name: template-policy-brief-gobernanza
description: >-
  Elaboración de resúmenes ejecutivos de política científica y tecnológica (Policy Briefs de 2 a 4 páginas) para rectorías, ministerios de ciencia (SECIHTI), comisiones legislativas y agencias de financiamiento. Orquesta el flujo de 5 fases delegando en las Agent Skills especializadas del stack: 1) Diagnóstico sectorial y auditoría OA (openalex-mexico-aggregations, open-access-monitor), 2) Demografía del claustro SNII (snii-identity-resolver, infotlachia-scholar-intelligence), 3) Evidencia multidimensional SOM contra el reduccionismo de rankings (som-methodological-expert), 4) Trade-offs de gobernanza y prospectiva, y 5) Matriz de recomendaciones prioritarias de política pública.
---

# Plantilla Maestra: Policy Brief de Gobernanza, Políticas de Ciencia y Tecnología (C&T) y Evidencia Multidimensional SOM
### *Especializada en síntesis ejecutiva para tomadores de decisiones de alta dirección (2 a 4 páginas)*

Esta plantilla está diseñada para que un **agente único** en LibreChat / `agentic-data-stack` o entornos de automatización elabore un **POLICY BRIEF** conciso, de máximo impacto institucional y rigurosamente fundamentado en evidencia cuantitativa, dirigido a titulares de rectorías, la Secretaría de Ciencia, Humanidades, Tecnología e Innovación (SECIHTI), consejos de investigación y comisiones legislativas.

Aporta como argumento científico central el **marco neurocomputacional de Mapas Autoorganizados de Kohonen (SOM)** (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor-García et al., 2017) para evidenciar el error de diseñar políticas públicas y asignaciones presupuestales basadas en rankings unidimensionales (*pesar y sumar*), demostrando que el sistema científico se organiza en clusters con perfiles y misiones cualitativas diferenciadas.

---

## Directivas Operativas para el Agente (Protocolo de Orquestación de Agent Skills)

Esta plantilla opera como una **meta-habilidad orquestadora** de formulación de política científica. Para asegurar el máximo rigor y contundencia ejecutiva, el agente NO debe ejecutar llamadas ad-hoc de bajo nivel a ciegas, sino que **debe orquestar y delegar cada fase analítica en la Agent Skill especializada correspondiente del ecosistema**.

El protocolo canónico de 5 fases se orquesta como sigue:

1. **Fase 1: Diagnóstico Cuantitativo del Sector y Auditoría de Acceso Abierto:**
   - **Agent Skills Orquestadas:** [`openalex-mexico-aggregations`](../openalex-mexico-aggregations/SKILL.md) y [`open-access-monitor`](/home/jlja/.gemini/config/skills/open-access-monitor/SKILL.md).
   - **Propósito y Directivas:**
     * Extraer métricas agregadas de producción, citas y FWCI en el Régimen B autónomo ($\\le 20$ autores) sobre `rag.works_academic_all` bajo la regla estricta de CERO JOINs.
     * Auditar la distribución por las 6 vías canónicas de publicación y cuantificar la fuga financiera en cuotas APC comerciales en USD a partir de `apc_paid_usd` y `apc_list_usd`.
   - **Artefactos Producidos:** Tabla 1 (Indicadores Diagnósticos Clave).

2. **Fase 2: Demografía del Claustro y Padrón Oficial SNII:**
   - **Agent Skills Orquestadas:** [`snii-identity-resolver`](../snii-identity-resolver/SKILL.md) e [`infotlachia-scholar-intelligence`](../infotlachia-scholar-intelligence/SKILL.md).
   - **Propósito y Directivas:**
     * Cuantificar la distribución del personal académico por niveles (Candidato a Emérito) y áreas del conocimiento.
     * Estimar el ratio de masa crítica consolidada (Nivel 2 + 3 + Eméritos) vs. novel (Candidato + Nivel 1), identificando riesgos demográficos de envejecimiento de líneas troncales y falta de relevo generacional.
   - **Artefactos Producidos:** Indicadores de masa crítica y estructura demográfica del claustro.

3. **Fase 3: Evidencia Neurocomputacional SOM contra la Falacia de los Rankings:**
   - **Agent Skill Orquestada:** [`som-methodological-expert`](../som-methodological-expert/SKILL.md).
   - **Propósito y Directivas:**
     * Fundamentar el rechazo a los rankings escalares comerciales (*pesar y sumar*) aplicando los principios del Manifiesto de Leiden (Hicks et al., 2015, Nature) y los estándares de la directriz GLOBAL (ISSI).
     * Proyectar el espacio de estados multidimensional institucional con retícula hexagonal SVD, U-Matrix y meta-clustering de Vesanto & Alhoniemi con Silhouette ($s^*$).
     * Demostrar que el sistema se organiza en clusters funcionales con misiones legítimas distintas (Élite Global, Soberanía Social/Diamante, Formación de Recursos), evidenciando que evaluar a todas bajo un mismo baremo perjudica la diversidad y las necesidades territoriales.
   - **Artefactos Producidos:** Tabla 2 (Tipología de Clusters Institucionales Revelados por el SOM).

4. **Fase 4: Articulación de Dilemas Estratégicos y Disyuntivas de Gobernanza (Trade-Offs):**
   - **Propósito y Directivas:**
     * Formular analíticamente los trade-offs centrales: 1) Visibilidad global subordinada en Big Science vs. Liderazgo intelectual de correspondencia endógeno; 2) Drenaje financiero por cuotas APC en USD vs. Fortalecimiento de la soberanía editorial Diamante; 3) Polarización metropolitana centralizada vs. Federalización de capacidades de investigación.
     * Evaluar escenarios prospectivos a 3 y 5 años (inercial vs. proactivo).

5. **Fase 5: Matriz de Recomendaciones Accionables y Verificación Técnica:**
   - **Propósito y Directivas:**
     * Formular la Tabla 3 con recomendaciones de política pública de alto impacto clasificadas por nivel de decisión (Rectoría / SECIHTI, Consejos Técnicos, Coordinaciones) con plazos e indicadores verificables.
     * Generar la ficha técnica con RORs, fecha de corte y script de verificación rápida reproducible (`scripts/verify_brief_metrics.py`).

---

## Disponibilidad de Datos y Reglas Anti-Fabricación (Verificadas contra el Corpus y las Herramientas)

**Columnas reales de `rag.works_academic_all`** (usar solo estas; no inventar nombres): `publication_year`, `cited_by_count`, `is_oa`, `oa_status` (valores: `closed`, `green`, `diamond`, `gold`, `bronze`, `hybrid`), `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `is_doaj_journal`, `is_core_journal`, `counts_by_year`.

1. **Número de autores:** no existe columna `authors_count`; usar `length(author_names)`.
2. **APC:** no existe `apc_usd`; usar `apc_paid_usd` (pagado) y `apc_list_usd` (precio de lista), indicando cuál se reporta.
3. **Primer autor y autor de correspondencia:** NO son columnas; solo existen dentro del JSON de `raw_data`. Si no se extraen de `raw_data` (consulta costosa, acotada a una sola entidad y sin JOINs), reportar `N/D (no disponible en el corpus)` en las celdas correspondientes y consignarlo como limitación. Nunca estimarlos ni completarlos con cifras plausibles.
4. **Cuartiles Q1/Q2 y colaboración con industria:** no existen en el corpus. No incluirlos como indicador calculado; si se mencionan, marcar `N/D`. Como proxies disponibles: `is_core_journal`, `is_doaj_journal`, `is_top_10`, `is_top_1`.
5. **Dependencias dentro de una institución (ej. Instituto de Neurobiología dentro de la UNAM):** el ROR solo identifica a la institución matriz. Para aislar una dependencia filtrar por `institution_names` con coincidencia insensible a mayúsculas y diacríticos, y declarar que el filtro es aproximado y puede subcontar variantes toponímicas.
6. **Coseno de Salton:** el índice que devuelve `get_geopolitical_collaboration_matrix` es una aproximación (usa un denominador proxy). Recalcular $S_{ij} = C_{ij}/\sqrt{C_i C_j}$ a partir de los conteos de coautoría ($C_{ij}$, $C_i$, $C_j$) y reportar el valor recalculado; si no es posible, rotular el índice como *aproximado*.
7. **Detección de quiebres (CUSUM / Pettitt):** no existe herramienta para ello. Calcularlos a partir de la serie anual extraída (declarando método y estadístico), o acotar los periodos con `analyze_scientific_growth_phases`; no atribuir a una herramienta resultados que no produce. La partición modular disponible es Louvain (`detect_louvain_communities`), no Leiden.
8. **Modo contingencia (`status: "fallback"`):** `train_som`, `evaluate_som_clusters` y `recluster_som` devuelven valores sintéticos (error de cuantización fijo, clusters y BMU ficticios) cuando el motor no está disponible. Si algún resultado trae `status: "fallback"`, NO usarlo para conclusiones: informar que el modelado SOM no pudo ejecutarse y limitar el análisis a lo no-SOM.
9. **Persistencia y Dashboard del SOM:** `train_som` cuenta con el parámetro `output_state_path` (ej. `output_state_path="/tmp/som_state.json"`) e `indicator_names`. Para generar el dashboard interactivo oficial con `knomap_render_som_dashboard`, se debe indicar `output_state_path` al invocar `train_som` y pasar esa misma ruta a `knomap_render_som_dashboard(som_state_path=...)`. Si el motor no está disponible, la herramienta devuelve `status: "error"` con la causa raíz; nunca inventar métricas ni volcar matrices numéricas completas de pesos en el cuerpo del texto.
10. **Matriz de entrada del SOM:** construirla solo con indicadores realmente calculados y estandarizados (z-score); las dimensiones `N/D` se excluyen del vector, no se rellenan.

---

## Reglas Editoriales Estrictas

- **LENGUAJE MODERADO Y SOBRIO (PROHIBICIÓN ABSOLUTA DE SUPERLATIVOS):** Estilo directo, propositivo, neutro y libre de retórica mercadotécnica o superlativos (*"revolucionario"*, *"sin precedentes"*, *"extraordinario"*).
- **ZERO-SCAFFOLDING LEAKAGE:** Redacción formal institucional apta para presentación ante órganos de gobierno universitario o comisiones de estado.
- **TABLAS EN EL CHAT:** Las Tablas 1, 2 y 3 deben desplegarse íntegramente en Markdown.

---

# [Título del Policy Brief: Desafíos Estratégicos, Evidencia Multidimensional y Opciones de Política Científica para [Tema / Institución]: Recomendaciones de Gobernanza Basadas en Evidencia]

> ## SÍNTESIS EJECUTIVA PARA DECISORES
> - **El Problema Crítico:** Resumen ejecutivo de 1 párrafo sobre la tensión estructural o brecha detectada en el sistema o institución.
> - **La Evidencia Central:** 3 datos cuantitativos irrefutables derivados del análisis cienciométrico y neurocomputacional SOM.
> - **La Recomendación Principal:** Curso de acción inmediato con mayor retorno social, epistémico y presupuestal.

---

## 1. CONTEXTO Y MAGNITUD CUANTITATIVA DEL PROBLEMA

- **1.1. Antecedentes del Fenómeno:**
  * Descripción sucinta del entorno institucional o nacional en que se enmarca la problemática.
- **1.2. Tabla 1: Indicadores Diagnósticos Clave:**

| Variable Estratégica | Cifra Actual | Parámetro de Comparación | Brecha Detectada | Diagnóstico Operativo |
| :--- | :--- | :--- | :--- | :--- |
| **Producción e Impacto Normalizado** | [X.XX] FWCI Régimen B | 1.00 (Media mundial) | [Déficit / Superávit] | Desempeño autónomo de la comunidad local |
| **Autonomía Científica (% Primer Autor / Corresp.)** | [XX.X]% / [XX.X]% | [XX.X]% (Media nacional) | [Asimetría detectada] | Capacidad de formulación y conducción |
| **Costo Comercial en APC (USD)** | $[XXX,XXX] USD | Presupuesto institucional | [Fuga financiera estimada] | Drenaje hacia conglomerados editoriales |
| **Masa Crítica en Padrón SNII** | [XX.X]% senior (N2, N3, Em.) | [XX.X]% jóvenes (Cand., N1) | [Riesgo de relevo generacional] | Sostenibilidad de las líneas a mediano plazo |

---

## 2. EVIDENCIA MULTIDIMENSIONAL SOM CONTRA EL REDUCCIONISMO DE LOS RANKINGS

*La falacia del "pesar y sumar": por qué un solo indicador escalar distorsiona las políticas públicas (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025).*

- **2.1. El Error Metodológico de los Rankings Comerciales y el Manifiesto de Leiden:**
  * Los rankings internacionales (ARWU, QS, THE) combinan indicadores heterogéneos mediante ponderaciones lineales arbitrarias, forzando a todas las instituciones a competir bajo un único modelo anglosajón intensivo en recursos.
  * Este reduccionismo viola los principios fundamentales del **Manifiesto de Leiden (Hicks et al., 2015, Nature)** y los estándares de transparencia de la directriz **GLOBAL (ISSI)**:
    1. *Principio 1:* La evaluación cuantitativa debe apoyar, nunca sustituir, el juicio cualitativo experto.
    2. *Principio 3:* Proteger la excelencia en la investigación de relevancia local y regional.
    3. *Principio 8:* Evitar el reduccionismo de indicadores únicos basados en clasificaciones unidimensionales.
  * Este reduccionismo castiga severamente la investigación orientada a problemas nacionales, las publicaciones en lenguas locales y el acceso abierto comunitario.
- **2.2. Demostración Neurocomputacional con Redes SOM:**
  * El modelado en espacios de estados con redes de Kohonen demuestra que las instituciones se agrupan en clusters cualitativamente distintos: no son "mejores o peores" en una escala unidimensional, sino que cumplen funciones y misiones académicas diferenciadas.
- **2.3. Tabla 2: Tipología de Clusters Institucionales Revelados por el SOM:**

| Cluster SOM ($K^*$) | Perfil Funcional Dominante | Misión Académica Legítima | Indicadores Cardinales en el SOM | Política Pública Diferenciada Recomendada |
| :--- | :--- | :--- | :--- | :--- |
| **Cluster Élite Global** | Investigación intensiva en frontera tecnológica | Liderazgo científico internacional y atracción de fondos | Alto FWCI, Top 1%, Colaboración internacional | Financiamiento de laboratorios centrales de vanguardia |
| **Cluster Soberanía y Pertinencia Social** | Fuerte anclaje territorial, liderazgo autoral y OA Diamante | Resolución de problemas regionales y vinculación comunitaria | Elevada tasa primer autor, 100% Diamante, alineación ODS | Evaluación cualitativa de impacto social y regional |
| **Cluster Formación y Docencia Avanzada** | Masa crítica orientada a posgrado y docencia | Formación de recursos humanos y extensión | Volumen constante, publicaciones orientadas a docencia | Estímulos a la titulación y desarrollo de material pedagógico |

---

## 3. DILEMAS Y DISYUNTIVAS DE GOBERNANZA (TRADE-OFFS)

- **3.1. Dilema 1: Visibilidad Global vs. Soberanía Epistémica:**
  * Contrastar el incentivo de publicar en mega-consorcios con miles de autores frente a la necesidad de respaldar proyectos endógenos con autoría de correspondencia local.
- **3.2. Dilema 2: Cuotas Comerciales (APC) vs. Acceso Abierto Diamante:**
  * Análisis del costo de oportunidad: el desvío de presupuestos públicos hacia pagos de cuotas APC corporativas (USD) frente a la inversión en infraestructura editorial pública, regional y sostenible.
- **3.3. Dilema 3: Concentración Centralizada vs. Descentralización Territorial:**
  * Riesgos de polarizar los recursos en unos pocos centros de la capital frente al fomento de capacidades científicas en las entidades federativas.

---

## 4. EVALUACIÓN DE ESCENARIOS PROSPECTIVOS

- **4.1. Escenario Inercial (Status Quo / Inacción):**
  * Consecuencias proyectadas a 3 y 5 años: profundización de la fuga en APC, estancamiento del impacto autónomo y crisis de relevo en el SNII.
- **4.2. Escenario Proactivo (Intervención Basada en Evidencia Multidimensional):**
  * Beneficios proyectados: reorientación de fondos hacia infraestructura propia, fortalecimiento de la soberanía autoral y consolidación de clusters de desarrollo tecnológico.

---

## 5. MATRIZ DE RECOMENDACIONES PRIORITARIAS Y CURSOS DE ACCIÓN

Presentar la **Tabla 3: Matriz de Recomendaciones Accionables para Decisores**:

| Nivel de Decisión | Acción de Política Recomendada | Plazo de Implementación | Indicador de Éxito / Meta Verificable |
| :--- | :--- | :--- | :--- |
| **Alta Dirección / Rectoría / SECIHTI** | Regular el pago institucional de cuotas APC comerciales y fortalecer la vía Diamante. | Inmediato (0–6 meses) | Ahorro del [XX]% en divisas transferidas por APC en USD. |
| **Consejos Técnicos / Comités de Evaluación** | Adoptar el modelo de evaluación por pares comparables del SOM, erradicando rankings escalares. | Corto Plazo (6–12 meses) | Normativa aprobada con perfiles cualitativos diferenciados. |
| **Coordinaciones de Investigación** | Fondo concursable de apoyo exclusivo a proyectos con liderazgo de correspondencia institucional. | Mediano Plazo (1–3 años) | Incremento de [X]% en la tasa de autor de correspondencia. |

---

## FUENTES Y METADATOS AUDITABLES

- **Ficha Técnica, Trazabilidad y Agent Skills Orquestadas:**
  * Agregaciones columnares CERO JOINs vía [`openalex-mexico-aggregations`](../openalex-mexico-aggregations/SKILL.md).
  * Monitoreo de vías de acceso abierto y costos APC vía [`open-access-monitor`](/home/jlja/.gemini/config/skills/open-access-monitor/SKILL.md).
  * Resolución de identidad y censo SNII vía [`snii-identity-resolver`](../snii-identity-resolver/SKILL.md) e [`infotlachia-scholar-intelligence`](../infotlachia-scholar-intelligence/SKILL.md).
  * Modelado neurocomputacional de perfiles SOM vía [`som-methodological-expert`](../som-methodological-expert/SKILL.md).
  * Base de datos: OpenAlex México en ClickHouse (`rag.works_academic_all`, fecha de corte: [Día Mes Año]).
  * Identificadores ROR consultados: [Lista canónica].
  * Verificación independiente: Las cifras de la Tabla 1 y los clusters de la Tabla 2 son auditables mediante el script reproducible `scripts/verify_brief_metrics.py` o re-ejecutando la skill `template-policy-brief-gobernanza` con los parámetros indicados.
- **Metodología neurocomputacional y gobernanza métrica:**
  * Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025). Redes neuronales autoorganizadas y mapeos de la ciencia. UNAM, IIBI.
  * Hicks, D., Wouters, P., Waltman, L., de Rijcke, S., & Rafols, I. (2015). Bibliometrics: The Leiden Manifesto for research metrics. *Nature*, 520(7548), 429–431.
  * International Society for Scientometrics and Informetrics (ISSI) / ScholCommLab (2023–2024). *GLOBAL: Guidance List for repOrting Bibliometric AnaLyses*. ISSI Guidelines Initiative.
