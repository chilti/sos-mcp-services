---
name: openalex-mexico-institutions
description: "Query and mapping of Mexico's national catalog of institutions, universities, and research centers over rag.institutions_seed_mexico, resolving ROR identifiers, institutional acronyms (UNAM, IPN, UAM, Cinvestav), states, and parent entities. Respond and label outputs in the user's language."
metadata:
  python: ">=3.10"
  script: "scripts/openalex_mexico_cli.py"
---

# OpenAlex Mexico Institutions

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

Search, disambiguation, and geolocation of Mexican institutions and scientific centers in the `rag.institutions_seed_mexico` table.

## Overview

Facilitates the identification of public and private universities, SECIHTI (formerly CONAHCyT) public research centers, and national health institutes, resolving their official ROR codes, known acronyms, and parent organizations.

## Dependencies

- **Python Environment:** Python 3.10+ (`clickhouse-connect`)
- **CLI Script:** [`scripts/openalex_mexico_cli.py`](scripts/openalex_mexico_cli.py)
- **ClickHouse Table:** `rag.institutions_seed_mexico`

## CLI Interface

### 1. Search by Acronym
Locates the institution and extracts its canonical ROR:
```bash
python scripts/openalex_mexico_cli.py get-institution \
  --acronym "UNAM" \
  --limit 5 \
  --output ./data/unam_institucion.json
```

### 2. Search by Name or Free Text
```bash
python scripts/openalex_mexico_cli.py get-institution \
  --query "Instituto Politécnico Nacional" \
  --output ./data/ipn_institucion.json
```

### 3. Filtering by Federal Entity (State)
Retrieves research centers located in a specific Mexican state:
```bash
python scripts/openalex_mexico_cli.py get-institution \
  --state "Jalisco" \
  --limit 20 \
  --output ./data/instituciones_jalisco.json
```

### 4. Direct Lookup by ROR Identifier
```bash
python scripts/openalex_mexico_cli.py get-institution \
  --ror "01tmp8f25" \
  --output ./data/institucion_detalle.json
```

## Linking Workflow

1. **Resolve Institution:** Use `get-institution` to obtain the unique ROR (`https://ror.org/...`).
2. **Query Production:** Pass that ROR to [`openalex-mexico-works-search`](../openalex-mexico-works-search/SKILL.md) to extract all publications from the institution.
3. **Evaluate Indicators:** Pass the ROR to [`openalex-mexico-aggregations`](../openalex-mexico-aggregations/SKILL.md) to calculate its OA share and APC expenditure.

## References

- [Catalog of Major Mexican Institutions and ROR Codes](references/institutions_mexico_catalog.md)

## Common Mistakes and Anti-Patterns (Avoid Frequent Errors)

- ❌ **Anti-pattern 1: Treating specific campuses as unlinked institutions**  
  Searching for Tec de Monterrey or UAM and treating individual campuses or branches as isolated entities without considering the parent institution.  
  **Solution:** Check the `parent_name` and `parent_id` fields to consolidate or disaggregate production according to the scope of the study.
- ❌ **Anti-pattern 2: Assuming every institution has a registered acronym**  
  Searching only by `--acronym "INSP"` for smaller institutions or state centers that are registered only under their full name.  
  **Solution:** If `--acronym` yields no results, fall back to `--query "Full or Partial Name"`.
- ❌ **Anti-pattern 3: Violating File-Output First**  
  Omitting `--output`, causing the metadata JSON to be printed to stdout.  
  **Solution:** Always save to a file (`--output ./data/institucion.json`).
