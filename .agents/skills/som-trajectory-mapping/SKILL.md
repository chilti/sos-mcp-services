---
name: som-trajectory-mapping
description: >-
  Expert in State-Space Trajectory Mapping using Kohonen Self-Organizing Maps (SOM), Centered Moving Average (CMA) preprocessing, continuous interpolation via parametric cubic splines, multi-entity extension in KnoMap (maximum 5 simultaneous entities in visualization), temporal inflection point detection, community maturation phases, and metric paradox diagnosis in scientometric evolution (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2025). Respond and label outputs in the user's language.
---

# SOM Trajectory Mapping: State-Space Trajectory Mapping

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Purpose and Theoretical Foundation

This skill formalizes and executes the **Multidimensional Profile Trajectory Mapping** technique, developed to track and visualize the continuous temporal evolutionary orbit of scientific entities (institutions, countries, or disciplinary fields) across extended annualized time series (20 to 50 years) projected onto a single Kohonen Self-Organizing Map.

The methodology is grounded and validated in:

> **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** *Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA*. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (Colección Metría de la Información y del Conocimiento Científico, pp. 293–313). Instituto de Investigaciones Bibliotecológicas y de la Información (IIBI), Universidad Nacional Autónoma de México. ISBN-e: 978-607-642-193-2.
>
> **Jiménez-Andrade, J. L. (2023).** *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). Universidad Nacional Autónoma de México.

### Complementarity with Neural Longitudinal Mapping
* **Neural Longitudinal Mapping ([`neural-longitudinal-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md)):** Generates a discrete sequence of spatially chained maps (Warm-Start). It is optimal for comparing **large systems of many simultaneous entities** across a few windows or periods (e.g., 3 to 5 decades or 5-year windows).
* **Trajectory Mapping ([`som-trajectory-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md)):** Models the continuous annual trajectory via **smooth state-space curves** over a single high-resolution map, enabling detailed inspection of inflection points and dynamics for a focal entity or a select peer/competitor group.

---

## 2. Dependencies and Value Chain (From Harvest to SOM)

This skill orchestrates continuous temporal evolution in latent space and operates on a longitudinal matrix of annual entity series smoothed with a Centered Moving Average (CMA) in the Workspace (`./matrices/series_cma_som.parquet`):

* **Upstream Skills (Annual Longitudinal Series Generation in the Workspace):**
  * **Option A (Standard from harvested `./corpus.parquet`): `tlachia-metrics-engine`** (`scripts/tlachia_metrics_cli.py annual-series --level ... --cma-window 3`): Computes year-by-year the **35+ scientometric indicators without truncating columns** for each entity and applies Centered Moving Average smoothing (3- or 5-year CMA):
    ```bash
    /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py annual-series \
      --input ./corpus.parquet \
      --level institution \
      --min-docs 2 \
      --cma-window 3 \
      --output ./matrices/series_cma_som.parquet
    ```
  * **Option B (TlachIA Metrics `.zip` packages): `tlachia-metrics-handler`**.
  * **Option C (Clarivate InCites annual series): `scientometrics-incites-expert`** (`get_incites_temporal_evolution`).
  * `som-methodological-expert`: Provides SVD spectral calibration, continuous over-gridding ($20N\text{--}30N$), and LabSOM chromatic rules.
* **Workspace-First CLI Execution of this Skill (`scripts/som_trajectory_cli.py`):**
  ```bash
  # Trains over the full universe of entities and traces splines for up to 5 focal entities
  /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/scripts/som_trajectory_cli.py \
    --input ./matrices/series_cma_som.parquet \
    --top-entities 5 \
    --indicator-cols "num_documents,cites_per_doc,h_index,fwci_avg,avg_percentile,pct_top_10,pct_oa,pct_international" \
    --html-out ./reports/som_trajectories.html \
    --png-es ./reports/som_trajectories_es.png \
    --png-en ./reports/som_trajectories_en.png \
    --json-out ./reports/som_trajectories.json \
    --lang en
  ```
* **Associated Software Tools:**
  * `scripts/som_trajectory_cli.py`: Standalone CLI to project continuous trajectories from `.parquet`/`.csv`/`.json`.
  * `services/knomap/tools/viz_tools.py`: `knomap_render_som_dashboard` (SVG rendering of Catmull-Rom splines over a hexagonal grid).
  * `services/knomap/tools/som_tools.py`: Network training and BMU coordinate projection.

---

## 3. Reusing `som-methodological-expert`

