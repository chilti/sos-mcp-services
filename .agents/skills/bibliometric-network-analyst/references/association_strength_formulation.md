# Formulación Matemática de la Fuerza de Asociación (Association Strength)

La **Fuerza de Asociación** (Van Eck & Waltman, 2007; 2009) es la medida de similitud normalizada óptima para redes bibliométricas, superando los sesgos del Coseno de Salton y del Índice de Jaccard en redes de co-ocurrencia.

---

## 1. Definición Formal

Sean dos nodos $i$ y $j$ con conteo observado de co-ocurrencia $c_{ij}$ y conteos marginales $s_i$ y $s_j$:

$$s_{ij} = \frac{c_{ij}}{e_{ij}} = \frac{2m \cdot c_{ij}}{s_i \cdot s_j}$$

donde:
* $c_{ij}$: Co-ocurrencia observada entre el nodo $i$ y el nodo $j$.
* $s_i = \sum_{k \ne i} c_{ik}$: Fuerza total del nodo $i$.
* $s_j = \sum_{k \ne j} c_{jk}$: Fuerza total del nodo $j$.
* $m = \frac{1}{2} \sum_{i} \sum_{j \ne i} c_{ij}$: Conteo total de todas las co-ocurrencias en la red.
* $e_{ij} = \frac{s_i s_j}{2m}$: Número esperado de co-ocurrencias si las ocurrencias ocurrieran aleatoriamente.

---

## 2. Ventajas sobre el Coseno de Salton

* **Invarianza a Escala:** Si todos los conteos de la red se multiplican por una constante, la fuerza de asociación permanece invariante.
* **Interpretación Probabilística Directa:** $s_{ij} > 1.0$ indica que los nodos coocurren con una frecuencia mayor a la esperada por azar; $s_{ij} < 1.0$ indica repulsión o independencia.
