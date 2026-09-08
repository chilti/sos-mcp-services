---
name: semantic-scholar-harvester
description: Extracción de artículos, resúmenes y grafos de citas desde Semantic Scholar Graph API hacia tablas canónicas (Parquet, JSON, CSV).
---

# Semantic Scholar Data Harvester

Herramienta autónoma e independiente para consultar la base de conocimiento de Semantic Scholar (`https://api.semanticscholar.org/graph/v1`), descargar publicaciones por palabras clave o autor, y reconstruir subgrafos de citación directa (entrantes y salientes).

---

## Capacidades

- **Búsqueda Temática Amplia:** Búsqueda textual y filtrado por rangos de años sin necesidad obligatoria de API key.
- **Construcción de Grafos de Citas:** Descarga simultánea de citas entrantes y referencias bibliográficas de cualquier artículo.
- **Mapeo Canónico Estandarizado:** Generación directa de archivos Parquet, JSON o CSV consumibles por los motores de indicadores y redes.

---

## Interfaz CLI

Entorno de ejecución:
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/semantic-scholar-harvester/scripts/s2_harvest_cli.py [subcomando] [opciones]
```

### 1. Búsqueda temática
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/semantic-scholar-harvester/scripts/s2_harvest_cli.py search-papers \
  --query "knowledge graphs science" \
  --year-from 2022 \
  --year-to 2024 \
  --limit 50 \
  --output ./s2_knowledge_graphs.parquet
```

### 2. Extracción de grafo de citaciones de un paper
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/semantic-scholar-harvester/scripts/s2_harvest_cli.py citation-graph \
  --paper-id "10.1038/s41586-020-2649-2" \
  --output ./paper_citation_subgraph.parquet
```

### 3. Publicaciones de un autor por S2 Author ID
```bash
/home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/semantic-scholar-harvester/scripts/s2_harvest_cli.py author-papers \
  --author-id "1741101" \
  --limit 50 \
  --output ./author_papers.parquet
```

---

## Referencias Técnicas
- [Campos y Estructura de Semantic Scholar Graph API](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/semantic-scholar-harvester/references/s2_graph_api_fields.md)
- [Concepto de Citas Influyentes](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/semantic-scholar-harvester/references/influential_citations_concept.md)
