---
name: som-methodological-expert
description: >-
  Experto en metodología neurocomputacional con redes autoorganizadas de Kohonen (SOM) para análisis multidimensional de perfiles de desempeño cienciométrico y bibliométrico (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor et al., 2017). Domina el dimensionamiento espectral SVD, reglas empíricas de sobremalla (20N-30N), topología hexagonal, la tríada visual LabSOM (U-Matrix roja/amarilla, mapas de componentes divergentes amarillo-rojo/verde y meta-clustering de Vesanto con Silhouette), diagnóstico de pares comparables y calibración de hiperparámetros.
---
# SOM Methodological Expert: Análisis Multidimensional de Perfiles de Desempeño

## 1. Propósito y Fundamentación Epistemológica

Esta skill formaliza y ejecuta la metodología neurocomputacional basada en **Mapas Autoorganizados de Kohonen (SOM)** para la caracterización, visualización y evaluación de **perfiles multidimensionales de desempeño cienciométrico y bibliométrico**, consolidada en la investigación:

> **Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025).** *Redes neuronales autoorganizadas y mapeos de la ciencia*. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (Colección Metría de la Información y del Conocimiento Científico, pp. 271–292). Instituto de Investigaciones Bibliotecológicas y de la Información (IIBI), Universidad Nacional Autónoma de México. ISBN-e: 978-607-642-193-2.

### Superación del Reduccionismo Unidimensional de los Rankings

* **Falacia del "Pesar y Sumar":** Los rankings universitarios y disciplinarios convencionales (ARWU, QS, THE) combinan indicadores disímiles mediante ponderaciones lineales arbitrarias para producir un solo número escalar. Este índice unidimensional oscurece las fortalezas y debilidades específicas de las instituciones y castiga la diversidad de misiones académicas.
* **Espacio Multidimensional y Comparación entre Pares:** Cada unidad de análisis (país, universidad, departamento o campo temático) se modela como un vector en un espacio abstracto $\mathbb{R}^n$, donde $n$ es el número de indicadores cienciométricos evaluados.
* **Perfiles Cualitativos:** Las entidades con métricas similares se agrupan de forma natural en el espacio euclidiano conformando *clusters*. La red SOM proyecta este espacio continuo en una retícula 2D preservando la topología, permitiendo comparar a cada entidad **únicamente frente a sus pares legítimos** (aquellos que comparten su perfil cualitativo).

### Linaje Histórico y Metodológico

1. **ViBlioSOM (1999–2002):** Colaboración fundacional entre Humberto Carrillo-Calvet (UNAM) y Gilberto Sotolongo-Aguilar (Instituto Finlay), continuada por María Victoria Guzmán-Sánchez (2009).
2. **LabSOM y DataSOMining (2004–2020):** Entorno pionero de minería de datos y visualización neurocomputacional desarrollado en la Facultad de Ciencias y el C3 de la UNAM.
3. **Caracterización Multiparamétrica del Rendimiento (2017):** Introducción formal del SOM para modelar perfiles de desempeño institucional y no solo redes de citas (Villaseñor-García, Arencibia-Jorge & Carrillo-Calvet, *Scientometrics*).
4. **Metodología Neurocomputacional para la Ciencia Mexicana (2021):** Extensión a perfiles temáticos y de investigación nacional (Lozano-Díaz, tesis doctoral UNAM).
5. **Mapeo Longitudinal Warm-Start (2024):** Encadenamiento intertemporal de mapas para evaluar dinámicas sinápticas ($\Delta W$) y trayectorias institucionales (Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet, *IJSMC*).
6. **Evidencia Científica y Mapeos de la Ciencia (2025):** Marco integral para la toma de decisiones informetricas basadas en evidencia (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge).

---

## 2. Dependencies y Cadena de Valor

Esta skill proporciona el núcleo neurocomputacional y metodológico para todo el pipeline de análisis dimensional:

* **Habilidades Upstream (Proveedores de Datos):**
  * [`tlachia-metrics-handler`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md): Extrae matrices $[N \times D]$ desde paquetes TlachIA Metrics / OpenAlex.
  * [`scientometrics-incites-expert`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/scientometrics-incites-expert/SKILL.md): Extrae matrices $[N \times D]$ desde paquetes Clarivate InCites.
