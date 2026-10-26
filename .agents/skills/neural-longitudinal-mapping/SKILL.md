---
name: neural-longitudinal-mapping
description: >-
  Experto en Mapeo Longitudinal Neurocomputacional con redes autoorganizadas de Kohonen (SOM) y encadenamiento Warm-Start intertemporal (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2025; Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet, 2024). Modela la evolución temporal de perfiles multidimensionales de desempeño institucional y secuencias de matrices bibliométricas en 3 niveles: Macro (tendencias, tasas Delta % y componentes), Meso (dinámica de clusters: escisión vs. fusión) y Micro (desplazamientos de entidades, perfiles singulares y maduración comunitaria), cuantificando la tensión de deriva sináptica (\Delta W) y la rotación de cohortes.
---

# Neural Longitudinal Mapping (SOM Warm-Start Chaining)

## 1. Fundamentación Epistemológica y Teórica

Esta skill implementa y orquesta la metodología científica de **Mapeo Neurolongitudinal con Redes Autoorganizadas de Kohonen (SOM)**, desarrollada y consolidada en las siguientes investigaciones canónicas:

> **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** *Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA*. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (Colección Metría de la Información y del Conocimiento Científico, pp. 293–313). Instituto de Investigaciones Bibliotecológicas y de la Información (IIBI), Universidad Nacional Autónoma de México. ISBN-e: 978-607-642-193-2.
>
> **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** *Neural longitudinal mapping of multidimensional performance profiles of Latin American universities*. **Iberoamerican Journal of Science Measurement and Communication**, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92
>
> **Jiménez-Andrade, J. L. (2023).** *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). Universidad Nacional Autónoma de México.

### Contexto Histórico y Teórico de la Metría de la Información
* **La Dimensión Histórica de la Bibliometría:** Tal como formula Gorbea Portal (2016), los estudios métricos deben integrar los referentes temporales a sus tres dimensiones cardinales: *descriptiva o clásica*, *evaluativa* e *histórica*. La mayoría de las herramientas existentes solo grafican curvas univariadas o redes de coocurrencia, ignorando la co-evolución acoplada de perfiles multidimensionales.
* **La Visión de Eugene Garfield (1994):** Garfield postuló que la cartografía longitudinal (*scientography*) es la vía fundamental para rastrear las huellas temporales y las relaciones dinámicas entre frentes de investigación y transformaciones de paradigmas.
* **Superación de la Invarianza Rotacional y Deriva Estocástica:**
  El entrenamiento no supervisado clásico de un SOM independiente para cada corte temporal genera discontinuidades arbitrarias (rotaciones, inversiones especulares o traslaciones de cuadrante). El **Mapeo Neurolongitudinal** supera esta barrera garantizando que todos los mapas de la secuencia temporal permanezcan **rígidamente anclados en una misma orientación espacial**, de modo que cualquier desplazamiento observado en la U-Matrix o en la posición de una entidad corresponda a una verdadera mutación en su perfil de desempeño.

---

## 2. Dependencies y Cadena de Valor

Esta skill implementa el encadenamiento intertemporal neurocomputacional y se articula con la siguiente arquitectura:

* **Habilidades Upstream (Extracción y Soporte Metodológico):**
  * [`tlachia-metrics-handler`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md): Extrae secuencias de matrices por periodos consecutivos (`02_Periodos`) desde paquetes TlachIA Metrics.
  * [`scientometrics-incites-expert`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/scientometrics-incites-expert/SKILL.md): Extrae matrices históricas y por ventanas quinquenales desde reportes Clarivate InCites.
  * [`som-methodological-expert`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md): **Hereda y reutiliza integralmente** la base matemática y visual:
    1. **Ratio de Aspecto Espectral SVD:** Proporción $\text{cols}/\text{rows} \approx \sigma_1 / \sigma_2$ calculada sobre la matriz agregada de perfiles.
    2. **Dimensionamiento de Malla:** Topología hexagonal y sobremalla empírica ($M \approx 20N\text{--}30N$ o Big SOM $10N$) para desplegar resolución topológica continua.
    3. **Tríada Visual LabSOM:** U-Matrix roja/amarilla, Mapas de Componentes divergentes amarillo-rojo/verde y Meta-clustering de Vesanto.
