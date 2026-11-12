---
name: neural-longitudinal-mapping
description: >-
  Expert in Neurocomputational Longitudinal Mapping with Kohonen Self-Organizing Maps (SOM) and intertemporal Warm-Start chaining (Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2025; Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet, 2024). Models the temporal evolution of multidimensional institutional performance profiles and sequences of bibliometric matrices across 3 levels: Macro (trends, Delta % growth rates, and components), Meso (cluster dynamics: splitting vs. merging), and Micro (entity displacements, singular profiles, and community maturation), quantifying synaptic drift tension (\Delta W) and cohort turnover. Respond and label outputs in the user's language.
---

# Neural Longitudinal Mapping (SOM Warm-Start Chaining)

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Epistemological and Theoretical Foundation

This skill implements and orchestrates the scientific methodology of **Neural Longitudinal Mapping with Kohonen Self-Organizing Maps (SOM)**, developed and consolidated in the following canonical works:

> **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** *Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA*. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (Colección Metría de la Información y del Conocimiento Científico, pp. 293–313). Instituto de Investigaciones Bibliotecológicas y de la Información (IIBI), Universidad Nacional Autónoma de México. ISBN-e: 978-607-642-193-2.
>
> **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** *Neural longitudinal mapping of multidimensional performance profiles of Latin American universities*. **Iberoamerican Journal of Science Measurement and Communication**, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92
>
> **Jiménez-Andrade, J. L. (2023).** *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). Universidad Nacional Autónoma de México.

### Historical and Theoretical Context of Information Metrics
* **The Historical Dimension of Bibliometrics:** As formulated by Gorbea Portal (2016), metric studies must integrate temporal referents into their three cardinal dimensions: *descriptive or classical*, *evaluative*, and *historical*. Most existing tools only plot univariate curves or co-occurrence networks, ignoring the coupled co-evolution of multidimensional profiles.
* **Eugene Garfield's Vision (1994):** Garfield postulated that longitudinal cartography (*scientography*) is the fundamental pathway for tracking temporal footprints and dynamic relationships among research fronts and paradigm shifts.
* **Overcoming Rotational Invariance and Stochastic Drift:**
  Classical unsupervised training of an independent SOM for each time slice generates arbitrary discontinuities (rotations, mirror inversions, or quadrant translations). **Neural Longitudinal Mapping** overcomes this barrier by ensuring that all maps in the temporal sequence remain **rigidly anchored in the same spatial orientation**, so that any displacement observed in the U-Matrix or in an entity's position corresponds to a genuine transformation in its performance profile.

---

## 2. Dependencies and Value Chain (From Harvest to SOM)

This skill implements Warm-Start neurocomputational intertemporal chaining and operates on sequences of period matrices (`./matrices/periodos_som.parquet`):

* **Upstream Skills (Extraction of Period Matrices in the Workspace):**
  * **Option A (Standard from harvested `./corpus.parquet`): `tlachia-metrics-engine`** (`scripts/tlachia_metrics_cli.py period-series --level ...`): Computes the **35+ scientometric indicators without truncating columns** for each entity across consecutive windows or periods:
    ```bash
    /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-engine/scripts/tlachia_metrics_cli.py period-series \
      --input ./corpus.parquet \
      --periods "2020-2022,2023-2026" \
      --level institution \
      --min-docs 2 \
      --output ./matrices/periodos_som.parquet
    ```
  * **Option B (TlachIA Metrics `.zip` packages): `tlachia-metrics-handler`** (`02_Periodos`).
  * **Option C (Clarivate InCites reports): `scientometrics-incites-expert`**.
  * `som-methodological-expert`: **Fully inherits and reuses** the mathematical and visual foundation:
    1. **SVD Spectral Aspect Ratio:** Proportion $\text{cols}/\text{rows} \approx \sigma_1 / \sigma_2$ computed over the aggregated profile matrix.
    2. **Grid Sizing:** Hexagonal topology and empirical over-gridding ($M \approx 20N\text{--}30N$ or Big SOM $10N$) to deploy continuous topological resolution.
    3. **LabSOM Visual Triad:** Red/yellow U-Matrix, yellow-red/green divergent Component Planes, and Vesanto Meta-clustering.
* **Complementary and Downstream Skills:**
  * `som-trajectory-mapping`: Complementary technique for continuous annual trajectories of a few focal entities via splines.
  * `services/knomap/tools/viz_tools.py`: `knomap_render_som_dashboard` to generate the HTML artifact for each time slice.
* **Legibility Rule for Large Matrices:**
  * If the time-series training matrix is large ($N > 40$ entities), **draw a reasonable and legible number of labels** (prioritizing the persistent core or limiting to 1 or 2 labels per cell).

---

## 3. Warm-Start Chaining Protocol (Refinement Chaining)

The foundation rests on the **structural inertia or continuity hypothesis**: the state of science in a given year or subperiod preserves the general structure of the preceding period. Therefore:

