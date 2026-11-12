# Methodological Foundation: Longitudinal Mapping with SOM

**Scientific Reference:**
> **Jiménez-Andrade, J. L., Martí-Lahera, Y., & Carrillo-Calvet, H. (2024).** *Neural longitudinal mapping of multidimensional performance profiles of Latin American universities.* **Iberoamerican Journal of Science Measurement and Communication**, 4(1), 1–16. https://doi.org/10.47909/ijsmc.92

---

## 1. The Fundamental Problem of Temporal Mapping with SOM

Kohonen Self-Organizing Maps (SOM) are unsupervised neural techniques ideal for projecting high-dimensional spaces ($D > 3$) onto a discrete two-dimensional plane (typically a hexagonal lattice). However, a direct, independent application of the SOM algorithm to successive temporal slices ($T_1, T_2, \dots, T_k$) produces inconsistent results for temporal analysis:

1. **Stochasticity and Rotational Invariance:** Given random initialization and stochastic data presentation, maps trained independently on very similar (or even identical) data adopt arbitrary orientations (90°/180° rotations or mirror inversions).
2. **Impossibility of Intertemporal Visual Comparison:** If the reference cartography rotates or permutes its thematic quadrants between year $t$ and year $t+1$, it becomes impossible to track continuous trajectories or determine whether a movement reflects a genuine transformation of the entity or an algorithmic artifact.

---

## 2. The Solution: Temporal Chaining (Warm-Start Chaining)

Standard SOM training is conceptualized in two stages:
1. **Global Ordering Phase:** With large neighborhood radii ($\sigma_0$) and high learning rates ($\alpha_0$), where the macroscopic topology of the lattice is determined.
2. **Refinement Phase:** With small neighborhood radii ($\sigma \to 1$) and small learning rates ($\alpha \ll 1$), where synaptic weight vectors are fine-tuned without altering the macroscopic orientation.

### Key Empirical Observation:
In bibliometric systems, university rankings, or research network dynamics, **entity profiles do not change chaotically or instantaneously from one year to the next**. The global distribution remains relatively stable.

Therefore:
- **Period 1 ($T_1$ - Full Training):** A complete map is trained from scratch to structure the base semantic space.
- **Subsequent Periods ($T_2 \dots T_k$ - Refinement Only):** Random initialization and the global ordering phase are completely skipped. The network at time $t$ is initialized with the converged weights from the previous period $W_{t-1}^*$, and **only the refinement phase** is executed using reduced neighborhoods and learning rates.

---

## 3. Canonical Hyperparameter Formulation

For a hexagonal lattice of dimensions $R \times C$:

$$\bar{D} = \frac{R + C}{2} \quad \text{(Average grid dimension)}$$

| Phase | Epochs | Initial Learning Rate ($\alpha$) | Initial Neighborhood Radius ($\sigma$) | Weight Initialization ($W_0$) |
| :--- | :---: | :---: | :---: | :--- |
| **Period 1 (Base)** | 1000 | $\alpha_0 = 0.9$ | $\sigma_{\text{base}} = \frac{1}{2} \bar{D} = \frac{R + C}{4}$ | Global (PCA or Random) |
| **Periods 2+ (Refinement)** | 200 | $\alpha = 0.1$ | $\sigma_{\text{refine}} = \frac{1}{8} \bar{D} = \frac{R + C}{16}$ | Weights from previous period: $W_{t-1}^*$ |

*Note on decay:* In Kohonen's sequential/online algorithm, $\sigma(t)$ and $\alpha(t)$ decay linearly or exponentially across epochs, converging to $\sigma \to 1.0$ and $\alpha \to 0.02$.

---

## 4. Three-Level Analytical Framework (Macro, Meso, Micro)

The paper introduces a rigorous methodology for interpreting the resulting temporal sequence of knowledge maps:

```
┌─────────────────────────────────────────────────────────────┐
│  MACRO LEVEL: Systemic Trends and Component Planes          │
│  - Shift of chromatic gradients (green → red)               │
│  - Regional/national homogenization or diversification      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  MESO LEVEL: Cluster Dynamics (Vesanto)                     │
│  - Cluster splitting: Profile differentiation               │
│  - Cluster merging: Profile homogenization                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  MICRO LEVEL: Individual Dynamics and Trajectories          │
│  - Euclidean displacement (Δx, Δy) on the lattice           │
│  - Identification of Singular Profiles (transient)          │
└─────────────────────────────────────────────────────────────┘
```

### Macro Level (Systemic)
- Examines the **dimension/component planes** (one heatmap per evaluated indicator, e.g., Teaching, Research, Citations).
- Enables detection of structural evolutions across the cohort (e.g., progressive dominance of high-performance zones) and regional specialization contrasts (e.g., profiles with high teaching and research vs. profiles with high citations and international impact).

### Meso Level (Cluster Dynamics)
- Applies agglomerative hierarchical clustering over neuron weights (Vesanto & Alhoniemi, 2000 methodology).
- Each cluster represents a **qualitative institutional profile**.
- **Cluster Splitting:** When entities sharing a cluster in $T_{t-1}$ separate in $T_t$, indicating **profile differentiation**.
- **Cluster Merging:** When entities from distinct clusters converge into a single cluster in $T_t$, indicating **profile homogenization**.

### Micro Level (Individual)
- Evaluates the movement of individual entities across the hexagonal grid.
- **Singular Profiles:** Entities that occupy their own cluster in isolation. Longitudinal analysis reveals their typically **transient** nature: in earlier or later years they usually share a cluster with peers as their indicators mature.

---

## 5. Quantifying Synaptic Drift ($\Delta W$)

To objectively measure the adaptive tension of the lattice between two consecutive periods $T_{t-1}$ and $T_t$, the weight vector drift per neuron $j$ is computed:

$$\Delta W_j = \| W_j^{(t)} - W_j^{(t-1)} \|_2 = \sqrt{\sum_{d=1}^D (w_{j,d}^{(t)} - w_{j,d}^{(t-1)})^2}$$

- A low $\Delta W$ value indicates a conserved, highly stable semantic region.
- A high $\Delta W$ value highlights quadrants where deep conceptual or performance restructuring occurred within the analyzed cohort.
