---
name: template-radar-frentes-investigacion
description: >-
  Cartografía cienciométrica de frentes de investigación emergentes, radar tecnológico y linajes aluviales AMI (Topics v5.0). Guía al agente en el protocolo canónico de 6 fases: 1) Radar de aceleración temática y Cuadrante de Frentes (Tabla 1), 2) Estructura taxonómica multinivel (Domain -> Field -> Subfield -> Topic con Diagrama Mermaid), 3) Dinámica longitudinal y cinéticas Price (Tabla 2), 4) Cartografía geopolítica bilateral de Salton (Tabla 3), 5) Cartografía Topológica Multidimensional con Redes SOM (malla hexagonal, Tríada Visual LabSOM y Tabla 4 de Clusters Temáticos), y 6) Alineación con los 17 ODS (Tabla 5) y Roadmap prospectivo.
---

# Plantilla Maestra: Reporte de Inteligencia Científica, Frentes de Investigación, Radar Tecnológico y Cartografía Topológica SOM
### *Especializada en mapeo temático multimodal (Topics v5.0, Linajes AMI, Coautoría Salton, Redes SOM y Alineación con ODS)*

Esta plantilla está diseñada para que un **agente único** en LibreChat / `agentic-data-stack` o entornos de automatización elabore un **REPORTE DE INTELIGENCIA CIENTÍFICA Y RADAR TECNOLÓGICO** de alto valor prospectivo para vicerrectorías de investigación, observatorios tecnológicos, agencias de financiamiento (SECIHTI, CONAHCYT, NSF, Horizon Europe) y comités de planeación estratégica.

Incorpora la **metodología neurocomputacional de Mapas Autoorganizados de Kohonen (SOM)** (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor-García et al., 2017) para proyectar la topología del paisaje científico y clasificar los frentes de investigación según sus perfiles multidimensionales de maduración, impacto normalizado y soberanía geopolítica.

---

## Directivas Operativas para el Agente (Protocolo MCP Real)

Antes de redactar el reporte, debes cosechar los datos cuantitativos mediante las herramientas MCP disponibles:

1. **Detección de Frentes y Linajes Aluviales AMI (`sos_topics`):**
   - Invocar `sos_topics`:
     * `detect_research_fronts_multimodal`: Extraer los frentes activos, identificación de clusters, palabras clave y métricas de aceleración.
     * `track_front_evolution_longitudinal(subfield_name)`: Reconstruir los linajes aluviales históricos, transiciones temporales (escisión, fusión, surgimiento).
2. **Jerarquía Taxonómica Multinivel y Cosecha (CERO JOINs):**
   - Navegar la jerarquía canónica: Domain $\to$ Field $\to$ Subfield $\to$ Topic.
   - Consultar `rag.works_academic_all` en `ClickHouse-OpenAlex` filtrando por campos temáticos nativos (`subfield`, `topic`) para extraer publicaciones, FWCI y distribución temporal sin usar JOINs.
3. **Cartografía Geopolítica de Cooperación Bilateral:**
   - Invocar `sos_topics` (`get_geopolitical_collaboration_matrix`) para obtener matrices de coautoría internacional normalizadas con Coseno de Salton ($S_{ij} = \frac{C_{ij}}{\sqrt{C_i C_j}}$) y ratios de soberanía epistémica (% primer autor país $i$ vs $j$).
4. **Modelado Topológico Multidimensional con Redes SOM (`sos_knomap`):**
   - Construir una matriz donde cada frente de investigación o topic sea un vector multidimensional definido por: 1) Tasa de aceleración anual $\alpha$, 2) Tiempo de duplicación $t_d$, 3) FWCI promedio, 4) Volumen de producción, 5) Coautoría internacional, 6) % Acceso Abierto Diamante, y 7) Grado de alineación a ODS.
   - Invocar `suggest_grid_size` para obtener el ratio espectral SVD ($\sigma_1 / \sigma_2$) y sobremalla hexagonal continua.
   - Invocar `train_som` y `evaluate_som_clusters` para identificar los clusters temáticos en dos etapas con Silhouette ($s^*$).
   - Invocar `knomap_render_som_dashboard` o renderizar la Tríada Visual LabSOM (U-Matrix roja/amarilla y Mapas de Componentes Verde-Amarillo-Rojo).
5. **Alineación con Objetivos de Desarrollo Sostenible (ODS 1–17):**
   - Invocar `sos_topics` (`get_sdg_impact_matrix`) o `sos_openalex` (`openalex_plot_sdg_grid`) para mapear la contribución a la Agenda 2030 de la ONU.
6. **Artefactos Visuales Nativos en LibreChat:**
   - Invocar `openalex_plot_sunburst`, `openalex_plot_topic_dynamics`, o `openalex_plot_geopolitical_sankey` y envolver el resultado con:
     ```markdown
     :::artifact{identifier="radar-frentes" type="text/html" title="Título de la Visualización"}
     [html_content retornado por la herramienta]
     :::
     ```

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

