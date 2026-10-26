---
name: som-trajectory-mapping
description: >-
  Experto en Mapeo de Trayectorias en el espacio de estados con redes autoorganizadas de Kohonen (SOM), preprocesamiento con medias móviles centradas (Centered Moving Averages), interpolación continua mediante splines cúbicos paramétricos, extensión multientidad en KnoMap (máximo 5 entidades simultáneas en visualización), detección de puntos de inflexión temporal, fases de maduración comunitaria y diagnóstico de paradojas métricas en la evolución cienciométrica (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2025).
---

# SOM Trajectory Mapping: Mapeo de Trayectorias en el Espacio de Estados

## 1. Propósito y Fundamentación Teórica

Esta skill formaliza y ejecuta la técnica de **Mapeo de Trayectorias de Perfiles Multidimensionales**, desarrollada para rastrear y visualizar la órbita evolutiva temporal continua de entidades científicas (instituciones, países o campos disciplinarios) a lo largo de series de tiempo extensas (20 a 50 años anualizados) proyectada sobre un único mapa autoorganizado de Kohonen.

La metodología está fundamentada y validada en:

> **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** *Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA*. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (Colección Metría de la Información y del Conocimiento Científico, pp. 293–313). Instituto de Investigaciones Bibliotecológicas y de la Información (IIBI), Universidad Nacional Autónoma de México. ISBN-e: 978-607-642-193-2.
>
> **Jiménez-Andrade, J. L. (2023).** *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). Universidad Nacional Autónoma de México.

### Complementariedad con el Mapeo Neurolongitudinal
* **Mapeo Neurolongitudinal ([`neural-longitudinal-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md)):** Genera una secuencia discreta de mapas espacialmente encadenados (Warm-Start). Es óptimo para comparar **sistemas masivos de muchas entidades simultáneas** a través de pocas ventanas o periodos (e.g. 3 a 5 décadas o quinquenios).
* **Mapeo de Trayectorias ([`som-trajectory-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md)):** Modela la trayectoria anual continua mediante **curvas suaves en el espacio de estados** sobre un único mapa de alta resolución, permitiendo examinar puntos de inflexión y dinámicas detalladas de una entidad o un conjunto selecto de competidores/pares.

---

## 2. Dependencies y Cadena de Valor

Esta skill orquesta la evolución temporal en el espacio latente y depende de la siguiente arquitectura:

* **Habilidades Upstream (Extracción y Soporte Matemático):**
  * [`scientometrics-incites-expert`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/scientometrics-incites-expert/SKILL.md): Extrae matrices de series anuales de InCites con suavizado ECMA (`get_incites_temporal_evolution`).
  * [`tlachia-metrics-handler`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md): Extrae series de tiempo multivariadas anuales desde paquetes TlachIA Metrics.
  * [`som-methodological-expert`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md): Provee la calibración espectral SVD, el dimensionamiento continuo ($20N\text{--}30N$) y las reglas cromáticas LabSOM.
* **Herramientas de Software Asociadas:**
  * [`services/knomap/tools/viz_tools.py`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/services/knomap/tools/viz_tools.py): `knomap_render_som_dashboard` (renderizado SVG de splines Catmull-Rom sobre malla hexagonal).
  * [`services/knomap/tools/som_tools.py`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/services/knomap/tools/som_tools.py): Entrenamiento de la red y proyección de coordenadas BMU.

---

## 3. Reutilización de `som-methodological-expert`

El Mapeo de Trayectorias **reutiliza directamente** los pilares metodológicos de [`som-methodological-expert`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md):
1. **Espacio de Estados Multidimensional:** Cada observación temporal de una entidad es un vector $x_t \in \mathbb{R}^n$ definido por los mismos $n$ indicadores normalizados (CNCI/FWCI, Top 1%, Top 10%, Q1, Average Percentile, colaboraciones).
2. **Dimensionamiento y Geometría de Malla:** Relación de aspecto espectral SVD ($\sigma_1 / \sigma_2$), topología hexagonal y sobremalla continua ($20N\text{--}30N$ o Big SOM $10N$).
3. **El Lienzo de la Tríada Visual LabSOM:** Las trayectorias se trazan superpuestas sobre:
   * **U-Matrix:** Revela qué barreras topológicas (crestas amarillas) o regiones de alta densidad (valles rojos) atravesaron las entidades en su historia.
   * **Mapas de Componentes:** Permiten auditar visualmente qué indicadores específicos (zonas rojas > promedio o verdes < promedio) fueron atrayendo o frenando la trayectoria en cada periodo.

