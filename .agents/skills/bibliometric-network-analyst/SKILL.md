---
name: bibliometric-network-analyst
description: Construction and analysis of bibliometric networks (co-authorship, co-occurrence, co-citation, bibliographic coupling, and direct citation), temporal period filtering, generation of interactive visual artifacts (KnoMap Force Graph and VOSviewer Engine), Association Strength normalization, modular partitioning with Leiden/Louvain, centrality calculation, and integration with static and longitudinal SOMs. Respond and label outputs in the user's language.
dependencies:
  - python: ">=3.10"
  - script: "scripts/biblio_network_cli.py"
---
# Bibliometric Network Analyst (KnoMap Biblio Networks)

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

This skill implements the analytical and visualization functionality of the **Biblio Networks** tab in KnoMap and the SOS-MCP ecosystem. It constructs, normalizes, partitions, and visualizes scientific network topologies to identify thematic communities, invisible colleges, co-authorship leaders, active research fronts, and temporal evolution.

---

## 1. Overview and Visualization Modes in KnoMap

Bibliometric networks model the social, conceptual, and intellectual interactions of science through directed or undirected graphs. This skill prioritizes rigorous structural network analysis and provides two complementary canonical visualizations as **standalone interactive HTML artifacts**:

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                     VISUALIZATION MODES IN KNOMAP BIBLIO NETWORKS                     │
├──────────────────────────┬─────────────────────────────┬──────────────────────────────┤
│ Visualization Mode       │ Technological Engine        │ Key Analytical Capabilities  │
├──────────────────────────┼─────────────────────────────┼──────────────────────────────┤
│ 1. KnoMap Force Graph    │ D3.js v7 Force Simulation   │ - Nodes by frequency/degree  │
│    (Native Diagram)      │ Interactive SVG Rendering   │ - Colors by Leiden cluster   │
│                          │ LabSOM Dark Mode            │ - 1-hop ego-network highlight│
│                          │                             │ - LCC filter (Giant Comp.)   │
│                          │                             │ - Live node inspector        │
├──────────────────────────┼─────────────────────────────┼──────────────────────────────┤
│ 2. VOSviewer Engine      │ Canvas 2D / WebGL           │ - Network View (Clusters)    │
│    (Canonical VOSviewer) │ Van Eck & Waltman Layout    │ - Overlay View (Scores/Years)│
│                          │ Compatible app.vosviewer.com│ - Density View (Heatmap)     │
│                          │ `vosviewer.json` Exporter   │ - Gaussian kernel density    │
└──────────────────────────┴─────────────────────────────┴──────────────────────────────┘
```

---

## 2. Network Typologies and Construction (`build-network`)

Constructs the network from a corpus in tabular or native formats (`.parquet`, `.csv`, `.json`, or Web of Science plain text `.txt` exports):

```bash
python scripts/biblio_network_cli.py build-network \
  --input /path/to/corpus.parquet \
  --network-type cooccurrence \
  --unit keywords \
  --counting full \
  --normalization association-strength \
  --min-freq 2 \
  --min-cooccur 1.0 \
  --auto-analyze \
  --html-knomap ./network_knomap.html \
  --html-vosviewer ./network_vosviewer.html \
  --vosviewer-json ./vosviewer.json \
  --som-matrix ./som_cooccurrence_matrix.csv \
  --output ./full_network.json
