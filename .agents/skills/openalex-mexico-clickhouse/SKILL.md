---
name: openalex-mexico-clickhouse
description: >-
  Motor maestro y orquestador analítico sobre la producción científica de México en ClickHouse (1.65M trabajos en rag.works_academic_all, 2.57M autores en rag.authors_seed_mexico, 456K instituciones en rag.institutions_seed_mexico). Orquesta agregaciones de acceso abierto (Diamond vs Gold APC), gasto en USD, búsqueda y desambiguación de autores con padrón SNII, catálogo institucional ROR, búsqueda semántica vectorial nomic (768d) y visualización interactiva, bajo la regla estricta de CERO JOINs y principio File-Output First.
metadata:
  python: ">=3.10"
  script: "shared_scripts/openalex_mexico_cli.py"
---

# OpenAlex México ClickHouse: Motor Analítico y Orquestador Nacional

## 1. Overview y Propósito

Esta skill actúa como el **orquestador central** para la consulta, extracción y análisis de la producción científica mexicana alojada en el clúster ClickHouse de la UNAM. 

La base de datos `rag` aloja el universo completo de investigación de México estructurado en tablas columnares masivas desnormalizadas:
* **`rag.works_academic_all` (~1.65 millones de registros):** Trabajos con afiliación mexicana, incluyendo métricas normalizadas de impacto (FWCI, percentil, Top 10%, Top 1%), tipología de acceso abierto (6 vías OA, APC pagado y de lista en USD), Objetivos de Desarrollo Sostenible (ODS 1–17), taxonomía temática (Domain, Field, Subfield, Topic) y embeddings vectoriales `nomic` de 768 dimensiones.
* **`rag.authors_seed_mexico` (~2.57 millones de registros):** Catálogo de autores con producción en México, métricas de citas, h-index y variantes hispanas.
* **`rag.academics_all` (~431 mil registros):** Investigadoras e investigadores con cruce del Padrón Oficial SNII, vigencia y adscripción.
* **`rag.institutions_seed_mexico` (~456 mil registros):** Catálogo institucional nacional con identificadores ROR, variantes de nombres y acrónimos (UNAM, IPN, UAM, Cinvestav, etc.).

---

## 2. Dependencies y Cadena de Valor

* **Entorno de Ejecución:** `python` con librería `clickhouse-connect`.
* **Script CLI Canónico:** `shared_scripts/openalex_mexico_cli.py` (motor multi-comando de 1,300 líneas con validación de seguridad integrada).
* **Parámetros de Conexión:** Servidor ClickHouse configurado en variables de entorno (`CLICKHOUSE_HOST=10.90.0.87`, `CLICKHOUSE_PORT=8124`, `CLICKHOUSE_DATABASE=rag`).
* **Habilidades Especializadas de la Suite:**
  * [`openalex-mexico-query-architect`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-query-architect/SKILL.md): Validador y consultor de sentencias SQL seguras.
  * [`openalex-mexico-aggregations`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-aggregations/SKILL.md): Agregaciones de vías OA, APC USD y series temporales.
  * [`openalex-mexico-works-search`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-works-search/SKILL.md): Extracción de publicaciones por filtros complejos.
  * [`openalex-mexico-author-search`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-author-search/SKILL.md): Desambiguación de investigadoras/es y nivel SNII.
  * [`openalex-mexico-institutions`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-institutions/SKILL.md): Mapeo ROR y catálogo institucional.
  * [`openalex-mexico-semantic-search`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-semantic-search/SKILL.md): Búsqueda semántica vectorial (embeddings nomic 768d).
  * [`openalex-mexico-visualizer`](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-visualizer/SKILL.md): Dashboards interactivos Plotly y redes PyVis.

---

## 3. Regla de Oro: Prohibición Estricta de JOINs

> [!CAUTION]
> En la infraestructura analítica de la UNAM, **queda terminantemente prohibido formular sentencias con `JOIN` directo** en ClickHouse.
> Toda consulta que contenga la palabra clave `JOIN` será interceptada y rechazada automáticamente con error por `openalex_mexico_cli.py`.

### ¿Por qué no se necesitan JOINs?
Porque la tabla `rag.works_academic_all` ya está completamente desnormalizada a nivel de documento. En lugar de cruzar tablas:
* **Para filtrar por institución:** Usar `has(institution_rors, 'https://ror.org/01tmp8f25')`.
* **Para filtrar por autor:** Usar `arrayExists(x -> positionCaseInsensitiveUTF8(x, 'Apellido Nombre') > 0, author_names)`.
* **Para clasificaciones temáticas:** Filtrar directamente sobre las columnas `domain`, `field`, `subfield` o `topic`.

