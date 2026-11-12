---
name: som-methodological-expert
description: >-
  Neurocomputational methodology expert in Kohonen Self-Organizing Maps (SOM) for multidimensional scientometric and bibliometric performance profile analysis (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor et al., 2017). Masters SVD spectral grid sizing, over-gridding rules (20N-30N), hexagonal topology, the LabSOM visual triad (red/yellow U-Matrix, yellow-red/green divergent component planes, and Vesanto meta-clustering with Silhouette), comparable peer diagnostics, and hyperparameter calibration. Respond and label outputs in the user's language.
---
# SOM Methodological Expert: Multidimensional Performance Profile Analysis

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Purpose and Epistemological Foundation

This skill formalizes and executes the neurocomputational methodology based on **Kohonen Self-Organizing Maps (SOM)** for characterizing, visualizing, and evaluating **multidimensional scientometric and bibliometric performance profiles**, consolidated in the foundational research:

> **Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025).** *Redes neuronales autoorganizadas y mapeos de la ciencia*. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (Colección Metría de la Información y del Conocimiento Científico, pp. 271–292). Instituto de Investigaciones Bibliotecológicas y de la Información (IIBI), Universidad Nacional Autónoma de México. ISBN-e: 978-607-642-193-2.

### Overcoming the One-Dimensional Reductionism of Rankings

* **The "Weigh and Sum" Fallacy:** Conventional university and disciplinary rankings (ARWU, QS, THE) combine heterogeneous indicators using arbitrary linear weights to produce a single scalar number. This one-dimensional index obscures the specific strengths and weaknesses of institutions and penalizes the diversity of academic missions.
* **Multidimensional Space and Peer Comparison:** Each unit of analysis (country, university, department, or thematic field) is modeled as a vector in an abstract space $\mathbb{R}^n$, where $n$ is the number of evaluated scientometric indicators.
* **Qualitative Profiles:** Entities with similar metrics naturally group together in Euclidean space to form *clusters*. The SOM network projects this continuous space onto a 2D lattice while preserving topology, allowing each entity to be compared **exclusively against its legitimate peers** (those sharing its qualitative profile).

### Historical and Methodological Lineage

1. **ViBlioSOM (1999–2002):** Foundational collaboration between Humberto Carrillo-Calvet (UNAM) and Gilberto Sotolongo-Aguilar (Finlay Institute), continued by María Victoria Guzmán-Sánchez (2009).
2. **LabSOM and DataSOMining (2004–2020):** Pioneering data mining and neurocomputational visualization environment developed at the Faculty of Sciences and C3 at UNAM.
3. **Multiparametric Performance Characterization (2017):** Formal introduction of SOM to model institutional performance profiles rather than solely citation networks (Villaseñor-García, Arencibia-Jorge & Carrillo-Calvet, *Scientometrics*).
4. **Neurocomputational Methodology for Mexican Science (2021):** Extension to thematic and national research profiles (Lozano-Díaz, PhD dissertation, UNAM).
5. **Warm-Start Longitudinal Mapping (2024):** Intertemporal chaining of maps to evaluate synaptic dynamics ($\Delta W$) and institutional trajectories (Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet, *IJSMC*).
6. **Scientific Evidence and Science Mapping (2025):** Comprehensive framework for evidence-based informetric decision-making (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge).

---

## 2. Dependencies and Value Chain (From Harvest to SOM)

This skill provides the neurocomputational and methodological core for the entire dimensional analysis pipeline. **The SOM does NOT directly consume the raw bibliographic corpus (`./corpus.parquet`), but rather an $[N \times D]$ indicator matrix by entity (`./matrices/indicadores_som.parquet`) computed in the preceding stage:**

