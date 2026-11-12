---
name: knomap-project-resumer
description: Abre o crea archivos de proyecto KnoMap (.knoMap v2.1, .json.gz del servidor o .knomap v2.0), inspecciona todos sus módulos científicos y el historial completo del Asistente IA (Copiloto Visual, Agente Autónomo, mapas, artefactos HTML/SVG/PNG y cachés LLM) bajo el principio File-Output First, reconstruye el workspace para retomar la investigación y empaqueta investigaciones completas de vuelta en un .knoMap listo para abrir en la interfaz web.
metadata:
  python: ">=3.10"
  tools: ["knomap-som-engine"]
---

# KnoMap Project Resumer: Continuación de Investigaciones Guardadas

## 1. Overview y Propósito

Esta skill permite **abrir un archivo `.knoMap` guardado desde la aplicación web/desktop** (o un `.json.gz` almacenado en el servidor de KnoMap, o un `.knomap` v2.0 del hub SQLite/MCP) y **retomar exactamente donde se quedó una investigación**, preservando:

1. **Matrices e Indicadores:** Matriz principal del SOM (`dataMatrix` y `originalDataMatrix`), unidades pre-cargadas de **TlachIA Metrics** e **InCites** (`Locations`, `Organizations`, `Sources`, `Topics`, etc.), y tablas de reducción de dimensionalidad.
2. **Modelos y Mapas Entrenados:** Pesos neuronales SOM (`weights`), U-Matrix, clusters, etiquetas mapeadas (`mapped_labels`), nombres de clusters (`clusterLabels`), coordenadas UMAP, historial multi-experimento (`savedRuns`) y resultados longitudinales (`longitudinalResults`).
3. **Redes Bibliométricas y EDA:** Grafos (`network.json`), archivos `vosviewer.json`, matrices de coocurrencia, redes por año, reportes EDA (`bradford_law`, `lotka_law`, métricas de autores) y registros semánticos (`semanticRecords`, clusters y coordenadas 2D).
4. **Memoria Completa del Asistente IA:**
   - **Contexto del estudio** (`studyContext`).
   - **Copiloto Visual** (`aiReport.entries`): texto analítico generado, diálogos multi-turno, datos capturados y figuras exportadas (`.png` / `.svg`).
   - **Agente Autónomo** (`aiReport.agentMessages`): historial conversacional, herramientas ejecutadas y artefactos interactivos (`.html` / `.svg`).
   - **Cachés de tarjetas IA** (`incitesLlmCache` y `tlachiaLlmCache`).

---

## 2. Dependencies y Cadena de Valor

- **Entrada Upstream:** Archivo exportado desde KnoMap (`*.knoMap`), respaldo del servidor (`*.json.gz`) o paquete portátil (`*.knomap`).
- **Habilidades Downstream (Continuación del Trabajo sobre el Workspace Extraído):**
  - `som-methodological-expert` — Reentrenar o reclustering sobre `./matrices/som_matrix.parquet`, o diagnosticar pares y generar dashboards desde `./reports/som_state.json`.
  - `som-trajectory-mapping` / `neural-longitudinal-mapping` — Continuar análisis temporal sobre series `*_time_series.json` / `*_longitudinal.json` o `./reports/longitudinal_state.json`.
  - `bibliometric-network-analyst` — Reanudar grafos y comunidades sobre `./networks/network.json`, `./networks/vosviewer.json` o `./networks/cooccurrence.csv`.
  - `scientometrics-incites-expert` / `tlachia-metrics-handler` — Trabajar sobre las matrices extraídas `./matrices/incites_*.csv` y `./matrices/tlachia_*.csv`.
  - `semantic-manifold-expert` — Reanudar reducción/clustering sobre `./matrices/semantic_records.parquet` y `./reports/semantic_clusters_state.json`.
  - `template-articulo-cientifico-imryd`, `template-informe-tecnico-institucional`, `template-policy-brief-gobernanza`, `template-radar-frentes-investigacion` — Redactar o ampliar el documento científico usando `./reports/assistant_history.md` y `./reports/assistant_figures/`.
- **Entorno y Script Principal:**
  - Python `>=3.10` con `pandas` y `pyarrow` (opcional para `.parquet`; fallback automático a `.csv` y `.json`).
  - Script ejecutable: `scripts/knomap_resume_cli.py` (invocar con `python scripts/knomap_resume_cli.py ...` desde el directorio de la skill o indicando su ruta relativa).
  - Herramienta MCP complementaria: `knomap-som-engine` (`knomap_render_som_dashboard`, `train_som`, `recluster_som`).

