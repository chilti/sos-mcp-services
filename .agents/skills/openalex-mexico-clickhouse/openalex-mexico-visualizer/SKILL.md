---
name: openalex-mexico-visualizer
description: "Generador de artefactos visuales interactivos (HTML con Plotly.js) y tarjetas ejecutivas PNG (200 DPI). Renderiza gráficas de barras para rankings institucionales/autores ('top-ranking'), series temporales duales ('timeseries'), donas de acceso abierto y APC ('oa-donut'), sunburst taxonómico multinivel ('sunburst'), cuadrícula de los 17 ODS ('sdg-grid') y catálogos de publicaciones ('dossier-works'). Guarda siempre en './reports/'."
metadata:
  python: "/home/ambientesPy/revistaslatam"
  script: "scripts/openalex_visualizer_cli.py"
---

# OpenAlex México Visualizer

Capa de presentación y motor de generación de artefactos visuales interactivos para la producción científica mexicana.

## Overview

Transforma los resultados analíticos en formato JSON generados por las skills de datos (`openalex-mexico-aggregations`, `openalex-mexico-semantic-search`, `openalex-mexico-works-search`, etc.) en:
1. **Gráficas de Barras Horizontales (`top-ranking`):** Ranking de capacidad institucional o autores coloreado por FWCI con tabla detallada y badges de adscripción.
2. **Series Temporales Duales (`timeseries`):** Publicaciones anuales combinadas con la evolución cronológica del FWCI relativo al benchmark mundial (1.00).
3. **Donuts de Acceso Abierto (`oa-donut`):** Distribución de las 6 modalidades (Diamante vs Comercial) y cuantificación del gasto en APC.
4. **Sunburst Taxonómico Jerárquico (`sunburst`):** Gráfica concéntrica multinivel (Dominio → Campo → Subcampo → Tópico) con zoom interactivo.
5. **Matriz Oficial de los 17 ODS (`sdg-grid`):** Cuadrícula con la paleta oficial de la ONU y tabla comparativa.
6. **Dossier de Publicaciones (`dossier-works`):** Catálogos de publicaciones con desglose de coautoría nacional vs internacional.
7. **Tarjetas Estáticas PNG:** Gráficas compactas a 200 DPI listas para incrustarse directamente en el chat.

## Dependencies

- **Entorno Python:** `/home/ambientesPy/revistaslatam`
- **Script CLI:** `scripts/openalex_visualizer_cli.py`
- **Librerías principales:** `plotly`, `matplotlib`, `pyvis`

---

## ⚠️ PROHIBICIÓN DE RECICLAJE Y FLUJO OBLIGATORIO EN 2 FASES

> [!CAUTION]
> ### 1. Prohibición Estricta de Reutilización de Archivos Ajenos
> **NUNCA busques ni enlaces archivos generados en directorios padre o sesiones anteriores (`../<hash>/`).**
> Si el usuario pide *"muestra el sunburst"*, *"grafica el ranking"* o *"haz una dona de OA"*:
> * **NO asumas que el archivo ya existe.**
> * **NO uses grep hacia carpetas hermanas.**
> * Si intentas enlazar un archivo externo, el visor de Canvas de OpenHands fallará mostrando una pantalla negra o texto crudo.

> [!IMPORTANT]
> ### 2. Flujo en Dos Fases Obligatorio
> * **Fase 1 (Cómputo Cuantitativo):** Ejecuta la skill analítica adecuada (`openalex-mexico-aggregations` o `openalex-mexico-works-search`) y genera el archivo JSON en `./data/<nombre>.json` dentro del workspace actual.
> * **Fase 2 (Renderizado):** Invoca `openalex_visualizer_cli.py` con ese JSON para producir el `.html` interactivo y la tarjeta `.png` en `./reports/`.
> * **Fase 3 (Presentación):** Invoca `canvas_ui_control` pasando la ruta local `./reports/<nombre>.png`.