* **Upstream Skills (Providers of $[N \times D]$ Matrices in the Workspace):**
  * **Option A (Standard from harvested `./corpus.parquet`): `tlachia-metrics-engine`** (`scripts/tlachia_metrics_cli.py by-entity`): Computes the full battery of **35+ scientometric indicators** per entity (`researcher`/`author`, `institution`, `country`, `source`, `subfield`, `topic`) **without truncating any columns**, enabling the agent to select the 4 cardinal dimensions or any combination of additional dimensions (H/G/M indices, the 6 OA routes, APC expenditure in USD, collaboration index, etc.):
    ```bash
    /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py by-entity \
      --input ./corpus.parquet \
      --level institution \
      --min-docs 2 \
      --output ./matrices/indicadores_som.parquet
    ```
  * **Option B (Exported TlachIA Metrics `.zip` packages): `tlachia-metrics-handler`** (`extract_tlachia_som_matrix`).
  * **Option C (Clarivate InCites CSV reports): `scientometrics-incites-expert`** (`extract_incites_som_matrix`).
* **Workspace-First CLI Execution of this Skill (`scripts/som_pipeline_cli.py`):**
  ```bash
  # Using all indicator columns or selecting specific dimensions with --indicator-cols
  /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/scripts/som_pipeline_cli.py \
    --input ./matrices/indicadores_som.parquet \
    --indicator-cols "num_documents,cites_per_doc,h_index,fwci_avg,avg_percentile,pct_top_10,pct_oa,pct_international" \
    --state-out ./reports/som_state.json \
    --html-out ./reports/som_dashboard.html \
    --png-clusters-es ./reports/som_clusters_es.png \
    --png-clusters-en ./reports/som_clusters_en.png \
    --png-umatrix-es ./reports/som_umatrix_es.png \
    --png-umatrix-en ./reports/som_umatrix_en.png \
    --diagnosis-out ./reports/som_diagnosis.json \
    --lang en
  ```
* **Downstream Skills (Evolution and Trajectories):**
  * `som-trajectory-mapping`: Intertemporal cubic spline tracing over the latent space (`./matrices/series_cma_som.parquet`).
  * `neural-longitudinal-mapping`: Inter-period Warm-Start chaining (`./matrices/periodos_som.parquet`).
* **Associated Software Tools:**
  * `scripts/som_pipeline_cli.py`: Standalone CLI reading `.parquet`/`.csv`/`.json` from the Workspace.
  * `services/knomap/tools/som_tools.py`: `suggest_grid_size`, `train_som`, `evaluate_som_clusters`, `recluster_som`.
  * `services/knomap/tools/viz_tools.py`: `knomap_render_som_dashboard`.

---

## 3. Grid Sizing and Hyperparameter Rules

To ensure the SOM functions as a high-resolution continuous representation rather than merely a discrete quantizer, the following methodological rules must be strictly followed:

### A. Spectral Aspect Ratio (SVD / PCA Aspect Ratio)

1. Center the numeric data matrix $X \in \mathbb{R}^{N \times D}$ relative to the mean of each indicator: $\tilde{X} = X - \mu_X$.
2. Compute the Singular Value Decomposition (SVD) of $\tilde{X}$ or the eigenvalues of the covariance matrix:

   $$
   \text{Spectral Ratio} = \frac{\sigma_1}{\sigma_2} \quad \left(\text{or } \sqrt{\frac{\lambda_1}{\lambda_2}}\right)
   $$
3. The proportion between the number of columns and rows of the lattice must match this ratio:

   $$
   \frac{\text{cols}}{\text{rows}} \approx \frac{\sigma_1}{\sigma_2}
   $$

   *(Typically bounded within the interval $[0.2, 5.0]$ to prevent excessively elongated or degenerate grids).*

### B. Over-Gridding and Number of Output Layer Neurons

* **Standard Big SOM (KnoMap Engine - Recommended for scientometric profiles):**
  To thoroughly explore the scientometric data structure, prevent distinct entities from collapsing onto the same neuron, and provide high topological resolution:

  $$
  \text{Total Neurons } M \approx \mathbf{10 \cdot N}
  $$

  *(Where $N$ is the number of analyzed observations/entities).*