---

## 3. Protocolo de Ejecución Paso a Paso

> **Regla estricta (*File-Output First*):** Un `.knoMap` puede pesar decenas de megabytes (matrices, pesos neuronales, miles de registros semánticos, PNGs en base64). **NUNCA** leas el archivo `.knoMap` completo directo al contexto del chat ni imprimas sus matrices a `stdout`. Ejecuta siempre `inspect` primero y luego `extract-workspace`.

### 3.1 Paso 1: Inspeccionar el Proyecto (`inspect`)

Obtén un inventario compacto de los módulos disponibles, corridas SOM, contexto de estudio y entradas del asistente sin saturar el contexto:

```bash
python scripts/knomap_resume_cli.py inspect \
  --input ./mi_estudio.knoMap \
  --output ./reports/project_inventory.json
```

Revisa `./reports/project_inventory.json` para decidir qué artefactos extraer y qué líneas de investigación existen ya en el proyecto.

### 3.2 Paso 2: Reconstruir el Workspace (`extract-workspace`)

Extrae matrices tabulares, estados SOM normalizados, redes bibliométricas, texto previo del asistente y todas las figuras/artefactos a disco dentro de `./matrices/`, `./networks/` y `./reports/`:

```bash
python scripts/knomap_resume_cli.py extract-workspace \
  --input ./mi_estudio.knoMap \
  --workspace-dir . \
  --output ./reports/resume_manifest.json
```

#### Artefactos Generados en el Workspace

| Directorio | Archivos Principales | Uso Downstream |
| :--- | :--- | :--- |
| `./matrices/` | `som_matrix.csv`, `som_matrix.parquet`, `som_matrix_original.csv`, `som_matrix_run_<N>_*.csv/.parquet`, `incites_<unidad>.csv`, `tlachia_<unidad>.csv`, `semantic_records.parquet` | Entrenamiento SOM, análisis estadístico, leyes, trayectorias |
| `./networks/` | `network.json`, `vosviewer.json`, `networks_by_year.json`, `cooccurrence.csv`, `eda_report.json`, `sankey_data.json` | Redes de coocurrencia/coautoría, Leiden/Louvain, EDA |
| `./reports/` | `som_state.json`, `som_state_run_*.json`, `saved_runs_index.json`, `longitudinal_state.json`, `semantic_clusters_state.json` | Visualización (`knomap_render_som_dashboard`), diagnóstico de pares |
| `./reports/` | `assistant_history.md`, `assistant_history.json`, `resume_manifest.json` | Leer interpretaciones previas, preguntas abiertas y contexto |
| `./reports/assistant_figures/` | `copilot_*.png`, `copilot_*.svg`, `copilot_*_data.json`, `agent_*.html`, `agent_*.svg` | Reutilizar mapas y figuras generadas en reportes IMRyD |

### 3.3 Paso 3: Leer el Estado Previo y Retomar la Investigación

1. Lee `./reports/assistant_history.md` para recuperar:
   - El **objetivo y contexto del estudio** (`studyContext`).
   - Qué **mapas y gráficas ya fueron interpretados** por el Copiloto Visual y dónde quedaron almacenadas sus figuras.
   - Qué **herramientas, respuestas y artefactos HTML5** ya produjo el Agente Autónomo.
   - Qué interpretaciones existen en los cachés de InCites / TlachIA.
2. Verifica en `./reports/resume_manifest.json` si hay experimentos previos (`savedRuns`) o datos que aún no se modelan (por ejemplo, si existe `tlachia_locations.csv` pero no `som_state.json`, o si faltan análisis longitudinales/redes).
3. Continúa con la skill especializada correspondiente sobre los archivos ya extraídos en `./matrices/`, `./networks/` y `./reports/`.

### 3.4 Paso 4 (Opcional): Guardar Nuevos Hallazgos de Vuelta al `.knoMap` (`update-knomap`)

Si después de continuar el análisis deseas que el usuario pueda **reabrir el `.knoMap` actualizado en la interfaz web de KnoMap** con el nuevo texto, un mapa HTML interactivo o un nuevo `som_state.json`:

```bash
python scripts/knomap_resume_cli.py update-knomap \
  --input ./mi_estudio.knoMap \
  --output ./mi_estudio_continuado.knoMap \
  --add-note-title "Análisis Longitudinal Complementario" \
  --add-note-file ./reports/nueva_interpretacion.md \
  --add-html-artifact ./reports/som_dashboard.html \
  --as-agent-message \
  --som-state-file ./reports/som_state.json
```

