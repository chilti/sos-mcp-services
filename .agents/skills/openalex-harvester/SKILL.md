---
name: openalex-harvester
description: Extracción, paginación por cursor y normalización de literatura científica desde OpenAlex hacia tablas canónicas (Parquet, JSON, CSV).
metadata:
  python: ">=3.10"
  script: "scripts/openalex_harvest_cli.py"
---
# OpenAlex Data Harvester

Herramienta autónoma e independiente para la recolección masiva de registros científicos desde la API de OpenAlex (`https://api.openalex.org` o endpoints locales), con soporte de paginación por cursor y mapeo al esquema tabular canónico.

---

## Capacidades

- **Búsqueda temática flexible:** Por palabras clave, títulos, tópicos y fechas a nivel mundial.
- **Producción autoral e institucional:** Descarga directa por ORCID, OpenAlex Author ID o ROR de instituciones.
- **Filtros de Ciencia Abierta:** Segmentación por vía de Acceso Abierto (`gold`, `diamond`, `green`, `hybrid`, `closed`).
- **Mapeo al Esquema Canónico:** Estandariza autores, afiliaciones, citas, FWCI, percentiles, APC y referencias en un archivo Parquet, JSON o CSV.

---

## Dependencies y Cadena de Valor

- **Entorno Python:** Python 3.10+ (con dependencias requeridas)
- **Script CLI:** `scripts/openalex_harvest_cli.py`
- **Habilidades Downstream:**
  - [`tlachia-metrics-engine`](../tlachia-metrics-engine/SKILL.md): Procesa el archivo Parquet canónico para calcular más de 30 indicadores cienciométricos.
  - [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md): Extrae redes de coautoría, acoplamiento bibliográfico y co-ocurrencia de términos.
  - [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Recibe la matriz de perfiles calculada a partir del corpus.
- **Diferenciación con `openalex-mexico-clickhouse`:**
  - Si la consulta es sobre **México** (universidades mexicanas, investigadores SNII, producción nacional), utilizar [`openalex-mexico-clickhouse`](../openalex-mexico-clickhouse/SKILL.md) que consulta el clúster ClickHouse local ultrarrápido con embeddings y CERO JOINs.
  - Usar `openalex-harvester` cuando se requiera cosechar literatura de **cualquier país o tema del mundo** directamente desde la API global de OpenAlex hacia archivos Parquet canónicos.

---

## Interfaz CLI

Entorno de ejecución:

```bash
python scripts/openalex_harvest_cli.py [subcomando] [opciones]
```

### 1. Búsqueda temática o de revista

```bash
python scripts/openalex_harvest_cli.py fetch-works \
  --query "quantum computing" \
  --year-from 2020 \
  --year-to 2024 \
  --limit 100 \
  --output ./data/quantum_works.parquet
```

### 2. Producción de un autor por ORCID o ID

```bash
python scripts/openalex_harvest_cli.py fetch-author-works \
  --author-id "0000-0002-1825-0097" \
  --limit 200 \
  --output ./data/author_works.parquet
```

### 3. Producción institucional por ROR

```bash
python scripts/openalex_harvest_cli.py fetch-institution-works \
  --ror "012gw1n35" \
  --year-from 2023 \
  --year-to 2024 \
  --limit 500 \
  --output ./data/unam_2023_2024.parquet
```

---

## Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Cosechar por API pública literatura que ya reside en ClickHouse local**  
  Usar `openalex-harvester` para descargar artículos de la UNAM o México a través de la API externa con latencia de red.  
  **Solución:** Para cualquier investigación de México, recurrir directamente a `openalex-mexico-clickhouse` (1.65M de obras locales con tiempo de respuesta en milisegundos).
- ❌ **Anti-patrón 2: Usar paginación tradicional por página para grandes volúmenes**  
  OpenAlex limita la paginación convencional a los primeros 10,000 registros.  
  **Solución:** El CLI utiliza automáticamente paginación por cursor (`cursor=*`) para recolecciones exhaustivas.
- ❌ **Anti-patrón 3: Exportar grandes volúmenes a JSON en lugar de Parquet**  
  Generar archivos JSON gigantescos para decenas de miles de artículos.  
  **Solución:** Usar `--output <ruta>.parquet`. El formato Parquet columnar reduce el tamaño en disco hasta un 85% y preserva los tipos de datos exactos.
- ❌ **Anti-patrón 4: Violación de File-Output First**  
  Intentar procesar sin especificar `--output`. El CLI requiere siempre una ruta de archivo estructurado de destino.

---

## Referencias Técnicas

- [Parámetros y Filtros de la API](references/openalex_api_parameters.md)
- [Guía de Paginación por Cursor](references/cursor_paging_guide.md)
