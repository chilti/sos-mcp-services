# Metodología Neurocomputacional SOM y Manejo de Paquetes TlachIA Metrics

**Fecha de Actualización:** Octubre 2026  
**Ecosistema:** KnoMap · TlachIA Metrics · sos-mcp-services · TlachIA-Hands  
**Fundamentación Científica:**  
1. Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025). *Redes neuronales autoorganizadas y mapeos de la ciencia*. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 271–292). UNAM, IIBI.
2. Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025). *Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA*. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 293–313). UNAM, IIBI.
3. Jiménez-Andrade, J. L. (2023). *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). UNAM.

---

## 1. Resumen Ejecutivo

Este documento formaliza las mejoras arquitectónicas, metodológicas y operativas implementadas en el ecosistema analítico de **sos-mcp-services** y **KnoMap Engine**. El objetivo central es dotar a los agentes de IA de un conjunto articulado de herramientas y habilidades para:

1. **Modelar perfiles cienciométricos multidimensionales** mediante redes neuronales autoorganizadas de Kohonen (SOM), superando la falacia de «pesar y sumar» de los rankings unidimensionales.
2. **Analizar la dimensión temporal** en dos modalidades complementarias:
   - *Mapeo Neurolongitudinal* (Warm-Start Chaining para comparar múltiples entidades a lo largo de subperiodos/décadas).
   - *Mapeo de Trayectorias* (órbitas continuas en el espacio de estados mediante medias móviles centradas y splines cúbicos paramétricos).
3. **Ingestar y procesar paquetes exportados de TlachIA Metrics (.zip y directorios)** de forma transparente, extrayendo matrices numéricas limpias para el SOM y recuperando los metadatos de documentos para análisis de redes bibliométricas complejas.

---

## 2. Arquitectura de Skills y Servicios

