---
name: bibliometric-network-analyst
description: Construcción y análisis de redes bibliométricas (coautoría, co-ocurrencia, co-citación, acoplamiento bibliográfico y citación directa), filtrado temporal por periodos, generación de artefactos visuales interactivos (KnoMap Force Graph y VOSviewer Engine), normalización con Association Strength, partición modular con Leiden/Louvain, cálculo de centralidades y conexión con SOM estático y longitudinal.
dependencies:
  - python: ">=3.10"
  - script: "scripts/biblio_network_cli.py"
---
# Bibliometric Network Analyst (KnoMap Biblio Networks)

Esta skill implementa la funcionalidad analítica y de visualización de la pestaña **Biblio Networks** de KnoMap y del ecosistema SOS-MCP. Construye, normaliza, particiona y visualiza topologías de redes científicas para identificar comunidades temáticas, colegios invisibles, líderes de coautoría, frentes activos y evolución temporal.

---

## 1. Overview y Modos de Visualización en KnoMap

Las redes bibliométricas modelan las interacciones sociales, conceptuales e intelectuales de la ciencia mediante grafos dirigidos o no dirigidos. Esta habilidad prioriza el análisis estructural riguroso de redes y proporciona dos visualizaciones canónicas complementarias como **artefactos HTML interactivos autónomos**:

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                     MODOS DE VISUALIZACIÓN EN KNOMAP BIBLIO NETWORKS                   │
├──────────────────────────┬─────────────────────────────┬──────────────────────────────┤
│ Modo de Visualización    │ Motor Tecnológico           │ Capacidades Analíticas Clave  │
├──────────────────────────┼─────────────────────────────┼──────────────────────────────┤
│ 1. KnoMap Force Graph    │ D3.js v7 Force Simulation   │ - Nodos por frecuencia/grado │
│    (Diagrama Propio)     │ Renderizado SVG interactivo │ - Colores por cluster Leiden │
│                          │ Dark Mode LabSOM            │ - Resaltado ego-red 1-salto  │
│                          │                             │ - Filtro LCC (Componente Max)│
│                          │                             │ - Inspector nodal en vivo    │
├──────────────────────────┼─────────────────────────────┼──────────────────────────────┤
│ 2. VOSviewer Engine      │ Canvas 2D / WebGL           │ - Network View (Clusters)    │
│    (VOSviewer Canónico)  │ Van Eck & Waltman Layout    │ - Overlay View (Scores/Años) │
│                          │ Compatible app.vosviewer.com│ - Density View (Densidad)    │
│                          │ Exportador `vosviewer.json` │ - Densidad kernel gaussiana  │
└──────────────────────────┴─────────────────────────────┴──────────────────────────────┘
```

---

## 2. Tipologías y Construcción de Redes (`build-network`)

Construye la red a partir de un corpus en formatos tabulares o nativos (`.parquet`, `.csv`, `.json` o exportaciones en texto plano de Web of Science `.txt`):

```bash
python scripts/biblio_network_cli.py build-network \
  --input /ruta/al/corpus.parquet \
  --network-type cooccurrence \
  --unit keywords \
  --counting full \
  --normalization association-strength \
  --min-freq 2 \
  --min-cooccur 1.0 \
  --auto-analyze \
  --html-knomap ./red_knomap.html \
  --html-vosviewer ./red_vosviewer.html \
  --vosviewer-json ./vosviewer.json \
  --som-matrix ./matriz_coocurrencia_som.csv \
  --output ./red_completa.json
