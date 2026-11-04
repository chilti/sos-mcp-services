---
name: template-policy-brief-gobernanza
description: >-
  Elaboración de resúmenes ejecutivos de política científica y tecnológica (Policy Briefs de 2 a 4 páginas) para rectorías, ministerios de ciencia (SECIHTI), comisiones legislativas y agencias de financiamiento. Opera bajo un protocolo en 2 etapas: I) Exploración empírica en el workspace mediante el menú de Agent Skills (agregaciones nacionales/institucionales, motor de 42+ indicadores, auditoría OA/APC, censo SNII, especialización AI/F-measure, frentes estratégicos, ODS y cartografía SOM), y II) Curaduría ejecutiva para seleccionar únicamente los 3 a 4 hallazgos empíricos más contundentes que sustentan las recomendaciones de política pública.
---

# Plantilla Maestra: Policy Brief de Gobernanza, Políticas de Ciencia y Tecnología (C&T) y Evidencia Multidimensional SOM
### *Especializada en síntesis ejecutiva basada en evidencia para tomadores de decisiones de alta dirección (2 a 4 páginas)*

Esta plantilla guía la elaboración de un **POLICY BRIEF** conciso, directo y rigurosamente fundamentado en evidencia cuantitativa, dirigido a titulares de rectorías, la Secretaría de Ciencia, Humanidades, Tecnología e Innovación (SECIHTI), consejos de investigación y comisiones legislativas.

Un Policy Brief efectivo **no es un volcado exhaustivo de todos los cálculos posibles**: requiere que el agente primero explore los datos con su menú de skills en el workspace (*Etapa I*) y luego realice una **curaduría ejecutiva estricta (*Etapa II*)** para seleccionar únicamente los hallazgos empíricos más contundentes y la configuración del **Mapa Autoorganizado de Kohonen (SOM)** (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor-García et al., 2017) que demuestre con mayor claridad por qué las políticas públicas deben diseñarse por perfiles y misiones diferenciadas en lugar de rankings unidimensionales (*pesar y sumar*).

---

## Etapa I: Menú de Agent Skills para la Exploración de Evidencia (*Fase de Laboratorio*)

El agente opera bajo el principio **Workspace-First** (`./corpus.parquet` $\to$ `./matrices/*.parquet` $\to$ `./reportes/`) y dispone del siguiente menú para construir la base de evidencia:

