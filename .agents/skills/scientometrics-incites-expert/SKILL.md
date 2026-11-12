---
name: scientometrics-incites-expert
description: >-
  Comprehensive manager and expert analyst for institutional scientometric benchmarking with Clarivate InCites. Inspects unit inventories (Organizations, Locations, Researchers, WoS Categories, Publication Sources, Research Areas ESI / SDG / Topics, Funding Agencies, Patentometrics), extracts windowed multidimensional matrices (Historical vs. Recent 5-year) ready for SOM, extracts longitudinal annual series (Trend) for PathSOM with ECMA smoothing, and computes strategic growth matrices (Strategic Growth Matrix: CAGR % vs. Volume). Respond and label outputs in the user's language.
---
# Scientometrics InCites Expert: Clarivate InCites Package Manager and Benchmarking

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Purpose and Activation

This skill activates when the user provides data, tabular reports, or exported packages from **Clarivate InCites Benchmarking & Analytics** (individual `.csv`, `.xlsx` files, or structured `.zip` archives) and needs to:

1. **Inspect and Validate the InCites Inventory:** Identify available analytical units (`Organizations`, `Locations`, `Researchers`, `WoS Categories`, `Publication Sources`, `Research Areas ESI / SDG / Topics`, `Funding Agencies`, `Patentometrics`), covered temporal windows, and present indicator schemas.
2. **Extract Multidimensional Matrices for SOM:** Extract clean $[N \times D]$ numeric profiles of specific entities, distinguishing between:
   * **Recent Window (5 years, e.g., 2021–2025):** For current status diagnosis and recent performance.
   * **Full Historical (`Whole`, e.g., 1980–2025):** For cumulative characterization of the historical trajectory.
   * Direct forwarding of matrices to [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md) and [`neural-longitudinal-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md).
3. **Model Annual Series and PathSOM Trajectories:** Extract annual series (*Trend*) applying centered exponential smoothing (ECMA-3 / ECMA-5) to track the evolutionary orbit of universities or countries in [`som-trajectory-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md).
4. **Compute the Strategic Growth Matrix:** Calculate Compound Annual Growth Rates (CAGR %) against current volume to classify entities into 4 analytical quadrants (*Star Leaders*, *Emerging Stars*, *Established Giants*, *Low Priority*).

---

## 2. Dependencies and Value Chain

This skill acts as the ingestion and normalization bridge from InCites into the UNAM ecosystem's neurocomputational modeling:

* **Downstream Skills (Data Consumers):**
  * [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md): Receives the clean $[N \times D]$ matrix for SVD spectral calibration, hexagonal over-grid sizing, and SOM training.
  * [`som-trajectory-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md): Receives ECMA-smoothed annual time series to generate continuous spline trajectory plots (maximum 5 simultaneous entities).
  * [`neural-longitudinal-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md): Receives sequences of intertemporal slices for Warm-Start chaining.
* **Complementary Skills:**
  * [`tlachia-metrics-handler`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md): Canonical equivalent for packages exported from TlachIA Metrics / OpenAlex.