```

### Tipologías de Red Soportadas (`--network-type` y `--unit`):
1. **Coocurrencia de Palabras Clave (`cooccurrence`, `keywords`):** Coaparición de términos de autor (`DE`), Keywords Plus (`ID`) o conceptos temáticos en los mismos documentos (frentes conceptuales).
2. **Coautoría (`coauthorship`):** Colaboración social entre investigadores (`authors`), afiliaciones institucionales (`institutions`) o bloques de países (`countries`).
3. **Acoplamiento Bibliográfico (`coupling`):** Grado en que dos documentos, autores o fuentes citan las mismas referencias bibliográficas comunes (frentes de investigación activos).
4. **Citación Directa (`direct-citation`):** Enlaces directos de citas entre unidades de análisis.

### Filtrado Temporal Opcional:
- `--period YYYY-YYYY` (ej. `--period 2020-2024` o `--period 2024`): acota el grafo al rango cronológico indicado.
- `--last-years N` (ej. `--last-years 5`): filtra automáticamente los últimos $N$ años respecto al año máximo del corpus.
- `--year-from YYYY` y `--year-to YYYY`: filtros de límite inferior y superior.
- `--max-terms N`: limita la red a los $N$ términos más destacados por frecuencia global.

---

## 3. Normalización Cienciométrica y Detección de Comunidades

### 3.1 Métodos de Normalización (`--normalization`):
* **Fuerza de Asociación (*Association Strength* de Van Eck & Waltman, 2009):** Medida estándar de VOSviewer y KnoMap:
  $$AS_{ij} = \frac{C_{ij}}{2 \cdot m \cdot s_i \cdot s_j}$$
  donde $C_{ij}$ es la coocurrencia observada, $s_i, s_j$ son las ocurrencias totales y $m$ es el total de enlaces. Normaliza por la expectativa de coocurrencia aleatoria.
* **Coseno de Salton:** Similitud geométrica normalizada por la media geométrica de las frecuencias: $S_{ij} = C_{ij} / \sqrt{C_i \cdot C_j}$.
* **Índice de Jaccard:** Razón entre intersección y unión: $J_{ij} = C_{ij} / (C_i + C_j - C_{ij})$.
* **Conteo:** Completo (`full`) o fraccional (`fractional`).

### 3.2 Partición Modular (Detección de Comunidades):
* **Algoritmo Leiden (`--algorithm leiden` - Recomendado):** Garantiza comunidades conexas y optimiza la modularidad de forma robusta, eliminando comunidades fragmentadas.
* **Algoritmo Louvain (`--algorithm louvain`):** Algoritmo heurístico clásico de modularidad.

### 3.3 Métricas de Centralidad Nodal:
Calculadas automáticamente con `--auto-analyze` o mediante el subcomando `calculate-centralities`:
- **Grado Ponderado / Fuerza de Enlaces (*Total Link Strength*):** Intensidad agregada de las conexiones del nodo.
- **Intermediación (*Betweenness Centrality*):** Identifica nodos puente que conectan comunidades conceptuales o colegios invisibles distintos.
- **PageRank:** Mide la autoridad y centralidad estructural del nodo dentro del flujo de la red.

---

## 4. Visualización Interactiva y Generación de Artefactos

Esta habilidad genera directamente los dos visualizadores interactivos de la pestaña **Biblio Networks** de KnoMap en archivos HTML autónomos listos para abrir en el navegador o presentar al usuario:

### 4.1 Artefacto 1: Visualizador KnoMap Force Graph (`render-knomap` o `--html-knomap`)

Genera un archivo HTML interactivo con motor D3.js Force Simulation en la estética visual Dark Mode de KnoMap:

```bash
python scripts/biblio_network_cli.py render-knomap \
  --input ./red_completa.json \
  --output ./artefacto_red_knomap.html \
  --title "Red de Coocurrencia Temática" \
  --subtitle "Ecosistema KnoMap Force-Directed Graph"
