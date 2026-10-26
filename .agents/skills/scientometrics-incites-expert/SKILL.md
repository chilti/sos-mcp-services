---
name: scientometrics-incites-expert
description: >-
  Gestor integral y analista experto en benchmarking cienciométrico institucional con Clarivate InCites. Inspecciona inventarios de unidades (Organizations, Locations, Researchers, WoS Categories, Publication Sources, Research Areas ESI / SDG / Topics, Funding Agencies, Patentometrics), extrae matrices multidimensionales por ventanas (Histórico vs Reciente 5 años) listas para SOM, extrae series anuales longitudinales (Trend) para PathSOM con suavizado ECMA y calcula matrices estratégicas de crecimiento (Strategic Growth Matrix: CAGR % vs Volumen).
---
# Scientometrics InCites Expert: Gestor de Paquetes y Benchmarking Clarivate InCites

## 1. Propósito y Activación

Esta skill se activa cuando el usuario proporciona datos, reportes tabulares o paquetes exportados desde **Clarivate InCites Benchmarking & Analytics** (archivos individuales `.csv`, `.xlsx` o archivos `.zip` estructurados) y requiere:

1. **Inspeccionar y Validar el Inventario InCites:** Identificar las unidades analíticas disponibles (`Organizations`, `Locations`, `Researchers`, `WoS Categories`, `Publication Sources`, `Research Areas ESI / SDG / Topics`, `Funding Agencies`, `Patentometrics`), las ventanas temporales cubiertas y los esquemas de indicadores presentes.
2. **Extraer Matrices Multidimensionales para el SOM:** Extraer perfiles numéricos limpios $[N \times D]$ de entidades específicas discriminando entre:
   * **Ventana Reciente (5 años, e.g. 2021–2025):** Para diagnóstico de coyuntura y desempeño actual.
   * **Histórico Completo (`Whole`, e.g. 1980–2025):** Para caracterización acumulada de la trayectoria histórica.
   * Envío directo de matrices a [`som-methodological-expert`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md) y [`neural-longitudinal-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md).
3. **Modelar Series Anuales y Trayectorias PathSOM:** Extraer series anuales (*Trend*) aplicando suavizado exponencial centrado (ECMA-3 / ECMA-5) para rastrear la órbita evolutiva de universidades o países en [`som-trajectory-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md).
4. **Calcular la Matriz de Crecimiento Estratégico (Strategic Growth Matrix):** Calcular tasas de crecimiento anual compuesto (CAGR %) frente a volumen actual para clasificar entidades en 4 cuadrantes analíticos (*Star Leaders*, *Emerging Stars*, *Established Giants*, *Low Priority*).

---

## 2. Dependencies y Cadena de Valor

Esta skill actúa como el puente de ingesta y normalización de InCites hacia el modelado neurocomputacional del ecosistema UNAM:

* **Habilidades Downstream (Consumidores de Datos):**
  * [`som-methodological-expert`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md): Recibe la matriz limpia $[N \times D]$ para calibración espectral SVD, dimensionamiento de sobremalla hexagonal y entrenamiento del SOM.
  * [`som-trajectory-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md): Recibe las series temporales anuales suavizadas con ECMA para generar el trazado de trayectorias con splines continuas (máximo 5 entidades simultáneas).
  * [`neural-longitudinal-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md): Recibe secuencias de cortes intertemporales para el encadenamiento Warm-Start.
* **Habilidades Complementarias:**
  * [`tlachia-metrics-handler`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md): Equivalente canónico para paquetes exportados desde TlachIA Metrics / OpenAlex.
