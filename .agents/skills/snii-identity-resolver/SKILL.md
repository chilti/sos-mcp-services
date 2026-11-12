---
name: snii-identity-resolver
description: Identity resolution, homonym disambiguation, and official verification of researchers in Mexico's 2025 SNII Registry (level, knowledge area, validity period, ORCID, and Scopus ID). Respond and label outputs in the user's language.
dependencies:
  - python: ">=3.10"
  - script: "scripts/snii_resolver_cli.py"
---

# SNII Identity Resolver

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Canonical verification and disambiguation module for researchers against the Official Registry of Mexico's National System of Researchers (*Sistema Nacional de Investigadoras e Investigadores*, SNII 2025).

## Overview
Distinguishes homonymous scientists, certifies their official accreditation level (Candidate to Emeritus), evaluation knowledge area (Areas I to IX), and links their persistent identifiers (ORCID and OpenAlex Author ID) to support national scientometric assessments.

## Dependencies
- **Python Environment:** Python 3.10+ (with required dependencies)
- Executable script: [`scripts/snii_resolver_cli.py`](file://scripts/snii_resolver_cli.py)

## Scripts & CLI Tools

### Resolve Identity (`resolve`)
Disambiguate an author against the official SNII registry:
```bash
python scripts/snii_resolver_cli.py resolve \
  --name "Rafael Torres Córdoba" \
  --institution "UNAM" \
  --output /path/to/identidad_torres.json
```

### Query SNII Profile (`profile`)
Retrieve the institutional profile and associated metrics:
```bash
python scripts/snii_resolver_cli.py profile \
  --name "Torres Córdoba" \
  --output /path/to/perfil_snii.json
```

## Workflow Steps
1. **Identify Author:** Receive an author name from OpenAlex or a bibliographic corpus.
2. **Validate SNII Status:** Run `resolve` to confirm whether the researcher is accredited in the national registry and retrieve their official level.
3. **Enrichment Handoff:** Connect the resolved ORCID with [`infotlachia-scholar-intelligence`](../infotlachia-scholar-intelligence/SKILL.md).

## References
- [Official SNII 2025 Registry Schema](references/snii_padron_2025_schema.md)
- [SECIHTI / CONAHCYT Knowledge Areas Taxonomy](references/conahcyt_areas_taxonomy.md)

## Troubleshooting & Edge Cases
- **Name Variations:** The CLI normalizes diacritics and evaluates institutional suffixes to ensure high disambiguation confidence (`disambiguation_confidence >= 0.90`).
