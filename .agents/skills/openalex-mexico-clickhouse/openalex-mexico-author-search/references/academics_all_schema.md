# Esquema de Datos: Autores e Investigadores de México en ClickHouse

## 1. Tabla `rag.authors_seed_mexico` (2,572,943 registros)
Catálogo unificado de autores asociados a México en OpenAlex con metadatos JSON completos:
- `id` (String): URI canónica (`https://openalex.org/A...`).
- `display_name` (String): Nombre principal reportado.
- `orcid` (String): Enlace ORCID normalizado.
- `raw_data` (String JSON): Objeto completo de OpenAlex con:
  - `works_count` (Int): Producción total del autor.
  - `cited_by_count` (Int): Citas totales acumuladas.
  - `summary_stats.h_index` (Int): Índice h calculado.
  - `last_known_institutions` (Array): Institución de adscripción más reciente con ROR.
  - `topics` (Array): Áreas temáticas y subcampos de especialización.

## 2. Tabla `rag.academics_all` (431,697 registros)
Padrón académico con resolución de dependencias institucionales y niveles SNII:
- `id` (String): Identificador canónico.
- `name` (String): Nombre completo.
- `institution` (String): Institución de adscripción.
- `dependency` (String): Facultad, centro o instituto (ej. `Facultad de Medicina`).
- `subdependency` (String): Departamento o división interna.
- `snii_level` (String): Nivel oficial (`Candidato`, `I`, `II`, `III`, `Emérito`).
- `paper_count` (UInt32): Número de publicaciones.
- `citation_count` (UInt32): Número de citas.