* **Small SOM (Compact Quantization):**
  Used for rapid executive synthesis or basic vector quantization:

  $$
  \text{Total Neurons } M \approx \mathbf{5 \cdot \sqrt{N}}
  $$

  $$
  M_{\text{Big}} \ge 10 \cdot N \quad (\text{minimum } 25 \text{ neurons})
  $$

  Recommended for continuous topological analysis, high-definition U-Matrix, and gradient detection.
* **Small SOM (Compact Clustering):**

  $$
  M_{\text{Small}} \approx 5 \cdot \sqrt{N} \quad (\text{minimum } 9 \text{ neurons})
  $$

  Used for rapid synthesis or when entities must be forced into a few representative centroids.

### C. Lattice Topology

* **Hexagonal Lattice (Mandatory):** Every interior neuron has 6 equidistant neighbors at distance 1. This eliminates the directional bias of square grids (where diagonal neighbors lie at distance $\sqrt{2}$).

### D. Epoch Protocol and Learning Parameters

* **Number of Iterations / Steps (Kohonen Rule):**
  * *Classical sequential training:* The number of iteration steps must be **at least 500 times the number of output layer neurons** ($T_{\text{steps}} \ge 500 \cdot M$).
  * *GPU-accelerated Batch training (PyTorch/CUDA in KnoMap):* 100 to 200 global convergence epochs with full-batch updates.
* **Neighborhood Function Radius ($\sigma$):**
  * **Initial radius ($\sigma_0$):** Set to half the radius or semi-axis of the output layer:
    $$
    \sigma_0 \approx \frac{1}{2} \max(\text{rows}, \text{cols}) \quad \text{or } \quad \frac{\text{rows} + \text{cols}}{4}
    $$
  * **Final radius ($\sigma_f$):** Scheduled to decay monotonically (exponentially or linearly) down to $1.0$, ensuring that in the final iterations adjustments are restricted to the Best Matching Unit (BMU) and its immediate neighbors.
* **Learning Rate ($\alpha$):**
  * **Initial value ($\alpha_0$):** Close to $1.0$ (or $0.9$ in global initialization).
  * **Final value ($\alpha_f$):** Decays smoothly down to $0.01$.
* **Synaptic Initialization:**
  * **PCA (Linear):** Neural weights are seeded along the hyperplane spanned by the first two principal components. This accelerates convergence and ensures a stable topological orientation.

---

## 4. The Analytical Visual Triad (LabSOM Standard)

Neurocomputational interpretation is not based on raw numerical tables, but on the synchronized interaction of three visual artifacts generated over the same hexagonal lattice:

```
+-------------------------------------------------------------------------------+
|                            THE LABSOM VISUAL TRIAD                            |
+-------------------------------------------------------------------------------+
|  1. U-MATRIX (Ultsch)       2. COMPONENT PLANES           3. META-CLUSTERING  |
|     (Topography / Borders)     (Gradients per variable)      (K Partition)    |
|                                                                               |
|      [RED]     = High dens.    [RED]   = > Mean              [Cat. Color 1]   |
|      (Clusters / Valleys)      [YELL.] = Average             [Cat. Color 2]   |
|      [YELL.]   = Borders       [GREEN] = < Mean              [Cat. Color 3]   |
|      (Low dens. / Ridges)                                                     |
+-------------------------------------------------------------------------------+
```

### 1. Unified Distance Matrix (U-Matrix)

* **Algorithm:** For each neuron $j$, computes the average Euclidean distance to its contiguous radius-1 neighbors:
  $$
  U_j = \frac{1}{|V_j|} \sum_{k \in V_j} \| W_j - W_k \|_2
  $$
* **Canonical LabSOM Color Convention:**
  * **Red:** Minimal inter-neuronal distances. Indicates neighboring neurons have nearly identical weight vectors $\rightarrow$ **High data density zones (cluster cores)**.
  * **Yellow:** Maximal inter-neuronal distances. Indicates a sharp jump in weight vectors $\rightarrow$ **Dividing boundaries / data gaps / topological ridges**.
  * **Red $\rightarrow$ Orange $\rightarrow$ Yellow Gradient:** Continuous topography of the performance landscape.