```

### Supported Network Typologies (`--network-type` and `--unit`):
1. **Keyword Co-occurrence (`cooccurrence`, `keywords`):** Co-appearance of author keywords (`DE`), Keywords Plus (`ID`), or thematic concepts in the same documents (conceptual fronts).
2. **Co-authorship (`coauthorship`):** Social collaboration among researchers (`authors`), institutional affiliations (`institutions`), or country blocs (`countries`).
3. **Bibliographic Coupling (`coupling`):** Degree to which two documents, authors, or sources cite the same common bibliographic references (active research fronts).
4. **Direct Citation (`direct-citation`):** Direct citation links between units of analysis.

### Optional Temporal Filtering:
- `--period YYYY-YYYY` (e.g., `--period 2020-2024` or `--period 2024`): restricts the graph to the specified chronological range.
- `--last-years N` (e.g., `--last-years 5`): automatically filters the last $N$ years relative to the maximum year in the corpus.
- `--year-from YYYY` and `--year-to YYYY`: lower and upper bound filters.
- `--max-terms N`: limits the network to the top $N$ terms by global frequency.

---

## 3. Scientometric Normalization and Community Detection

### 3.1 Normalization Methods (`--normalization`):
* **Association Strength (Van Eck & Waltman, 2009):** Standard similarity measure in VOSviewer and KnoMap:
  $$AS_{ij} = \frac{C_{ij}}{2 \cdot m \cdot s_i \cdot s_j}$$
  where $C_{ij}$ is the observed co-occurrence, $s_i, s_j$ are total occurrences, and $m$ is the total number of links. It normalizes by expected random co-occurrence.
* **Salton's Cosine:** Geometric similarity normalized by the geometric mean of frequencies: $S_{ij} = C_{ij} / \sqrt{C_i \cdot C_j}$.
* **Jaccard Index:** Ratio between intersection and union: $J_{ij} = C_{ij} / (C_i + C_j - C_{ij})$.
* **Counting:** Full (`full`) or fractional (`fractional`).

### 3.2 Modular Partitioning (Community Detection):
* **Leiden Algorithm (`--algorithm leiden` - Recommended):** Guarantees connected communities and robustly optimizes modularity, eliminating fragmented communities.
* **Louvain Algorithm (`--algorithm louvain`):** Classical heuristic modularity algorithm.

### 3.3 Node Centrality Metrics:
Calculated automatically with `--auto-analyze` or via the `calculate-centralities` subcommand:
- **Weighted Degree / Total Link Strength:** Aggregate intensity of a node's connections.
- **Betweenness Centrality:** Identifies bridge nodes connecting distinct conceptual communities or invisible colleges.
- **PageRank:** Measures the structural authority and centrality of a node within the network flow.

---

## 4. Interactive Visualization and Artifact Generation

This skill directly generates the two interactive viewers from KnoMap's **Biblio Networks** tab as standalone HTML files ready to open in a browser or present to the user:

### 4.1 Artifact 1: KnoMap Force Graph Viewer (`render-knomap` or `--html-knomap`)

Generates an interactive HTML file powered by a D3.js Force Simulation engine in the KnoMap Dark Mode visual aesthetic:

```bash
python scripts/biblio_network_cli.py render-knomap \
  --input ./full_network.json \
  --output ./artifact_knomap_network.html \
  --title "Thematic Co-occurrence Network" \
  --subtitle "KnoMap Force-Directed Graph Ecosystem"
```

**Interactive Features:**
- **Dynamic Force Simulation:** Organic layout with continuous D3 zoom and pan.
- **1-Hop Ego-Network Highlighting:** Hovering over a node illuminates its connected neighbors and edges with their association strength while dimming the rest of the network.
- **Live Node Inspector Card:** Displays in real time: node label, community cluster, occurrences, weighted degree (Total Link Strength), PageRank, and betweenness centrality.
- **Largest Connected Component (LCC) Filter:** Checkbox to isolate only the giant connected component and hide disconnected islands.
- **Real-Time Search:** Text input to quickly locate and highlight nodes.
- **Graphics Export:** Button to download the graph in vector SVG format.

---

### 4.2 Artifact 2: VOSviewer Engine (`render-vosviewer` or `--html-vosviewer`)

Generates an HTML viewer featuring the three canonical VOSviewer views and exports the official `vosviewer.json` file:

```bash
python scripts/biblio_network_cli.py render-vosviewer \
  --input ./full_network.json \
  --output ./artifact_vosviewer_map.html \
  --output-json ./vosviewer.json \
  --title "VOSviewer Science Mapping"
```

**Visualization Modes Available in the Interface:**
1. **● Network Visualization:** Nodes rendered as circles proportional to occurrences, colored by modular community, and linked by curved lines with intensity proportional to edge weight.
2. **◐ Overlay Visualization:** Continuous color gradient (Viridis / Plasma / Coolwarm) mapped onto a continuous numerical metric (PageRank, average publication year, or citations), complete with a colorbar legend.
3. **◎ Density Visualization:** **Continuous heat surface computed via a 2D Gaussian kernel** following Van Eck & Waltman's original formulation (thermal palette Blue $\to$ Cyan $\to$ Green $\to$ Yellow $\to$ Red), revealing areas of highest conceptual concentration.
4. **Interoperability:** Built-in button to download `vosviewer.json` and direct link to open the map in the official [app.vosviewer.com](https://app.vosviewer.com) web application or import it into KnoMap's Biblio Networks tab.

---

## 5. Longitudinal Sequential Networks (`sequential-networks`)

Splits the corpus into consecutive periods or sliding windows, builds the network for each period with Leiden communities and centralities, and generates a unified evolution manifest:

```bash
python scripts/biblio_network_cli.py sequential-networks \
  --input /path/to/corpus.parquet \
  --output-dir ./longitudinal_networks \
  --network-type cooccurrence \
  --unit keywords \
  --window 5 \
  --step 5 \
  --max-terms 50 \
  --normalization association-strength
