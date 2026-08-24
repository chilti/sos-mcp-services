---
name: infotlachia-scholar-intelligence
description: Diccionario exhaustivo de inteligencia bibliométrica de Info TlachIA (DuckDB analytics_cache, Padrón SNII 2025, 4 niveles de agregación, APC estimado, Gini temático, UMAP 2D/3D y Parquets analíticos).
---

# Skill: Info TlachIA Scholar Intelligence

## 1. Alcance y Niveles de Agregación
Se activa para cualquier consulta sobre investigadores de México, dependencias de la UNAM, instituciones nacionales o análisis global del padrón SNII.

### Los 4 Niveles de Granularidad:
1. **Nivel 1 (Investigador):** Identificación canónica en Padrón SNII 2025 (20,333 investigadores). Datos: Nivel (Candidato, 1, 2, 3, Emérito), Área de Conocimiento (I a IX), Institución y Subdependencia de Acreditación, ORCID verificado, Scopus Author ID y OpenAlex Author ID.
2. **Nivel 2 (Dependencia):** Subdependencias académicas (ej. Facultad de Ciencias, Instituto de Física, ICN, FES Iztacala). Métricas agregadas y coautorías internas.
3. **Nivel 3 (Institución):** Universidades y Centros Públicos de Investigación (UNAM, CINVESTAV, UAM, IPN, ITESM, etc.) vinculados mediante identificador canónico ROR.
4. **Nivel 4 (México / Nacional):** Producción agregada del país en ClickHouse (`works_flat` con 569M de papers y `works_academic_all` con papers de autores en México).

---

## 2. Indicadores y Métricas Precalculadas Disponibles
* **FWCI (Field-Weighted Citation Impact):** Citas normalizadas por campo, tipo de documento y año (1.0 = promedio mundial).
* **Excelencia (% Top 10%):** Proporción de artículos en el 10% más citado a nivel mundial.
* **Desglose de Acceso Abierto (6 Vías):**
  * **Diamante:** Revistas no comerciales sin cobro por publicar ni leer ($0 APC).
  * **Gold APC:** Revistas de acceso abierto comerciales con cobro de procesamiento de artículo.
  * **Hybrid:** Artículos abiertos dentro de revistas de suscripción cerrada.
  * **Bronze:** Acceso libre en la web del editor sin licencia abierta formal.
  * **Green:** Autoarchivo en repositorios institucionales/temáticos.
  * **Closed:** Acceso cerrado tradicional.
* **Gasto Estimado en APC (USD):** Monto total acumulado pagado a editoriales comerciales por concepto de Article Processing Charges.
* **Índice de Gini Temático:** Concentración vs. dispersión disciplinar (cercano a 0 = hiper-especializado; cercano a 1 = alta diversidad interdisciplinaria).
* **Posicionamiento UMAP:** Coordenadas 2D/3D para ubicar al investigador frente a sus pares del mismo nivel y área.

---

## 3. Manejador de Base de Datos Embebido: DuckDB (`analytics_cache.duckdb`)
Ubicación: `/home/sinapsisai/data/analytics_cache.duckdb` (4.97 GB).
Consultas SQL ultrarrápidas (< 5ms) mediante la herramienta `query_duckdb_analytics(sql_query)`.

### Columnas Canónicas de Filtrado en DuckDB:
* `db_level`: `'NATIONAL'`, `'INSTITUTION'`, `'ENTITY'` o `'RESEARCHER'`.
* `db_institution_name`: Nombre de la institución (ej. `'UNIVERSIDAD NACIONAL AUTONOMA DE MEXICO (UNAM)'`).
* `db_entity_name`: Nombre de la dependencia o facultad (ej. `'FACULTAD DE CIENCIAS'`).
* `db_academic_name`: Nombre oficial del investigador en formato `'APELLIDO PATERNO MATERNO, NOMBRES'`.
* `db_view_mode`: `'capacidad_instalada'` o `'produccion_institucional'`.

### Las 14 Tablas Consolidadas:
1. `institucion_annual` (63k filas): Series temporales anuales de instituciones.
2. `institucion_total` (3k filas): Totales acumulados por institución.
3. `investigador_annual` (409k filas): Series anuales por investigador SNII.
4. `investigador_total` (90k filas): Totales consolidados por investigador (H-index, FWCI, citas, docs).
5. `investigador_recent` (43k filas): Producción de los últimos 3 años.
6. `papers_profesor` (1.25M filas): Artículos por investigador con DOI, citas, año y topics.
7. `papers_institucion` (4.22M filas): Artículos completos indexados por institución.
8. `topics_institucion` (223k filas): Tópicos por institución y facultad.
9. `topics_investigador` (377k filas): Tópicos clasificados por investigador.
10. `keywords_institucion` (1.11M filas): Palabras clave agregadas por institución.
11. `keywords_investigador` (3.73M filas): Palabras clave por investigador.
12. `thematic_evolution_institucion` (949k filas): Evolución temática temporal institucional.
13. `thematic_evolution_investigador` (819k filas): Evolución temática temporal por investigador.
14. `umap_investigadores` (18.7k filas): Coordenadas UMAP 2D del Padrón Nacional.

---

## 4. Fuentes ClickHouse Masivas
* `works_academic_all`: Tabla materializada con 1,652,927 artículos de académicos de México.
* `works_flat`: 569,000,000 de trabajos globales de OpenAlex.