* **Habilidades Downstream (Evolución y Trayectorias):**
  * [`som-trajectory-mapping`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md): Trazado de splines cúbicos intertemporales sobre el espacio latente.
  * [`neural-longitudinal-mapping`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md): Encadenamiento Warm-Start interperiódico.
* **Herramientas de Software Asociadas:**
  * [`services/knomap/tools/som_tools.py`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/services/knomap/tools/som_tools.py): `suggest_grid_size`, `train_som`, `evaluate_som_clusters`, `recluster_som`.
  * [`services/knomap/tools/viz_tools.py`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/services/knomap/tools/viz_tools.py): `knomap_render_som_dashboard`.

---

## 3. Dimensionamiento de Malla y Reglas de Hiperparámetros

Para garantizar que el SOM funcione como una representación continua de alta resolución y no simplemente como un cuantizador discreto, se deben seguir rigurosamente las siguientes reglas metodológicas:

### A. Relación de Aspecto Espectral (Aspect Ratio SVD / PCA)

1. Centrar la matriz de datos numéricos $X \in \mathbb{R}^{N \times D}$ respecto a la media de cada indicador: $\tilde{X} = X - \mu_X$.
2. Calcular la descomposición en valores singulares (SVD) de $\tilde{X}$ o los valores propios de la matriz de covarianza:
   $$
   \text{Ratio Espectral} = \frac{\sigma_1}{\sigma_2} \quad \left(\text{o } \sqrt{\frac{\lambda_1}{\lambda_2}}\right)
   $$
3. La proporción entre el número de columnas y filas de la retícula debe ajustarse a este ratio:
   $$
   \frac{\text{cols}}{\text{rows}} \approx \frac{\sigma_1}{\sigma_2}
   $$

   *(Típicamente acotado en el intervalo $[0.2, 5.0]$ para evitar mallas excesivamente alargadas o degeneradas).*

### B. Sobremalla y Número de Neuronas en la Capa de Salida

* **Regla de Dedo Empírica para Perfiles de Desempeño (Carrillo-Calvet et al., 2025):**
  Para explorar a fondo la estructura de datos cienciométricos y disponer de múltiples neuronas representativas por cada *cluster*, dimensionar la malla con:
  $$
  \text{Total Neuronas } M \approx \mathbf{20 \cdot N \text{ a } 30 \cdot N}
  $$

  *(Donde $N$ es el número de observaciones/entidades analizadas).*
* **Big SOM Estándar (KnoMap Engine):**
  $$
  M_{\text{Big}} \ge 10 \cdot N \quad (\text{mínimo } 25 \text{ neuronas})
  $$

  Recomendado para análisis topológico continuo, U-Matrix de alta definición y detección de gradientes.
* **Small SOM (Clustering Compacto):**
  $$
  M_{\text{Small}} \approx 5 \cdot \sqrt{N} \quad (\text{mínimo } 9 \text{ neuronas})
  $$

  Utilizado para síntesis rápida o cuando las entidades deben forzarse a pocos centroides representativos.

### C. Topología Reticular

* **Malla Hexagonal (Mandatoria):** Cada neurona interior posee 6 vecinos equidistantes a distancia 1. Esto elimina el sesgo direccional de las retículas cuadradas (donde los vecinos diagonales están a distancia $\sqrt{2}$).

### D. Protocolo de Épocas y Parámetros de Aprendizaje

* **Número de Iteraciones / Pasos (Regla de Kohonen):**
  * *Entrenamiento secuencial clásico:* El número de pasos de iteración debe ser **al menos 500 veces el número de neuronas de la capa de salida** ($T_{\text{pasos}} \ge 500 \cdot M$).
  * *Entrenamiento Batch acelerado en GPU (PyTorch/CUDA en KnoMap):* 100 a 200 épocas de convergencia global con actualización de lotes completos.