* **Habilidades Complementarias y Downstream:**
  * [`som-trajectory-mapping`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md): Técnica complementaria para trayectorias continuas anuales de pocas entidades clave mediante splines.
  * [`services/knomap/tools/viz_tools.py`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/services/knomap/tools/viz_tools.py): `knomap_render_som_dashboard` para generar el artefacto HTML por cada corte temporal.
* **Regla de Legibilidad para Matrices Grandes:**
  * Si la matriz de entrenamiento de la serie temporal es grande ($N > 40$ entidades), se debe procurar **dibujar una cantidad razonable y legible de etiquetas** (priorizando el núcleo persistente o limitando a 1 o 2 etiquetas por celda).

---

## 3. Protocolo de Encadenamiento Warm-Start (Refinement Chaining)

El fundamento descansa en la **hipótesis de inercia o continuidad estructural**: el estado de la ciencia de un año o subperiodo conserva la estructura general del periodo precedente. Por tanto:

```
+-----------------------------------------------------------------------------------+
|                  PROTOCOLO DE ENCADENAMIENTO TEMPORAL WARM-START                 |
+-----------------------------------------------------------------------------------+
|  Periodo Base (T_1):                                                              |
|    - Inicialización global (PCA)                                                  |
|    - Fase 1 (Ordenamiento Global) + Fase 2 (Refinamiento Fino)                    |
|    - Épocas base (e.g. 1000 iteraciones) -> Pesos óptimos W_1*                    |
|                                                                                   |
|  Periodos Sucesivos (T_2, T_3, ..., T_k):                                         |
|    - 1. Condición inicial: W_t^(0) = W_{t-1}* (Pesos del periodo anterior)        |
|    - 2. Desactivar Fase 1 (se omite el ordenamiento global)                       |
|    - 3. Vecindad inicial pequeña (sigma_0 ≈ 1/8 D_bar) decreciendo a 1.0           |
|    - 4. Tasa de aprendizaje inicial pequeña (alpha_0 ≈ 0.1) decreciendo a 0.01     |
|    - 5. Duración: Solo la DÉCIMA PARTE (1/10) de las iteraciones base              |
|         (T_refine = 1/10 * T_base = 100 a 200 épocas)                             |
+-----------------------------------------------------------------------------------+
```

### Tabla Canónica de Hiperparámetros

Para una malla hexagonal de $R \times C$, el tamaño promedio es $\bar{D} = \frac{R + C}{2}$.

| Fase de Entrenamiento | Épocas | Tasa de Aprendizaje ($\alpha$) | Radio de Vecindad ($\sigma$) | Inicialización Sináptica |
| :--- | :---: | :---: | :---: | :--- |
| **Periodo 1: Full Training (Base $T_1$)** | **1000** | $\alpha_0 = \mathbf{0.9} \rightarrow 0.01$ | $\sigma_0 = \frac{1}{2} \bar{D} \rightarrow 1.0$ | Global (PCA) |
| **Periodos $2+$: Refinement (Warm-Start $T_t$)** | **100 a 200** *(1/10 de base)* | $\alpha = \mathbf{0.1} \rightarrow 0.01$ | $\sigma = \frac{1}{8} \bar{D} \rightarrow 1.0$ | Pesos convergidos $W_{t-1}^*$ |

---

## 4. Marco Analítico Integral e Interpretación Cienciométrica

Al interpretar y reportar la secuencia temporal, el agente estructura su diagnóstico en los siguientes ejes canónicos:

### 1. Nivel Macro: Evolución Sistémica y Componentes
* **Tasas de Crecimiento Intertemporal ($\Delta\%$ de la media):** Variación porcentual de la media nacional/institucional en cada indicador entre cortes.
* **Deriva de Gradientes Cromáticos:** Rastreo de la expansión o contracción de zonas rojas (alto desempeño) frente a zonas verdes en los mapas de componentes.
* **Preservación o Ruptura de Cuadrantes de Impacto:** Verificar si el polo de excelencia permanece estable en un cuadrante o experimenta giros provocados por reestructuraciones disciplinarias.

