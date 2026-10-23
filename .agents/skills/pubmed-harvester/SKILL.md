---
name: pubmed-harvester
description: Extracción, paginación y normalización de literatura biomédica y clínica desde la API oficial de PubMed (NCBI E-utilities) hacia el esquema tabular canónico (Parquet, JSON, CSV).
---

# PubMed Data Harvester

Herramienta autónoma e independiente para la recolección de publicaciones indexadas en la National Library of Medicine (NLM / PubMed) mediante E-utilities (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils`), estandarizando automáticamente al esquema tabular canónico de la suite `sos-mcp-services`.

---

## Capacidades

- **Búsqueda Avanzada Entrez:** Soporte completo de términos MeSH, campos `[Title/Abstract]`, `[Affiliation]` y filtros de fechas.
- **Producción Autoral y Clínica:** Extracción por nombre de autor (`[Author]`) y cruce con afiliación (`[Affiliation]`).
- **Detección de Acceso Abierto en PMC:** Clasificación automática de obras con texto completo disponible en PubMed Central (`pmcid`).
- **Esquema Canónico:** Estandariza autores, identificadores cruzados (`pmid`, `doi`, `pmcid`), revista, fechas y vía de Acceso Abierto.

---

## Interfaz CLI

Entorno de ejecución:
```bash
python scripts/pubmed_harvest_cli.py [subcomando] [opciones]
```

### 1. Búsqueda Temática y de Afiliación
```bash
python scripts/pubmed_harvest_cli.py fetch-works \
  --query "idiopathic pulmonary fibrosis" \
  --affiliation "Mexico" \
  --year-from 2020 \
  --year-to 2026 \
  --limit 50 \
  --output ./ipf_mexico.parquet
```

### 2. Producción de un Autor por Nombre
```bash
python scripts/pubmed_harvest_cli.py fetch-author-works \
  --author "Pardo Annie" \
  --affiliation "UNAM" \
  --limit 100 \
  --output ./annie_pardo_pubmed.parquet
```

---

## Referencias Técnicas
- [Guía Técnica de E-utilities](references/pubmed_eutils_guide.md)