```
+-----------------------------------------------------------------------------------+
|                        WARM-START TEMPORAL CHAINING PROTOCOL                      |
+-----------------------------------------------------------------------------------+
|  Base Period (T_1):                                                               |
|    - Global initialization (PCA)                                                  |
|    - Phase 1 (Global Ordering) + Phase 2 (Fine Refinement)                        |
|    - Base epochs (e.g., 1000 iterations) -> Optimal weights W_1*                  |
|                                                                                   |
|  Subsequent Periods (T_2, T_3, ..., T_k):                                         |
|    - 1. Initial condition: W_t^(0) = W_{t-1}* (Weights from previous period)      |
|    - 2. Disable Phase 1 (global ordering is skipped)                              |
|    - 3. Small initial neighborhood (sigma_0 ≈ 1/8 D_bar) decaying to 1.0          |
|    - 4. Small initial learning rate (alpha_0 ≈ 0.1) decaying to 0.01              |
|    - 5. Duration: Only ONE-TENTH (1/10) of base iterations                        |
|         (T_refine = 1/10 * T_base = 100 to 200 epochs)                            |
+-----------------------------------------------------------------------------------+
```

### Canonical Hyperparameter Table

For a hexagonal lattice of $R \times C$, the average size is $\bar{D} = \frac{R + C}{2}$.

| Training Phase | Epochs | Learning Rate ($\alpha$) | Neighborhood Radius ($\sigma$) | Synaptic Initialization |
| :--- | :---: | :---: | :---: | :--- |
| **Period 1: Full Training (Base $T_1$)** | **1000** | $\alpha_0 = \mathbf{0.9} \rightarrow 0.01$ | $\sigma_0 = \frac{1}{2} \bar{D} \rightarrow 1.0$ | Global (PCA) |
| **Periods $2+$: Refinement (Warm-Start $T_t$)** | **100 to 200** *(1/10 of base)* | $\alpha = \mathbf{0.1} \rightarrow 0.01$ | $\sigma = \frac{1}{8} \bar{D} \rightarrow 1.0$ | Converged weights $W_{t-1}^*$ |

---

## 4. Comprehensive Analytical Framework and Scientometric Interpretation

When interpreting and reporting the temporal sequence, the agent structures its diagnosis across the following canonical axes:

### 1. Macro Level: Systemic Evolution and Components
* **Intertemporal Growth Rates ($\Delta\%$ of the mean):** Percentage variation of the national/institutional mean in each indicator between slices.
* **Chromatic Gradient Drift:** Tracking the expansion or contraction of red zones (high performance) relative to green zones in the component planes.
* **Preservation or Rupture of Impact Quadrants:** Verifying whether the pole of excellence remains stable in a quadrant or undergoes shifts caused by disciplinary restructuring.

### 2. Cohort Dynamics and Retention
* **Intertemporal Retention Rate:** Percentage of entities active in $T_{t-1}$ that remain active in $T_t$.
* **Entrants vs. Departures:** Detection of emerging disciplines or institutions vs. those losing publication critical mass.
* **Persistent Core:** Set of actors inhabiting the network uninterruptedly throughout the entire historical series.

### 3. Meso Level: Cluster Dynamics (Vesanto)
* **Cluster Splitting:** Entities grouped together in $T_{t-1}$ that divide into separate clusters in $T_t$. Diagnosis: *Profile differentiation and specialization*.
* **Cluster Merging:** Entities from distinct clusters that converge into the same group. Diagnosis: *Homogenization or standardization of research practices*.