### 2. Dinámica de Cohortes y Retención
* **Tasa de Retención Intertemporal:** Porcentaje de entidades activas en $T_{t-1}$ que se mantienen en $T_t$.
* **Entrantes vs. Deserciones:** Detección de disciplinas o instituciones emergentes vs. aquellas que pierden masa crítica de publicación.
* **Núcleo Persistente:** Conjunto de actores que habitan la red ininterrumpidamente a lo largo de toda la serie histórica.

### 3. Nivel Meso: Dinámica de Clusters (Vesanto)
* **Cluster Splitting (Escisión):** Entidades agrupadas en $T_{t-1}$ que se dividen en clusters separados en $T_t$. Diagnóstico: *Diferenciación y especialización de perfiles*.
* **Cluster Merging (Fusión):** Entidades de clusters distintos que convergen en el mismo grupo. Diagnóstico: *Homogeneización o estandarización de prácticas de investigación*.

### 4. Nivel Micro: Desplazamientos, Perfiles Singulares y Diagnóstico de Maduración
* **Desplazamiento Euclidiano en la Retícula:** $\Delta d_i = \| \text{BMU}_i^{(t)} - \text{BMU}_i^{(t-1)} \|_2$.
* **Perfiles Singulares / Atípicos ($|C_k| = 1$):** Entidades que se aíslan completamente en un cluster individual debido a volúmenes masivos o citación desproporcionada (ejemplo: *Clinical Medicine* en México). **Recomendación metodológica:** Tratar como perfil atípico y analizarlo en detalle mediante la técnica de **Mapeo de Trayectorias** ([`som-trajectory-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md)).
* **Resolución de Paradojas Métricas (Métricas No Acotadas vs. Acotadas):**
  * *La Paradoja CNCI vs. Average Percentile:* Si una entidad exhibe un CNCI muy alto (e.g. $> 1.8$, duplicando la media mundial) pero un *Average Percentile* modesto (e.g. $36$ frente a la media mundial de $50$), el diagnóstico cienciométrico indica que **el impacto está inflado por un número reducido de artículos atípicos hipercitados (*Black Swans* o colaboraciones masivas en salud)**, mientras que el grueso de la producción tiene citación baja.
* **Indicador de Maduración Comunitaria:**
  * Ocurre cuando el **% Documents in Top 10%** cruza consistentemente la media mundial ($> 10\%$). Esto demuestra que la disciplina ha dejado de depender de unos pocos investigadores de élite aislados (% Top 1%) y ha alcanzado una **masa crítica comunitaria** con producción de alta calidad sostenida.

### 5. Tensión Adaptativa y Deriva Sináptica ($\Delta W$)
Cuantificación de la deriva sináptica por neurona entre cortes contiguos:
$$\Delta W_j = \| W_j^{(t)} - W_j^{(t-1)} \|_2$$
Identifica qué cuadrantes del mapa concentran las mayores transformaciones estructurales del conocimiento o desempeño frente a regiones inertes.

---

## 5. Scripts de Utilidad: `neural_longitudinal_cli.py`

Ubicación del script CLI de ejecución: [`scripts/neural_longitudinal_cli.py`](file:///home/labsom/knomap/engine/skills/neural-longitudinal-mapping/scripts/neural_longitudinal_cli.py)

```bash
# 1. Preparación de serie temporal por ventanas
python neural_longitudinal_cli.py prepare \
  --input dataset.parquet \
  --entity-col university \
  --period-col year \
  --window 5 --step 5 \
  --output prepared_series.json

# 2. Entrenamiento Warm-Start Chaining
python neural_longitudinal_cli.py train \
  --input prepared_series.json \
  --rows 10 --cols 20 \
  --base-epochs 1000 --refine-epochs 200 \
  --output longitudinal_results.json

# 3. Análisis evolutivo en 3 niveles y cohortes
python neural_longitudinal_cli.py analyze \
  --input longitudinal_results.json \
  --output dynamics_analysis.json

# 4. Generación de reporte Markdown estructurado
python neural_longitudinal_cli.py report \
  --analysis dynamics_analysis.json \
  --mode external_mcp \
  --output report_longitudinal.md

# 5. Generación de Dashboards Hexagonales KnoMap por periodo
# Invocar knomap_render_som_dashboard desde viz_tools.py para cada corte temporal:
# render_knomap_som_dashboard(som_state_t, output_path=f"dashboard_som_{period}.html", max_labels_per_neuron=2)
```

---

## 6. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Reentrenamiento independiente con PCA en cortes sucesivos ($T_2, T_3, \dots$)**  
  Inicializar cada periodo temporal desde cero con PCA o pesos aleatorios. Esto provoca rotaciones arbitrarias, traslaciones o inversiones especulares del espacio latente, haciendo imposible la comparación longitudinal de trayectorias.  
  **Solución:** Aplicar estrictamente el protocolo Warm-Start: inicializar $T_t$ con los pesos convergidos del periodo previo: $W_t^{(0)} = W_{t-1}^*$.
- ❌ **Anti-patrón 2: Ejecutar el número completo de épocas base (1000 iteraciones) en periodos de refinamiento**  
  Entrenar $T_t$ durante cientos de épocas con tasa de aprendizaje grande ($\alpha_0 > 0.1$), borrando la memoria estructural de la secuencia anterior.  
  **Solución:** La duración del refinamiento Warm-Start debe ser estrictamente de 1/10 de las épocas base (100 a 200 épocas) con $\alpha_0 = 0.1 \rightarrow 0.01$ y radio $\sigma_0 = \frac{1}{8}\bar{D}$.
- ❌ **Anti-patrón 3: No cuantificar la tensión de deriva sináptica ($\Delta W$)**  
  Reportar desplazamientos de entidades o migraciones de clusters sin auditar la deriva sináptica global $\Delta W = \|W_t - W_{t-1}\|_F$.  
  **Solución:** Calcular siempre $\Delta W$ para verificar si la red experimentó una acomodación suave o una mutación estructural violenta en el sistema de indicadores.
- ❌ **Anti-patrón 4: Tratar de etiquetar todas las entidades en secuencias masivas**  
  En series temporales de 50 o 100 universidades, rotular cada una en todos los cortes temporales satura los hexágonos e impide rastrear las migraciones.  
  **Solución:** Identificar el *núcleo persistente* y las entidades singulares, limitando a 1 o 2 etiquetas por neurona mediante `max_labels_per_neuron`.
- ❌ **Anti-patrón 5: Violación de File-Output First**  
  Volcar en la consola del LLM las matrices de pesos de los 5 periodos concatenados.  
  **Solución:** Escribir los resultados en archivos estructurados (`longitudinal_results.json` y `report_longitudinal.md`) y generar dashboards HTML por cada periodo.

---

## 7. Referencias Bibliográficas

1. **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 293–313). UNAM, Instituto de Investigaciones Bibliotecológicas y de la Información. ISBN-e: 978-607-642-193-2.
2. **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** Neural longitudinal mapping of multidimensional performance profiles of Latin American universities. *Iberoamerican Journal of Science Measurement and Communication*, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92
3. **Jiménez-Andrade, J. L. (2023).** *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). Universidad Nacional Autónoma de México.
4. **Gorbea-Portal, S. (2016).** Una nueva perspectiva teórica de la bibliometría basada en su dimensión histórica y sus referentes temporales. *Investigación Bibliotecológica: archivonomía, bibliotecología e información*, 30(70), 11–16. https://doi.org/10.1016/j.ibbai.2016.10.001
5. **Garfield, E. (1994).** Scientography: Mapping the tracks of science. *Current Contents: Social & Behavioural Sciences*, 7(45), 5–10.
6. **Villaseñor-García, E. A., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2017).** Multiparametric characterization of scientometric performance profiles assisted by neural networks: A study of Mexican higher education institutions. *Scientometrics*, 110(1), 77–104. https://doi.org/10.1007/s11192-016-2166-0