1. **Extracción y Diagnóstico Cuantitativo Base:**
   - [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md) y [`openalex-mexico-aggregations`](../openalex-mexico-aggregations/SKILL.md) (para política científica nacional/institucional sobre `rag.works_academic_all` con **CERO JOINs**), o [`openalex-search-engineer`](../openalex-search-engineer/SKILL.md) (`rag.works_flat`) y [`scientometrics-incites-expert`](../scientometrics-incites-expert/SKILL.md) para comparativas internacionales.
   - [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Cálculo de la matriz completa de **46 columnas (42 indicadores numéricos + 4 metadatos)** sin truncar en `./matrices/`.
2. **Menú de Dimensiones de Política Pública a Explorar:**
   - **Evidencia Multidimensional SOM contra el Reduccionismo de Rankings:** [`som-methodological-expert`](../som-methodological-expert/SKILL.md), [`som-trajectory-mapping`](../som-trajectory-mapping/SKILL.md) y [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md) para identificar tipologías de instituciones, estados o áreas temáticas según sus perfiles reales de desempeño.
   - **Soberanía Editorial y Gasto en APC (USD):** [`open-access-monitor`](../open-access-monitor/SKILL.md) y [`journal-editorial-intelligence`](../journal-editorial-intelligence/SKILL.md) para cuantificar las 6 vías de Acceso Abierto y el gasto en cuotas comerciales APC frente a la vía Diamante.
   - **Demografía Académica y Padrón SNII:** [`snii-identity-resolver`](../snii-identity-resolver/SKILL.md) e [`infotlachia-scholar-intelligence`](../infotlachia-scholar-intelligence/SKILL.md) para evaluar masa crítica, descentralización territorial y relevo generacional.
   - **Especialización Temática, Frentes Estratégicos y Agenda 2030 (ODS):** [`topics-research-fronts-intelligence`](../topics-research-fronts-intelligence/SKILL.md), [`geopolitical-collaboration-analyst`](../geopolitical-collaboration-analyst/SKILL.md), [`sdg-impact-intelligence`](../sdg-impact-intelligence/SKILL.md) e indicadores de priorización interna ($DShareC$, $AI$) vs. participación global ($CShareD$, $\text{F-measure}$) (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2026).

---

## Etapa II: Criterios de Curaduría Ejecutiva y Descarte

Para preservar la contundencia de un documento de 2 a 4 páginas para tomadores de decisiones, el agente aplica las siguientes reglas:

1. **Enfoque en el Problema de Política Pública:**
   - Seleccionar del laboratorio **únicamente los indicadores y dimensiones que sustentan directamente la disyuntiva de política pública planteada por el usuario** (ej. si el Policy Brief trata sobre financiamiento a ciencia de frontera o sobre transición a Acceso Abierto Diamante, priorizar esas métricas y descartar del documento análisis accesorios que distraigan al decisor).
2. **Selección de Dimensiones del SOM con Mayor Claridad Normativa:**
   - Elegir en `--indicator-cols` el subconjunto de indicadores de `./matrices/` que produzca la tipología de clusters más nítida (mayor coeficiente Silhouette $s^*$) y que permita asociar cada cluster con un **instrumento de política pública diferenciado** (ej. *Cluster de Frontera Internacional*, *Cluster de Soberanía y Pertinencia Regional/Diamante*, *Cluster en Consolidación*).
3. **Tablas Limpias sin Columnas `N/D`:**
   - Presentar tablas compactas únicamente con variables verificadas y con señal real en el workspace. Prohibido incluir filas o columnas vacías con `N/D`.
4. **Bitácora de Evidencia (`./reportes/exploration_log.md`):**
   - Conservar en `./reportes/exploration_log.md` el registro de los cálculos realizados en el workspace para respaldo técnico ante comisiones revisoras.

---

## Disponibilidad de Datos y Reglas Editoriales Estrictas

- **Columnas verificadas en ClickHouse (`rag.works_academic_all` y `rag.works_flat`):** `publication_year`, `cited_by_count`, `is_oa`, `oa_status`, `fwci`, `percentile`, `is_top_10`, `is_top_1`, `author_names`, `institution_rors`, `institution_names`, `country_code`, `all_country_codes`, `domain`, `field`, `subfield`, `topic`, `keywords`, `sdg_ids`, `apc_paid_usd`, `apc_list_usd`, `is_doaj_journal`, `is_core_journal`.
- **Lenguaje Ejecutivo, Sobrio y Propositivo:** Prohibición absoluta de adjetivos hiperbólicos (*"revolucionario"*, *"sin precedentes"*, *"espectacular"*). Cero menciones a prompts, tokens o comandos internos en el cuerpo del documento.

---

# Estructura Modular del Policy Brief

# [Título del Policy Brief: Evidencia Multidimensional y Opciones de Política Científica para [Tema / Subsistema / Institución]]

> ## SÍNTESIS EJECUTIVA PARA DECISORES
> - **El Problema Estratégico:** Definición concisa (1 párrafo) de la tensión estructural o reto de gobernanza abordado.
> - **La Evidencia Central:** 3 a 4 datos cuantitativos clave derivados del análisis cienciométrico y de la cartografía SOM en el workspace.
> - **La Recomendación Principal:** Acción normativa o presupuestal prioritaria con mayor retorno epistémico, institucional y social.

---

## 1. DIAGNÓSTICO CUANTITATIVO DEL PROBLEMA
- **1.1. Contexto y Magnitud Empírica:**
  * Síntesis de los hallazgos principales seleccionados tras la exploración del corpus.
- **1.2. Tabla 1: Indicadores Diagnósticos Clave:**
  * Tabla ejecutiva con las variables realmente calculadas y relevantes para el caso (ej. volumen e impacto autónomo, especialización $DShareC / CShareD$, vías de Acceso Abierto y gasto en APC en USD, colaboración o estructura del claustro SNII), su parámetro de comparación y su implicación operativa.

---

## 2. EVIDENCIA MULTIDIMENSIONAL SOM PARA EL DISEÑO DE POLÍTICAS DIFERENCIADAS
*Por qué los indicadores escalares únicos distorsionan la asignación de recursos (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2026; Manifiesto de Leiden, Hicks et al., 2015).*

- **2.1. Crítica Metodológica al Reduccionismo de Rankings ("Pesar y Sumar"):**
  * Explicación concisa de cómo las clasificaciones unidimensionales castigan la diversidad de misiones institucionales y la investigación orientada a problemas estratégicos o regionales.
- **2.2. Tabla 2: Tipología de Clusters Revelados por el SOM y Política Pública Diferenciada:**
  * Presentar los clusters reales obtenidos en `./reportes/som_diagnosis.json` (con sus entidades o frentes representativos, fortalezas en zonas rojas, vulnerabilidades en zonas verdes y el instrumento de política diferenciada recomendado para cada perfil).

---

## 3. DISYUNTIVAS ESTRATÉGICAS (TRADE-OFFS) Y ESCENARIOS PROSPECTIVOS
- Articulación de los **2 o 3 dilemas reales de gobernanza** respaldados por la evidencia del estudio (ej. *Visibilidad inducida vs. liderazgo propio y especialización*; *Drenaje presupuestal en cuotas APC comerciales vs. fortalecimiento de ecosistemas de Acceso Abierto Diamante y Verde*; *Concentración vs. articulación en redes interinstitucionales*).
- Contraste conciso entre el **Escenario Inercial (Status Quo)** y el **Escenario de Intervención Basada en Perfiles Multidimensionales**.

---

## 4. MATRIZ DE RECOMENDACIONES PRIORITARIAS Y CURSOS DE ACCIÓN
Presentar la **Tabla 3: Matriz de Recomendaciones Accionables para Órganos de Decisión**:

| Nivel de Decisión / Órgano Responsable | Acción de Política Recomendada | Horizonte de Implementación | Indicador de Éxito / Meta Verificable |
| :--- | :--- | :--- | :--- |
| **[Ej. Rectoría / SECIHTI / Dirección]** | [Acción concreta derivada de los datos] | Corto Plazo (0–12 meses) | [Métrica cuantitativa auditable] |
| **[Ej. Consejos Técnicos / Comisiones Evaluadoras]** | [Adopción de evaluación por perfiles comparables SOM / criterios de especialización] | Corto–Mediano Plazo (1–2 años) | [Métrica o lineamiento verificable] |
| **[Ej. Coordinaciones / Fondos Sectoriales]** | [Incentivo focalizado según los hallazgos del estudio] | Mediano Plazo (1–3 años) | [Meta de impacto, colaboración o ahorro] |

---

## FICHA TÉCNICA Y FUENTES AUDITABLES
- Declaración de las fuentes de datos (`rag.works_academic_all` / `rag.works_flat` / Padrón SNII), fecha de corte, parámetros de filtrado, artefactos reproducibles en `./matrices/` y `./reportes/` (incluyendo `som_dashboard.html` y `exploration_log.md`) y referencias metodológicas (Carrillo-Calvet et al., 2025; Jiménez-Andrade et al., 2024, 2025, 2026; Villaseñor-García et al., 2017; Hicks et al., 2015; Directriz GLOBAL - ISSI).
