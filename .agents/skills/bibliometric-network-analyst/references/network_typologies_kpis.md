# Tipologías de Redes Bibliométricas e Indicadores Topológicos

Esta referencia define las tipologías de red generadas en KnoMap y sus interpretaciones cienciométricas.

---

## 1. Tipologías de Red

| Tipo de Red | Unidad de Análisis | Significado Cienciométrico | Tipo de Estructura |
|---|---|---|---|
| **Co-ocurrencia de Keywords** | Palabras clave (autor/plus) | Estructura conceptual, frentes temáticos y proximidad semántica | Conceptual |
| **Coautoría** | Autores, instituciones, países | Redes de colaboración, capital social y comunidades invisibles | Social |
| **Co-citación** | Referencias o autores citados | Base intelectual del campo y genealogía teórica compartida | Intelectual |
| **Acoplamiento Bibliográfico** | Documentos, autores, fuentes | Frente de investigación activo (trabajos que citan las mismas fuentes) | Frente Activo |
| **Citación Directa** | Trabajos, revistas | Flujo de conocimiento e impacto citacional acumulado | Histórica / Impacto |

---

## 2. Detección de Comunidades (Leiden vs Louvain)

* **Algoritmo Leiden (Traag et al., 2019):** Es la evolución formal de Louvain. Garantiza que todas las comunidades detectadas estén topológicamente conectadas, evitando la creación de comunidades fragmentadas o subóptimas. Se utiliza como estándar predeterminado.
* **Parámetro de Resolución ($\gamma$):**
  * $\gamma = 1.0$: Partición estándar equilibrada.
  * $\gamma > 1.0$: Partición fina (mayor número de micro-comunidades especializadas).
  * $\gamma < 1.0$: Partición agregada (fusión de clusters en macro-áreas).

---

## 3. Métricas de Centralidad de Red

* **Degree Centrality:** Volumen total de colaboraciones o co-ocurrencias de un nodo.
* **Betweenness Centrality:** Mide la frecuencia con la que un nodo actúa como puente en los caminos más cortos entre otros nodos (identifica términos o autores interdisciplinares).
* **PageRank:** Importancia recursiva de un nodo en función de la autoridad de sus vecinos.