### 2. Component Planes

* **Purpose:** Display the distribution of weight values $W_{j, d}$ for each dimension $d \in \{1, \dots, D\}$ across the entire lattice. Exactly $D$ spatially aligned heatmaps are generated.
* **LabSOM Divergent Palette:**
  * **Yellow:** Reference point (corpus mean or median).
  * **Green:** Below-average values (performance below the national or disciplinary mean).
  * **Red:** Above-average values (outstanding performance or high impact).
* **Visual Covariance Diagnosis and Interpretation:**
  * **Positive correlation:** Two maps with identical spatial color distributions (e.g., red in the same quadrant) indicate strongly correlated indicators.
  * **Orthogonality / Trade-offs:** Zones where one indicator is green while another is red reveal asymmetric profiles (e.g., high volume but low normalized citation impact).

### 3. Two-Stage Clustering Map (Vesanto & Alhoniemi, 2000 Methodology)

* **Foundation:** To avoid noise inherent in individual data points, clustering is not applied to raw data, but to the **reference vectors (weights $W$) of the trained neurons**.
* **Procedure:**
  1. Apply Agglomerative Hierarchical Clustering (Ward or Complete Linkage) or $k$-means to the weight matrix $W \in \mathbb{R}^{M \times D}$.
  2. Evaluate partition quality for $K \in [2, K_{\max}]$ using the **Silhouette coefficient** ($s$), complemented by the Davies-Bouldin index (minimum) and Calinski-Harabasz index (maximum).
  3. Select the partition $K^*$ that maximizes the mean Silhouette coefficient.
  4. Color each hexagon with a qualitative/categorical hue corresponding to its neuron's cluster (KnoMap golden-angle HSL palette).
  5. Each entity projected onto its Best Matching Unit (BMU) inherits that neuron's cluster label.

### 4. Standard Label Mapping and Legibility Principle for Large Matrices

* **Standard Label Mapping:** Each evaluated entity (country, university, discipline, or author) is projected onto its winning neuron (BMU) on the hexagonal grid and displayed as a centered text label within the cell.
* **Legibility Principle for Large Matrices:**
  When the training matrix is large ($N > 40$ observations or multiple entities sharing the same BMU), **hexagons must never be overcrowded with overlapping text that renders the map unreadable**.
  * **Visual Quota Rule:** Draw a reasonable, legible number of labels (typically at most 1 to 2 names per winning neuron, or select the top 30 to 50 most prominent entities in the corpus by volume or impact).
  * **Interactive Access:** In KnoMap, the map retains all entities in memory for exploration via hover *tooltips* or through the label toggle/filter button (`🏷️ Labels`), keeping the visual map clean.

---

## 5. Scientometric Evaluation Methodological Workflow

To apply this methodology to any institutional, disciplinary, or geographic corpus:

### Step 1: Indicator Selection and Curation

Configure a balanced multidimensional battery covering the 4 cardinal axes of scientific performance:

1. **Volume / Capacity:** Total document output or fractional share (*Share %*).
2. **Normalized Impact and Visibility:**
   * CNCI (*Category Normalized Citation Impact*) or FWCI (*Field-Weighted Citation Impact*), where the world average is $1.0$.
   * *Average Percentile* (mean percentile in citation rankings).
3. **Scientific Excellence:**
   * *% Documents in Top 1%* (international elite).
   * *% Documents in Top 10%* (high-impact research).
   * *% Documents in Q1 Journals* (top-quartile publication).
4. **Collaboration and Linkage:**
   * *% International Collaboration*.
   * *% Industry Collaboration* (productive sector linkage).
   * *% Domestic / Institutional Collaboration*.

### Step 2: Variable Normalization

* Primarily apply division by the maximum, or use $z$-score standardization or range scaling depending on dispersion, ensuring that absolute volume indicators (e.g., thousands of papers) do not distort Euclidean distances relative to percentage or normalized ratio indicators.

