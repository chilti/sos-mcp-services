---
name: revistaslatam-editorial-intelligence
description: Diccionario exhaustivo de Revistas Latam (Catálogo de Revistas Iberoamericanas, evaluación editorial, checklist de indización DOAJ/SciELO/Redalyc/Latindex 2.0, Acceso Abierto Diamante y multilingüismo).
---

# Skill: Revistas Latam Editorial Intelligence

## 1. Alcance y Evaluación Editorial Iberoamericana
Se activa para diagnósticos cienciométricos de revistas científicas, políticas de Acceso Abierto Diamante ($0 APC), indización y visibilidad internacional en América Latina, el Caribe, España y Portugal.

---

## 2. Indicadores y Checklist de Indización
1. **Acceso Abierto Diamante vs Comercial:**
   * Monitoreo de gratuidad total (sin cobro al autor ni al lector) frente al modelo APC comercial.
2. **Matriz de Indización Internacional y Regional:**
   * Índices globales: Scopus (SJR, Citescore, Cuartil Q1-Q4), Web of Science (JCR, ESCI).
   * Índices de calidad regional: DOAJ (Directorio de Revistas de Acceso Abierto con Seal), SciELO (Scientific Electronic Library Online), Redalyc (Red de Revistas Científicas de ALyC), Latindex Catálogo 2.0 (cumplimiento de 38 criterios de calidad editorial), Dialnet, MIAR, AmeliCA.
3. **Métricas de Internacionalización y Calidad:**
   * Endogamia editorial: Porcentaje de autores y revisores externos a la institución editora.
   * Internacionalización del Comité Editorial y de los autores firmantes.
   * Flujo editorial: Días promedio de revisión por pares, tasa de aceptación/rechazo y periodicidad.
4. **Multilingüismo y Políticas de Autoarchivo:**
   * Distribución de artículos por idioma (Español, Portugués, Inglés).
   * Políticas de autoarchivo y derechos de autor registradas en Sherpa Romeo y Diadorim (políticas Verde, Azul, Amarilla, etc.).

---

## 3. Fuentes de Datos y Microservicio
* `revistaslatam-mcp` (Puerto 8013): Microservicio de consulta editorial y metadatos de revistas.
* `pipeline_revistaslatam/`: Bases de datos locales de revistas, editoriales y cruces de indexación.