---

## 3. Extensión Multientidad en KnoMap y Regla de Legibilidad Visual

En **KnoMap** se extendió la formulación original (pensada inicialmente para una sola entidad) para permitir el **benchmarking comparativo de múltiples trayectorias simultáneas**. Sin embargo, para evitar el colapso de la legibilidad gráfica, se establece el siguiente principio de diseño:

```
+-------------------------------------------------------------------------------+
|             PRINCIPIO DE DESACOPLAMIENTO: ENTRENAMIENTO VS VISUALIZACIÓN      |
+-------------------------------------------------------------------------------+
|  1. FASE DE ENTRENAMIENTO (Muestreo Completo):                                |
|     - Se pueden mapear e incluir MUCHAS entidades (e.g., 20 a 100 instituciones|
|       o disciplinas) para poblar adecuadamente el espacio de estados y        |
|       garantizar una malla SOM representativa de todo el sistema.             |
|                                                                               |
|  2. FASE DE VISUALIZACIÓN Y ANÁLISIS (Filtro Selectivo):                      |
|     - REGLA DE ORO: MÁXIMO 5 ENTIDADES simultáneamente en el mapa.            |
|     - Motivo: Trazar decenas de splines con bucles, lazos y retrocesos llena  |
|       el mapa de "espagueti" visual, destruyendo la capacidad interpretativa. |
|     - Se recomienda seleccionar grupos de pares directos (ej. UNAM vs IPN vs  |
|       UAM vs Cinvestav; o Matemáticas vs Computación vs Ingeniería).          |
+-------------------------------------------------------------------------------+
```

