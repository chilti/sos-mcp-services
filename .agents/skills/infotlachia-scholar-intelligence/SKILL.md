---
name: infotlachia-scholar-intelligence
description: Diccionario exhaustivo de inteligencia bibliométrica de Info TlachIA (Padrón SNII 2025, 4 niveles de agregación, APC estimado, Gini temático, UMAP 2D/3D y Parquets analíticos).
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

## 3. Diccionario de Tablas Parquet y ClickHouse
* `institucion_annual`: Series temporales anuales de producción, citas y FWCI por institución ROR.
* `investigador_annual`: Series temporales anuales por investigador SNII.
* `papers_profesor`: Relación de papers individuales (DOI, título, año, citas, fwci, oa_status, apc_usd) por académico.
* `papers_institucion`: Publicaciones indexadas por ROR institucional.
* `topics`: Mapeo a los 4,500 tópicos de SciVal/OpenAlex.
* `umap_investigadores`: Coordenadas UMAP y métricas normalizadas.
* `works_academic_all`: Tabla materializada en ClickHouse con la producción de autores SNII.
