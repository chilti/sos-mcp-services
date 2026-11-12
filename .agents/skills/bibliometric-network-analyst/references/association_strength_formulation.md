# Mathematical Formulation of Association Strength

**Association Strength** (Van Eck & Waltman, 2007; 2009) is the optimal normalized similarity measure for bibliometric networks, overcoming the biases of Salton's Cosine and the Jaccard Index in co-occurrence networks.

---

## 1. Formal Definition

Let $i$ and $j$ be two nodes with observed co-occurrence count $c_{ij}$ and marginal counts $s_i$ and $s_j$:

$$s_{ij} = \frac{c_{ij}}{e_{ij}} = \frac{2m \cdot c_{ij}}{s_i \cdot s_j}$$

where:
* $c_{ij}$: Observed co-occurrence between node $i$ and node $j$.
* $s_i = \sum_{k \ne i} c_{ik}$: Total link strength of node $i$.
* $s_j = \sum_{k \ne j} c_{jk}$: Total link strength of node $j$.
* $m = \frac{1}{2} \sum_{i} \sum_{j \ne i} c_{ij}$: Total count of all co-occurrences in the network.
* $e_{ij} = \frac{s_i s_j}{2m}$: Expected number of co-occurrences if occurrences were statistically independent (random).

---

## 2. Advantages over Salton's Cosine

* **Scale Invariance:** If all counts in the network are multiplied by a constant, the association strength remains invariant.
* **Direct Probabilistic Interpretation:** $s_{ij} > 1.0$ indicates that the nodes co-occur more frequently than expected by chance; $s_{ij} < 1.0$ indicates repulsion or independence.