* **Associated Software Tools:**
  * [`incites_parser.py`](file:///c:/Users/jlja/Documents/Proyectos/knomap/engine/incites_parser.py): InCites parsing engine in KnoMap.
  * [`services/knomap/tools/incites_tools.py`](file:///mnt/expansion/desplegados/sos-mcp-services/services/knomap/tools/incites_tools.py): MCP tools exposed to the agent.

---

## 3. Anatomy of Clarivate InCites Reports and Packages

Reports exported from InCites have specific formatting characteristics that the agent must handle rigorously:

```
[InCites Package / Clarivate Export]
├── Individual CSV Files                         # Metadata headers (e.g., "InCites dataset updated...")
│   ├── Organizations.csv                        # Unicode UTF-8 or UTF-16 LE with BOM, comma/tab delimiters
│   ├── Locations.csv
│   └── WoS Categories.csv
└── Structured Packages (.zip or Directories)
    ├── 01_Matrices_Desempeño_Longitudinal/      # Inter-period variations (Δ% Docs, Δ CNCI, Δ Q1)
    │   ├── Organizations Performance Matrix.csv
    │   └── Locations Performance Matrix.csv
    ├── 02_Periodos_Consecutivos/                # Fixed 5-year or custom windows
    │   ├── Organizations 2016-2020.csv
    │   └── Organizations 2021-2025.csv
    ├── 03_Historico_Completo/                   # Cumulative profile across the entire time horizon
    │   ├── Organizations.csv                    # Complete Whole profile
    │   └── WoS Categories.csv
    └── 04_Tendencias_Anuales/                   # Year-by-year annual series
        ├── Organizations Trend.csv              # Annual measurements for ECMA smoothing and PathSOM
        └── Locations Trend.csv
```

### Reading and Cleaning Rules for InCites

1. **Skip Initial Metadata Rows:** CSVs downloaded directly from InCites typically begin with 1 to 3 system metadata lines (e.g., `"InCites dataset updated Feb 28, 2026. Includes Web of Science™ content..."`). If not skipped, the parser collapses the entire table into a single column. The agent must scan the first 15 lines and detect the real header row with the highest delimiter count.
2. **Encoding Detection:** Transparently support `utf-8-sig`, `utf-16-le` (typical of InCites Excel exports), and `latin-1`.
3. **Numeric Cleaning:** Convert textual percentages (e.g., `"24.50%"`) to floating-point numbers (`24.50`) and empty values or dashes (`"-"`, `"n/a"`) to `0.0`.

---

## 4. Correspondence with the KnoMap User Interface

When this file is processed in KnoMap's **InCites Explorer** module (`InCitesExplorer.tsx` and `ExploradorDatos.tsx`), the agent's behavior should mirror the user experience on the platform:

| Tab / Selector in KnoMap | Canonical Entity (`unit_name`)              | Benchmarking Object                                                 |
| :----------------------- | :------------------------------------------ | :------------------------------------------------------------------ |
| **Organizations**        | `Organizations`                             | Universities, research centers, and academic departments            |
| **Locations**            | `Locations`                                 | Countries, regions, and geopolitical territories                    |
| **Researchers**          | `Researchers` / `Authors`                   | Web of Science researchers and authors                              |
| **WoS Categories**       | `WoS Categories`                            | 254 canonical Web of Science disciplinary areas                     |
| **Publication Sources**  | `Publication Sources`                       | Journals and conferences indexed in Web of Science Core Collection  |
| **Research Areas ESI**   | `Research Areas ESI`                        | 22 canonical Essential Science Indicators fields                    |
| **Research Areas SDG**   | `Research Areas SDG`                        | UN Sustainable Development Goals (SDGs 1–17)                        |
| **Citation Topics**      | `Research Areas Topic` (Macro/Meso/Micro)   | Clarivate hierarchical Citation Topics taxonomy                     |
| **Funding Agencies**     | `Funding Agencies`                          | Research funding entities and agencies                              |
| **Patentometrics**       | `Patentometrics`                            | Citing patents and technological impact                             |
| **Baseline Indicators**  | `Data Indicators`                           | Comparative baseline indicators against the global average          |

### Integrated Analytical Views in KnoMap:

* **Section 1: Baseline Summary Cards & Comparison Table:** Comparative tables against the world average (Baseline = 1.0 for CNCI/JNCI).
* **Section 2: Strategic Growth Matrix:** Interactive scatter plot dividing entities into 4 quadrants according to their CAGR % and volume.
* **Section 3: Multidimensional Profiles:**
  * *4D Bubble Chart:* X-axis (CNCI), Y-axis (% Top 10%), Bubble Size (WoS Documents), Color (Dominant quartile or region).
  * *Quartile Bar Chart:* Percentage breakdown across quartiles Q1, Q2, Q3, Q4.
  * *Sunburst Chart:* Hierarchical navigation of Research Areas (Macro $\to$ Meso $\to$ Micro).
  * *Cluster Profile Radar:* Centroid profile and institutional benchmarking.
* **Section 4: PathSOM (Send to SOM):** Tabular matrix selection for non-linear trajectory modeling.

---

## 5. MCP Extraction and Modeling Protocol

The agent executes the following step-by-step workflow using `knomap-som-engine` tools:

```
+-------------------------------------------------------------------------------+
|                      INCITES -> SOM & STRATEGY WORKFLOW                       |
+-------------------------------------------------------------------------------+
| 1. inspect_incites_package(package_path="...")                                |
|       ↓ (Returns available units, periods, and detected schema)               |
| 2. USER DECISION:                                                             |
|       ├─ A. SOM Profile Modeling:                                             |
|       │     get_incites_unit_matrix(unit_name="Organizations", ...)           |
|       │     ↓ (Passes data & labels to suggest_grid_size and train_som)       |
|       │     Apply methodology in som-methodological-expert                    |
|       │                                                                       |
|       ├─ B. PathSOM Trajectories (Institutional Orbit):                       |
|       │     get_incites_temporal_evolution(entities=["UNAM","USP",...])       |
|       │     ↓ (Apply cubic splines and ECMA smoothing)                        |
|       │     Apply methodology in som-trajectory-mapping (max. 5 entities)     |
|       │                                                                       |
|       └─ C. Strategic Growth Diagnosis:                                       |
|             compute_strategic_growth_matrix(indicator="WoS Documents", ...)   |
|             ↓ (Computes CAGR % and classifies into 4 management quadrants)    |
|             Issue institutional investment and prioritization recommendations |
+-------------------------------------------------------------------------------+
```

### Step 1: Inspect the InCites Package or Report

Invoke `knomap-som-engine -> inspect_incites_package`:

```python
# Example MCP call:
inspect_incites_package(
    package_path=r"C:\Users\jlja\Documents\Reportes\InCites_Benchmarking_Iberoamerica.zip"
)
```

* **Response:** Returns `session_dir` (indexed temporary directory), list of `available_units`, summary of files by period (`Whole`, `5Years`, `Trend`, `PerformanceMatrix`), and catalog of detected indicators.

### Step 2: Extract the Multidimensional Performance Matrix

Invoke `knomap-som-engine -> get_incites_unit_matrix`:

```python
# Extracting institutions with a balanced InCites battery:
get_incites_unit_matrix(
    session_dir=session_dir,
    unit_name="Organizations",
    use_recent_5years=True,     # True: 2021-2025 (current performance); False: Whole (historical)
    selected_indicators=[
        "Category Normalized Citation Impact (CNCI)",
        "Journal Normalized Citation Impact (JNCI)",
        "% Documents in Top 10%",
        "% Documents in Top 1%",
        "% Documents in Q1 Journals",
        "International Collaborations (%)",
        "Industry Collaborations (%)",
        "Average Percentile",
        "Web of Science Documents"
    ],
    filter_min_threshold=50.0,   # Minimum critical mass threshold (e.g., 50 WoS documents)
    limit_top_n=50               # Top 50 leading institutions
)
```

* **Response:** Returns `labels` (clean institutional names), `indicators`, and `data` ($[N \times D]$ matrix of clean real numbers without NaNs ready for Z-score normalization).

### Step 3: Send to the SOM Pipeline

Once the `data` matrix and `labels` are obtained:

1. **Compute Dimensions:** Invoke `knomap-som-engine -> suggest_grid_size(data=data)` to calculate the SVD aspect ratio ($\sigma_1/\sigma_2$) and over-gridding ($20N\text{--}30N$ neurons according to [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)).
2. **Train SOM:** Invoke `knomap-som-engine -> train_som(data=data, labels=labels, rows=rows, cols=cols, init="pca")`.
3. **Optimize Clusters:** Invoke `knomap-som-engine -> evaluate_som_clusters` to calibrate the optimal $K$ via Silhouette Score.
4. **Interpret Results:** Analyze the U-Matrix and component planes to identify comparable peer groups and differentiated strengths.

### Step 4: Extract Annual Series and PathSOM Trajectories

To examine the continuous historical evolution of a select competitor group:
Invoke `knomap-som-engine -> get_incites_temporal_evolution`:

```python
get_incites_temporal_evolution(
    session_dir=session_dir,
    unit_name="Organizations",
    entities=["UNAM", "Universidade de Sao Paulo", "Tecnologico de Monterrey", "UBA"],
    indicators=["CNCI", "% Documents in Top 10%", "Web of Science Documents"],
    smoothing="ecma3"           # "ecma3" (3-year window), "ecma5", or "raw"
)
```

* **Response:** Returns annualized time series with centered smoothing for each indicator.
* **Integration:** Transfer to [`som-trajectory-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md) respecting the **KnoMap Golden Rule (maximum 5 simultaneous entities)** to prevent visual spline saturation.

### Step 5: Compute the Strategic Growth Matrix

Invoke `knomap-som-engine -> compute_strategic_growth_matrix`:

```python
compute_strategic_growth_matrix(
    session_dir=session_dir,
    unit_name="Organizations",
    indicator="Web of Science Documents",
    entities=["UNAM", "USP", "UNICAMP", "UFRJ", "PUC Chile"]
)
```

* **Compound Annual Growth Rate (CAGR %) Calculation:**
  $$
  \text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}}\right)^{\frac{1}{t_{\text{final}} - t_{\text{initial}}}} - 1
  $$
* **Resulting Strategic Quadrants:**
  * **Star Leaders (High Growth, High Volume):** Dynamic leaders expanding their output at rates exceeding the system average.
  * **Emerging Stars (High Growth, Moderate Volume):** Emerging hotspots and opportunity niches that should receive priority institutional support.
  * **Established Giants (Low Growth, High Volume):** Consolidated traditional institutions with massive volume but maturing or stagnating growth rates.
  * **Low Priority (Low Growth, Low Volume):** Entities or areas with low traction requiring restructuring or strategic reallocation.

---

## 6. Exhaustive Battery of Canonical Clarivate InCites Indicators

When advising the user on selecting indicators for institutional benchmarking, structuring the query across 5 canonical dimensions is recommended:

```
+-------------------------------------------------------------------------------+
|                     CLARIVATE INCITES INDICATOR TAXONOMY                      |
+-------------------------------------------------------------------------------+
| 1. Capacity and Critical Mass:                                                |
|    - Web of Science Documents, % Top 10%, % Top 1%, % Q1, % Q2, % Q3, % Q4    |
| 2. Normalized Impact and Citation:                                            |
|    - CNCI (World = 1.0), JNCI, Times Cited, Citation Impact, Average Pct      |
| 3. Collaboration and Internationalization:                                    |
|    - % International Collab, % Industry Collab, % Domestic, % Academic        |
| 4. Open Access (Clarivate Open Access Schema):                                |
|    - % All OA, % DOAJ Gold, % Other Gold, % Bronze, % Green Published/Accepted|
| 5. Funding and Technological Impact:                                          |
|    - Funding Agency Documents, Patent Citations to Web of Science             |
+-------------------------------------------------------------------------------+
```

### 1. Capacity and Critical Mass

* `Web of Science Documents`: Absolute volume of articles, reviews, and proceedings indexed in WoS Core Collection.
* `% Documents in Top 10%`: Proportion of documents in the top world citation decile within their respective field and year.
* `% Documents in Top 1%`: Proportion of articles in the international elite percentile.
* `% Documents in Q1 Journals`: Percentage of output published in first-quartile Journal Citation Reports (JCR) journals. Equally supports `% Documents in Q2 Journals`, `% Documents in Q3 Journals`, and `% Documents in Q4 Journals`.

### 2. Field- and Journal-Normalized Impact

* `Category Normalized Citation Impact (CNCI)`: **Flagship InCites indicator**. Ratio of observed citations to expected citations for documents of the same type, year, and WoS category ($\text{World} = 1.0$). Enables fair comparison across disciplines with disparate citation habits (e.g., Mathematics vs. Biomedicine).
* `Journal Normalized Citation Impact (JNCI)`: Citations received normalized against the average of the publishing journal ($\text{World} = 1.0$). Reveals whether authors outperform the average impact of the journals in which they publish.
* `Times Cited`: Cumulative raw citations received in Web of Science.
* `Citation Impact`: Simple average citations per document ($\text{Times Cited} / \text{WoS Documents}$).
* `Average Percentile`: Mean percentile in the global citation distribution ($\text{World} = 50.0$). In standard InCites, a lower value indicates higher impact (e.g., Percentile 10 is higher than Percentile 60); KnoMap handles it consistently with the excellence percentile scale.
* `% Documents Cited`: Proportion of output that has received at least one citation.
* `H-Index`: Hirsch's h-index computed over the indexed body of work.

### 3. Collaboration and Transnational Integration

* `International Collaborations (%)`: Percentage of articles with co-authors affiliated with institutions in at least two different countries.
* `Domestic Collaborations (%)`: Inter-institutional collaboration within the same country.
* `Industry Collaborations (%)`: Proportion of documents with corporate or business sector co-authors (science-industry linkage).
* `Academic Collaborations (%)`: Collaboration among universities and academic centers.

### 4. Open Access (Clarivate Open Access Taxonomy)

* `% All Open Access Documents`: Overall openness degree of the output.
* `% DOAJ Gold Documents`: Articles in Open Access journals registered in DOAJ.
* `% Other Gold Documents`: Publication in hybrid or APC-based journals outside DOAJ.
* `% Bronze Documents`: Free-to-read articles on the publisher platform without a formal open license.
* `% Green Published Documents` / `% Green Accepted Documents`: Self-archiving in thematic or institutional repositories.

### 5. Funding and Technological Impact

* `Funding Agencies Documents`: Volume and proportion of publications explicitly declaring sponsorship or grants in acknowledgment sections.
* `Patent Citations to Web of Science`: Citations received from international patents, evidencing technology transfer.

---

## 7. Benchmarking Interpretive Framework and Metric Paradoxes

When formulating scientometric diagnoses with InCites, the agent must apply the following advanced criteria:

### A. Auditing the CNCI vs. Percentile Paradox

`CNCI` is an arithmetic mean with no upper bound. A single hyper-cited multicenter mega-article (e.g., WHO report, Phase III clinical trial, or CERN high-energy physics paper) with hundreds of citations can artificially inflate institutional CNCI above $1.5$ or $2.0$, masking the fact that most faculty publish at average levels. Therefore:

* **Robustness Diagnosis:** Always contrast CNCI against `% Documents in Top 10%` and `% Documents in Q1 Journals`.
* If $\text{CNCI} > 2.0$ but $\% \text{Top 10\%} < 8\%$, the agent must flag a **singular hyper-citation bias**.

### B. Recent Window (5 Years) vs. Historical Window

* **Recent Window (2021–2025):** Recommended window for institutional decision-making, hiring policy evaluation, and current budget allocation.
* **Historical Window (`Whole`):** Reflects long-term inertia and reputation accumulated over decades, but often overestimates traditional institutions that may have slowed down in recent years.

---

## 8. Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Reading CSVs without skipping initial Clarivate metadata**  
  Calling `pd.read_csv()` directly without skipping the 1 to 3 metadata lines (`"InCites dataset updated Feb 28, 2026..."`), causing the entire table to collapse into a single corrupted column.  
  **Solution:** Scan the first 15 lines looking for the real header or use the canonical `clean_and_read_file()` function from `incites_parser.py`.
- ❌ **Anti-pattern 2: Simple arithmetic average of ratios in Micro Topics**  
  Computing the simple mean of `CNCI`, `JNCI`, or `% Documents in Top 10%` when aggregating Micro Topics to Meso or Macro Topics.  
  **Solution:** Absolute production counts (`Web of Science Documents`, `Times Cited`) are summed; normalized impact indicators are computed as a document-weighted average: $\frac{\sum (\text{CNCI}_i \cdot \text{Docs}_i)}{\sum \text{Docs}_i}$.
- ❌ **Anti-pattern 3: Failing to handle alternative InCites encodings (UTF-16 LE)**  
  Assuming all files use standard UTF-8. Direct InCites downloads formatted for Excel frequently use `utf-16-le` with BOM or `latin-1`.  
  **Solution:** Implement dynamic fallback: `utf-8-sig` $\rightarrow$ `utf-16-le` $\rightarrow$ `latin-1`.
- ❌ **Anti-pattern 4: Saturating the conversation with massive arrays (Violating File-Output First)**  
  Dumping complete numeric matrices of 50 institutions or 20-year annual series into the LLM text response.  
  **Solution:** Persist the clean matrix in `session_dir/matrix_incites.json` or the scratch/artifacts directory, returning only dimensions, descriptive statistics, and the file path.
- ❌ **Anti-pattern 5: Assuming widespread excellence from a high CNCI alone**  
  Diagnosing an institution as a world leader solely because its CNCI exceeds 2.0 without contrasting against Average Percentile or % Top 10%.  
  **Solution:** Always audit for outlier mega-collaborations (*Black Swans*) before certifying institutional leadership.

---

## 9. Technical References

- [SOM Methodological Expert](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)
- [SOM Trajectory Mapping](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md)
- [Neural Longitudinal Mapping](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md)
- [TlachIA Metrics Handler](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md)
- [KnoMap Engine InCites Parser](file:///c:/Users/jlja/Documents/Proyectos/knomap/engine/incites_parser.py)
- [KnoMap Frontend InCites Explorer](file:///c:/Users/jlja/Documents/Proyectos/knomap/frontend/src/components/InCitesExplorer.tsx)
- [InCites Tools in sos-mcp-services](file:///mnt/expansion/desplegados/sos-mcp-services/services/knomap/tools/incites_tools.py)