* **Radio de la Función de Vecindad ($\sigma$):**
  * **Radio inicial ($\sigma_0$):** Se establece en la mitad del radio o semieje de la capa de salida:
    $$
    \sigma_0 \approx \frac{1}{2} \max(\text{rows}, \text{cols}) \quad \text{o } \quad \frac{\text{rows} + \text{cols}}{4}
    $$
  * **Radio final ($\sigma_f$):** Se programa para decrecer monótonamente (exponencial o linealmente) hasta $1.0$, garantizando que en las iteraciones finales el ajuste se limite a la neurona ganadora (BMU) y sus vecinas inmediatas.
* **Factor / Tasa de Aprendizaje ($\alpha$):**
  * **Valor inicial ($\alpha_0$):** Próximo a $1.0$ (o $0.9$ en inicialización global).
  * **Valor final ($\alpha_f$):** Decrece suavemente hasta $0.01$.
* **Inicialización Sináptica:**
  * **PCA (Lineal):** Los pesos neuronales se siembran sobre el hiperplano abarcado por los dos primeros componentes principales. Acelera la convergencia y asegura una orientación topológica estable.

---

## 3. La Tríada Visual de Análisis (Estándar LabSOM)

La interpretación neurocomputacional no se basa en tablas numéricas crudas, sino en la interacción sincronizada de tres artefactos visuales generados sobre la misma malla hexagonal:

```
+-------------------------------------------------------------------------------+
|                             LA TRÍADA VISUAL LABSOM                           |
+-------------------------------------------------------------------------------+
|  1. U-MATRIX (Ultsch)       2. COMPONENT PLANES           3. META-CLUSTERING  |
|     (Topografía / Fronteras)   (Gradientes por variable)     (Partición K)    |
|                                                                               |
|      [ROJO]    = Alta dens.     [ROJO]  = > Media             [Color Cat. 1]  |
|      (Clusters / Valles)        [AMAR.] = Promedio            [Color Cat. 2]  |
|      [AMAR.]   = Fronteras      [VERDE] = < Media             [Color Cat. 3]  |
|      (Baja dens. / Crestas)                                                   |
+-------------------------------------------------------------------------------+
```

### 1. Matriz de Distancias Unificadas (U-Matrix)

* **Algoritmo:** Para cada neurona $j$, calcula la distancia euclidiana promedio respecto a sus vecinas contiguas de radio 1:
  $$
  U_j = \frac{1}{|V_j|} \sum_{k \in V_j} \| W_j - W_k \|_2
  $$
* **Convención Cromática Canónica de LabSOM:**
  * **Rojo:** Distancias interneuronales mínimas. Indica que las neuronas vecinas tienen vectores de pesos casi idénticos $\rightarrow$ **Zonas de alta densidad de datos (núcleos de clusters)**.
  * **Amarillo:** Distancias interneuronales máximas. Indica un salto brusco en los vectores de pesos $\rightarrow$ **Fronteras divisorias / ausencia de datos / crestas topológicas**.
  * **Gradiente Rojo $\rightarrow$ Naranja $\rightarrow$ Amarillo:** Topografía continua del paisaje de desempeño.

### 2. Mapas de Componentes (Component Planes)

* **Propósito:** Muestran la distribución de los valores de los pesos $W_{j, d}$ para cada dimensión $d \in \{1, \dots, D\}$ a lo largo de toda la retícula. Se generan exactamente $D$ mapas de calor alineados espacialmente.
* **Paleta Divergente de LabSOM:**
  * **Amarillo:** Punto de referencia (promedio o mediana del corpus analizado).
  * **Verde:** Valores inferiores al promedio (desempeño por debajo de la media nacional o disciplinar).
  * **Rojo:** Valores superiores al promedio (desempeño sobresaliente o alto impacto).
* **Diagnóstico de Covarianza Visual e Interpretación:**
  * **Correlación positiva:** Dos mapas con idéntica distribución espacial de colores (por ejemplo, rojo en el mismo cuadrante) indican indicadores fuertemente correlacionados.
  * **Ortogonalidad / Compensación:** Zonas donde un indicador es verde mientras otro es rojo revelan perfiles asimétricos (e.g., alto volumen pero baja citación normalizada).

### 3. Mapa de Clustering en Dos Etapas (Metodología de Vesanto & Alhoniemi, 2000)

