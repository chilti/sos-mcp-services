---
name: revistaslatam-indicators-engine
description: Analytical engine for editorial evaluation of Ibero-American scientific journals, institutional endogamy calculation, multilingual balance, and auditing of the 38 Latindex Catalog 2.0 criteria. Respond and label outputs in the user's language.
---

# Revistas Latam Indicators Engine

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Standalone analytical engine to diagnose editorial health, scientometric visibility, and regulatory compliance of Ibero-American scientific journals from canonical tabular data or metadata manifests, without requiring the Revistas Latam web interface.

---

## Capabilities

- **Journal Scientometric Profile:** Citation counts, citations per document, H-index, Egghe's G-index, Hirsch's M-quotient, and Price Index of obsolescence.
- **Institutional Editorial Endogamy Rate:** Quantifies the proportion of authors affiliated with the publishing institution versus external national and international authors, benchmarking against Latindex, SciELO, and Redalyc thresholds.
- **Multilingual Balance:** Proportion of articles in Spanish, Portuguese, and English with Shannon diversity entropy calculation.
- **Latindex Catalog 2.0 Audit:** Automated checklist of the 8 mandatory basic criteria and additional digital quality criteria.

---

## CLI Interface

Execution environment:
```bash
python scripts/revistaslatam_indicators_cli.py [subcommand] [options]
```

### 1. Journal Scientometric Profile
```bash
python scripts/revistaslatam_indicators_cli.py journal-profile \
  --corpus ./articulos_revista.parquet \
  --journal-name "Revista Mexicana de Sociología" \
  --output ./perfil_revista.md
```

### 2. Institutional Editorial Endogamy Assessment
```bash
python scripts/revistaslatam_indicators_cli.py editorial-endogamy \
  --corpus ./articulos_revista.parquet \
  --host-institution "Universidad Nacional Autónoma de México" \
  --host-country "MX" \
  --output ./endogamia_reporte.json
```

### 3. Article Linguistic Distribution
```bash
python scripts/revistaslatam_indicators_cli.py multilingual-balance \
  --corpus ./articulos_revista.parquet \
  --output ./balance_idiomas.json
```

### 4. Latindex Catalog 2.0 Criteria Audit
```bash
python scripts/revistaslatam_indicators_cli.py latindex-audit \
  --metadata ./revista_metadata.json \
  --output ./auditoria_latindex.json
```

---

## Technical References
- [International Standards for Editorial Endogamy](references/editorial_endogamy_standards.md)
- [Latindex Catalog 2.0 Criteria Audit Manual](references/latindex_catalogo_2_audit_manual.md)