```

### Key Options:
- `--window N`: Window size in years (e.g., `5` for five-year periods, `10` for decades).
- `--step S`: Step size (disjoint windows if $S = W$; sliding windows if $S < W$).
- `--periods "P1,P2,..."`: Explicit list of custom periods (e.g., `"2000-2009,2010-2019,2020-2024"`).
- `--max-terms M`: Number of concepts retained in the **shared canonical vocabulary** (ensuring aligned $M \times M$ matrices across all periods).

---

## 6. Advanced Connection with the SOM Ecosystem (Neurocomputational Analysis)

Although bibliometric network analysis is completely standalone and does not require neural networks, the KnoMap ecosystem integrates a **direct bridge between graph topology and Kohonen Self-Organizing Maps (SOM)** grounded in early foundational work (ViBlioSOM; Sotolongo, Carrillo-Calvet et al., 1999–2002) and contemporary multidimensional profile methodology (*Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet, 2024*; *Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025*).

### 6.1 SOM on Static or Period Networks (Adjacency Matrix Mapping)

In traditional network analysis, each term or author is visualized as a discrete node in a force-directed space. However, its **relational profile** with the rest of the discipline can be modeled as a continuous numerical vector in $\mathbb{R}^N$.

Using the `export-som-matrix` subcommand (which reproduces the `handleSendToSOM` button in KnoMap's Biblio Networks tab):

```bash
python scripts/biblio_network_cli.py export-som-matrix \
  --input ./full_network.json \
  --output-csv ./som_cooccurrence_matrix.csv \
  --output-json ./som_cooccurrence_matrix.json
```

This yields a symmetric $N \times N$ adjacency/co-occurrence matrix:
* Each **row** represents the relational profile of a term $i$.
* The **diagonal** contains the occurrence frequency of the term ($C_i$).
* The **off-diagonal** elements contain the normalized Association Strength with all other terms ($AS_{ij}$).

#### Integration with [`som-methodological-expert`](../som-methodological-expert/SKILL.md):
When feeding this $N \times N$ matrix into the SOM engine:
1. **Topological Preservation:** Terms with similar co-occurrence profiles map onto the same neuron or adjacent neurons on the hexagonal grid.
2. **U-Matrix Inspection:** The Unified Distance Matrix (U-Matrix) reveals valleys of high conceptual density and separating ridges between subfields.
3. **Partition Cross-Comparison (Leiden vs. Vesanto):** Enables cross-comparing communities detected via graph modularity (Leiden/Louvain) against continuous meta-clusters computed over the SOM using Vesanto's algorithm and the Silhouette criterion.

---

### 6.2 Longitudinal SOM (Warm-Start Chaining)

The `sequence_manifest.json` file emitted by the `sequential-networks` subcommand is **100% compatible without intermediate conversion** with the temporal chaining engine of [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md):

```bash
# 1. Train chained longitudinal sequence (Warm-Start: W_t = W_{t-1}^*)
python scripts/neural_longitudinal_cli.py train \
  --input ./longitudinal_networks/sequence_manifest.json \
  --rows 8 --cols 12 \
  --output ./longitudinal_results.json

# 2. Compute Macro, Meso, and Micro dynamics
python scripts/neural_longitudinal_cli.py analyze \
  --input ./longitudinal_results.json \
  --output ./dynamics_analysis.json

# 3. Generate Markdown report with community evolution
python scripts/neural_longitudinal_cli.py report \
  --analysis ./dynamics_analysis.json \
  --output ./report_longitudinal.md
```

This connection enables tracking:
* **Macro Level:** Global synaptic drift rate ($\Delta W$).
* **Meso Level:** Merging and splitting of research fronts across decades.
* **Micro Level:** Trajectories of core concepts across the latent space.

---

## 7. Troubleshooting and Best Practices

- **Browser Visualization:** Generated `.html` files are completely static and require no backend server; they can be opened by double-clicking or served from any CDN.
- **Sparse / Disconnected Networks:** In small corpora with many sporadic terms, use `--min-freq 2` or check the "Giant Component Only (LCC)" box in the KnoMap interface to isolate the coherent thematic core.
- **Connected Community Guarantee:** Always use `--algorithm leiden` instead of Louvain to prevent internally disconnected clusters.
- **Canonical Export to VOSviewer:** The generated `vosviewer.json` file can be dragged and dropped directly into the official interface at [app.vosviewer.com](https://app.vosviewer.com).