### 4. Micro Level: Displacements, Singular Profiles, and Maturation Diagnosis
* **Euclidean Displacement on the Lattice:** $\Delta d_i = \| \text{BMU}_i^{(t)} - \text{BMU}_i^{(t-1)} \|_2$.
* **Singular / Outlier Profiles ($|C_k| = 1$):** Entities that become completely isolated in an individual cluster due to massive volumes or disproportionate citation (e.g., *Clinical Medicine* in Mexico). **Methodological recommendation:** Treat as an outlier profile and analyze it in detail using the **Trajectory Mapping** technique ([`som-trajectory-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md)).
* **Resolving Metric Paradoxes (Unbounded vs. Bounded Metrics):**
  * *The CNCI vs. Average Percentile Paradox:* If an entity exhibits a very high CNCI (e.g., $> 1.8$, doubling the world average) but a modest *Average Percentile* (e.g., $36$ vs. the world average of $50$), the scientometric diagnosis indicates that **impact is inflated by a small number of hyper-cited outlier papers (*Black Swans* or massive health collaborations)**, while the bulk of output has low citation.
* **Community Maturation Indicator:**
  * Occurs when **% Documents in Top 10%** consistently crosses the world average ($> 10\%$). This demonstrates that the discipline has stopped relying on a few isolated elite researchers (% Top 1%) and has achieved a **community critical mass** with sustained high-quality production.

### 5. Adaptive Tension and Synaptic Drift ($\Delta W$)
Quantification of synaptic drift per neuron between contiguous slices:
$$\Delta W_j = \| W_j^{(t)} - W_j^{(t-1)} \|_2$$
Identifies which quadrants of the map concentrate the greatest structural transformations of knowledge or performance versus inert regions.

---

## 5. Utility Scripts: `neural_longitudinal_cli.py`

Location of the execution CLI script: [`scripts/neural_longitudinal_cli.py`](file://scripts/neural_longitudinal_cli.py)

```bash
# 1. Windowed time-series preparation
python neural_longitudinal_cli.py prepare \
  --input dataset.parquet \
  --entity-col university \
  --period-col year \
  --window 5 --step 5 \
  --output prepared_series.json

# 2. Warm-Start Chaining training
python neural_longitudinal_cli.py train \
  --input prepared_series.json \
  --rows 10 --cols 20 \
  --base-epochs 1000 --refine-epochs 200 \
  --output longitudinal_results.json

# 3. 3-level evolutionary and cohort analysis
python neural_longitudinal_cli.py analyze \
  --input longitudinal_results.json \
  --output dynamics_analysis.json

# 4. Structured Markdown report generation
python neural_longitudinal_cli.py report \
  --analysis dynamics_analysis.json \
  --mode external_mcp \
  --lang en \
  --output report_longitudinal.md

# 5. KnoMap Hexagonal Dashboards generation per period
# Invoke knomap_render_som_dashboard from viz_tools.py for each time slice:
# render_knomap_som_dashboard(som_state_t, output_path=f"dashboard_som_{period}.html", max_labels_per_neuron=2)
```

---

## 6. Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Independent PCA retraining in subsequent slices ($T_2, T_3, \dots$)**  
  Initializing each time period from scratch with PCA or random weights. This causes arbitrary rotations, translations, or mirror inversions of the latent space, making longitudinal trajectory comparison impossible.  
  **Solution:** Strictly apply the Warm-Start protocol: initialize $T_t$ with the converged weights from the previous period: $W_t^{(0)} = W_{t-1}^*$.
- ❌ **Anti-pattern 2: Running the full number of base epochs (1000 iterations) in refinement periods**  
  Training $T_t$ for hundreds of epochs with a large learning rate ($\alpha_0 > 0.1$), erasing the structural memory of the preceding sequence.  
  **Solution:** Warm-Start refinement duration must strictly be 1/10 of base epochs (100 to 200 epochs) with $\alpha_0 = 0.1 \rightarrow 0.01$ and radius $\sigma_0 = \frac{1}{8}\bar{D}$.
- ❌ **Anti-pattern 3: Failing to quantify synaptic drift tension ($\Delta W$)**  
  Reporting entity displacements or cluster migrations without auditing global synaptic drift $\Delta W = \|W_t - W_{t-1}\|_F$.  
  **Solution:** Always compute $\Delta W$ to verify whether the network underwent smooth accommodation or a violent structural mutation in the indicator system.
- ❌ **Anti-pattern 4: Attempting to label all entities in massive sequences**  
  In time series of 50 or 100 universities, labeling every entity in every time slice saturates the hexagons and prevents tracking migrations.  
  **Solution:** Identify the *persistent core* and singular entities, limiting labels to 1 or 2 per neuron via `max_labels_per_neuron`.
- ❌ **Anti-pattern 5: Violating File-Output First**  
  Dumping the concatenated weight matrices of all 5 periods into the LLM console.  
  **Solution:** Write results to structured files (`longitudinal_results.json` and `report_longitudinal.md`) and generate HTML dashboards for each period.

---

## 7. Bibliographic References

1. **Jiménez-Andrade, J. L., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2025).** Análisis y visualización de la evolución de perfiles cienciométricos multidimensionales con IA. En S. Gorbea Portal & M. Piña Pozas (Coords.), *La metría de la información-conocimiento y los datos en la búsqueda de evidencias científicas* (pp. 293–313). UNAM, Instituto de Investigaciones Bibliotecológicas y de la Información. ISBN-e: 978-607-642-193-2.
2. **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** Neural longitudinal mapping of multidimensional performance profiles of Latin American universities. *Iberoamerican Journal of Science Measurement and Communication*, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92
3. **Jiménez-Andrade, J. L. (2023).** *Métodos y aplicaciones de la red neuronal SOM para el análisis temporal de datos multidimensionales* (Tesis doctoral). Universidad Nacional Autónoma de México.
4. **Gorbea-Portal, S. (2016).** Una nueva perspectiva teórica de la bibliometría basada en su dimensión histórica y sus referentes temporales. *Investigación Bibliotecológica: archivonomía, bibliotecología e información*, 30(70), 11–16. https://doi.org/10.1016/j.ibbai.2016.10.001
5. **Garfield, E. (1994).** Scientography: Mapping the tracks of science. *Current Contents: Social & Behavioural Sciences*, 7(45), 5–10.
6. **Villaseñor-García, E. A., Arencibia-Jorge, R., & Carrillo-Calvet, H. (2017).** Multiparametric characterization of scientometric performance profiles assisted by neural networks: A study of Mexican higher education institutions. *Scientometrics*, 110(1), 77–104. https://doi.org/10.1007/s11192-016-2166-0