* **Fundamento:** Para evitar el ruido inherente a los datos individuales, el agrupamiento no se aplica sobre los datos crudos, sino sobre los **vectores de referencia (pesos $W$) de las neuronas entrenadas**.
* **Procedimiento:**
  1. Aplicar Clustering Jerárquico Aglomerativo (Ward o Complete Linkage) o $k$-means sobre la matriz de pesos $W \in \mathbb{R}^{M \times D}$.
  2. Evaluar la calidad de la partición para $K \in [2, K_{\max}]$ mediante el **coeficiente Silhouette** ($s$), complementado con el índice de Davies-Bouldin (mínimo) y Calinski-Harabasz (máximo).
  3. Seleccionar la partición $K^*$ que maximiza el coeficiente Silhouette medio.
  4. Pintar cada hexágono con un color cualitativo/categórico correspondiente al cluster de su neurona (paleta HSL de paso áureo de KnoMap).
  5. Cada entidad proyectada en su Best Matching Unit (BMU) hereda la etiqueta de cluster de dicha neurona.

### 4. Mapeo Normal de Etiquetas y Principio de Legibilidad para Matrices Masivas

* **Mapeo Normal de Etiquetas:** Cada entidad evaluada (país, universidad, disciplina o autor) se proyecta en su neurona ganadora (BMU) en la malla hexagonal, mostrándose como etiqueta de texto centrada en la celda.
* **Principio de Legibilidad para Matrices Grandes:**
  Cuando la matriz de entrenamiento es muy grande ($N > 40$ observaciones o múltiples entidades compartiendo la misma BMU), **nunca se deben saturar los hexágonos con textos encimados que hagan incomprensible el mapa**.
  * **Regla de Cuota Visual:** Se debe procurar dibujar una cantidad razonable y legible de etiquetas (típicamente un máximo de 1 a 2 nombres por neurona ganadora, o seleccionar las 30 a 50 entidades más sobresalientes del corpus según volumen o impacto).
  * **Acceso Interactivo:** En KnoMap, el mapa mantiene todas las entidades en memoria para explorarlas mediante *tooltips* al pasar el cursor o a través del botón de filtro/ocultamiento de etiquetas (`🏷️ Labels`), manteniendo el mapa visualmente limpio.

---

## 4. Flujo Metodológico de Evaluación Cienciométrica

Para aplicar esta metodología sobre cualquier corpus institucional, disciplinario o geográfico:

### Paso 1: Selección y Curaduría de Indicadores

Configurar una batería multidimensional equilibrada que cubra los 4 ejes cardinales del desempeño científico:

1. **Volumen / Capacidad:** Producción total de documentos o fracción (*Share %*).
2. **Impacto Normalizado y Visibilidad:**
   * CNCI (*Category Normalized Citation Impact*) o FWCI (*Field-Weighted Citation Impact*), donde el promedio mundial es $1.0$.
   * *Average Percentile* (percentil medio en el ranking de citas).
3. **Excelencia Científica:**
   * *% Documents in Top 1%* (élite internacional).
   * *% Documents in Top 10%* (investigación de alto impacto).
   * *% Documents in Q1 Journals* (publicación en cuartil superior).
4. **Colaboración y Vinculación:**
   * *% International Collaboration*.
   * *% Industry Collaboration* (vinculación con el sector productivo).
   * *% Domestic / Institutional Collaboration*.

### Paso 2: Normalización de Variables

* Aplicar estandarización $z$-score o normalización de escala según la dispersión, garantizando que indicadores de volumen absoluto (e.g., miles de papers) no distorsionen las distancias euclidianas frente a indicadores porcentuales o ratios normalizados.

### Paso 3: Ejecución y Validación Topológica

* Ejecutar el entrenamiento con inicialización PCA y malla hexagonal bajo el ratio SVD $\sigma_1 / \sigma_2$ y sobremalla $20N-30N$.
* **Métricas de Diagnóstico:**
  * **Error de Cuantización Medio (QE):** Distancia euclidiana media entre cada dato y el vector de pesos de su BMU ($\frac{1}{N} \sum \|x_i - W_{\text{bmu}(i)}\|$). Evalúa la fidelidad de ajuste.
  * **Error Topológico (TE):** Proporción de datos cuyas dos primeras BMUs no son neuronas adyacentes en la malla. Evalúa la preservación de la topología continua ($TE < 0.05$ es deseable).

