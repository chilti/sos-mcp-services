---
name: arxiv-harvester
description: Descarga y normalización de preprints científicos desde la API Atom XML de arXiv hacia tablas canónicas (Parquet, JSON, CSV).
---

# arXiv Data Harvester

Herramienta autónoma e independiente para la recolección de literatura científica y preprints desde el repositorio abierto de arXiv (`https://export.arxiv.org/api/query`), con respeto riguroso del intervalo de cortesía de 3 segundos y conversión al formato tabular canónico.

---

## Capacidades

- **Búsqueda por Taxonomía:** Filtrado temático por categorías oficiales (`cs.AI`, `stat.ML`, `physics.soc-ph`, etc.).
- **Descarga por Identificadores:** Recuperación directa de listas de IDs de arXiv.
- **Acceso Abierto Verde:** Marcado estandarizado de preprints con metadatos de autoría y enlaces a versiones.
- **Formato Canónico:** Archivos Parquet, JSON o CSV listos para análisis en redes y descriptores temáticos.

---

## Interfaz CLI

Entorno de ejecución:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/arxiv-harvester/scripts/arxiv_harvest_cli.py [subcomando] [opciones]
```

### 1. Búsqueda temática por categoría y palabras clave
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/arxiv-harvester/scripts/arxiv_harvest_cli.py search \
  --category "cs.AI" \
  --query "large language models" \
  --limit 50 \
  --output ./arxiv_llms.parquet
```

### 2. Recuperación por lista de identificadores
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/arxiv-harvester/scripts/arxiv_harvest_cli.py fetch-by-ids \
  --id-list "2301.07041,2303.08774,2401.12345" \
  --output ./arxiv_selected.parquet
```

---

## Referencias Técnicas
- [Taxonomía de Categorías de arXiv](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/arxiv-harvester/references/arxiv_categories_taxonomy.md)
- [Sintaxis de Consultas y Reglas de la API](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/arxiv-harvester/references/arxiv_query_syntax.md)