*(Sin `--as-agent-message`, la nota se inserta como una nueva entrada en el **Copiloto Visual**.)*

### 3.5 Paso 5 (Flujo Inverso Agente → Humano): Crear un Proyecto `.knoMap` Nuevo desde Cero (`create-knomap`)

Cuando un agente concluye una investigación autónoma en un workspace (por ejemplo, tras ejecutar `som-methodological-expert`, `som-trajectory-mapping`, `bibliometric-network-analyst` o `semantic-manifold-expert`), puede empaquetar **matrices, modelos SOM entrenados (`savedRuns`), redes, trayectorias, figuras PNG, artefactos HTML interactivos y el reporte científico completo** en un archivo `.knoMap` (`version 2.1`) o `.json.gz` nuevo para que el usuario humano lo abra directamente en KnoMap Web:

```bash
python scripts/knomap_resume_cli.py create-knomap \
  --workspace-dir . \
  --output ./reports/mi_investigacion_completa.knoMap \
  --title "Estudio Cienciométrico Completo" \
  --study-desc "Análisis multidimensional SOM, redes bibliométricas y trayectorias." \
  --report-md ./reports/reporte_final.md \
  --add-copilot-entry "Mapa de Trayectorias|./reports/som_trajectories_es.png|./reports/interpretacion_som.md" \
  --add-html-artifact ./reports/som_dashboard.html \
  --auto-attach-figures
```

**Comportamiento de `create-knomap`:**
- **Auto-descubrimiento en el workspace:** Si omites `--som-state`, busca automáticamente `./reports/som_state_run_*.json` o `./reports/som_state.json`, empareja sus matrices normalizadas/originales en `./matrices/`, construye `hexGrid`, convierte `umatrix` a 2D y detecta automáticamente trayectorias `XX_ENTIDAD` (o usa `--trajectories A,B,C`).
- **Módulos complementarios:** Si existen en `./networks/` o `./reports/`, incrusta automáticamente `network.json`, `vosviewer.json`, `eda_report.json`, `longitudinal_state.json`, `semantic_records.parquet` y `dim_reduction_state.json`.
- **Asistente IA listo para revisión humana:** Adjunta el reporte final en `aiReport.agentMessages` (junto con artefactos HTML interactivos) y cada pareja figura+análisis en `aiReport.entries` (Copiloto Visual).

---

## 4. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1:** Abrir un `.knoMap` directamente con `read_file` o imprimir `json.load()` a `stdout`.  
  **Solución:** Usar siempre `inspect --output ...` y `extract-workspace` para no colapsar la ventana de contexto con matrices y PNGs en base64.
- ❌ **Anti-patrón 2:** Asumir que la extensión `.knoMap` siempre es JSON plano o siempre es gzip.  
  **Solución:** Los proyectos exportados desde la interfaz web suelen ser JSON plano (`v2.1`), mientras que los respaldos del servidor (`.json.gz`) están comprimidos con gzip y los del hub CLI (`.knomap v2.0`) usan otro esquema. `knomap_resume_cli.py` detecta los tres automáticamente.
- ❌ **Anti-patrón 3:** Pasar `result` crudo del `.knoMap` web directamente a `knomap_render_som_dashboard`.  
  **Solución:** El formato web usa claves en camelCase (`mappedLabels`, `compNames`, `config.rows`, `umatrix` 2D), mientras que el motor Python espera snake_case (`mapped_labels`, `indicators`, `rows`, `umatrix` 1D). `extract-workspace` genera `./reports/som_state.json` ya convertido y normalizado (reconstruyendo `mapped_labels` desde `bmus` + `labels` si hiciera falta).
- ❌ **Anti-patrón 4:** Re-cosechar datos desde OpenAlex o InCites cuando ya están dentro del `.knoMap`.  
  **Solución:** Revisar primero `./matrices/incites_*.csv`, `./matrices/tlachia_*.csv` y `./matrices/semantic_records.parquet` extraídos por `extract-workspace`.
- ❌ **Anti-patrón 5:** Ignorar el historial previo del asistente al continuar el análisis.  
  **Solución:** Leer siempre `./reports/assistant_history.md` antes de redactar nuevas interpretaciones para mantener coherencia terminológica, hipótesis y tono con lo ya trabajado.

---

## 5. Referencias Técnicas

- [`scripts/knomap_resume_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/knomap-project-resumer/scripts/knomap_resume_cli.py)
- [`som-methodological-expert`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)
- [`tlachia-metrics-handler`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/tlachia-metrics-handler/SKILL.md)
- [`bibliometric-network-analyst`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/bibliometric-network-analyst/SKILL.md)
