# Guide to Temporal and Period-Based Longitudinal Analysis in TlachIA

The TlachIA scientometric metrics engine analyzes the historical evolution of a scientific corpus across three temporal scales:
1. **Continuous annual series** (`annual-series`)
2. **Focused single periods** (`calculate-summary --last-years 5` or `--period 2019-2024`)
3. **Consecutive periods and sliding windows** (`period-series`)

---

## 1. Temporal Partitioning Modes

### A. Consecutive Fixed Windows (`--window N`)
Divides the total corpus interval into non-overlapping blocks of $N$ years:
- If the corpus spans 2000 to 2024 with `--window 5`:
  `[2000-2004, 2005-2009, 2010-2014, 2015-2019, 2020-2024]`
- If the corpus spans 2005 to 2024 with `--window 10`:
  `[2005-2014, 2015-2024]`

### B. Sliding / Rolling Windows (`--window N --step S`)
Captures smooth transition dynamics with overlap:
- `--window 5 --step 1`:
  `[2015-2019, 2016-2020, 2017-2021, 2018-2022, 2019-2023, 2020-2024]`

### C. Explicit Period List (`--periods "P1,P2,..."`)
Defines institutional or multi-year policy milestones:
- `--periods "2006-2012,2012-2018,2018-2024"`

### D. Single or Most Recent Period (`--single-period` or `--last-years`)
- `--single-period "2020-2024"`: evaluates exclusively that five-year window.
- `--last-years 5`: dynamically computes the most recent five-year window without requiring prior knowledge of the maximum year.

---

## 2. Inter-Period Variation and Growth Rates

At each temporal transition from $t-1$ to $t$, the engine quantifies:
- **Output Growth ($\Delta \text{Docs}$):**
  $$\text{doc\_growth\_pct} = \frac{\text{Docs}_t - \text{Docs}_{t-1}}{\text{Docs}_{t-1}} \times 100$$
- **Citation Variation ($\Delta \text{Citations}$):**
  $$\text{cite\_growth\_pct} = \frac{\text{Citas}_t - \text{Citas}_{t-1}}{\text{Citas}_{t-1}} \times 100$$

---

## 3. Longitudinal Entity Matrices for SOM (`--level`)

When combining `period-series` with `--level researcher` or `--level institution`, the engine generates a longitudinal structure:
- Each row represents an entity in a specific period along with its metrics (`num_documents`, `times_cited`, `cites_per_doc`, `h_index`, `pct_oa`).
- This longitudinal matrix can be exported to `.parquet` or `.csv` and fed directly into the Warm-Start temporal chaining algorithms of the [`neural-longitudinal-mapping`](file:///home/labsom/knomap/.agents/skills/neural-longitudinal-mapping/SKILL.md) skill.
