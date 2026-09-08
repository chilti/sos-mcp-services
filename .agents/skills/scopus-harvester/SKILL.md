---
name: scopus-harvester
description: Extracción, paginación y normalización de literatura científica desde la API de Elsevier Scopus hacia tablas canónicas (Parquet, JSON, CSV).
---

# Scopus Data Harvester

Herramienta autónoma e independiente para la recolección de publicaciones indexadas en Elsevier Scopus a través de su API oficial (`https://api.elsevier.com/content/search/scopus`), con estandarización directa al esquema tabular canónico.

---

## Capacidades

- **Búsqueda Avanzada Scopus:** Soporte completo de sintaxis booleana y códigos de campo (`TITLE-ABS-KEY`, `AUTH`, `AFFIL`, `PUBYEAR`, etc.).
- **Perfiles de Autor e Institución:** Extracción por Scopus Author ID (`AU-ID`) o Scopus Affiliation ID (`AF-ID`).
- **Resiliencia de Red:** Detección automática y manejo de backoff ante límites de cuota (HTTP 429).
- **Citas Brutas Confiables:** Normaliza citas acumuladas (`citedby-count`) y metadatos sin suposiciones de FWCI.

---

## Interfaz CLI

Entorno de ejecución:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/scopus-harvester/scripts/scopus_harvest_cli.py [subcomando] [opciones]
```

### 1. Búsqueda temática
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/scopus-harvester/scripts/scopus_harvest_cli.py search \
  --query 'TITLE-ABS-KEY("deep learning" AND "medical imaging")' \
  --year-from 2021 \
  --year-to 2024 \
  --limit 50 \
  --output ./scopus_deep_learning.parquet
```

### 2. Publicaciones de un autor por AU-ID
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/scopus-harvester/scripts/scopus_harvest_cli.py author-profile \
  --author-id "57200234567" \
  --limit 100 \
  --output ./author_scopus.parquet
```

### 3. Publicaciones institucionales por AF-ID
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/scopus-harvester/scripts/scopus_harvest_cli.py affil-works \
  --af-id "60028190" \
  --year-from 2023 \
  --year-to 2024 \
  --limit 100 \
  --output ./unam_scopus_2023.parquet
```

---

## Referencias Técnicas
- [Sintaxis de Búsqueda Avanzada de Scopus](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/scopus-harvester/references/scopus_search_syntax.md)
- [Políticas de Cuota y Respuestas HTTP 429](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/scopus-harvester/references/elsevier_quota_policies.md)