### Paso 4: Caracterización de Perfiles y Detección de Polos

Al redactar el diagnóstico cienciométrico derivado de la red:

* **Identificación de Pares:** Entidades que caen dentro del mismo cluster de la malla comparten un perfil cualitativo homogéneo.
* **Perfiles Singulares ($|C_k| = 1$):** Entidades aisladas que constituyen el único miembro de su cluster (e.g., instituciones altamente especializadas o anomalías metodológicas).
* **Polos de Excelencia:** Identificar qué cuadrantes de la retícula concentran simultáneamente tonalidades rojas en CNCI/FWCI, Top 1% y Q1, y describir la combinación de factores causales (e.g., tracción por colaboración internacional vs. tracción por industria).

---

## 5. Protocolo de Invocación MCP (`knomap-som-engine`)

Cuando el usuario requiera dimensionar, entrenar o calibrar un SOM mediante los servicios del ecosistema:

### 1. Dimensionamiento Óptimo

Invocar `knomap-som-engine -> suggest_grid_size` pasando la matriz de datos:

* Devuelve el ratio de aspecto espectral SVD ($\sigma_1 / \sigma_2$).
* Proporciona la recomendación de malla Big SOM ($10N$ o $20N$) y Small SOM ($5\sqrt{N}$) con topología hexagonal.

### 2. Entrenamiento del Modelo

Invocar `knomap-som-engine -> train_som` con:

* `data`: Matriz numérica normalizada.
* `labels`: Lista de nombres de las instituciones, áreas o autores.
* `rows` y `cols`: Obtenidos de `suggest_grid_size`.
* `method`: `"batch"` (GPU CUDA en PyTorch) o `"sequential"`.
* `init`: `"pca"` (recomendado) o `"random"`.
* `iterations`: 100–200 para batch.
* `clustering_algorithm`: `"kmeans"` o `"hierarchical"`.
* `n_clusters`: Valor inicial preliminar.

### 3. Calibración del K Óptimo

Invocar `knomap-som-engine -> evaluate_som_clusters` pasando los vectores de pesos neuronales devueltos por el entrenamiento:

* Explora $K \in [2, K_{\max}]$ computando el coeficiente Silhouette, Davies-Bouldin y Calinski-Harabasz.
* Recomienda el $K^*$ que maximiza el consenso de partición.

### 4. Reasignación de Clusters en Caliente

Invocar `knomap-som-engine -> recluster_som` pasando los pesos y el nuevo $K^*$:

* Reclasifica instantáneamente todos los hexágonos sin requerir un nuevo reentrenamiento de la red neuronal.

### 5. Generación del Dashboard Visual Oficial KnoMap

Invocar `knomap-som-engine -> knomap_render_som_dashboard` (o `render_knomap_som_dashboard` en `viz_tools.py`):

* Genera el artefacto HTML autónomo interactivo con la representación gráfica oficial de KnoMap:
  * **Malla Hexagonal *Flat-topped*** con fronteras topológicas negras entre clusters y paleta LabSOM.
  * **Insignias de Cluster** calculadas en los medoides geométricos de cada agrupación.
  * **Etiquetas de Unidades** con filtrado de densidad para matrices grandes (`max_labels_per_neuron`).
  * **Cluster Profile Radar** en la esquina superior derecha comparando el perfil multidimensional del cluster frente a las unidades analizadas.
  * **Rejilla 2x3 de Mapas de Componentes** con paleta LabSOM Verde-Amarillo-Rojo y barras de color continuas con marcas Max, Mean y Min.

---

## 6. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Uso de topología rectangular o cuadrada**  
  Configurar la retícula como cuadrícula ortogonal. En una malla cuadrada, los 4 vecinos diagonales están a distancia $\sqrt{2} \approx 1.414$ frente a los 4 axiales a distancia $1.0$, introduciendo una asimetría geométrica artificial.  
  **Solución:** Utilizar siempre topología hexagonal *flat-topped*, donde los 6 vecinos inmediatos son estrictamente equidistantes.
