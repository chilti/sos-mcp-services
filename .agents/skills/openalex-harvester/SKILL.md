---
name: openalex-harvester
description: Extracción, paginación por cursor y normalización de literatura científica desde OpenAlex hacia tablas canónicas (Parquet, JSON, CSV).
---

# OpenAlex Data Harvester

Herramienta autónoma e independiente para la recolección masiva de registros científicos desde la API de OpenAlex (`https://api.openalex.org` o endpoints locales), con soporte de paginación por cursor y mapeo al esquema tabular canónico.

---

## Capacidades

- **Búsqueda temática flexible:** Por palabras clave, títulos, tópicos y fechas.
- **Producción autoral e institucional:** Descarga directa por ORCID, OpenAlex Author ID o ROR de instituciones.
- **Filtros de Ciencia Abierta:** Segmentación por vía de Acceso Abierto (`gold`, `diamond`, `green`, `hybrid`, `closed`).
- **Mapeo al Esquema Canónico:** Estandariza autores, afiliaciones, citas, FWCI, percentiles, APC y referencias en un archivo Parquet, JSON o CSV.

---

## Interfaz CLI

Entorno de ejecución:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-harvester/scripts/openalex_harvest_cli.py [subcomando] [opciones]
```

### 1. Búsqueda temática o de revista
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-harvester/scripts/openalex_harvest_cli.py fetch-works \
  --query "quantum computing" \
  --year-from 2020 \
  --year-to 2024 \
  --limit 100 \
  --output ./quantum_works.parquet
```

### 2. Producción de un autor por ORCID o ID
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-harvester/scripts/openalex_harvest_cli.py fetch-author-works \
  --author-id "0000-0002-1825-0097" \
  --limit 200 \
  --output ./author_works.parquet
```

### 3. Producción institucional por ROR
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-harvester/scripts/openalex_harvest_cli.py fetch-institution-works \
  --ror "012gw1n35" \
  --year-from 2023 \
  --year-to 2024 \
  --limit 500 \
  --output ./unam_2023_2024.parquet
```

---

## Referencias Técnicas
- [Parámetros y Filtros de la API](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-harvester/references/openalex_api_parameters.md)
- [Guía de Paginación por Cursor](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-harvester/references/cursor_paging_guide.md)