- **LENGUAJE MODERADO Y SOBRIO (PROHIBICIÓN ABSOLUTA DE SUPERLATIVOS):** Emplear terminología cienciométrica formal, objetiva y fundamentada en distribuciones empíricas. Queda estrictamente prohibido el uso de hipérboles mercadotécnicas (*"revolucionario"*, *"sin precedentes"*, *"extraordinario"*, *"asombroso"*, *"pionero"*).
- **ZERO-SCAFFOLDING LEAKAGE:** Excluir referencias internas a herramientas computacionales, prompts o tokens del chat.
- **TABLAS ESTRUCTURADAS OBLIGATORIAS:** Presentar las Tablas 1, 2, 3, 4 y 5 íntegramente en Markdown en el cuerpo del texto.

---

# [Título del Reporte: Radar Cienciométrico, Cartografía Topológica SOM e Inteligencia Prospectiva en [Dominio / Frente Temático]: Mapeo de Frentes Emergentes, Linajes de Conocimiento y Alineación Estratégica]

## 1. RESUMEN EJECUTIVO Y RADAR DE ACELERACIÓN TEMÁTICA

- **1.1. Síntesis Estratégica del Dominio:**
  * Diagnóstico global del ritmo de crecimiento, masa crítica de publicaciones, dispersión geográfica y grado de madurez del frente tecnológico o científico.
- **1.2. Tabla 1: Cuadrante de Frentes de Investigación (Research Fronts v5.0):**

| Frente de Investigación / Topic ID | Denominación Canónica del Frente | Fase del Ciclo de Vida | Tasa Crecimiento Anual ($\alpha$) | Tiempo Duplicación ($t_d$) | FWCI Promedio | Volumen Trabajos | Polo Geopolítico Líder (% Liderazgo) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Topic [XXXXX]** | [Frente A: ej. Polaritones y Condensados Cuánticos] | Emergente / Acelerado | [X.XX]% | [X.XX] años | [X.XX] | [N] | [País A] ([XX]%) |
| **Topic [YYYYY]** | [Frente B: ej. Guías de Onda Plasmónicas] | Consolidado / Maduro | [X.XX]% | [X.XX] años | [X.XX] | [N] | [País B] ([XX]%) |
| **Topic [ZZZZZ]** | [Frente C: ej. Resonadores Clásicos de Cavidad] | En declive / Residual | [X.XX]% | [X.XX] años | [X.XX] | [N] | [País C] ([XX]%) |

---

## 2. ESTRUCTURA TAXONÓMICA MULTINIVEL Y CONVERGENCIA DISCIPLINAR

- **2.1. Desglose Jerárquico (Domain $\to$ Field $\to$ Subfield $\to$ Topic):**
  * Caracterización de los campos y subcampos disciplinarios que convergen en el área analizada.
- **2.2. Diagrama de Convergencia Taxonómica (Mermaid Obligatorio):**

```mermaid
graph TD
    Domain[Dominio General: Physical Sciences] --> Field1[Campo 1: Physics and Astronomy]
    Domain --> Field2[Campo 2: Materials Science]
    Field1 --> Sub1[Subcampo A: Condensed Matter Physics]
    Field2 --> Sub2[Subcampo B: Electronic, Optical and Magnetic Materials]
    Sub1 --> Top1[Topic Principal: Polariton Condensation]
    Sub2 --> Top1
    Top1 --> Front[Frente de Investigación Emergente: Microcavidades y Metamateriales]
```

---

## 3. DINÁMICA LONGITUDINAL, LINAJES AMI Y DIFERENCIACIÓN TEMÁTICA

- **3.1. Trayectoria Histórica y Linajes Aluviales:**
  * Análisis de linajes de conocimiento: cómo frentes históricos se bifurcaron (*escisión*) o cómo disciplinas dispares convergieron (*fusión*) para dar lugar al frente actual.
- **3.2. Tabla 2: Dinámica de Crecimiento Cinético y Tiempos de Duplicación:**

| Periodo Analítico | Volumen Trabajos | Tasa de Aceleración ($\alpha$) | Tiempo Duplicación ($t_d$) | Coeficiente $R^2$ | P-valor Modelo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ventana Histórica (T-10 a T-5)** | [N] | [X.XXX] | [X.XX] años | [0.XXX] | [0.XXX] |
| **Ventana Reciente (T-5 a Actual)** | [N] | [X.XXX] | [X.XX] años | [0.XXX] | [0.XXX] |

---

## 4. CARTOGRAFÍA GEOPOLÍTICA DE COLABORACIÓN Y MATRIZ DE SALTON

- **4.1. Afinidad Bilateral y Bloques Regionales:**
  * Identificación de los ejes de colaboración más densos mediante el Coseno de Salton ($S_{ij}$).
  * Benchmarking por bloques geopolíticos (América Latina, Unión Europea, Norteamérica, Asia-Pacífico).
