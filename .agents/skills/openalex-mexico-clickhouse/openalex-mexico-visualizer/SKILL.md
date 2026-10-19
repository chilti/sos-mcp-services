---
name: openalex-mexico-visualizer
description: Generador de artefactos visuales interactivos y dashboards analíticos (HTML con Plotly.js, Redes PyVis y Tarjetas PNG) a partir de los datos cienciométricos extraídos por las skills del ecosistema OpenAlex México.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/openalex_visualizer_cli.py"
---

# OpenAlex México Visualizer

Capa de presentación y motor de generación de artefactos visuales interactivos para la producción científica mexicana.

## Overview

Transforma los resultados analíticos en formato JSON generados por las skills de datos (`openalex-mexico-aggregations`, `openalex-mexico-semantic-search`, `openalex-mexico-works-search`, etc.) en:
1. **Dashboards Ejecutivos HTML:** Archivos autocontenidos con tarjetas de KPIs, gráficos interactivos de Plotly.js y tablas dinámicas listos para el panel de vista previa.
2. **Series Temporales Duales:** Publicaciones anuales combinadas con la evolución cronológica del FWCI relativo al benchmark mundial (1.00).
3. **Donuts de Acceso Abierto:** Distribución de las 6 modalidades (Diamante vs Comercial) y cuantificación del gasto en APC.
4. **Rankings de Capacidad:** Barras horizontales interactivas con desambiguación y banderas de afiliación mexicana.
5. **Sunburst Taxonómico Jerárquico:** Gráfica multinivel concéntrica (Dominio → Campo → Subcampo → Tópico) con zoom interactivo.
6. **Matriz Oficial de los 17 ODS:** Cuadrícula con la paleta oficial de la ONU y tabla comparativa.
7. **Tarjetas Estáticas PNG:** Gráficas compactas a 200 DPI listas para incrustarse directamente en el chat.

## Dependencies

- **Entorno Python:** `/home/ambientesPy/revistaslatam`
- **Script CLI:** [`scripts/openalex_visualizer_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/openalex-mexico-clickhouse/openalex-mexico-visualizer/scripts/openalex_visualizer_cli.py)
- **Librerías principales:** `plotly`, `matplotlib`, `pyvis`

## CLI Interface

### 1. Generación Automática (Detección Inteligente)
El visualizador detecta la estructura interna del JSON (`top_entities`, `grouped_by`, `works`, etc.) y renderiza el artefacto correspondiente:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_visualizer_cli.py \
  --input ./data/datos.json \
  --title "Análisis Cienciométrico de Litio en México" \
  --output ./reports/artefacto_interactivo.html \
  --png ./reports/tarjeta_chat.png
```

### 2. Forzar un Tipo de Visualización Específico
Tipos disponibles (`--type`):
- `sunburst`: Para estructuras taxonómicas jerárquicas multinivel (Dominio → Campo → Subcampo → Tópico) en temas específicos (litio, IA, etc.).
- `sdg-grid`: Para la cuadrícula oficial de los 17 Objetivos de Desarrollo Sostenible (ODS).
- `top-ranking`: Para listas de autores o instituciones ordenadas por impacto o producción.
- `timeseries`: Para series temporales anuales con línea dual de FWCI y publicaciones.
- `oa-donut`: Para gráficos de proporción de vías de Acceso Abierto y gasto APC en USD.
- `dossier-works`: Para catálogos de publicaciones con desglose de coautoría internacional.
- `network`: Para redes interactivas de colaboración científica.

**Ejemplo para Sunburst de líneas de investigación:**
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_visualizer_cli.py \
  --input ./data/litio.json \
  --type sunburst \
  --title "Taxonomía de Investigación en Litio y Almacenamiento de Energía en México" \
  --output ./reports/sunburst_litio.html \
  --png ./reports/sunburst_litio.png
```

## Reglas Obligatorias para el Agente (LLM)

1. **REGLA DE ORO DE UBICACIÓN (WORKSPACE SOBERANO):**
   - **NUNCA guardes artefactos de salida (`--output`, `--png`) en `/tmp/`.**
   - El visor del panel derecho y el explorador de archivos de OpenHands **únicamente pueden leer archivos dentro del directorio de trabajo actual del proyecto**. Si guardas en `/tmp/`, el visor arrojará error `404 Not Found`.
   - Crea un subdirectorio `./reports/` o `./data/` dentro del workspace actual y guarda siempre allí tus archivos (ej. `./reports/sunburst.html`, `./reports/tarjeta.png`).

2. **Uso Exclusivo del CLI Oficial:**
   - **No improvises scripts de Plotly o Matplotlib hechos a mano.** Utiliza siempre `openalex_visualizer_cli.py`. El CLI ya implementa el tema visual oscuro oficial, tipografías ejecutivas, CDN optimizado y generación simultánea de la tarjeta PNG.

3. **Flujo en Dos Fases:**
   - **Fase 1 (Cómputo):** Obtén los datos crudos ejecutando la skill de datos idónea (`aggregations`, `works-search`, etc.) y guarda el resultado en `./data/datos.json`.
   - **Fase 2 (Visualización):** Invoca `openalex-mexico-visualizer` pasando dicho JSON para generar el HTML y el PNG en `./reports/`.

4. **Presentación de la Respuesta al Usuario:**
   - Proporciona tu resumen analítico cuantitativo en texto sobrio.
   - Incrusta la tarjeta estática PNG generada: `![Gráfica](reports/tarjeta.png)`.
   - Ofrece el enlace clickable relativo al artefacto interactivo: `[Abrir Dashboard Interactivo](reports/artefacto.html)`.