---

## 4. Subcomandos CLI Canónicos (File-Output First)

Todos los comandos deben ejecutarse especificando `--output <ruta>` obligatoria y límites explícitos:

### 1. Agregaciones Cienciométricas (`aggregate`)
```bash
python shared_scripts/openalex_mexico_cli.py aggregate \
  --group-by "oa_status" \
  --filter "publication_year >= 2020" \
  --output ./data/acceso_abierto_mexico.json
```

### 2. Búsqueda de Publicaciones Científicas (`search-works`)
```bash
python shared_scripts/openalex_mexico_cli.py search-works \
  --query "artificial intelligence in education" \
  --year-from 2020 --year-to 2025 \
  --only-top-10 \
  --limit 100 \
  --output ./data/ia_educacion_top10.json
```

### 3. Búsqueda y Desambiguación de Investigadores (`search-authors`)
```bash
python shared_scripts/openalex_mexico_cli.py search-authors \
  --name "Gorbea Portal" \
  --institution "UNAM" \
  --limit 10 \
  --output ./data/investigador_desambiguado.json
```

### 4. Ranking de Entidades Líderes en un Tema (`top-entities`)
```bash
python shared_scripts/openalex_mexico_cli.py top-entities \
  --topic "Vaccines" \
  --entity-type "institutions" \
  --limit 20 \
  --output ./data/top_instituciones_vacunas.json
```

### 5. Búsqueda Semántica Vectorial (`semantic-search`)
```bash
python shared_scripts/openalex_mexico_cli.py semantic-search \
  --query "soberanía alimentaria y maíces nativos" \
  --threshold 0.75 \
  --limit 50 \
  --output ./data/busqueda_semantica_maiz.json
```

### 6. Validación de Consultas SQL (`validate-query`)
```bash
python shared_scripts/openalex_mexico_cli.py validate-query \
  --query "SELECT title, publication_year FROM rag.works_academic_all WHERE has(institution_rors, 'https://ror.org/01tmp8f25') LIMIT 10" \
  --output ./data/reporte_validacion.json
```

---

## 5. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Formular consultas con sentencias `JOIN`**  
  Intentar cruzar `rag.works_academic_all` con `rag.authors_seed_mexico` usando `JOIN`. El motor de ClickHouse degrada su rendimiento y `openalex_mexico_cli.py` aborta la ejecución con `ValueError`.  
  **Solución:** Consultar las columnas de arrays nativas pre-materializadas (`author_names`, `institution_rors`).
- ❌ **Anti-patrón 2: Consultas `SELECT *` sin `--limit` ni `--output`**  
  Intentar extraer cientos de miles de filas sin paginación ni límite, saturando la memoria del servidor y la consola.  
  **Solución:** Especificar siempre un `--limit` deliberado (e.g. 50, 100) y escribir a un archivo estructurado mediante `--output`.
- ❌ **Anti-patrón 3: Búsquedas de nombres sensibles a mayúsculas o sin diacríticos**  
  Usar `author_name = 'Jose Lopez'` o `LIKE '%Lopez%'`. Omitir acentos o variaciones de capitalización omite hasta el 60% de los registros en nombres hispanos.  
  **Solución:** Usar `positionCaseInsensitiveUTF8(x, 'López') > 0` o el subcomando `search-authors` que normaliza diacríticos automáticamente.
- ❌ **Anti-patrón 4: Contar coautores internacionales como investigadoras/es mexicanas/os**  
  Asumir que todos los autores de un artículo mexicano pertenecen a instituciones del país. Un artículo multicéntrico puede tener 20 coautores extranjeros y 1 mexicano.  
  **Solución:** Desambiguar autores usando `rag.academics_all` o filtrando autores vinculados a RORs de México.
- ❌ **Anti-patrón 5: Violación de File-Output First (Almacenar en `/tmp/`)**  
  Guardar los resultados en directorios temporales globales del sistema operativo que pueden ser borrados o inaccesibles.  
  **Solución:** Guardar siempre los resultados dentro del workspace actual (`./data/` o en `scratch/` del artefacto).

---

## 6. Referencias Técnicas

- [OpenAlex México CLI Engine](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/shared_scripts/openalex_mexico_cli.py)
- [Query Architect (Guardián CERO JOINs)](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-query-architect/SKILL.md)
- [Aggregations Engine](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-aggregations/SKILL.md)
- [Estándar Canónico de Diseño de Skills](file:///c:/Users/jlja/Documents/Proyectos/sos-mcp-services/docs/estandar_diseno_skills_cientificas.md)
