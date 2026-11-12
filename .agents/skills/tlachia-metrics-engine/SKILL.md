---
name: tlachia-metrics-engine
description: Standalone scientometric engine for computing 30+ indicators (FWCI, H-index, Top 10%, APC USD, 6 OA pathways, Gini) and annual and period-based longitudinal temporal analyses over canonical tables. Respond and label outputs in the user's language.
---

# TlachIA Metrics Engine

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Independent analytical engine for computing the comprehensive suite of TlachIA scientometric, economic, and open science indicators from any normalized tabular file (`.parquet`, `.csv`, `.json`), without requiring the web interface or central TlachIA Metrics database.

---

## Capabilities

- **Consolidated Suite of 30+ Indicators:** Volume, citations, H-index, i10, FWCI, percentiles, Top 10%, and Top 1%.
- **Annual Temporal Analysis:** Generation of continuous year-by-year time series (`annual-series`) with annual growth rate calculations ($\Delta \text{Docs}$, $\Delta \text{Citations}$).
- **Longitudinal Period Analysis:** Evaluation across fixed windows (`--window 5` or `--window 10`), sliding windows (`--window 5 --step 1`), specific periods, or the latest five-year period (`--last-years 5`), producing longitudinal entity matrices for SOM.
- **Open Access Monitoring:** Breakdown across the 6 pathways (Gold, Diamond, Hybrid, Green, Bronze, Closed).
- **Publication Economics:** Accrued commercial APC expenditure in USD and quantification of savings from Diamond Open Access.
- **Multi-Level Aggregation:** Breakdown by researcher (`researcher`), department/institution (`institution`), country (`country`), journal (`source`), subfield (`subfield`), or topic (`topic`).
- **Thematic Gini Diversity:** Quantification of the degree of concentration or dispersion of the research front.

---

## CLI Interface

Execution environment:
```bash
python scripts/tlachia_metrics_cli.py [subcommand] [options]
```

### 1. Scientometric Summary (with optional temporal filters)
```bash
# Global summary (English default; pass --lang es for Spanish)
python scripts/tlachia_metrics_cli.py calculate-summary \
  --corpus ./corpus.parquet \
  --output ./tlachia_summary.md \
  --lang en

# Summary of the last 5 years
python scripts/tlachia_metrics_cli.py calculate-summary \
  --corpus ./corpus.parquet \
  --last-years 5 \
  --output ./summary_last_5years.md
```

### 2. Year-by-Year Annual Time Series
```bash
python scripts/tlachia_metrics_cli.py annual-series \
  --corpus ./corpus.parquet \
  --year-from 2018 \
  --year-to 2024 \
  --output ./annual_series.md
```

### 3. Longitudinal Analysis Across Consecutive Periods or Windows
```bash
# Consecutive 5-year periods
python scripts/tlachia_metrics_cli.py period-series \
  --corpus ./corpus.parquet \
  --window 5 \
  --output ./periods_5years.md

# Explicit list of periods for decadal analysis
python scripts/tlachia_metrics_cli.py period-series \
  --corpus ./corpus.parquet \
  --periods "2000-2009,2010-2019,2020-2024" \
  --output ./decadal_periods.parquet

# Longitudinal matrix of researchers per period (for SOM mapping)
python scripts/tlachia_metrics_cli.py period-series \
  --corpus ./corpus.parquet \
  --window 5 \
  --level researcher \
  --output ./researchers_longitudinal_som.parquet
```

### 4. Cross-Sectional Aggregation at the Researcher Level
```bash
python scripts/tlachia_metrics_cli.py aggregate-by \
  --corpus ./corpus.parquet \
  --level researcher \
  --output ./authors_indicators.parquet
```

### 5. Thematic Gini Concentration Coefficient
```bash
python scripts/tlachia_metrics_cli.py gini-diversity \
  --corpus ./corpus.parquet \
  --column keywords_plus
```

---

## Technical References
- [Temporal and Period-Based Longitudinal Analysis Guide](references/longitudinal_periods_guide.md)
- [Mathematical Handbook of TlachIA Scientometric Indicators](references/tlachia_indicators_mathematical_handbook.md)
- [APC Economic Model and Diamond Savings](references/apc_economic_model.md)