### Mapeo Normal de Etiquetas vs. Trazado de Splines para Trayectorias
* **Mapeo Normal de Etiquetas:** En [`som-methodological-expert`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md) y [`neural-longitudinal-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md), las etiquetas se proyectan de forma estática sobre sus respectivas neuronas ganadoras (BMU) en el plano.
* **Trazado de Splines (Trayectorias):** En esta skill, además de las etiquetas puntuales, **se mapean splines continuos (Catmull-Rom)** que conectan la secuencia intertemporal de neuronas ganadoras para cada entidad a lo largo de los años, complementados con waypoints circulares y flechas de dirección.
* **Regla de Legibilidad para Matrices de Entrenamiento Masivas:**
  Si la matriz con la que se entrena el SOM es muy grande (decenas o cientos de entidades incluidas para garantizar que la red represente con fidelidad todo el espacio de estados), **se debe procurar dibujar una cantidad razonable de etiquetas estáticas** (e.g. limitando el número de etiquetas por celda a 1 o 2, o seleccionando únicamente las entidades más sobresalientes del corpus) para que se puedan leer con claridad en el mapa sin empalmarse.
* **Selección de Trayectorias de Especial Interés:**
  En el caso de las trayectorias temporales, **generalmente dibujamos unas cuantas (máximo 5 entidades de especial interés)**, tales como las instituciones líderes o competidores directos de un grupo de referencia (ej. UNAM, IPN, UAM, Cinvestav). Dibujar demasiadas splines saturaría la retícula de curvas entrecruzadas, anulando el valor diagnóstico del mapa.

### Directrices de Codificación para Trayectorias Múltiples:
* **Paleta de Curvas Contrastante:** Asignar un color distintivo y sólido para cada una de las 1 a 5 entidades activas (evitando confundirse con la paleta divergente rojo-amarillo-verde de los componentes de fondo).
* **Direccionalidad:** Indicar el vector temporal con flechas o marcadores numéricos de año en los puntos nodales clave (e.g. inicio de década o puntos de inflexión).
* **Interactividad en KnoMap:** Permitir encender y apagar entidades de forma dinámica mediante un selector de capas (*Entity Toggles*).

---

## 4. Protocolo Matemático y Algorítmico Paso a Paso

```
+-------------------------------------------------------------------------------+
|                       PIPELINE DEL MAPEO DE TRAYECTORIAS                      |
+-------------------------------------------------------------------------------+
| 1. Serie Temporal Anualizada    x_t^e ∈ R^n  (t = 1980, ..., 2022; e ∈ Ents)  |
|               ↓                                                               |
| 2. Suavizado Centrado          y_t^e = ∑_{r=-s}^s a_r x_{t+r}^e (sin lag)     |
|               ↓                                                               |
| 3. Proyección SOM               p_t^e = (u_t^e, v_t^e) en retícula hexagonal   |
|               ↓                                                               |
| 4. Splines Cúbicos             u^e(t), v^e(t) paramétricos [4(N-1) ecuac.]    |
|               ↓                                                               |
| 5. Filtrado Visual             Renderizar máx. 5 entidades simultáneas        |
|               ↓                                                               |
| 6. Diagnóstico Cienciométrico  Inflexiones, Maduración, Paradojas y Converg. |
+-------------------------------------------------------------------------------+
```

### Paso 1: Preprocesamiento con Medias Móviles Centradas (Centered Moving Averages)
Las mediciones anuales crudas en cienciometría contienen fluctuaciones estocásticas y ruido a corto plazo. 

* **Cálculo de la Media Móvil Centrada:**
  $$y_t = \sum_{r=-s}^{s} a_r x_{t+r}$$
  donde $s$ es el semiancho de la ventana y $a_r$ son los coeficientes de ponderación ($\sum a_r = 1$; si $a_r$ es constante, es media simple; si decrece con $|r|$, es ponderada).
* **Justificación frente a Medias Convencionales:**
  * Las medias *backward-looking* (hacia atrás) introducen un **retraso temporal artificial** en los picos y valles.
  * Las medias *forward-looking* (hacia adelante) provocan un **adelanto artificial**.
  * La **media móvil centrada** preserva la inercia y tendencia de la serie histórica **sin desfase de fase**, manteniendo sincronizados los puntos críticos temporales.
* **Tratamiento en los Extremos (Condición de Frontera):**
  En los bordes iniciales y finales donde la ventana no está completa:
  $$y_1 = x_1, \quad y_2 = \frac{x_1 + x_2}{2}, \quad \dots \quad \text{y simétricamente en } y_N$$

### Paso 2: Proyección de la Órbita en la Retícula SOM
1. Cada vector anual suavizado $y_t^e$ de la entidad $e$ se proyecta sobre la red neuronal SOM entrenada, determinando su neurona ganadora (BMU):
   $$\text{BMU}^e(t) = \arg\min_j \| y_t^e - W_j \|_2$$
2. Se extraen las coordenadas planas $(u_t^e, v_t^e)$ asociadas a la BMU en la retícula hexagonal.

### Paso 3: Trazado Continuo con Splines Cúbicos Paramétricos
Para conectar los $N$ puntos cronológicos $(u_t^e, v_t^e)$ mediante una curva suave en el plano:
* **El Problema de las Curvas Complejas:** Las trayectorias de desempeño no son funciones matemáticas unívocas $y = f(x)$, ya que una disciplina o universidad puede mejorar, estancarse, retroceder o ciclarse en el plano.
* **Formulación Paramétrica Desacoplada en $t$:**
  Se interpola una colección de $N-1$ polinomios cúbicos para cada eje cartesiano respecto al parámetro temporal $t$:
  $$u_i(t) = a_{ui} + b_{ui}t + c_{ui}t^2 + d_{ui}t^3$$
  $$v_i(t) = a_{vi} + b_{vi}t + c_{vi}t^2 + d_{vi}t^3$$
  para $i \in \{1, 2, \dots, N-1\}$.
* **Resolución del Sistema Lineal:**
  Se construyen y resuelven dos sistemas independientes de $4(N-1)$ ecuaciones lineales asegurando:
  1. Interpolación exacta en los nodos de paso: $u_i(t_i) = u_t$, $u_i(t_{i+1}) = u_{t+1}$.
  2. Continuidad de primer orden (velocidad suave de transición): $u'_i(t_{i+1}) = u'_{i+1}(t_{i+1})$.
  3. Continuidad de segundo orden (curvatura suave): $u''_i(t_{i+1}) = u''_{i+1}(t_{i+1})$.
  4. Condiciones de frontera natural o periódica en los extremos.

---

## 5. Marco de Interpretación Cienciométrica de Trayectorias

Al analizar visualmente el recorrido de las curvas sobre los mapas de componentes y la U-Matrix, el agente debe evaluar los siguientes hitos:

### A. Detección de Puntos de Inflexión y Despegue
* Localizar en la trayectoria los años exactos donde la curva cambia de cuadrante o acelera su vector tangente.
* *Ejemplo canónico (Medicina Clínica en México):* Entre 1980 y 2002 orbitaba en cuadrantes de bajo impacto relativo; a partir de **2003** sufre una inflexión pronunciada hacia la esquina superior derecha del mapa, iniciando un crecimiento exponencial y sostenido.

### B. Análisis Comparativo de Pares (Convergencia vs. Divergencia)
Cuando se grafican 2 a 5 entidades simultáneas:
* **Trayectorias Paralelas / Convergentes:** Entidades que transitan hacia las mismas regiones de la retícula, indicando homogeneización de políticas y rendimientos similares.
* **Trayectorias Divergentes:** Entidades que partieron de una misma zona en los años 80 pero cuyas curvas se separan radicalmente hacia distintos cuadrantes (e.g. una hacia colaboración industrial y otra hacia internacionalización en Q1).

### C. Análisis de Fuerzas de Tracción por Indicadores
Al superponer las curvas sobre los mapas de componentes:
* **Tracción por Internacionalización:** Avance hacia zonas rojas de *% International Collaboration*.
* **Tracción por Vinculación Productiva:** Desplazamiento hacia regiones rojas de *% Industry Collaboration*.
* **Migración hacia Cuartil Superior:** Avance hacia el polo rojo de *% Documents in Q1 Journals*.

### D. Auditoría de Paradojas Métricas: CNCI vs. Average Percentile
Uno de los diagnósticos más críticos que debe emitir el agente al auditar trayectorias:
* **Métrica No Acotada (CNCI / FWCI):** Es una media aritmética sin límite superior. Un conjunto diminuto de publicaciones hipercitadas (e.g. ensayos clínicos multicéntricos o reportes globales) puede disparar el promedio general por encima de la media mundial ($> 1.0$), generando una ilusión de excelencia generalizada.
* **Métrica Acotada (Average Percentile $\le 100$):** Los artículos hipercitados saturan en percentil 100 y no pueden jalar más el promedio. Si el *Average Percentile* de la entidad se sitúa por debajo de 50 (e.g. 36), se concluye con rigor estadístico que **el grueso de la comunidad científica aún produce artículos en percentiles bajos de citación**, dependiendo de un nicho de élite.

### E. Identificación de la Fase de Maduración Comunitaria
* **Fase 1 (Élite Aislada):** Se observa un incremento en el % Top 1% y en el CNCI, pero el % Top 10% permanece estancado por debajo del 10%. La producción de excelencia está confinada a pocos autores.
* **Fase 2 (Maduración Comunitaria Plena):** Ocurre cuando la trayectoria cruza y sostiene el indicador **% Documents in Top 10% por encima del 10% (media mundial)**. Diagnóstico: *La comunidad académica ha alcanzado masa crítica institucional, democratizando la capacidad de publicar con alto impacto relativo*.

---

## 6. Integración con MCP y Scripts del Ecosistema

Para orquestar un estudio de trayectoria desde el entorno analítico:

1. **Extracción y Suavizado Temporal:**
   * Invocar `knomap-som-engine -> get_incites_temporal_evolution` pasando las entidades de interés (1 a 5 seleccionadas) y la lista de años.
   * Aplicar la media móvil centrada de 3 o 5 periodos sobre los indicadores numéricos.
2. **Entrenamiento o Carga de Malla:**
   * Utilizar `knomap-som-engine -> train_som` o cargar la matriz entrenada en `som-methodological-expert` (que puede contener todo el universo de entidades para que la malla sea representativa).
3. **Generación de Trayectorias y Splines:**
   * Invocar `knomap-som-engine -> knomap_render_som_dashboard` (o `render_knomap_som_dashboard` en `services/knomap/tools/viz_tools.py`), pasando la lista de trayectorias en `selected_trajectories` (máximo 5 entidades). El generador calcula automáticamente los splines cúbicos Catmull-Rom continuos, waypoints circulares y marcadores direccionales en SVG sobre la malla hexagonal nativa de KnoMap.
4. **Emisión de Reporte Diagnóstico:**
   * Desglosar las etapas históricas (pre-despegue, despegue, consolidación), los puntos de inflexión temporal, la resolución de paradojas métricas y la comparación de dinámicas entre los competidores seleccionados.

---

## 7. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Trazar más de 5 entidades simultáneamente en la visualización**  
  Proyectar trayectorias para 10, 20 o más instituciones o países al mismo tiempo. Esto crea un "efecto espagueti" donde las curvas se cruzan caóticamente, ocultando puntos de inflexión y arruinando la legibilidad.  
  **Solución:** Aunque el SOM puede entrenarse con 100 entidades para que la malla sea representativa, **en el dashboard se deben visualizar máximo 5 entidades** (grupos de pares comparables o competidores directos).
- ❌ **Anti-patrón 2: Trazar trayectorias con datos crudos sin suavizado temporal**  
  Utilizar los valores anuales puros sin filtrar. Las series temporales bibliométricas presentan ruido estocástico anual (e.g. un año con un congreso especial genera picos artificiales) que produce quiebres bruscos y trayectorias en zigzag sin significado estructural.  
  **Solución:** Aplicar siempre Centered Moving Average (CMA) de 3 o 5 periodos o suavizado exponencial ECMA-3 / ECMA-5 antes de calcular los splines.
- ❌ **Anti-patrón 3: Conectar puntos anuales con segmentos rectos rígidos**  
  Unir las neuronas ganadoras (BMUs) anuales con polilíneas ortogonales o líneas rectas. El espacio latente del SOM es una variedad continua; las líneas rectas rompen la topología del movimiento.  
  **Solución:** Utilizar siempre splines cúbicos paramétricos continuos (Catmull-Rom) con waypoints circulares y marcadores direccionales SVG.
- ❌ **Anti-patrón 4: Imprimir todas las etiquetas anuales sobre la curva**  
  Intentar rotular cada año (e.g. 1990, 1991, 1992... 2025) a lo largo de la spline, empastando la retícula hexagonal.  
  **Solución:** Rotular únicamente los puntos extremos (inicio y fin) y puntos de inflexión temporal mayores, dejando que los waypoints circulares representen los pasos intermedios.
- ❌ **Anti-patrón 5: Violación de File-Output First**  
  Imprimir en el chat las coordenadas completas de los splines y waypoints en formato JSON gigante.  
  **Solución:** Generar el dashboard autónomo en `scratch/som_trajectories_dashboard.html` y retornar un resumen ejecutivo con el enlace al artefacto.

---

## 8. Referencias Canónicas

1. **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 293–313). UNAM, Instituto de Investigaciones Bibliotecológicas y de la Información. ISBN-e: 978-607-642-193-2.
2. **Jiménez-Andrade, J. L. (2023).** *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). Universidad Nacional Autónoma de México.
3. **Chatfield, C., & Xing, H. (2019).** *The Analysis of Time Series: An Introduction with R*. CRC Press, Taylor & Francis Group. https://doi.org/10.1201/9781351259446
4. **Gorbea-Portal, S. (2016).** Una nueva perspectiva teórica de la bibliometría basada en su dimensión histórica y sus referentes temporales. *Investigación Bibliotecológica: archivonomía, bibliotecología e información*, 30(70), 11–16. https://doi.org/10.1016/j.ibbai.2016.10.001
5. **Garfield, E. (1994).** Scientography: Mapping the tracks of science. *Current Contents: Social & Behavioural Sciences*, 7(45), 5–10.