---

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
- `top-ranking`: **Gráfica de barras horizontales** para rankings de instituciones o investigadoras/es ordenadas por publicaciones y coloreadas por FWCI.
- `sunburst`: Para estructuras taxonómicas jerárquicas multinivel (Dominio → Campo → Subcampo → Tópico) en temas específicos (litio, IA, etc.).
- `sdg-grid`: **Cuadrícula oficial de los 17 ODS de la ONU (Agenda 2030)** con paleta cromática oficial, tabla comparativa de FWCI y soporte para los 4 niveles: Nacional (México completo), Institucional (por ROR o acrónimo), Autor/Investigador (por OpenAlex ID o nombre) y Temático.
- `timeseries`: Para series temporales anuales con línea dual de FWCI y publicaciones con benchmark en 1.00.
- `oa-donut`: Para gráficos de dona de proporción de vías de Acceso Abierto y gasto APC en USD.
- `dossier-works`: Para catálogos de publicaciones con desglose de coautoría internacional.
- `network`: Para redes interactivas de colaboración científica en física de resortes.
- `collaborating-countries`: Para el mapa mundi coroplético interactivo de países colaboradores internacionales (Plotly.js).
- `scientific-vocabulary`: Para el vocabulario científico y nube interactiva de palabras con buscador en vivo y gráfica de frecuencias.
- `coauthra-network`: Para la red dinámica de coautoría interactiva con CoAuthra (vía ORCID u OpenAlex ID).
- `quadrant-matrix`: Matriz estratégica de 4 cuadrantes (Liderazgo vs Impacto FWCI).
- `geopolitical-sankey`: Diagrama de flujos de colaboración geopolítica por bloques regionales.
- `multidimensional-radar`: Gráfica radial multidimensional de perfil analítico cienciométrico.
- `topic-dynamics`: Trayectoria temporal de burbujas y aceleración de frentes temáticos.

**Ejemplo para Gráfica de Barras de Instituciones o Autores:**
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/openalex_visualizer_cli.py \
  --input ./data/top_instituciones_litio.json \
  --type top-ranking \
  --title "Instituciones Líderes en Litio en México" \
  --output ./reports/ranking_instituciones_litio.html \
  --png ./reports/ranking_instituciones_litio.png
```

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

2. **Uso Preferente del CLI Oficial vs. Scripting Ad-Hoc:**
   - **Vía Primaria (Catálogo Estándar):** Utiliza siempre `openalex_visualizer_cli.py` para las gráficas estándar del catálogo (barras horizontales, series temporales, donas OA, sunburst, ODS). Ya implementa el tema visual oscuro oficial, tipografías ejecutivas, CDN optimizado y exportación simultánea de la tarjeta PNG.
   - **Vía Secundaria (Visualizaciones Libres Ad-Hoc):** Si el usuario solicita un tipo de gráfico especializado no soportado por el CLI (ej. diagramas de dispersión bivariados, gráficos de radar/araña, diagramas de violín o boxplots), estás plenamente autorizado para escribir y ejecutar un script de Python usando `/home/ambientesPy/revistaslatam/bin/python` con `plotly` o `matplotlib`.
   - *Condición estricta para scripts libres:* Guarda siempre el `.html` interactivo y la tarjeta `.png` dentro de `./reports/` y utiliza plantilla de tema oscuro (`template="plotly_dark"` o fondo `#0B0F19`) para preservar la armonía visual de TlachIA-Hands.

3. **Flujo en Dos Fases:**
   - **Fase 1 (Cómputo):** Obtén los datos crudos ejecutando la skill de datos idónea (`aggregations`, `works-search`, etc.) y guarda el resultado en `./data/datos.json`.
   - **Fase 2 (Visualización):** Invoca `openalex-mexico-visualizer` (o ejecuta el script Python libre) pasando dicho JSON para generar el HTML y el PNG en `./reports/`.

4. **Presentación de la Respuesta al Usuario:**
   - Proporciona tu resumen analítico cuantitativo en texto sobrio.
   - Incrusta la tarjeta estática PNG generada: `![Gráfica](reports/tarjeta.png)`.
   - Ofrece el enlace clickable relativo al artefacto interactivo: `[Abrir Dashboard Interactivo](reports/artefacto.html)`.