```

**Características Interactivas:**
- **Simulación de Fuerzas Dinámica:** Disposición orgánica con zoom y paneo continuo mediante D3.
- **Resaltado de Ego-Red de 1-Salto:** Al colocar el cursor sobre un nodo, se iluminan sus vecinos conectados y sus aristas con su fuerza de asociación, atenuando el resto de la red.
- **Tarjeta Inspectora de Nodo:** Despliega en vivo: nombre, cluster comunitario, ocurrencias, grado ponderado (Total Link Strength), PageRank e intermediación.
- **Filtro de Componente Conexo Máximo (LCC):** Casilla para aislar únicamente el componente principal y ocultar islas inconexas.
- **Búsqueda en Tiempo Real:** Campo de texto para localizar y resaltar nodos rápidamente.
- **Exportación de Gráficos:** Botón para descargar el grafo en formato vectorial SVG.

---

### 4.2 Artefacto 2: VOSviewer Engine (`render-vosviewer` o `--html-vosviewer`)

Genera un visualizador HTML con las tres vistas canónicas de VOSviewer y exporta el archivo `vosviewer.json` oficial:

```bash
python scripts/biblio_network_cli.py render-vosviewer \
  --input ./red_completa.json \
  --output ./artefacto_vosviewer_map.html \
  --output-json ./vosviewer.json \
  --title "Cartografía Científica VOSviewer"
```

**Modos de Visualización Disponibles en la Interfaz:**
1. **● Network Visualization:** Nodos con círculos proporcionales a las ocurrencias, coloreados por comunidad modular, enlazados por líneas con intensidad proporcional al peso.
2. **◐ Overlay Visualization:** Gradiente continuo de color (Viridis / Plasma / Coolwarm) sobre una métrica numérica continua (PageRank, antigüedad media o citas), con barra de escala cromática.
3. **◎ Density Visualization:** **Superficie de calor continuo calculada mediante un kernel gaussiano 2D** según la formulación original de Van Eck & Waltman (paleta térmica Azul $\to$ Cian $\to$ Verde $\to$ Amarillo $\to$ Rojo), que revela las áreas de mayor concentración conceptual.
4. **Interoperabilidad:** Botón integrado para descargar `vosviewer.json` y enlace directo para abrir el mapa en la aplicación oficial [app.vosviewer.com](https://app.vosviewer.com) o importarlo en la pestaña Biblio Networks de KnoMap.

---

## 5. Redes Secuenciales Longitudinales (`sequential-networks`)

Descompone el corpus en periodos consecutivos o ventanas deslizantes, construye la red de cada periodo con comunidades Leiden y centralidades, y genera el manifiesto unificado de evolución:

```bash
python scripts/biblio_network_cli.py sequential-networks \
  --input /ruta/al/corpus.parquet \
  --output-dir ./redes_longitudinales \
  --network-type cooccurrence \
  --unit keywords \
  --window 5 \
  --step 5 \
  --max-terms 50 \
  --normalization association-strength
```

### Opciones Clave:
- `--window N`: Tamaño de ventana en años (ej. `5` para quinquenios, `10` para décadas).
- `--step S`: Paso de desplazamiento (disjuntas si $S = W$; o deslizantes si $S < W$).
- `--periods "P1,P2,..."`: Lista explícita de periodos personalizados (ej. `"2000-2009,2010-2019,2020-2024"`).
- `--max-terms M`: Número de conceptos retenidos en el **vocabulario canónico compartido** (garantiza matrices $M \times M$ alineadas en todos los periodos).

---

## 6. Conexión Avanzada con el Ecosistema SOM (Análisis Neurocomputacional)

Aunque el análisis de redes bibliométricas es completamente autónomo y no requiere de redes neuronales, el ecosistema KnoMap integra una **conexión directa entre la topología de grafos y los Mapas Autoorganizados de Kohonen (SOM)** basada en investigaciones tempranas (ViBlioSOM; Sotolongo, Carrillo-Calvet et al., 1999–2002) y en la metodología contemporánea de perfiles multidimensionales (*Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet, 2024*; *Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025*).

### 6.1 SOM sobre Red Estática o por Periodo (Mapeo de Matrices de Adyacencia)

En el análisis de redes tradicional, cada término o autor se visualiza como un nodo discreto en un espacio de fuerzas. Sin embargo, su **perfil de relación** con el resto de la disciplina puede modelarse como un vector numérico continuo en $\mathbb{R}^N$.

Mediante el subcomando `export-som-matrix` (que reproduce el botón `handleSendToSOM` de la pestaña Biblio Networks de KnoMap):

```bash
python scripts/biblio_network_cli.py export-som-matrix \
  --input ./red_completa.json \
  --output-csv ./matriz_coocurrencia_som.csv \
  --output-json ./matriz_coocurrencia_som.json