Trajectory Mapping **directly reuses** the methodological pillars of [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md):
1. **Multidimensional State Space:** Each temporal observation of an entity is a vector $x_t \in \mathbb{R}^n$ defined by the same $n$ normalized indicators (CNCI/FWCI, Top 1%, Top 10%, Q1, Average Percentile, collaborations).
2. **Grid Sizing and Geometry:** SVD spectral aspect ratio ($\sigma_1 / \sigma_2$), hexagonal topology, and continuous over-gridding ($20N\text{--}30N$ or Big SOM $10N$).
3. **The LabSOM Visual Triad Canvas:** Trajectories are plotted superimposed over:
   * **U-Matrix:** Reveals which topological barriers (yellow ridges) or high-density regions (red valleys) entities crossed throughout their history.
   * **Component Planes:** Allow visual auditing of which specific indicators (red zones > mean or green zones < mean) attracted or slowed the trajectory in each period.

---

## 4. Multi-Entity Extension in KnoMap and Visual Legibility Rule

In **KnoMap**, the original formulation (initially designed for a single entity) was extended to enable **comparative benchmarking of multiple simultaneous trajectories**. However, to prevent visual legibility collapse, the following design principle is enforced:

```
+-------------------------------------------------------------------------------+
|               DECOUPLING PRINCIPLE: TRAINING VS. VISUALIZATION                |
+-------------------------------------------------------------------------------+
|  1. TRAINING PHASE (Full Sampling):                                           |
|     - MANY entities (e.g., 20 to 100 institutions or disciplines) can be      |
|       mapped and included to properly populate the state space and guarantee  |
|       a SOM lattice representative of the entire system.                      |
|                                                                               |
|  2. VISUALIZATION AND ANALYSIS PHASE (Selective Filter):                      |
|     - GOLDEN RULE: MAXIMUM 5 ENTITIES simultaneously on the map.              |
|     - Reason: Tracing dozens of splines with loops, knots, and reversals      |
|       fills the map with visual "spaghetti," destroying interpretability.     |
|     - Selecting direct peer groups is recommended (e.g., UNAM vs IPN vs       |
|       UAM vs Cinvestav; or Mathematics vs Computer Science vs Engineering).   |
+-------------------------------------------------------------------------------+
```

