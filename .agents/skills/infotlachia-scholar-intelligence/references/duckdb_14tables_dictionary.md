# Diccionario de Tablas de `analytics_cache.duckdb`

El almacén analítico de Info TlachIA se gestiona en DuckDB (`analytics_cache.duckdb`, 5.9 GB) para consultas de latencia ultrabaja ($< 10\text{ms}$).

---

## 1. Las 14 Tablas Consolidadas

| Tabla | Registros | Nivel de Análisis | Columnas Clave |
|---|---|---|---|
| `investigador_total` | 90,000 | Investigador (Consolidado) | `academic_name`, `is_snii`, `num_documents`, `citations`, `fwci_avg`, `pct_top_10`, `h_index`, `apc_paid_usd` |
| `investigador_annual` | 409,000 | Investigador $\times$ Año | Series temporales anuales de producción e impacto por autor |
| `investigador_recent` | 43,000 | Investigador (Últimos 3 años) | Dinámica de impacto reciente y citas en ventana móvil |
| `institucion_total` | 3,000 | Institución y Dependencia | Totales acumulados por universidad y facultad |
| `institucion_annual` | 63,000 | Institución $\times$ Año | Series temporales institucionales |
| `papers_profesor` | 1,250,000 | Documentos por Investigador | `academic_name`, `doi`, `title`, `year`, `citations`, `topics` |
| `papers_institucion` | 4,220,000 | Documentos por Institución | Documentos indexados por universidad |
| `topics_investigador` | 377,000 | Tópicos de Investigadores | Desglose temático de autores |
| `topics_institucion` | 223,000 | Tópicos Institucionales | Especialización temática por facultad |
| `keywords_investigador`| 3,730,000 | Palabras Clave de Autores | Palabras clave frecuentes por investigador |
| `keywords_institucion` | 1,110,000 | Palabras Clave Institucionales | Palabras clave por dependencia |
| `thematic_evolution_investigador` | 819,000 | Evolución de Tópicos (Autor) | Migración temporal de temas por autor |
| `thematic_evolution_institucion` | 949,000 | Evolución de Tópicos (Inst) | Trayectoria temática institucional |
| `umap_investigadores` | 18,700 | Coordenadas 2D/3D | Posicionamiento topológico de investigadores SNII |

---

## 2. Columnas Canónicas de Filtrado

* `db_level`: `'NATIONAL'`, `'INSTITUTION'`, `'ENTITY'`, `'RESEARCHER'`.
* `db_institution_name`: Nombre canónico (e.g. `'UNIVERSIDAD NACIONAL AUTONOMA DE MEXICO (UNAM)'`).
* `db_entity_name`: Nombre de la facultad o instituto (e.g. `'FACULTAD DE CIENCIAS'`).
* `db_academic_name`: Nombre normalizado (`'APELLIDO PATERNO MATERNO, NOMBRES'`).
