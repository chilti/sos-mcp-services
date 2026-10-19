# Catálogo y Especificación de Artefactos Visuales

## 1. Principios de Diseño
Los artefactos generados por `openalex-mexico-visualizer` se apegan a los estándares de visualización cienciométrica de alto nivel:
- **Sobriedad y Rigor Académico:** Sin elementos decorativos innecesarios; enfoque en densidad de información y claridad analítica.
- **Paleta Cromática Canónica:**
  - *Diamante:* `#00A86B` (Verde esmeralda / No comercial)
  - *Dorada (APC):* `#E39918` (Amarillo oro)
  - *Híbrida:* `#3B82F6` (Azul comercial)
  - *Verde (Repositorio):* `#10B981`
  - *Bronce:* `#CD7F32`
  - *Cerrada:* `#6B7280`
  - *Línea de Benchmark Mundial FWCI:* `#EF4444` (Rojo discreto en $y=1.00$)
- **Responsividad y Autocontención:** Archivos `.html` portables que pueden visualizarse sin conexión a un servidor local ni dependencias de backend.

## 2. Tipos de Artefactos y Esquemas de Entrada

| Tipo de Artefacto | Estructura de Entrada JSON Esperada | Componentes Renderizados |
| :--- | :--- | :--- |
| `top-ranking` | `{ "top_entities": [ { "rank", "display_name", "total_works", "total_citations", "avg_fwci", "pct_top_10", "institution", "is_mexican_affiliated" } ] }` | Barra horizontal Plotly con escala Viridis por FWCI + Tabla comparativa con banderas de adscripción. |
| `timeseries` | `{ "grouped_by": "publication_year", "results": [ { "dimension", "total_works", "total_citations", "avg_fwci", "total_apc_paid_usd" } ] }` | Gráfica dual: barras de producción anual + línea de FWCI con benchmark $1.00$ + Tarjetas de KPIs. |
| `oa-donut` | `{ "grouped_by": "oa_status", "results": [ { "dimension", "total_works", "total_apc_paid_usd" } ] }` | Donut interactivo con las 6 vías de acceso + Tarjetas de gasto en APC y volumen Diamante. |
| `dossier-works` | `{ "works": [ { "title", "publication_year", "cited_by_count", "fwci", "oa_status", "authors_disambiguated" } ] }` | Tarjetas de resumen (Citas totales, FWCI medio, % Top 10) + Tabla filtrable con desglose nacional vs internacional. |
| `network` | `{ "works": [ { "author_names": [...] } ] }` | Grafo interactivo PyVis con física de resortes y nodos ponderados por coautoría. |
