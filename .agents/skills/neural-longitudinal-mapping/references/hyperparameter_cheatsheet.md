# Longitudinal Hyperparameters and Calibration Cheatsheet

This quick reference guide provides exact calibration tables and calculation rules for parameterizing longitudinal SOM networks based on the methodology of **Jiménez-Andrade et al. (2024)**.

---

## 1. Calibration Table by Grid Size

The Gaussian neighborhood radius ($\sigma$) depends directly on the average grid dimension:
$$\bar{D} = \frac{\text{rows} + \text{cols}}{2}$$

| Grid Dimensions ($R \times C$) | $\bar{D}$ | $\sigma_{\text{base}} = \frac{1}{2} \bar{D}$ | $\sigma_{\text{refine}} = \frac{1}{8} \bar{D}$ | Base Epochs | Refinement Epochs | $\alpha_0$ | $\alpha_{\text{refine}}$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$8 \times 12$** | 10.0 | **5.00** | **1.250** | 1000 | 200 | 0.9 | 0.1 |
| **$10 \times 20$** *(Canonical Paper)* | 15.0 | **7.50** | **1.875** | 1000 | 200 | 0.9 | 0.1 |
| **$12 \times 18$** | 15.0 | **7.50** | **1.875** | 1000 | 200 | 0.9 | 0.1 |
| **$14 \times 24$** | 19.0 | **9.50** | **2.375** | 1200 | 250 | 0.9 | 0.1 |
| **$16 \times 30$** | 23.0 | **11.50** | **2.875** | 1500 | 300 | 0.9 | 0.1 |

---

## 2. Data Normalization Rules

1. **Performance and Ranking Indicators (0 to 100):**
   - If indicators are already bounded within the standard $[0, 100]$ scale (e.g., normalized THE, QS, Leiden, or InCites sub-scores), **no additional rescaling should be applied**. Preserving the natural range facilitates direct visual interpretation of excellence (red) and lagging (green) zones.
2. **Co-occurrence / Bibliometric Frequency Matrices:**
   - For co-authorship or co-word networks, apply **cosine normalization (Salton)** or **association strength (Inclusion)** to bound similarity within $[0, 1]$ prior to training.
3. **Heterogeneous Metrics with Disparate Scales:**
   - When combining indicators with different units (e.g., budget in USD vs. paper counts vs. impact percentage), apply column-wise **Min-Max Scaling** to map all variables to $[0, 100]$ before assembling the longitudinal sequence.

---

## 3. Diagnostic Criteria and Result Interpretation

### Macro Level (Chromatic Gradients Across Dimensions)
- **Increasing dominance of red color:** Systemic collective improvement in the indicator.
- **Persistence of green zones:** Structural gaps that did not narrow over the analyzed period.
- **Visual correlation between dimensions:** If two component planes exhibit identical coloring patterns (e.g., Teaching and Research), this indicates high structural covariance in the analyzed set.

### Meso Level (Cluster Dynamics - Vesanto)
- **Cluster Splitting:** A unified group in $T_{t-1}$ subdivides in $T_t$. Diagnosis: *Profile differentiation*; subsets of entities adopted divergent development strategies.
- **Cluster Merging:** Entities from distinct clusters in $T_{t-1}$ group under the same cluster in $T_t$. Diagnosis: *Profile homogenization*; convergence in performance patterns.

### Micro Level (Trajectories and Singular Profiles)
- **Displacement to a contiguous cluster:** Gradual profile adjustment without abrupt discontinuities.
- **Cross-quadrant jump to an opposite quadrant:** Paradigm shift or major institutional restructuring.
- **Singular Profile ($|C_k| = 1$):** Entity isolated in its own cluster. This is typically a **transient** condition over time (in earlier or later periods it usually associates with other peers as the environment evolves).

### Synaptic Drift Quantification ($\Delta W$)
- **$\Delta W < 0.15 \times \text{range}$:** Highly stable semantic region / anchor quadrant.
- **$\Delta W > 0.40 \times \text{range}$:** High adaptive tension quadrant; intense reconfiguration of profiles.
