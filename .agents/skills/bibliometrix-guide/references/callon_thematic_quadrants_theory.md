# Theoretical Foundations of Callon's Strategic Diagram (1991)

**Callon's Strategic Diagram** (Callon, Courtial & Laville, 1991; Cobo et al., 2011; Aria & Cuccurullo, 2017) is one of the core science mapping methodologies implemented in the `bibliometrix` package through the `thematicMap()` function.

---

## 1. Callon's Structural Metrics

Given a keyword co-occurrence graph partitioned into thematic clusters or subnetworks $C_k$:

### 1.1 Callon's Centrality ($c$)
Measures the degree of interaction of a thematic network with other parts of the knowledge graph. It quantifies the strength of external links connecting terms in the cluster with terms belonging to other clusters:

$$c = 10 \sum e_{ij}$$

where $i$ is a keyword in the analyzed cluster and $j$ is an external keyword belonging to another cluster.
* **High Centrality:** The theme is structurally core, transversal, and acts as a connector node across the discipline.
* **Low Centrality:** The theme is peripheral or marginal in global conceptual exchange.

### 1.2 Callon's Density ($d$)
Measures the internal cohesion or level of conceptual development of the thematic cluster. It quantifies the mean strength of internal links among the terms making up the cluster:

$$d = 100 \frac{\sum e_{ij}}{w}$$

where $i$ and $j$ are keywords within the same cluster and $w$ is the number of terms in the cluster.
* **High Density:** The theme possesses a strongly articulated theoretical apparatus, specialized technical vocabulary, and a mature scientific community.
* **Low Density:** The theme has weak internal links, dispersed concepts, or is in an unconsolidated exploratory stage.

---

## 2. The Four Quadrants of the Strategic Diagram

By plotting **Centrality** on the horizontal axis ($X$) and **Density** on the vertical axis ($Y$), typically centering the origin at the median of both distributions, 4 analytical quadrants are formed:

```
                   Density (Internal Cohesion)
                               ▲
                               │
           QUADRANT II         │        QUADRANT I
      Highly Specialized /     │       Motor Themes
          Niche Themes         │     (Motor Themes)
    (High Density, Low Centr.) │ (High Density, High Centr.)
                               │
   ────────────────────────────┼────────────────────────────► Centrality
                               │                              (External Links)
          QUADRANT III         │        QUADRANT IV
       Emerging or Declining   │   Basic and Transversal
             Themes            │          Themes
    (Low Density, Low Centr.)  │ (Low Density, High Centr.)
                               │
```

### Quadrant I: Motor Themes
* **Coordinates:** High Centrality and High Density.
* **Meaning:** Themes that are well developed internally and strongly connected structurally to the rest of the discipline. They are the intellectual drivers and priority research lines of the field.

### Quadrant II: Niche / Highly Specialized Themes
* **Coordinates:** Low Centrality and High Density.
* **Meaning:** Themes with strong internal cohesion and highly consolidated technical vocabulary, but few connections to other areas. They represent peripheral specialties, niche subdisciplines, or highly specific techniques.

### Quadrant III: Emerging or Declining Themes
* **Coordinates:** Low Centrality and Low Density.
* **Meaning:** Themes that are weakly structured internally and marginal relative to the rest of the field. They may represent embryonic fronts in gestation (*emerging*) or, conversely, past trends being abandoned (*declining*). Longitudinal intertemporal analysis (`thematicEvolution()`) is the decisive criterion to distinguish between the two trajectories.

### Quadrant IV: Basic and Transversal Themes
* **Coordinates:** High Centrality and Low Density.
* **Meaning:** Themes with broad presence across the literature and multiple transversal connections, but low internal density (general or foundational concepts of the discipline, e.g., "methodology", "health", "education", "model"). They are necessary pillars but do not constitute hyper-specialized research lines on their own.

---

## 3. Longitudinal Thematic Evolution (`thematicEvolution`)

The `thematicEvolution()` function splits the corpus into discrete chronological periods ($T_1, T_2, \dots, T_k$), computes co-occurrence clusters in each period, and traces shared term flows via Sankey / alluvial diagrams weighted by the Inclusion Index:

$$I_{ij} = \frac{\#(C_i \cap C_j)}{\min(\#C_i, \#C_j)}$$

This quantitative flow reveals:
1. **Thematic Convergence (Merge):** Multiple clusters from $T_1$ converge into a single cluster in $T_2$.
2. **Thematic Divergence (Split):** A general theme in $T_1$ subdivides into several independent sublines in $T_2$.
3. **Stability (Continuity):** The core vocabulary remains stable over time.