El pipeline se organiza en tres capas coordinadas:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CAPA 1: INGESTA Y GESTIÓN DE DATOS                              │
│                                                                                        │
│   • tlachia-metrics-handler: Gestor de paquetes ZIP y directorios de TlachIA Metrics.  │
│     - Herramientas MCP: inspect_tlachia_package, get_tlachia_unit_matrix,              │
│                         get_tlachia_temporal_evolution, get_tlachia_works_metadata.    │
│   • tlachia-metrics-engine: Cálculo autónomo de 30+ indicadores sobre corpus crudo.    │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     ▼                                           ▼
┌────────────────────────────────────────┐  ┌────────────────────────────────────────────┐
│   CAPA 2: MODELADO NEURAL SOM          │  │    CAPA 3: REDES BIBLIOMÉTRICAS            │
│                                        │  │                                            │
│ • som-methodological-expert (Base)     │  │ • bibliometric-network-analyst:            │
│   - Malla hexagonal, SVD, sobremalla   │  │   - Coautoría institucional/país           │
│     20N-30N, Tríada Visual LabSOM      │  │   - Acoplamiento bibliográfico             │
│   - Meta-clustering Vesanto+Silhouette │  │   - Co-ocurrencia de keywords/conceptos    │
│                                        │  │   (Alimentado por works_file de TlachIA)   │
│ • neural-longitudinal-mapping          │  └────────────────────────────────────────────┘
│   - Warm-Start Chaining (1/10 épocas)  │
│   - Dinámica Macro / Meso / Micro      │
│   - Tensión de deriva sináptica (ΔW)   │
│                                        │
│ • som-trajectory-mapping               │
│   - Medias móviles centradas (no lag)  │
│   - Splines cúbicos paramétricos       │
│   - Desacoplamiento (entrenar N,       │
│     visualizar máx. 5 entidades)       │
└────────────────────────────────────────┘
```

---

## 3. Mejoras a la Metodología SOM

### A. Capa Base: `som-methodological-expert`
Se actualizó [.agents/skills/som-methodological-expert/SKILL.md](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md) pasando de un borrador preliminar de 24 líneas a una especificación de casi 200 líneas con las siguientes bases formales:

1. **Fundamentación Epistemológica:**
   - Demostración de las fallas inherentes a los rankings unidimensionales (ARWU, THE, QS) que aplican pesos arbitrarios para colapsar dimensiones ortogonales en un solo número.
   - Formalización del **principio de comparación entre pares legítimos**: las entidades se ubican en un espacio $\mathbb{R}^n$, y únicamente se comparan frente a las que habitan su mismo cluster topológico.
   - Registro del linaje histórico del grupo: ViBlioSOM (1999–2002) $\rightarrow$ LabSOM/DataSOMining (2004–2020) $\rightarrow$ Villaseñor et al. (*Scientometrics*, 2017) $\rightarrow$ Lozano-Díaz (2021) $\rightarrow$ Jiménez-Andrade et al. (2024) $\rightarrow$ Carrillo-Calvet et al. (2025).
2. **Reglas Cuantitativas de Hiperparámetros:**
   - **Aspect Ratio Espectral SVD:** Proporción de la malla $\text{cols}/\text{rows} \approx \sigma_1/\sigma_2$ derivada de la descomposición singular de los datos centrados.
   - **Regla de Sobremalla Empírica (2025):** Para análisis continuo de perfiles cienciométricos, utilizar entre **$20N$ y $30N$ neuronas** en la capa de salida. Se mantienen las opciones de Big SOM ($10N$) y Small SOM ($5\sqrt{N}$).
   - **Topología Hexagonal Mandatoria:** 6 vecinos equidistantes a distancia 1 para eliminar el sesgo diagonal de las mallas cuadradas.
   - **Régimen de Aprendizaje:** Al menos $500 \times M$ iteraciones en modo secuencial o 100–200 épocas en modo batch PyTorch/CUDA; radio $\sigma$ de $\frac{1}{2}\bar{D} \rightarrow 1.0$; tasa $\alpha$ de $1.0 \rightarrow 0.01$.
3. **La Tríada Visual LabSOM:**
   - **U-Matrix (Ultsch):** Gradiente canónico donde el **rojo** representa distancias mínimas (alta densidad / núcleos de cúmulos) y el **amarillo** representa distancias máximas (fronteras / crestas / valles vacíos).
   - **Mapas de Componentes:** Planos divergentes centrados en la media (amarillo = promedio nacional/corpus; rojo = superior a la media; verde = inferior a la media). Permite evaluar visualmente la correlación cruzada entre indicadores.
   - **Meta-Clustering de Vesanto:** Agrupamiento jerárquico aglomerativo aplicado sobre los **vectores de pesos neuronales $W$** (no sobre los datos individuales ruidosos), con selección del corte $K^*$ optimizado mediante el coeficiente **Silhouette**.

---

### B. Evolución Multi-Entidad: `neural-longitudinal-mapping`
Se enriqueció [.agents/skills/neural-longitudinal-mapping/SKILL.md](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md) incorporando los avances del capítulo de Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet (2025):

1. **Protocolo Riguroso de Refinamiento Warm-Start:**
   - Para el periodo base ($T_1$): Entrenamiento global completo (PCA + ordenamiento global + refinamiento).
   - Para los periodos siguientes ($T_t$, $t \ge 2$):
     1. Condición inicial: $W_t^{(0)} = W_{t-1}^*$ (pesos del periodo previo).
     2. Se desactiva la fase de ordenamiento global.
     3. Radio inicial reducido ($\sigma \approx \frac{1}{8}\bar{D} \rightarrow 1.0$) y tasa de aprendizaje reducida ($\alpha \approx 0.1 \rightarrow 0.01$).
     4. Duración: Únicamente **la décima parte (1/10)** de las iteraciones base ($T_{\text{refine}} = \frac{1}{10}T_{\text{base}}$).
   - Garantía: Se elimina la invarianza rotacional y la deriva estocástica, manteniendo todos los mapas anclados rígidamente en el mismo marco de coordenadas.
2. **Marco Analítico de 3 Niveles:**
   - **Nivel Macro:** Tasas de crecimiento intertemporal ($\Delta\%$ de la media de cada indicador) y deriva de gradientes cromáticos.
   - **Nivel Meso (Dinámica de Clusters):** Diagnóstico de *Escisión (Splitting)* = diferenciación de perfiles vs. *Fusión (Merging)* = homogeneización o estandarización.
   - **Nivel Micro:** Desplazamiento euclidiano $(\Delta x, \Delta y)$ en la retícula y detección de perfiles singulares ($|C_k| = 1$).
   - **Tensión de Deriva Sináptica ($\Delta W_j$):** $\|W_j^{(t)} - W_j^{(t-1)}\|_2$ para identificar qué regiones semánticas experimentan mayor dinamismo estructural.
3. **Diagnóstico de Paradojas Métricas:**
   - Explicación de la divergencia entre **indicadores no acotados** (CNCI/FWCI) e **indicadores acotados** (*Average Percentile* $\le 100$). Unos pocos artículos hipercitados elevan la media aritmética, pero el percentil promedio audita la distribución de la masa crítica general.
4. **Hito de Maduración Comunitaria:**
   - Detección de la fase en la cual el **% Documents in Top 10%** cruza y sostiene el umbral mundial del 10%, evidenciando que el rendimiento ha dejado de ser un nicho elitista aislado (% Top 1%) para convertirse en una capacidad colectiva consolidada.

---

### C. Órbitas Continuas: `som-trajectory-mapping` (Nueva Skill)
Se creó [.agents/skills/som-trajectory-mapping/SKILL.md](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md) para modelar la trayectoria temporal anual continua de entidades individuales o de un conjunto selecto de competidores:

1. **Preprocesamiento con Medias Móviles Centradas (*Centered Moving Averages*):**
   $$y_t = \sum_{r=-s}^{s} a_r x_{t+r}$$
   - Elimina la volatilidad estocástica anual.
   - A diferencia de las medias *backward* o *forward*, la media centrada **no introduce desfase de fase temporal (*lag*)**, preservando la sincronía real de picos y valles históricos.
   - Tratamiento de bordes: promedio progresivo con los datos disponibles en los extremos.
2. **Interpolación por Splines Cúbicos Paramétricos:**
   - Dado que las trayectorias cienciométricas no son funciones unívocas $y = f(x)$ (pueden retroceder, girar o formar lazos), se parametrizan desacopladas respecto al tiempo $t$:
     $$u_i(t) = a_{ui} + b_{ui}t + c_{ui}t^2 + d_{ui}t^3, \quad v_i(t) = a_{vi} + b_{vi}t + c_{vi}t^2 + d_{vi}t^3$$
   - Se formulan y resuelven dos sistemas lineales de $4(N-1)$ ecuaciones garantizando continuidad suave en posición, velocidad ($C^1$) y curvatura ($C^2$).
3. **Extensión Multientidad de KnoMap (Principio de Desacoplamiento):**
   - **Durante el Entrenamiento:** Se pueden incluir decenas o cientos de entidades en la matriz de datos para construir un mapa denso y representativo de todo el espacio de estados.
   - **Durante la Visualización:** Se aplica la regla metodológica de **graficar un máximo de 5 entidades simultáneamente**, evitando el abarrotamiento («espagueti visual») y preservando la capacidad analítica.
   - **Benchmarking:** Permite comparar trayectorias paralelas/convergentes vs. divergentes y detectar años exactos de rebasamiento.

---

## 4. Manejo de Paquetes TlachIA Metrics

### A. Estructura del Paquete Exportado (.zip)
TlachIA Metrics (`openalex_indicators_engine`) genera paquetes con la siguiente estructura canónica:
- `manifest.json`: Metadatos del corpus, filtros aplicados y fecha.
- `LEEME_ESTRUCTURA.txt`: Documentación de los campos generados.
- `01_Matrices_Desempeño_Longitudinal`: Matrices de desempeño con variaciones $\Delta\%$ interperiódicas (`Locations Performance Matrix.csv`, `Organizations Performance Matrix.csv`).
- `02_Periodos_Consecutivos`: Tablas desagregadas por lustros (`Locations 2016-2020.csv`, `Locations 2021-2026.csv`).
- `03_Historico_Completo`: Tablas históricas acumuladas (`Locations.csv`, `Organizations.csv`, `Publication Sources.csv`, `Research Areas Topic.csv`).
- `04_Tendencias_Anuales`: Series de tiempo anuales (`Locations Trend.csv`).
- `05_Tablas_Parquet_y_Datos`: Tablas binarias optimizadas y el archivo canónico de documentos completos (`*_openalex_works.csv`).

---

### B. Herramientas MCP Implementadas (`services/knomap/tools/tlachia_tools.py`)
Se desarrollaron e integraron al servidor `knomap-som-engine` en [services/knomap/mcp_server.py](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/services/knomap/mcp_server.py):

| Herramienta MCP | Entradas | Salida / Capacidad |
| :--- | :--- | :--- |
| `inspect_tlachia_package` | `package_path` (ruta a .zip o directorio) | Descomprime, indexa en sesión temporal, lista las unidades disponibles (`Locations`, `Organizations`, etc.), detecta el archivo de obras y resume los indicadores. |
| `get_tlachia_unit_matrix` | `session_dir_or_zip`, `unit_name`, `period_mode`, `selected_indicators`, `limit_top_n`, `min_documents` | Extrae la matriz numérica $[N \times D]$ limpia sin NaNs y las etiquetas de entidades, lista para ingresar a `suggest_grid_size` y `train_som`. |
| `get_tlachia_temporal_evolution` | `session_dir_or_zip`, `unit_name`, `entities`, `indicators`, `smoothing` | Extrae series anuales suavizadas (ECMA-3, ECMA-5) listas para graficar trayectorias de hasta 5 entidades. |
| `get_tlachia_works_metadata` | `session_dir_or_zip` | Localiza `works_file_path` (`*_openalex_works.csv`), valida el conteo de documentos y audita campos para redes (autores, afiliaciones, referencias, keywords). |

---

### C. Skill Agéntica: `tlachia-metrics-handler`
Ubicada en [.agents/skills/tlachia-metrics-handler/SKILL.md](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md), orienta al agente para ejecutar los siguientes flujos:

1. **Flujo Hacia el SOM (Perfil de Desempeño de Países):**
   ```python
   # 1. Inspeccionar paquete
   inv = inspect_tlachia_package(package_path=".../Artificial_Intelligence_in_Education.zip")
   
   # 2. Extraer matriz de Locations con indicadores canónicos
   matrix_res = get_tlachia_unit_matrix(
       session_dir_or_zip=inv["session_dir"],
       unit_name="Locations",
       selected_indicators=[
           "Field-Weighted Citation Impact (FWCI)",
           "Citation Impact",
           "% Documents in Top 10%",
           "% Documents in Top 1%",
           "Average Percentile",
           "% All Open Access Documents",
           "% Free to Read / Diamond Documents",
           "% International Collaborations",
           "Share"
       ],
       limit_top_n=50
   )
   
   # 3. Modelado en SOM
   grid = suggest_grid_size(data=matrix_res["data"])
   som = train_som(data=matrix_res["data"], labels=matrix_res["labels"], rows=grid["big_som_recommendation"]["rows"], cols=grid["big_som_recommendation"]["cols"])
   k_opt = evaluate_som_clusters(weights=som["weights"])
   ```

2. **Flujo Hacia Redes Bibliométricas:**
   ```python
   # Recuperar el archivo canónico de obras para coautoría o acoplamiento
   works_meta = get_tlachia_works_metadata(session_dir_or_zip=inv["session_dir"])
   # works_meta["works_file_path"] -> Transferir a bibliometric-network-analyst
   ```

---

## 5. Validación Experimental con Datos Reales

Las nuevas herramientas y flujos fueron probados en vivo con el dataset:  
`C:\Users\jlja\Downloads\Artificial_Intelligence_in_Education.zip`

**Resultados de la Ejecución:**
* **Inspección de Paquete:** Estado exitoso. Unidades indexadas: `Corpus`, `Locations`, `Organizations`, `Publication Sources`, `Research Areas Topic`.
* **Extracción de `Locations`:** 152 países procesados con 33 indicadores cienciométricos calculados.
* **Matriz Extraída:** Vector de 50 países líderes por volumen $[50 \times 10]$ con métricas normalizadas (FWCI, Top 1%, Top 10%, Percentil, Diamond OA, Colaboración internacional y Share), lista para su entrenamiento neuronal.
* **Metadatos de Documentos:** Archivo localizado: `Artificial_Intelligence_in_Education_openalex_works.csv` con **38,657 documentos completos**, auditado positivamente para coautoría (`author_names`), colaboración institucional (`institution_names`), acoplamiento bibliográfico (`referenced_works`) y co-ocurrencia conceptual (`keywords`, `concepts`).

---

## 6. Estado del Catálogo de Skills Relacionadas

| Skill | Estado | Ubicación | Enfoque Metodológico |
| :--- | :---: | :--- | :--- |
| `som-methodological-expert` | **Actualizada (199 líneas)** | `sos-mcp-services` | Fundamentos SOM, ratio espectral SVD, sobremalla $20N\text{--}30N$, Tríada LabSOM y clustering de Vesanto. |
| `neural-longitudinal-mapping` | **Actualizada (195 líneas)** | `sos-mcp-services` | Mapeo longitudinal Warm-Start (1/10 épocas), niveles Macro/Meso/Micro, tensión $\Delta W$ y dinámica de cohortes. |
| `som-trajectory-mapping` | **Nueva (174 líneas)** | `sos-mcp-services` | Mapeo de trayectorias en $\mathbb{R}^n$, medias centradas, splines cúbicos y desacoplamiento multientidad (máx. 5). |
| `tlachia-metrics-handler` | **Nueva (181 líneas)** | `sos-mcp-services` | Ingesta de paquetes ZIP de TlachIA, extracción de matrices SOM y localización de obras para redes bibliométricas. |
| `tlachia-metrics-engine` | **Operativa (97 líneas)** | `sos-mcp-services` | Motor autónomo de cálculo de 30+ indicadores cienciométricos sobre corpus bibliográfico tabular. |
| `bibliometric-network-analyst` | **Operativa (164 líneas)** | `sos-mcp-services` | Construcción de redes de coautoría, acoplamiento y coocurrencia (consumidor de `works_file`). |
