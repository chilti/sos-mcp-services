---
name: tlachia-metrics-handler
description: >-
  Comprehensive handler for exported TlachIA Metrics packages (.zip and directories). Inspects unit inventories (Locations, Organizations, Sources, Topics), extracts scientometric indicator matrices ready for SOM training, and retrieves the canonical document metadata file for bibliometric network analysis (co-authorship, bibliographic coupling, and co-occurrence). Respond and label outputs in the user's language.
---

# TlachIA Metrics Handler: Package Manager and Analytical Extraction

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Purpose and Activation

This skill activates when the user provides a **package exported from TlachIA Metrics** (a `.zip` file or unpacked directory, e.g., `Artificial_Intelligence_in_Education.zip`) and requires:

1. **Inspecting the Package Inventory:** Identifying available analytical units (`Locations`, `Organizations`, `Publication Sources`, `Research Areas Topic`, `Corpus`), temporal periods, and general corpus metadata.
2. **Extracting Multidimensional Matrices for SOM:** Extracting clean $[N \times D]$ tabular profiles of specific entities (e.g., countries in `Locations`, universities in `Organizations`) by selecting desired scientometric indicators to feed into [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md), [`neural-longitudinal-mapping`](file:///home/labsom/knomap/.agents/skills/neural-longitudinal-mapping/SKILL.md), or [`som-trajectory-mapping`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md).
3. **Locating and Preparing the Works Metadata File (`works_file`):** Extracting and validating the canonical documents file (`*_openalex_works.csv` or `.parquet`) for downstream complex network analysis with [`bibliometric-network-analyst`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/bibliometric-network-analyst/SKILL.md) (co-authorship, bibliographic coupling, co-citation, and keyword co-occurrence).

---

## 2. Anatomy of a TlachIA Metrics Package

Canonical packages downloaded from TlachIA Metrics follow a standardized 5-tier architecture:

```
[TlachIA Metrics Package / .zip]
├── manifest.json                                # Corpus metadata, date, and query parameters
├── LEEME_ESTRUCTURA.txt                         # Structure and field documentation
├── 01_Matrices_Desempeño_Longitudinal/          # Matrices with inter-period variations (Δ% Docs, Δ FWCI)
│   ├── Locations Performance Matrix.csv
│   └── Organizations Performance Matrix.csv
├── 02_Periodos_Consecutivos/                    # Tables disaggregated by 5-year or fixed windows
│   ├── Locations 2016-2020.csv
│   └── Locations 2021-2026.csv
├── 03_Historico_Completo/                       # Cumulative profile across the full time horizon
│   ├── Locations.csv                            # (150+ countries with 30+ indicators)
│   └── Organizations.csv                        # (Universities and institutes)
├── 04_Tendencias_Anuales/                       # Year-by-year time series
│   └── Locations Trend.csv                      # (Annual measurements for smoothing and trajectories)
└── 05_Tablas_Parquet_y_Datos/                   # Columnar data and full works
    ├── <Corpus_Name>_openalex_works.csv         # Canonical enriched document file
    └── locations_full.parquet                   # High-speed binary version
```

---

## 3. Correspondence with the KnoMap User Interface

When this file is visually loaded into the KnoMap interface, the agent's behavior emulates the user's experience on the platform:

| KnoMap Tab | Canonical Entity (`unit_name`) | Object of Analysis |
| :--- | :--- | :--- |
| **Locations** | `Locations` | Countries and territories (ISO-2 / ISO-3 code) |
| **Organizations** | `Organizations` | Universities, research centers, and departments |
| **Sources** | `Publication Sources` | Scientific journals, conferences, and repositories |
| **Topics / Areas** | `Research Areas Topic` | Thematic research lines (OpenAlex Topics) |
| **Subfields / Fields**| `Research Areas Subfield` / `Field`| Higher-level disciplinary taxonomy |
| **SDG** | `Research Areas SDG` | Sustainable Development Goals (SDGs 1–17) |
| **Corpus** | `Corpus` | Macro aggregate indicators of the entire field |

* ***«Send to SOM»* Action:** In KnoMap, selecting an entity and a set of numeric columns in the table sends the data to the SOM engine. The agent reproduces this workflow programmatically via CLI or MCP tools.

---

## 4. MCP Extraction and Modeling Protocol

The agent executes the following step-by-step workflow:

```
+-------------------------------------------------------------------------------+
|                      TLACHIA -> SOM & NETWORKS WORKFLOW                       |
+-------------------------------------------------------------------------------+
| 1. inspect_tlachia_package(package_path="...")                                |
|       ↓ (Returns available units, session_dir, and works_file)                |
| 2. USER DECISION:                                                             |
|       ├─ A. SOM Profile Modeling:                                             |
|       │     get_tlachia_unit_matrix(unit_name="Locations", indicators=[...])  |
|       │     ↓ (Passes data & labels to suggest_grid_size and train_som)       |
|       │     Apply methodology in som-methodological-expert                    |
|       │                                                                       |
|       ├─ B. Temporal Trajectories (Country Orbits):                           |
|       │     get_tlachia_temporal_evolution(entities=["RU","US","CN",...])     |
|       │     ↓ (Apply cubic splines and centered moving averages)              |
|       │     Apply methodology in som-trajectory-mapping (max. 5 entities)     |
|       │                                                                       |
|       └─ C. Bibliometric Network Analysis:                                    |
|             get_tlachia_works_metadata(session_dir="...")                     |
|             ↓ (Obtains works_file_path with author/reference columns)         |
|             Hand off to bibliometric-network-analyst                          |
+-------------------------------------------------------------------------------+
```

### Step 1: Inspect the Package
Invoke `knomap-som-engine -> inspect_tlachia_package`:
```python
# Example MCP call:
inspect_tlachia_package(
    package_path=r"C:\Users\jlja\Downloads\Artificial_Intelligence_in_Education.zip"
)
```
* **Response:** Returns `session_dir` (indexed temporary directory), `available_units` list, and metadata for the works/articles file (`document_count`).

### Step 2: Extract the Performance Matrix (e.g., Countries in `Locations`)
Invoke `knomap-som-engine -> get_tlachia_unit_matrix`:
```python
# Country extraction with balanced indicators:
get_tlachia_unit_matrix(
    session_dir_or_zip=session_dir,
    unit_name="Locations",
    period_mode="Whole",        # "Whole" (historical) or "5Years" (recent)
    selected_indicators=[
        "Field-Weighted Citation Impact (FWCI)",
        "Citation Impact",
        "% Documents in Top 10%",
        "% Documents in Top 1%",
        "Average Percentile",
        "% All Open Access Documents",
        "% Free to Read / Diamond Documents",
        "% International Collaborations",
        "% Industry Collaborations",
        "Share"
    ],
    limit_top_n=50,             # Top 50 leading countries by volume
    min_documents=10.0          # Optional: minimum critical mass threshold
)
```
* **Response:** Returns `labels` (country codes), `indicators`, and `data` ($[N \times D]$ matrix of clean real numbers without NaNs).

### Step 3: Send to the SOM Pipeline
Once the `data` matrix and `labels` are obtained:
1. **Compute Dimensions:** Invoke `knomap-som-engine -> suggest_grid_size(data=data)` to obtain the SVD aspect ratio ($\sigma_1/\sigma_2$) and over-grid size ($20N\text{--}30N$ neurons according to [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)).
2. **Train SOM:** Invoke `knomap-som-engine -> train_som(data=data, labels=labels, rows=rows, cols=cols, init="pca")`.
3. **Optimize Clusters:** Invoke `knomap-som-engine -> evaluate_som_clusters` to calibrate optimal $K$ via Silhouette Score.
4. **Interpret Results:** Examine the U-Matrix and component planes to identify clusters of countries with analogous profiles (legitimate peers), poles of excellence, and outlier profiles.

### Step 4: Retrieve the Works File for Bibliometric Networks
If the user wishes to analyze scientific collaboration networks among authors, institutions, or countries, or thematic co-occurrence / bibliographic coupling networks:
Invoke `knomap-som-engine -> get_tlachia_works_metadata`:
```python
get_tlachia_works_metadata(session_dir_or_zip=session_dir)
```
* **Response:** Provides the absolute `works_file_path` (e.g., `.../Artificial_Intelligence_in_Education_openalex_works.csv`), confirms document volume (e.g., 38,657), and validates that required columns are present:
  * `author_names` / `author_ids` $\rightarrow$ Co-authorship networks.
  * `institution_names` / `country_codes` $\rightarrow$ Institutional and geopolitical collaboration networks.
  * `referenced_works` $\rightarrow$ Bibliographic coupling and co-citation.
  * `keywords` / `concepts` $\rightarrow$ Conceptual co-occurrence networks.
* This path is ready to be passed directly to [`bibliometric-network-analyst`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/bibliometric-network-analyst/SKILL.md).

---

## 5. Canonical Indicator Suite for `Locations` (Countries)

When advising the user on selecting indicators to characterize country performance profiles, the following balanced 5-dimension suite is recommended:

1. **Capacity and Output:**
   * `Documents`: Absolute volume of articles from the country in the topic.
   * `Share`: Percentage share of total global corpus output.
2. **Normalized Impact and Visibility:**
   * `Field-Weighted Citation Impact (FWCI)`: Citations normalized by field, year, and document type (World = 1.0).
   * `Citation Impact`: Average citations per document.
   * `Average Percentile`: Average citation ranking percentile (World = 50.0).
3. **Scientific Excellence:**
   * `% Documents in Top 10%`: Proportion of articles in the top global decile.
   * `% Documents in Top 1%`: Proportion in the international elite percentile.
4. **Open Science and Publishing Mode:**
   * `% All Open Access Documents`: Overall degree of openness.
   * `% Free to Read / Diamond Documents`: Publishing in Diamond Open Access (no APC charged).
   * `Estimated Diamond Savings (USD)`: Cumulative savings generated via the Diamond route.
5. **Collaboration and Internationalization:**
   * `% International Collaborations`: Degree of insertion in transnational networks.
   * `% Industry Collaborations`: Linkages with industry and the productive sector.
   * `% Global South Collaborations`: Intra-regional collaboration or collaboration with Global South countries.

---

## 6. Technical References

- [SOM Methodological Expert](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)
- [SOM Trajectory Mapping](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md)
- [Neural Longitudinal Mapping](file:///home/labsom/knomap/.agents/skills/neural-longitudinal-mapping/SKILL.md)
- [Bibliometric Network Analyst](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/bibliometric-network-analyst/SKILL.md)
- [KnoMap Engine Tlachia Parser](file:///c:/Users/jlja/Documents/Proyectos/knomap/engine/tlachia_parser.py)
