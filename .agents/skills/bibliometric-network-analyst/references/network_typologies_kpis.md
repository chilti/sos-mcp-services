# Bibliometric Network Typologies and Topological Indicators

This reference defines the network typologies generated in KnoMap and their scientometric interpretations.

---

## 1. Network Typologies

| Network Type | Unit of Analysis | Scientometric Meaning | Structure Type |
|---|---|---|---|
| **Keyword Co-occurrence** | Keywords (author/plus) | Conceptual structure, thematic fronts, and semantic proximity | Conceptual |
| **Co-authorship** | Authors, institutions, countries | Collaboration networks, social capital, and invisible colleges | Social |
| **Co-citation** | Cited references or cited authors | Intellectual base of the field and shared theoretical genealogy | Intellectual |
| **Bibliographic Coupling** | Documents, authors, sources | Active research front (works citing the same sources) | Active Front |
| **Direct Citation** | Works, journals | Knowledge flow and cumulative citation impact | Historical / Impact |

---

## 2. Community Detection (Leiden vs. Louvain)

* **Leiden Algorithm (Traag et al., 2019):** The formal evolution of Louvain. It guarantees that all detected communities are topologically connected, preventing the creation of fragmented or suboptimal communities. It is used as the default standard.
* **Resolution Parameter ($\gamma$):**
  * $\gamma = 1.0$: Balanced standard partition.
  * $\gamma > 1.0$: Fine-grained partition (higher number of specialized micro-communities).
  * $\gamma < 1.0$: Coarse partition (merges clusters into macro-areas).

---

## 3. Network Centrality Metrics

* **Degree Centrality:** Total volume of collaborations or co-occurrences of a node.
* **Betweenness Centrality:** Measures how frequently a node acts as a bridge along the shortest paths between other nodes (identifies interdisciplinary terms or authors).
* **PageRank:** Recursive importance of a node based on the authority of its neighbors.