* **Herramientas de Software Asociadas:**
  * [`incites_parser.py`](file:///c:/Users/jlja/Documents/Proyectos/knomap/engine/incites_parser.py): Motor de parsing de InCites en KnoMap.
  * [`services/knomap/tools/incites_tools.py`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/services/knomap/tools/incites_tools.py): Herramientas MCP expuestas al agente.

---

## 3. Anatomía de Reportes y Paquetes Clarivate InCites

Los reportes exportados de InCites presentan particularidades técnicas de formato que el agente debe manejar con rigor:

```
[Paquete InCites / Exportación Clarivate]
├── Archivos CSV Individuales                    # Cabeceras de metadatos (e.g. "InCites dataset updated...")
│   ├── Organizations.csv                        # Unicode UTF-8 o UTF-16 LE con BOM, separadores coma/tab
│   ├── Locations.csv
│   └── WoS Categories.csv
└── Paquetes Estructurados (.zip o Directorios)
    ├── 01_Matrices_Desempeño_Longitudinal/      # Variaciones interperiódicas (Δ% Docs, Δ CNCI, Δ Q1)
    │   ├── Organizations Performance Matrix.csv
    │   └── Locations Performance Matrix.csv
    ├── 02_Periodos_Consecutivos/                # Ventanas fijas quinquenales o personalizadas
    │   ├── Organizations 2016-2020.csv
    │   └── Organizations 2021-2025.csv
    ├── 03_Historico_Completo/                   # Perfil acumulado de todo el horizonte temporal
    │   ├── Organizations.csv                    # Perfil completo Whole
    │   └── WoS Categories.csv
    └── 04_Tendencias_Anuales/                   # Series anuales año por año
        ├── Organizations Trend.csv              # Mediciones anuales para suavizado ECMA y PathSOM
        └── Locations Trend.csv
```

### Reglas de Lectura y Limpieza para InCites

1. **Omitir Filas de Metadatos Iniciales:** Los CSV descargados directamente desde InCites suelen comenzar con 1 a 3 líneas de metadatos del sistema (ej. `"InCites dataset updated Feb 28, 2026. Includes Web of Science™ content..."`). Si no se omiten, el parser colapsa toda la tabla en una sola columna. El agente debe escanear las primeras 15 líneas y detectar la fila de encabezados reales con mayor conteo de separadores.
2. **Detección de Codificación:** Soportar de forma transparente `utf-8-sig`, `utf-16-le` (típico de exportaciones de Excel de InCites) y `latin-1`.
3. **Limpieza Numérica:** Convertir porcentajes textuales (e.g. `"24.50%"`) a números reales flotantes (`24.50`) y valores vacíos o guiones (`"-"`, `"n/a"`) a `0.0`.

---

## 3. Correspondencia con la Interfaz de Usuario en KnoMap

Cuando este archivo se procesa en el módulo **InCites Explorer** de KnoMap (`InCitesExplorer.tsx` y `ExploradorDatos.tsx`), el comportamiento del agente debe emular la experiencia del usuario en la plataforma:

| Pestaña / Selector en KnoMap | Entidad Canónica (`unit_name`)           | Objeto de Benchmarking                                              |
| :---------------------------- | :------------------------------------------ | :------------------------------------------------------------------ |
| **Organizations**       | `Organizations`                           | Universidades, centros de investigación y dependencias             |
| **Locations**           | `Locations`                               | Países, regiones y territorios geopolíticos                       |
| **Researchers**         | `Researchers` / `Authors`               | Investigadores y autores de Web of Science                          |
| **WoS Categories**      | `WoS Categories`                          | 254 áreas disciplinarias canónicas de Web of Science              |
| **Publication Sources** | `Publication Sources`                     | Revistas y conferencias indexadas en Web of Science Core Collection |
| **Research Areas ESI**  | `Research Areas ESI`                      | 22 campos canónicos de Essential Science Indicators                |
| **Research Areas SDG**  | `Research Areas SDG`                      | Objetivos de Desarrollo Sostenible (ODS 1–17) de la ONU            |
| **Citation Topics**     | `Research Areas Topic` (Macro/Meso/Micro) | Taxonomía jerárquica de Citation Topics de Clarivate              |
| **Funding Agencies**    | `Funding Agencies`                        | Entidades y agencias de financiamiento de la investigación         |
| **Patentometrics**      | `Patentometrics`                          | Patentes citantes e impacto tecnológico                            |
| **Baseline Indicators** | `Data Indicators`                         | Indicadores baseline comparativos frente al promedio global         |

### Vistas Analíticas Integradas en KnoMap:

* **Sección 1: Baseline Summary Cards & Comparison Table:** Tablas comparativas frente a la media mundial (Baseline = 1.0 para CNCI/JNCI).
* **Sección 2: Strategic Growth Matrix:** Gráfico de dispersión interactivo dividiendo las entidades en 4 cuadrantes según su CAGR % y su volumen.
* **Sección 3: Multidimensional Profiles:**
  * *4D Bubble Chart:* Eje X (CNCI), Eje Y (% Top 10%), Tamaño de Burbuja (WoS Documents), Color (Cuartil dominante o región).
  * *Quartile Bar Chart:* Desglose porcentual en cuartiles Q1, Q2, Q3, Q4.
  * *Sunburst Chart:* Navegación jerárquica de Research Areas (Macro $\to$ Meso $\to$ Micro).
  * *Cluster Profile Radar:* Perfil de centroide y benchmarking institucional.
* **Sección 4: PathSOM (Send to SOM):** Selección de matriz tabular para modelado no lineal de trayectorias.

---

## 4. Protocolo MCP de Extracción y Modelado

El agente ejecuta el siguiente flujo paso a paso mediante las herramientas de `knomap-som-engine`:

```
+-------------------------------------------------------------------------------+
|                       FLUJO DE TRABAJO INCITES -> SOM & ESTRATEGIA            |
+-------------------------------------------------------------------------------+
| 1. inspect_incites_package(package_path="...")                                |
|       ↓ (Retorna unidades disponibles, periodos y esquema detectado)          |
| 2. DECISIÓN DEL USUARIO:                                                      |
|       ├─ A. Modelado de Perfiles SOM:                                         |
|       │     get_incites_unit_matrix(unit_name="Organizations", ...)           |
|       │     ↓ (Pasa data & labels a suggest_grid_size y train_som)            |
|       │     Aplicar metodología en som-methodological-expert                  |
|       │                                                                       |
|       ├─ B. Trayectorias PathSOM (Órbita de Instituciones):                   |
|       │     get_incites_temporal_evolution(entities=["UNAM","USP",...])       |
|       │     ↓ (Aplicar splines cúbicos y suavizado ECMA)                      |
|       │     Aplicar metodología en som-trajectory-mapping (máx. 5 entidades)   |
|       │                                                                       |
|       └─ C. Diagnóstico de Crecimiento Estratégico:                          |
|             compute_strategic_growth_matrix(indicator="WoS Documents", ...)   |
|             ↓ (Calcula CAGR % y clasifica en 4 cuadrantes de gestión)         |
|             Emitir recomendaciones de inversión y priorización institucional  |
+-------------------------------------------------------------------------------+
```

### Paso 1: Inspeccionar el Paquete o Reporte InCites

Invocar `knomap-som-engine -> inspect_incites_package`:

```python
# Ejemplo de llamada MCP:
inspect_incites_package(
    package_path=r"C:\Users\jlja\Documents\Reportes\InCites_Benchmarking_Iberoamerica.zip"
)
```

* **Respuesta:** Devuelve `session_dir` (directorio temporal indexado), lista de `available_units`, resumen de archivos por periodo (`Whole`, `5Years`, `Trend`, `PerformanceMatrix`) y catálogo de indicadores detectados.

### Paso 2: Extraer la Matriz de Desempeño Multidimensional

Invocar `knomap-som-engine -> get_incites_unit_matrix`:

```python
# Extracción de instituciones con batería balanceada de InCites:
get_incites_unit_matrix(
    session_dir=session_dir,
    unit_name="Organizations",
    use_recent_5years=True,     # True: 2021-2025 (desempeño actual); False: Whole (histórico)
    selected_indicators=[
        "Category Normalized Citation Impact (CNCI)",
        "Journal Normalized Citation Impact (JNCI)",
        "% Documents in Top 10%",
        "% Documents in Top 1%",
        "% Documents in Q1 Journals",
        "International Collaborations (%)",
        "Industry Collaborations (%)",
        "Average Percentile",
        "Web of Science Documents"
    ],
    filter_min_threshold=50.0,   # Umbral mínimo de masa crítica (ej. 50 documentos WoS)
    limit_top_n=50               # Top 50 instituciones líderes
)
```

* **Respuesta:** Devuelve `labels` (nombres institucionales limpios), `indicators` y `data` (matriz $[N \times D]$ de números reales limpios sin NaNs lista para normalización Z-score).

### Paso 3: Enviar al Pipeline SOM

Una vez obtenida la matriz `data` y las etiquetas `labels`:

1. **Calcular Dimensiones:** Invocar `knomap-som-engine -> suggest_grid_size(data=data)` para calcular el aspect ratio SVD ($\sigma_1/\sigma_2$) y la sobremalla ($20N\text{--}30N$ neuronas según [`som-methodological-expert`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)).
2. **Entrenar SOM:** Invocar `knomap-som-engine -> train_som(data=data, labels=labels, rows=rows, cols=cols, init="pca")`.
3. **Optimizar Clusters:** Invocar `knomap-som-engine -> evaluate_som_clusters` para calibrar el $K$ óptimo vía Silhouette Score.
4. **Interpretar Resultados:** Analizar la U-Matrix y los mapas de componentes para identificar grupos de pares comparables y fortalezas diferenciadas.

### Paso 4: Extraer Series Anuales y Trayectorias PathSOM

Para examinar la evolución histórica continua de un grupo selecto de competidores:
Invocar `knomap-som-engine -> get_incites_temporal_evolution`:

```python
get_incites_temporal_evolution(
    session_dir=session_dir,
    unit_name="Organizations",
    entities=["UNAM", "Universidade de Sao Paulo", "Tecnologico de Monterrey", "UBA"],
    indicators=["CNCI", "% Documents in Top 10%", "Web of Science Documents"],
    smoothing="ecma3"           # "ecma3" (ventana de 3 años), "ecma5" o "raw"
)
```

* **Respuesta:** Devuelve las series de tiempo anualizadas con suavizado centrado para cada indicador.
* **Integración:** Transferir a [`som-trajectory-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md) respetando la **Regla de Oro de KnoMap (máximo 5 entidades simultáneas)** para evitar la saturación visual de splines.

### Paso 5: Calcular la Matriz de Crecimiento Estratégico (Strategic Growth Matrix)

Invocar `knomap-som-engine -> compute_strategic_growth_matrix`:

```python
compute_strategic_growth_matrix(
    session_dir=session_dir,
    unit_name="Organizations",
    indicator="Web of Science Documents",
    entities=["UNAM", "USP", "UNICAMP", "UFRJ", "PUC Chile"]
)
```

* **Cálculo de la Tasa de Crecimiento Anual Compuesto (CAGR %):**
  $$
  \text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{inicial}}}\right)^{\frac{1}{t_{\text{final}} - t_{\text{inicial}}}} - 1
  $$
* **Cuadrantes Estratégicos Resultantes:**
  * **Star Leaders (Alto Crecimiento, Alto Volumen):** Líderes dinámicos que expanden su producción a tasas superiores a la media del sistema.
  * **Emerging Stars (Alto Crecimiento, Volumen Moderado):** Focos emergentes y nichos de oportunidad que deben recibir impulso institucional prioritario.
  * **Established Giants (Bajo Crecimiento, Alto Volumen):** Instituciones tradicionales consolidadas con volumen masivo pero maduración o estancamiento en tasas de crecimiento.
  * **Low Priority (Bajo Crecimiento, Bajo Volumen):** Entidades o áreas con baja tracción que requieren reestructuración o reasignación estratégica.

---

## 5. Batería Exhaustiva de Indicadores Canónicos Clarivate InCites

Al asesorar al usuario en la selección de indicadores para benchmarking institucional, se recomienda estructurar la consulta en 5 dimensiones canónicas:

```
+-------------------------------------------------------------------------------+
|                 TAXONOMÍA DE INDICADORES CLARIVATE INCITES                    |
+-------------------------------------------------------------------------------+
| 1. Capacidad y Masa Crítica:                                                  |
|    - Web of Science Documents, % Top 10%, % Top 1%, % Q1, % Q2, % Q3, % Q4    |
| 2. Impacto Normalizado y Citación:                                            |
|    - CNCI (Mundial = 1.0), JNCI, Times Cited, Citation Impact, Average Pct    |
| 3. Colaboración e Internacionalización:                                       |
|    - % International Collab, % Industry Collab, % Domestic, % Academic       |
| 4. Acceso Abierto (Clarivate Open Access Schema):                             |
|    - % All OA, % DOAJ Gold, % Other Gold, % Bronze, % Green Published/Accepted|
| 5. Financiamiento e Impacto Tecnológico:                                      |
|    - Funding Agency Documents, Patent Citations to Web of Science             |
+-------------------------------------------------------------------------------+
```

### 1. Capacidad y Masa Crítica

* `Web of Science Documents`: Volumen absoluto de artículos, revisiones y actas indexadas en WoS Core Collection.
* `% Documents in Top 10%`: Proporción de documentos en el decil superior mundial de citas en su respectivo campo y año.
* `% Documents in Top 1%`: Proporción de artículos en el percentil de élite internacional.
* `% Documents in Q1 Journals`: Porcentaje de producción publicada en revistas del primer cuartil de Journal Citation Reports (JCR). Soportar igualmente `% Documents in Q2 Journals`, `% Documents in Q3 Journals` y `% Documents in Q4 Journals`.

### 2. Impacto Normalizado por Campo y Revista

* `Category Normalized Citation Impact (CNCI)`: **Indicador insignia de InCites**. Es el cociente entre las citas recibidas y las citas esperadas para documentos del mismo tipo, año y categoría de WoS ($\text{Mundial} = 1.0$). Permite comparar de forma justa disciplinas con hábitos de citación dispares (e.g. Matemáticas vs. Biomedicina).
* `Journal Normalized Citation Impact (JNCI)`: Citas recibidas normalizadas respecto al promedio de la revista donde se publicó ($\text{Mundial} = 1.0$). Revela si los autores superan el impacto medio de los journals donde publican.
* `Times Cited`: Citas brutas acumuladas recibidas en Web of Science.
* `Citation Impact`: Promedio simple de citas por documento ($\text{Times Cited} / \text{WoS Documents}$).
* `Average Percentile`: Percentil promedio en la distribución mundial de citas ($\text{Mundial} = 50.0$). En el estándar de InCites, un valor menor indica mayor impacto (e.g. Percentil 10 es más alto que Percentil 60); en KnoMap se maneja de forma coherente con la escala de percentiles de excelencia.
* `% Documents Cited`: Proporción de la producción que ha recibido al menos una cita.
* `H-Index`: Índice h de Hirsch calculado sobre el conjunto de obras indexadas.

### 3. Colaboración e Inserción Transnacional

* `International Collaborations (%)`: Porcentaje de artículos con coautores afiliados a instituciones de al menos dos países distintos.
* `Domestic Collaborations (%)`: Colaboración interinstitucional dentro del mismo país.
* `Industry Collaborations (%)`: Proporción de documentos con coautores del sector empresarial o corporativo (vínculo ciencia-industria).
* `Academic Collaborations (%)`: Colaboración entre universidades y centros académicos.

### 4. Acceso Abierto (Taxonomía Clarivate Open Access)

* `% All Open Access Documents`: Grado de apertura global de la producción.
* `% DOAJ Gold Documents`: Artículos en revistas de Acceso Abierto registradas en DOAJ.
* `% Other Gold Documents`: Publicación en revistas híbridas o con cargo de APC fuera de DOAJ.
* `% Bronze Documents`: Artículos de libre lectura en la plataforma editorial sin licencia formal abierta.
* `% Green Published Documents` / `% Green Accepted Documents`: Autoarchivo en repositorios temáticos o institucionales.

### 5. Financiamiento e Impacto Tecnológico

* `Funding Agencies Documents`: Volumen y proporción de publicaciones que declaran explícitamente patrocinio o subsidios en las secciones de agradecimientos.
* `Patent Citations to Web of Science`: Citas recibidas desde patentes internacionales, evidenciando transferencia tecnológica.

---

## 6. Marco Interpretativo de Benchmarking y Paradojas Métricas

Al formular diagnósticos cienciométricos con InCites, el agente debe aplicar los siguientes criterios avanzados:

### A. Auditoría de la Paradoja CNCI vs. Percentil

El `CNCI` es una media aritmética sin cota superior. Un solo mega-artículo multicéntrico hipercitado (e.g. reporte de la OMS, ensayo clínico fase III o física de altas energías con CERN) con cientos de citas puede inflar artificialmente el CNCI institucional por encima de $1.5$ o $2.0$, ocultando que la gran mayoría de la facultad publica en niveles promedio. Por ello:

* **Diagnóstico de Robustez:** Siempre contrastar el CNCI con el `% Documents in Top 10%` y el `% Documents in Q1 Journals`.
* Si $\text{CNCI} > 2.0$ pero el $\% \text{Top 10\%} < 8\%$, el agente debe alertar de un **sesgo por hipercitación singular**.

### B. Ventana Reciente (5 años) vs. Ventana Histórica

* **Ventana Reciente (2021–2025):** Es la ventana recomendada para la toma de decisiones institucionales, evaluación de políticas de contratación y asignación presupuestal actual.
* **Ventana Histórica (`Whole`):** Refleja la inercia y reputación de largo plazo acumulada durante décadas, pero suele sobreestimar a instituciones tradicionales que pudieron haber desacelerado en años recientes.

---

## 7. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Lectura de CSV sin saltar metadatos iniciales de Clarivate**  
  Usar `pd.read_csv()` directo sin saltar las 1 a 3 líneas de metadatos (`"InCites dataset updated Feb 28, 2026..."`), provocando que la tabla entera colapse en una sola columna corrupta.  
  **Solución:** Escanear las primeras 15 líneas buscando la cabecera real o utilizar la función canónica `clean_and_read_file()` de `incites_parser.py`.
- ❌ **Anti-patrón 2: Promedio aritmético simple de ratios en Micro Topics**  
  Calcular la media simple de `CNCI`, `JNCI` o `% Documents in Top 10%` al agregar Micro Topics a Meso o Macro Topics.  
  **Solución:** Los conteos de producción absoluta (`Web of Science Documents`, `Times Cited`) se suman; los indicadores normalizados de impacto se calculan como promedio ponderado por documentos: $\frac{\sum (\text{CNCI}_i \cdot \text{Docs}_i)}{\sum \text{Docs}_i}$.
- ❌ **Anti-patrón 3: No prever codificaciones alternativas de InCites (UTF-16 LE)**  
  Asumir que todos los archivos vienen en UTF-8 estándar. Las descargas directas de InCites formateadas para Excel frecuentemente usan `utf-16-le` con BOM o `latin-1`.  
  **Solución:** Implementar fallback dinámico: `utf-8-sig` $\rightarrow$ `utf-16-le` $\rightarrow$ `latin-1`.
- ❌ **Anti-patrón 4: Saturación de la conversación con arrays masivos (Violación de File-Output First)**  
  Volcar matrices numéricas completas de 50 instituciones o series anuales de 20 años en la respuesta textual del LLM.  
  **Solución:** Persistir la matriz limpia en `session_dir/matrix_incites.json` o en el directorio de scratch/artefactos, y retornar únicamente dimensiones, estadísticas descriptivas y la ruta del archivo.
- ❌ **Anti-patrón 5: Asumir excelencia generalizada a partir de un CNCI elevado**  
  Diagnosticar a una institución como líder mundial únicamente porque su CNCI excede 2.0 sin contrastar con el percentil promedio o el % Top 10%.  
  **Solución:** Auditar siempre la presencia de mega-colaboraciones atípicas (*Black Swans*) antes de certificar liderazgo institucional.

---

## 8. Referencias Técnicas

- [SOM Methodological Expert](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)
- [SOM Trajectory Mapping](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md)
- [Neural Longitudinal Mapping](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md)
- [TlachIA Metrics Handler](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md)
- [KnoMap Engine InCites Parser](file:///c:/Users/jlja/Documents/Proyectos/knomap/engine/incites_parser.py)
- [KnoMap Frontend InCites Explorer](file:///c:/Users/jlja/Documents/Proyectos/knomap/frontend/src/components/InCitesExplorer.tsx)
- [InCites Tools en sos-mcp-services](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/services/knomap/tools/incites_tools.py)
