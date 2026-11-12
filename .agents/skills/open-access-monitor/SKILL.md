---
name: open-access-monitor
description: Analytical monitoring of the 6 Open Access pathways (Diamond, Gold APC, Hybrid, Bronze, Green, Closed), estimation of commercial APC expenditure in USD, and transition trend analysis. Respond and label outputs in the user's language.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/open_access_monitor_cli.py"
---

# Open Access Monitor

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Scientometric module specialized in classifying and quantifying the 6 canonical Open Access pathways, scientific sovereignty, and commercial publication cost estimation via APCs.

## Overview

This module audits document collections (Parquet, CSV, or JSON) to measure Open Access penetration, contrast non-commercial models (Diamond) against commercial market models (Gold APC, Hybrid), and model the temporal transition of publications.

## Dependencies

- Python environment: `/home/ambientesPy/revistaslatam`
- Executable script: [`scripts/open_access_monitor_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/scripts/open_access_monitor_cli.py)

## CLI Interface

### 1. Open Access Pathway Breakdown (`breakdown`)
Computes absolute and percentage distributions across the 6 pathways, generating a JSON report and dual high-resolution (300 DPI) publication figures:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/scripts/open_access_monitor_cli.py breakdown \
  --input /path/to/corpus.parquet \
  --output /path/to/oa_breakdown.json \
  --plot-es /path/to/oa_distribution_es.png \
  --plot-en /path/to/oa_distribution_en.png \
  --plotly-html /path/to/oa_distribution.html \
  --lang en
```

### 2. Commercial APC Expenditure Estimation (`apc-spending`)
Computes monetary expenditure in USD derived from articles published in Gold and Hybrid journals:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/scripts/open_access_monitor_cli.py apc-spending \
  --input /path/to/corpus.parquet \
  --gold-apc-usd 2200 \
  --hybrid-apc-usd 3200 \
  --output /path/to/apc_spending.json \
  --lang en
```

### 3. Annual Transition Trends (`transition-trend`)
Analyzes the annual chronological series of Open Access adoption:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/open-access-monitor/scripts/open_access_monitor_cli.py transition-trend \
  --input /path/to/corpus.parquet \
  --output /path/to/oa_trend.json \
  --lang en
```