### Step 3: Execution and Topological Validation

* Execute training with PCA initialization and hexagonal lattice under the SVD ratio $\sigma_1 / \sigma_2$ and $20N\text{--}30N$ over-gridding.
* **Diagnostic Metrics:**
  * **Mean Quantization Error (QE):** Mean Euclidean distance between each data vector and its BMU weight vector ($\frac{1}{N} \sum \|x_i - W_{\text{bmu}(i)}\|$). Evaluates fitting fidelity.
  * **Topological Error (TE):** Proportion of data vectors whose first and second BMUs are not adjacent neurons on the lattice. Evaluates continuous topology preservation ($TE < 0.05$ is desirable).

### Step 4: Profile Characterization and Pole Detection

When writing the scientometric diagnosis derived from the network:

* **Peer Identification:** Entities falling within the same lattice cluster share a homogeneous qualitative profile.
* **Singular Profiles ($|C_k| = 1$):** Isolated entities that constitute the sole member of their cluster (e.g., highly specialized institutions or methodological outliers).
* **Poles of Excellence:** Identify which quadrants of the lattice simultaneously concentrate red hues in CNCI/FWCI, Top 1%, and Q1, and describe the combination of causal drivers (e.g., traction via international collaboration vs. industry collaboration).

---

## 6. MCP Invocation Protocol (`knomap-som-engine`)

When the user needs to size, train, or calibrate a SOM using ecosystem services:

### 1. Optimal Grid Sizing

Invoke `knomap-som-engine -> suggest_grid_size` passing the data matrix:

* Returns the SVD spectral aspect ratio ($\sigma_1 / \sigma_2$).
* Provides both Big SOM ($10N$ or $20N$) and Small SOM ($5\sqrt{N}$) recommendations with hexagonal topology.

### 2. Model Training

Invoke `knomap-som-engine -> train_som` with:

* `data`: Normalized numeric matrix.
* `labels`: List of institution, area, or author names.
* `rows` and `cols`: Obtained from `suggest_grid_size`.
* `method`: `"batch"` (PyTorch CUDA GPU) or `"sequential"`.
* `init`: `"pca"` (recommended) or `"random"`.
* `iterations`: 100–200 for batch.
* `clustering_algorithm`: `"kmeans"` or `"hierarchical"`.
* `n_clusters`: Preliminary initial value.
* `output_state_path`: (Optional but recommended for the dashboard) JSON file path within the Workspace to persist the state (e.g., `./reports/som_state.json`).
* `indicator_names`: (Optional) Variable/column names for the dashboard component planes.

### 3. Optimal K Calibration

Invoke `knomap-som-engine -> evaluate_som_clusters` passing the neural weight vectors returned by training:

* Explores $K \in [2, K_{\max}]$ computing Silhouette, Davies-Bouldin, and Calinski-Harabasz scores.
* Recommends the $K^*$ that maximizes partition consensus.

### 4. Hot Cluster Reassignment

Invoke `knomap-som-engine -> recluster_som` passing the weights and the new $K^*$:

* Instantly reclassifies all hexagons without retraining the neural network.

### 5. Official KnoMap Visual Dashboard Generation

Invoke `knomap-som-engine -> knomap_render_som_dashboard` (or `render_knomap_som_dashboard` in `viz_tools.py`):

* Generates the standalone interactive HTML artifact featuring KnoMap's official graphical representation:
  * **Flat-topped Hexagonal Lattice** with black topological boundaries between clusters and the LabSOM palette.
  * **Cluster Badges** computed at the geometric medoids of each group.
  * **Unit Labels** with density filtering for large matrices (`max_labels_per_neuron`).
  * **Cluster Profile Radar** in the upper-right corner comparing the cluster's multidimensional profile against analyzed units.
  * **2x3 Component Planes Grid** with the LabSOM Green-Yellow-Red palette and continuous colorbars with Max, Mean, and Min ticks.

---