### Standard Label Mapping vs. Spline Tracing for Trajectories
* **Standard Label Mapping:** In [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md) and [`neural-longitudinal-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md), labels are statically projected onto their respective winning neurons (BMUs) on the plane.
* **Spline Tracing (Trajectories):** In this skill, in addition to point labels, **continuous (Catmull-Rom) splines** are mapped connecting the intertemporal sequence of winning neurons for each entity across years, complemented by circular waypoints and directional arrows.
* **Legibility Rule for Large Training Matrices:**
  If the matrix used to train the SOM is large (dozens or hundreds of entities included to ensure the network faithfully represents the entire state space), **a reasonable number of static labels should be drawn** (e.g., limiting labels per cell to 1 or 2, or selecting only the most prominent entities in the corpus) so they can be read clearly without overlapping.
* **Selecting Trajectories of Special Interest:**
  For temporal trajectories, **we generally draw only a few (at most 5 entities of special interest)**, such as leading institutions or direct competitors within a reference group (e.g., UNAM, IPN, UAM, Cinvestav). Drawing too many splines would saturate the lattice with intersecting curves, nullifying the diagnostic value of the map.

### Encoding Guidelines for Multiple Trajectories:
* **Contrasting Curve Palette:** Assign a distinct, solid color to each of the 1 to 5 active entities (avoiding confusion with the divergent red-yellow-green background component palette).
* **Directionality:** Indicate the temporal vector with arrows or numerical year markers at key nodal points (e.g., start of a decade or inflection points).
* **Interactivity in KnoMap:** Allow dynamic toggling of entities on and off via a layer selector (*Entity Toggles*).

---

## 5. Step-by-Step Mathematical and Algorithmic Protocol

```
+-------------------------------------------------------------------------------+
|                          TRAJECTORY MAPPING PIPELINE                          |
+-------------------------------------------------------------------------------+
| 1. Annualized Time Series       x_t^e ∈ R^n  (t = 1980, ..., 2022; e ∈ Ents)  |
|               ↓                                                               |
| 2. Centered Smoothing           y_t^e = ∑_{r=-s}^s a_r x_{t+r}^e (zero lag)   |
|               ↓                                                               |
| 3. SOM Projection               p_t^e = (u_t^e, v_t^e) on hexagonal lattice   |
|               ↓                                                               |
| 4. Cubic Splines                parametric u^e(t), v^e(t) [4(N-1) equations]  |
|               ↓                                                               |
| 5. Visual Filtering             Render max. 5 simultaneous entities           |
|               ↓                                                               |
| 6. Scientometric Diagnosis      Inflections, Maturation, Paradoxes & Converg. |
+-------------------------------------------------------------------------------+
```

### Step 1: Preprocessing with Centered Moving Averages (CMA)
Raw annual measurements in scientometrics contain stochastic fluctuations and short-term noise.

* **Centered Moving Average Calculation:**
  $$y_t = \sum_{r=-s}^{s} a_r x_{t+r}$$
  where $s$ is the half-width of the window and $a_r$ are the weighting coefficients ($\sum a_r = 1$; if $a_r$ is constant, it is a simple moving average; if it decays with $|r|$, it is weighted).
* **Justification over Conventional Moving Averages:**
  * *Backward-looking* averages introduce an **artificial temporal lag** in peaks and troughs.
  * *Forward-looking* averages cause an **artificial lead**.
  * The **centered moving average** preserves the inertia and trend of the historical series **with zero phase shift**, keeping critical temporal points synchronized.
* **Boundary Treatment (Boundary Condition):**
  At the initial and final edges where the window is incomplete:
  $$y_1 = x_1, \quad y_2 = \frac{x_1 + x_2}{2}, \quad \dots \quad \text{and symmetrically at } y_N$$

### Step 2: Orbit Projection onto the SOM Lattice
1. Each smoothed annual vector $y_t^e$ of entity $e$ is projected onto the trained SOM neural network, determining its winning neuron (BMU):
   $$\text{BMU}^e(t) = \arg\min_j \| y_t^e - W_j \|_2$$
2. The planar coordinates $(u_t^e, v_t^e)$ associated with the BMU on the hexagonal lattice are extracted.

### Step 3: Continuous Tracing with Parametric Cubic Splines
To connect the $N$ chronological points $(u_t^e, v_t^e)$ with a smooth curve in the plane:
* **The Complex Curve Problem:** Performance trajectories are not single-valued mathematical functions $y = f(x)$, because a discipline or university may improve, stagnate, regress, or loop in the plane.
* **Decoupled Parametric Formulation in $t$:**
  A collection of $N-1$ cubic polynomials is interpolated for each Cartesian axis with respect to the temporal parameter $t$:
  $$u_i(t) = a_{ui} + b_{ui}t + c_{ui}t^2 + d_{ui}t^3$$
  $$v_i(t) = a_{vi} + b_{vi}t + c_{vi}t^2 + d_{vi}t^3$$
  for $i \in \{1, 2, \dots, N-1\}$.
* **Linear System Solution:**
  Two independent systems of $4(N-1)$ linear equations are constructed and solved, ensuring:
  1. Exact interpolation at waypoints: $u_i(t_i) = u_t$, $u_i(t_{i+1}) = u_{t+1}$.
  2. First-order continuity (smooth transition velocity): $u'_i(t_{i+1}) = u'_{i+1}(t_{i+1})$.
  3. Second-order continuity (smooth curvature): $u''_i(t_{i+1}) = u''_{i+1}(t_{i+1})$.
  4. Natural or periodic boundary conditions at the endpoints.

---

## 6. Scientometric Trajectory Interpretation Framework

When visually analyzing the path of curves across the component planes and U-Matrix, the agent must evaluate the following milestones:

### A. Inflection and Takeoff Point Detection
* Locate the exact years along the trajectory where the curve changes quadrant or accelerates its tangent vector.
* *Canonical example (Clinical Medicine in Mexico):* Between 1980 and 2002 it orbited in low relative-impact quadrants; starting in **2003** it underwent a sharp inflection toward the upper-right corner of the map, initiating sustained exponential growth.

### B. Comparative Peer Analysis (Convergence vs. Divergence)
When plotting 2 to 5 simultaneous entities:
* **Parallel / Convergent Trajectories:** Entities transitioning toward the same regions of the lattice, indicating policy homogenization and similar performance.
* **Divergent Trajectories:** Entities that started in the same zone in the 1980s but whose curves separate radically toward different quadrants (e.g., one toward industry collaboration and another toward Q1 internationalization).

### C. Indicator Traction Force Analysis
By superimposing curves over component planes:
* **Internationalization Traction:** Advancement toward red zones of *% International Collaboration*.
* **Productive Linkage Traction:** Displacement toward red regions of *% Industry Collaboration*.
* **Upper-Quartile Migration:** Advancement toward the red pole of *% Documents in Q1 Journals*.

### D. Auditing Metric Paradoxes: CNCI vs. Average Percentile
One of the most critical diagnoses the agent must issue when auditing trajectories:
* **Unbounded Metric (CNCI / FWCI):** An arithmetic mean with no upper bound. A tiny set of hyper-cited publications (e.g., multicenter clinical trials or global reports) can drive the overall average above the world mean ($> 1.0$), creating an illusion of widespread excellence.
* **Bounded Metric (Average Percentile $\le 100$):** Hyper-cited articles saturate at percentile 100 and cannot pull the average further. If the entity's *Average Percentile* sits below 50 (e.g., 36), one concludes with statistical rigor that **the bulk of the scientific community still produces papers in low citation percentiles**, relying on an elite niche.

### E. Identifying the Community Maturation Phase
* **Phase 1 (Isolated Elite):** An increase is observed in % Top 1% and CNCI, but % Top 10% remains stagnant below 10%. Excellence output is confined to a few authors.
* **Phase 2 (Full Community Maturation):** Occurs when the trajectory crosses and sustains the **% Documents in Top 10% indicator above 10% (world average)**. Diagnosis: *The academic community has reached institutional critical mass, democratizing the capacity to publish with high relative impact*.

---

## 7. Integration with MCP and Ecosystem Scripts

To orchestrate a trajectory study from the analytical environment:

1. **Temporal Extraction and Smoothing:**
   * Invoke `knomap-som-engine -> get_incites_temporal_evolution` passing the entities of interest (1 to 5 selected) and the list of years.
   * Apply the 3- or 5-period centered moving average over the numeric indicators.
2. **Grid Training or Loading:**
   * Use `knomap-som-engine -> train_som` or load the matrix trained in `som-methodological-expert` (which may contain the entire universe of entities so the lattice is representative).
3. **Trajectory and Spline Generation:**
   * Invoke `knomap-som-engine -> knomap_render_som_dashboard` (or `render_knomap_som_dashboard` in `services/knomap/tools/viz_tools.py`), passing the list of trajectories in `selected_trajectories` (maximum 5 entities). The generator automatically computes continuous Catmull-Rom cubic splines, circular waypoints, and directional SVG markers over KnoMap's native hexagonal grid.
4. **Diagnostic Report Issuance:**
   * Break down historical stages (pre-takeoff, takeoff, consolidation), temporal inflection points, metric paradox resolution, and dynamic comparisons among selected competitors.

---

## 8. Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Plotting more than 5 simultaneous entities in the visualization**  
  Projecting trajectories for 10, 20, or more institutions or countries at the same time. This creates a "spaghetti effect" where curves cross chaotically, hiding inflection points and ruining legibility.  
  **Solution:** Although the SOM can be trained with 100 entities so the grid is representative, **at most 5 entities should be visualized in the dashboard** (comparable peer groups or direct competitors).
- ❌ **Anti-pattern 2: Plotting trajectories with raw unsmoothed data**  
  Using pure unfiltered annual values. Bibliometric time series exhibit annual stochastic noise (e.g., a special conference year generating artificial spikes) that produces sharp breaks and zigzagging trajectories without structural meaning.  
  **Solution:** Always apply a 3- or 5-period Centered Moving Average (CMA) or exponential smoothing (ECMA-3 / ECMA-5) before computing splines.
- ❌ **Anti-pattern 3: Connecting annual points with rigid straight segments**  
  Joining annual winning neurons (BMUs) with orthogonal polylines or straight lines. The SOM latent space is a continuous manifold; straight lines break the topology of motion.  
  **Solution:** Always use continuous parametric cubic splines (Catmull-Rom) with circular waypoints and directional SVG markers.
- ❌ **Anti-pattern 4: Printing every annual label along the curve**  
  Attempting to label every single year (e.g., 1990, 1991, 1992... 2025) along the spline, cluttering the hexagonal lattice.  
  **Solution:** Label only the endpoints (start and end) and major temporal inflection points, letting circular waypoints represent intermediate steps.
- ❌ **Anti-pattern 5: Violating File-Output First**  
  Printing full spline and waypoint coordinates as a massive JSON dump in the chat.  
  **Solution:** Generate the standalone dashboard in `./reports/som_trajectories.html` and return an executive summary with the artifact link.

---

## 9. Canonical References

1. **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 293–313). UNAM, Instituto de Investigaciones Bibliotecológicas y de la Información. ISBN-e: 978-607-642-193-2.
2. **Jiménez-Andrade, J. L. (2023).** *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). Universidad Nacional Autónoma de México.
3. **Chatfield, C., & Xing, H. (2019).** *The Analysis of Time Series: An Introduction with R*. CRC Press, Taylor & Francis Group. https://doi.org/10.1201/9781351259446
4. **Gorbea-Portal, S. (2016).** Una nueva perspectiva teórica de la bibliometría basada en su dimensión histórica y sus referentes temporales. *Investigación Bibliotecológica: archivonomía, bibliotecología e información*, 30(70), 11–16. https://doi.org/10.1016/j.ibbai.2016.10.001
5. **Garfield, E. (1994).** Scientography: Mapping the tracks of science. *Current Contents: Social & Behavioural Sciences*, 7(45), 5–10.