- ❌ **Anti-patrón 2: Sub-dimensionamiento de la malla ($M < 20N$)**  
  Usar mallas pequeñas (tipo cuantizador vectorial de 10x10 neuronas) para modelar perfiles institucionales. Esto provoca que entidades cualitativamente distintas colapsen en la misma neurona.  
  **Solución:** Aplicar la regla empírica de sobremalla: $M \approx 20N\text{--}30N$ neuronas (o Big SOM $10N$), permitiendo que el SOM actúe como un espacio continuo de alta resolución.
- ❌ **Anti-patrón 3: Entrenar con variables heterogéneas sin estandarización previa (Z-score)**  
  Introducir directamente indicadores de volumen (e.g. $10,000$ documentos) junto a indicadores normalizados de impacto (e.g. $\text{FWCI} = 1.25$ o $\text{CNCI} = 1.10$). La varianza de los documentos absorberá el 99% del cálculo de distancia euclidiana, anulando el impacto cualitativo.  
  **Solución:** Centrar y estandarizar cada indicador ($z = \frac{x - \mu}{\sigma}$) o normalizar por la media antes del cálculo de SVD y entrenamiento.
- ❌ **Anti-patrón 4: Saturación de etiquetas de texto en la visualización**  
  Querer imprimir el nombre de las 50 o 100 entidades simultáneamente sobre los hexágonos sin filtros de densidad, provocando un empastamiento ilegible.  
  **Solución:** Aplicar `max_labels_per_neuron = 1` o `2`, mostrar etiquetas solo para entidades de interés prioritario o implementar botón interactivo de aumento/disminución de tipografía en el dashboard.
- ❌ **Anti-patrón 5: Violación de File-Output First con los pesos neuronales**  
  Volcar la matriz de pesos $[M \times D]$ con miles de flotantes en la respuesta del LLM.  
  **Solución:** Persistir el modelo y el dashboard HTML en archivos locales (`scratch/som_dashboard.html`), devolviendo únicamente las métricas de cuantización ($Q_e$, $T_e$), Silhouette y el enlace al artefacto.

---

## 7. Referencias Bibliográficas Fundamentales

Si el usuario solicita fundamentos formales o justificación bibliográfica, citar las siguientes obras canónicas:

1. **Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025).** Redes neuronales autoorganizadas y mapeos de la ciencia. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 271–292). UNAM, Instituto de Investigaciones Bibliotecológicas y de la Información. ISBN-e: 978-607-642-193-2.
2. **Villaseñor-García, E. A., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2017).** Multiparametric characterization of scientometric performance profiles assisted by neural networks: A study of Mexican higher education institutions. *Scientometrics*, 110(1), 77–104. https://doi.org/10.1007/s11192-016-2166-0
3. **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** Neural longitudinal mapping of multidimensional performance profiles of Latin American universities. *Iberoamerican Journal of Science Measurement and Communication*, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92
4. **Lozano-Díaz, I. A. (2021).** *Metodología neurocomputacional para el análisis de perfiles cienciométricos de la ciencia mexicana* (Tesis doctoral). Universidad Nacional Autónoma de México.
5. **Sotolongo-Aguilar, G., Guzmán-Sánchez, M. V., & Carrillo-Calvet, H. (2002).** ViBlioSOM: Visualización de información bibliométrica mediante el mapeo autoorganizado. *Revista Española de Documentación Científica*, 25(4), 477–484. https://doi.org/10.3989/redc.2002.v25.i4.281
6. **Vesanto, J., & Alhoniemi, E. (2000).** Clustering of the Self-Organizing Map. *IEEE Transactions on Neural Networks*, 11(3), 586–600. https://doi.org/10.1109/72.846731
7. **Ultsch, A. (2003).** The U-Matrix as visualization for projections of high-dimensional data. *Proceedings of the 11th IFCS Biennial Conference*, 283–290.
8. **Kohonen, T. (2013).** Essentials of the Self-Organizing Map. *Neural Networks*, 37, 52–65. https://doi.org/10.1016/j.neunet.2012.09.018