```

Se obtiene una matriz simétrica de adyacencia/coocurrencia de dimensión $N \times N$:
* Cada **fila** representa el perfil relacional de un término $i$.
* La **diagonal** contiene la frecuencia de ocurrencias del término ($C_i$).
* Los elementos **fuera de la diagonal** contienen la Fuerza de Asociación normalizada con todos los demás términos ($AS_{ij}$).

#### Integración con [`som-methodological-expert`](../som-methodological-expert/SKILL.md):
Al alimentar esta matriz $N \times N$ al motor SOM:
1. **Preservación Topológica:** Los términos con perfiles de coocurrencia similares se mapean en la misma neurona o en neuronas contiguas de la retícula hexagonal.
2. **Inspección de la U-Matrix:** La matriz de distancias unificadas (U-Matrix) revela valles de alta densidad conceptual y crestas de separación entre subcampos.
3. **Contraste de Particiones (Leiden vs. Vesanto):** Permite contrastar de forma cruzada las comunidades detectadas mediante modularidad de grafos (Leiden/Louvain) con los meta-clusters continuos calculados sobre el SOM con el algoritmo de Vesanto y criterio Silhouette.

---

### 6.2 SOM Longitudinal (Warm-Start Chaining)

El archivo `sequence_manifest.json` emitido por el subcomando `sequential-networks` es **100% compatible sin conversión intermedia** con el motor de encadenamiento temporal de [`neural-longitudinal-mapping`](../neural-longitudinal-mapping/SKILL.md):

```bash
# 1. Entrenar secuencia longitudinal encadenada (Warm-Start: W_t = W_{t-1}^*)
python scripts/neural_longitudinal_cli.py train \
  --input ./redes_longitudinales/sequence_manifest.json \
  --rows 8 --cols 12 \
  --output ./longitudinal_results.json

# 2. Computar dinámicas Macro, Meso y Micro
python scripts/neural_longitudinal_cli.py analyze \
  --input ./longitudinal_results.json \
  --output ./dynamics_analysis.json

# 3. Generar reporte Markdown con evolución de comunidades
python scripts/neural_longitudinal_cli.py report \
  --analysis ./dynamics_analysis.json \
  --output ./report_longitudinal.md
```

Esta conexión permite rastrear:
* **Nivel Macro:** Tasa de deriva sináptica global ($\Delta W$).
* **Nivel Meso:** Fusión y escisión de frentes de investigación entre décadas.
* **Nivel Micro:** Desplazamiento de conceptos nodales dentro del espacio latente.

---

## 7. Troubleshooting y Buenas Prácticas

- **Visualización en Navegador:** Los archivos `.html` generados son completamente estáticos y no requieren servidor backend; pueden abrirse con doble clic o servirse desde cualquier CDN.
- **Redes Ralas / Desconectadas:** En corpus pequeños con muchos términos esporádicos, use `--min-freq 2` o active la casilla "Solo Componente Conexo (LCC)" en la interfaz KnoMap para aislar el núcleo temático coherente.
- **Garantía Conexa de Comunidades:** Emplear siempre `--algorithm leiden` en lugar de Louvain para evitar clusters internamente inconexos.
- **Exportación Canónica a VOSviewer:** El archivo `vosviewer.json` generado puede arrastrarse directamente en la interfaz oficial de [app.vosviewer.com](https://app.vosviewer.com).
