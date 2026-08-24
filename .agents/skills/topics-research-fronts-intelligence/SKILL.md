---
name: topics-research-fronts-intelligence
description: Diccionario exhaustivo de Topics & Research Fronts v5.0 (Linajes aluviales AMI, coautoría internacional país-país, cuadrantes geopolíticos, jerarquía taxonómica Sunburst y alineación con ODS 1-17).
---

# Skill: Topics & Research Fronts Intelligence

## 1. Alcance y Motor de Frentes de Investigación v5.0
Se activa para análisis de frentes de investigación, linajes temáticos longitudinales, diplomacia científica internacional y evaluación de impacto en Desarrollo Sostenible (ODS).

---

## 2. Indicadores y Visualizaciones Precalculadas Disponibles
1. **Linajes Longitudinales (Métrica AMI - Adjusted Mutual Information):**
   * Rastreo temporal de frentes en ventanas móviles ($T_1, T_2, \dots, T_k$).
   * Detección de dinámicas: Persistencia (estabilidad), División (*splits*), Fusión (*merges*) y Emergencia de micro-frentes nuevos.
2. **Mapa Coroplético y Red de Coautoría Internacional (`_collab.parquet`):**
   * Matriz de coautorías internacionales (`country_a`, `country_b`, `count`).
   * Red topológica mundial por regiones (América del Norte, Europa, Latinoamérica, Asia-Pacífico).
3. **Cuadrantes de Posicionamiento Geopolítico:**
   * Scatter plot: Eje X: $\log(\text{Producción})$, Eje Y: FWCI promedio, Tamaño: % Top 10% (Excelencia).
   * Clasificación en 4 cuadrantes: Líderes consolidados, Productores masivos, Nichos de excelencia y Emergentes.
4. **Composición Taxonómica Jerárquica (Sunburst):**
   * Estructura arbórea: `Domain` $\rightarrow$ `Field` $\rightarrow$ `Subfield` $\rightarrow$ `Topic` para medir concentración disciplinar.
5. **Alineación con Objetivos de Desarrollo Sostenible (ODS 1 al 17):**
   * Mapeo de publicaciones por institución/país vinculadas a las metas de la ONU (`_inst.parquet`, `sdg_docs`).

---

## 3. Fuentes de Datos Locales
* `data/cache_temas/`: Tablas parquet agregadas por subcampo, país e institución.
* `_collab.parquet`: Pares de colaboración internacional.
* `_inst.parquet`: Desempeño institucional y desglose ODS.