- **4.2. Tabla 3: Matriz de Cooperación Bilateral y Soberanía Epistémica:**

| Par de Países ($i - j$) | Publicaciones Conjuntas ($C_{ij}$) | Coseno de Salton ($S_{ij}$) | FWCI Conjunto | Ratio Primer Autor País $i$ vs País $j$ | Tasa de Autor Corresp. Institucional |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [País A – País B] | [N] | [0.XXX] | [X.XX] | [XX]% vs [XX]% | [XX.X]% |
| [País A – País C] | [N] | [0.XXX] | [X.XX] | [XX]% vs [XX]% | [XX.X]% |

---

## 5. CARTOGRAFÍA TOPOLÓGICA MULTIDIMENSIONAL CON REDES SOM (KOHONEN)

*Mapeo neurocomputacional continuo del paisaje temático para clasificar frentes de investigación sin reduccionismos unidimensionales (Carrillo-Calvet et al., 2025).*

- **5.1. Arquitectura de Malla y Calibración SVD:**
  * Dimensionamiento con relación de aspecto espectral $\sigma_1 / \sigma_2$, sobremalla continua hexagonal $20N-30N$, inicialización PCA y partición en dos etapas con coeficiente Silhouette máximo ($s^*$).
- **5.2. Interpretación de la Tríada Visual LabSOM:**
  * **U-Matrix:** Identificación de barreras topológicas (crestas amarillas) entre subdominios teóricos y valles densos (rojo) donde convergen frentes consolidados.
  * **Mapas de Componentes:** Gradientes espaciales (Verde < Media < Rojo) revelando el trade-off entre velocidad cinética ($\alpha$), citación normalizada (FWCI) y adopción en acceso abierto diamante.
- **5.3. Tabla 4: Clasificación Topológica de Clusters Temáticos en el SOM:**

| Cluster SOM ($K^*$) | Frentes de Investigación Agrupados | Perfil Multidimensional Dominante | Componentes Sobresalientes (Rojo) | Vulnerabilidades (Verde) | ODS Predominante Vinculado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cluster 1 (Frontera de Ruptura)** | [Frente A, Frente D, ...] | Alta aceleración cinética, alto FWCI y tracción global | Tasa $\alpha$, FWCI, Top 10% | Baja adopción regional Sur Global | ODS 9 (Industria / Innovación) |
| **Cluster 2 (Consolidados / Maduros)** | [Frente B, Frente E, ...] | Elevado volumen acumulado, baja duplicación y alta citación | Volumen, Citas acumuladas | Tasa de aceleración reciente | ODS 7 (Energía Asequible) |
| **Cluster 3 (Nicho Regional / Diamante)** | [Frente C, Frente F, ...] | Enfoque en problemáticas locales, liderazgo autoral y OA Diamante | OA Diamante, Coautoría nacional (N/D si no se calcula primer autor) | Presencia en revistas núcleo | ODS 3 / ODS 13 (Salud / Clima) |

---

## 6. ALINEACIÓN CON OBJETIVOS DE DESARROLLO SOSTENIBLE (ODS 1–17)

- **6.1. Mapeo de Contribución a la Agenda 2030 de la ONU:**
  * Cuantificación del porcentaje de la producción del frente vinculado a los 17 ODS.
- **6.2. Tabla 5: Distribución Temática por ODS Relevantes:**

| ODS de la ONU | Denominación del Objetivo | Publicaciones Vinculadas (N) | Porcentaje del Frente (%) | FWCI Promedio en el ODS | Coautoría Internacional (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ODS [X]** | [Nombre del ODS: ej. ODS 7 Energía Asequible] | [N] | [XX.X]% | [X.XX] | [XX.X]% |
| **ODS [Y]** | [Nombre del ODS: ej. ODS 9 Industria e Innovación] | [N] | [XX.X]% | [X.XX] | [XX.X]% |

---

## 7. IMPLICACIONES ESTRATÉGICAS Y HOJA DE RUTA PROSPECTIVA (ROADMAP)

- **7.1. Oportunidades de Liderazgo Científico:**
  * Identificación de nichos temáticos desatendidos con alto potencial de impacto epistémico y social, y baja saturación de competidores hegemónicos.
- **7.2. Hoja de Ruta Tecnológica para Órganos de Decisión:**
  * Directrices operativas a 1, 3 y 5 años para comités de evaluación y fondos sectoriales para fomentar la inserción soberana en frentes emergentes.

---

## ANEXOS Y FUENTES AUDITABLES

- Relación de metadatos de Topics, identificadores OpenAlex y parámetros del modelo de partición modular.
- Referencias metodológicas:
  * Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025). Redes neuronales autoorganizadas y mapeos de la ciencia. UNAM, IIBI.
  * Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025). Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA. UNAM, IIBI.
