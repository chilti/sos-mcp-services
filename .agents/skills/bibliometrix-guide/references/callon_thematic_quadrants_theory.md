# Fundamentos Teóricos del Diagrama Estratégico de Callon (1991)

El **Diagrama Estratégico de Callon** (Callon, Courtial & Laville, 1991; Cobo et al., 2011; Aria & Cuccurullo, 2017) es una de las metodologías centrales de cartografía de la ciencia implementadas en el paquete `bibliometrix` a través de la función `thematicMap()`.

---

## 1. Métricas Estructurales de Callon

Dado un grafo de coocurrencia de palabras clave particionado en clusters o subredes temáticas $C_k$:

### 1.1 Centralidad de Callon ($c$)
Mide el grado de interacción de una red temática con otras partes del grafo de conocimiento. Cuantifica la fuerza de los enlaces externos que unen los términos del cluster con términos pertenecientes a otros clusters:

$$c = 10 \sum e_{ij}$$

donde $i$ es una palabra clave del cluster analizado y $j$ es una palabra clave externa perteneciente a otro cluster.
* **Alta Centralidad:** El tema es estructuralmente medular, transversal y actúa como nodo conector en la disciplina.
* **Baja Centralidad:** El tema es periférico o marginal en el intercambio conceptual global.

### 1.2 Densidad de Callon ($d$)
Mide la cohesión interna o nivel de desarrollo conceptual del cluster temático. Cuantifica la fuerza media de los enlaces internos entre los términos que componen el cluster:

$$d = 100 \frac{\sum e_{ij}}{w}$$

donde $i$ y $j$ son palabras clave dentro del mismo cluster y $w$ es el número de términos del cluster.
* **Alta Densidad:** El tema posee un aparato teórico fuertemente articulado, vocabulario técnico especializado y comunidad científica madura.
* **Baja Densidad:** El tema tiene enlaces internos débiles, conceptos dispersos o se encuentra en etapa exploratoria no consolidada.

---

## 2. Los Cuatro Cuadrantes del Diagrama Estratégico

Al graficar la **Centralidad** en el eje de las abscisas ($X$) y la **Densidad** en el eje de las ordenadas ($Y$), habitualmente centrando el origen en la mediana de ambas distribuciones, se configuran 4 cuadrantes analíticos:

```
                  Densidad (Cohesión Interna)
                              ▲
                              │
          CUADRANTE II        │        CUADRANTE I
     Temas Muy Especializados │       Temas Motores
         / Temas de Nicho     │     (Motor Themes)
   (Alta Densidad, Baja Centr.)│ (Alta Densidad, Alta Centr.)
                              │
  ────────────────────────────┼────────────────────────────► Centralidad
                              │                              (Enlaces Externos)
         CUADRANTE III        │        CUADRANTE IV
      Temas Emergentes o      │       Temas Básicos y
         en Declinación       │        Transversales
   (Baja Densidad, Baja Centr.)│ (Baja Densidad, Alta Centr.)
                              │
```

### Cuadrante I: Temas Motores (*Motor Themes*)
* **Coordenadas:** Alta Centralidad y Alta Densidad.
* **Significado:** Temas bien desarrollados internamente y con fuerte conexión estructural con el resto de la disciplina. Son los motores intelectuales y las líneas de investigación prioritarias del campo.

### Cuadrante II: Temas de Nicho / Muy Especializados (*Niche Themes*)
* **Coordenadas:** Baja Centralidad y Alta Densidad.
* **Significado:** Temas con sólida cohesión interna y vocabulario técnico altamente consolidado, pero con pocas conexiones con otras áreas. Representan especialidades periféricas, subdisciplinas de nicho o técnicas muy específicas.

### Cuadrante III: Temas Emergentes o en Declinación (*Emerging or Declining Themes*)
* **Coordenadas:** Baja Centralidad y Baja Densidad.
* **Significado:** Temas débilmente estructurados internamente y marginales respecto al resto del campo. Pueden representar frentes embrionarios en gestación (*emerging*) o, por el contrario, modas pasadas en proceso de abandono (*declining*). El análisis longitudinal intertemporal (`thematicEvolution()`) es el criterio decisivo para distinguir entre ambas trayectorias.

### Cuadrante IV: Temas Básicos y Transversales (*Basic and Transversal Themes*)
* **Coordenadas:** Alta Centralidad y Baja Densidad.
* **Significado:** Temas con amplia presencia en toda la literatura y conexiones transversales múltiples, pero con baja densidad interna (conceptos generales o fundacionales de la disciplina, p. ej. "metodología", "salud", "educación", "modelo"). Son pilares necesarios pero no conforman líneas hiper-especializadas por sí mismos.

---

## 3. Evolución Temática Longitudinal (`thematicEvolution`)

La función `thematicEvolution()` divide el corpus en periodos cronológicos discretos ($T_1, T_2, \dots, T_k$), calcula los clusters de coocurrencia en cada periodo y traza los flujos de términos compartidos mediante diagramas de Sankey / aluviales ponderados por el Índice de Inclusión de Cowen:

$$I_{ij} = \frac{\#(C_i \cap C_j)}{\min(\#C_i, \#C_j)}$$

Este flujo cuantitativo revela:
1. **Fusión temática (*Convergence*):** Múltiples clusters de $T_1$ convergen en un único cluster en $T_2$.
2. **Escisión temática (*Divergence*):** Un tema general en $T_1$ se subdivide en varias sublíneas independientes en $T_2$.
3. **Continuidad (*Stability*):** El núcleo de vocabulario permanece estable a lo largo del tiempo.