## 7. Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Using rectangular or square topology**
  Configuring the lattice as an orthogonal grid. In a square grid, the 4 diagonal neighbors are at distance $\sqrt{2} \approx 1.414$ compared to the 4 axial neighbors at distance $1.0$, introducing artificial geometric asymmetry.
  **Solution:** Always use *flat-topped* hexagonal topology, where all 6 immediate neighbors are strictly equidistant.
- ❌ **Anti-pattern 2: Under-sizing the grid (Small SOM for institutional profiles)**
  Using small grids ($5\sqrt{N}$) to model institutional profiles or bibliographic sources. This causes qualitatively distinct entities to collapse onto the same neuron.
  **Solution:** Always apply the **standard Big SOM ($M \approx 10N$ neurons)** with SVD spectral aspect ratio, allowing the SOM to act as a high-resolution continuous topological space.
- ❌ **Anti-pattern 3: Training on heterogeneous variables without prior standardization (Z-score)**
  Feeding raw volume indicators (e.g., $10,000$ documents) directly alongside normalized impact indicators (e.g., $\text{FWCI} = 1.25$ or $\text{CNCI} = 1.10$). Document variance will absorb 99% of the Euclidean distance calculation, nullifying qualitative impact.
  **Solution:** Center and standardize each indicator ($z = \frac{x - \mu}{\sigma}$) or normalize before SVD calculation and training.
- ❌ **Anti-pattern 4: Overcrowding text labels in the visualization**
  Attempting to print all 50 or 100 entity names simultaneously over hexagons without density filters, causing an unreadable overlap.
  **Solution:** Apply `max_labels_per_neuron = 1` or `2`, display labels only for priority entities, or use interactive font scaling controls in the dashboard.
- ❌ **Anti-pattern 5: Violating File-Output First with neural weights**
  Dumping the $[M \times D]$ weight matrix with thousands of floats into the LLM response.
  **Solution:** Persist the model and HTML dashboard to local files (`./reports/som_dashboard.html`), returning only the quantization metrics ($Q_e$, $T_e$), Silhouette score, and artifact link.

---

## 8. Fundamental Bibliographic References

When the user requests formal foundations or bibliographic justification, cite the following canonical works:

1. **Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025).** Redes neuronales autoorganizadas y mapeos de la ciencia. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 271–292). UNAM, Instituto de Investigaciones Bibliotecológicas y de la Información. ISBN-e: 978-607-642-193-2.
2. **Villaseñor-García, E. A., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2017).** Multiparametric characterization of scientometric performance profiles assisted by neural networks: A study of Mexican higher education institutions. *Scientometrics*, 110(1), 77–104. https://doi.org/10.1007/s11192-016-2166-0
3. **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** Neural longitudinal mapping of multidimensional performance profiles of Latin American universities. *Iberoamerican Journal of Science Measurement and Communication*, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92
4. **Lozano-Díaz, I. A. (2021).** *Metodología neurocomputacional para el análisis de perfiles cienciométricos de la ciencia mexicana* (Tesis doctoral). Universidad Nacional Autónoma de México.
5. **Sotolongo-Aguilar, G., Guzmán-Sánchez, M. V., & Carrillo-Calvet, H. (2002).** ViBlioSOM: Visualización de información bibliométrica mediante el mapeo autoorganizado. *Revista Española de Documentación Científica*, 25(4), 477–484. https://doi.org/10.3989/redc.2002.v25.i4.281
6. **Vesanto, J., & Alhoniemi, E. (2000).** Clustering of the Self-Organizing Map. *IEEE Transactions on Neural Networks*, 11(3), 586–600. https://doi.org/10.1109/72.846731
7. **Ultsch, A. (2003).** The U-Matrix as visualization for projections of high-dimensional data. *Proceedings of the 11th IFCS Biennial Conference*, 283–290.
8. **Kohonen, T. (2013).** Essentials of the Self-Organizing Map. *Neural Networks*, 37, 52–65. https://doi.org/10.1016/j.neunet.2012.09.018
