---
name: bibliometric-network-analyst
description: Construcción y análisis de redes bibliométricas (coautoría, co-ocurrencia, co-citación, acoplamiento bibliográfico y citación directa), filtrado temporal por periodos, secuencias longitudinales para SOM Warm-Start, normalización con Association Strength, partición modular con Leiden/Louvain y cálculo de centralidades.
dependencies:
  - python: "/home/ambientesPy/revistaslatam"
  - script: "scripts/biblio_network_cli.py"
---

# Bibliometric Network Analyst

Construye y analiza topologías de redes científicas para identificar comunidades temáticas, líderes de coautoría, colegios invisibles, frentes activos y evolución longitudinal de grafos.

## Overview
Las redes bibliométricas permiten mapear la estructura social, conceptual e intelectual de la ciencia. Este módulo implementa las tipologías soportadas en KnoMap y el ecosistema SOS-MCP:
- **Tipologías:** Coocurrencia de términos/palabras clave, coautoría, acoplamiento bibliográfico y citación directa.
- **Normalizaciones:** Fuerza de Asociación (*Association Strength* de Van Eck & Waltman), Coseno de Salton y Jaccard.
- **Partición Modular:** Detección de comunidades con el algoritmo **Leiden** (garantizando comunidades conexas) o **Louvain**.
- **Métricas:** Grado ponderado, centralidad de intermediación (*betweenness*) y PageRank.
- **Dimensión Temporal:** Filtrado de red por periodo individual (`--period`, `--last-years`) y descomposición en redes secuenciales longitudinales (`sequential-networks`) en ventanas decenales, quinquenales o deslizantes, generando el manifiesto `sequence_manifest.json` directamente compatible con el entrenamiento neuronal Warm-Start de [`neural-longitudinal-mapping`](file:///home/labsom/knomap/.agents/skills/neural-longitudinal-mapping/SKILL.md).

## Dependencies
- Entorno Python: `/home/ambientesPy/revistaslatam`
- Paquetes clave: `networkx`, `igraph`, `leidenalg`, `scipy`, `pandas`
- Script ejecutable: [`scripts/biblio_network_cli.py`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/bibliometric-network-analyst/scripts/biblio_network_cli.py)

---

## Scripts & CLI Tools

### 1. Construcción de Red Estática o por Periodo (`build-network`)
Extrae la red a partir de un corpus (.parquet, .csv o .json), con soporte de filtrado temporal:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/biblio_network_cli.py build-network \
  --input /ruta/al/corpus.parquet \
  --network-type cooccurrence \
  --unit keywords \
  --counting full \
  --normalization association-strength \
  --min-freq 3 \
  --output /ruta/a/red_keywords.json
```

#### Filtrado Temporal Opcional:
- `--period YYYY-YYYY` (ej. `--period 2020-2024` o `--period 2024`): acota el grafo al rango indicado.
- `--last-years N` (ej. `--last-years 5`): filtra automáticamente los últimos $N$ años respecto al año máximo del corpus.
- `--year-from YYYY` y `--year-to YYYY`: acotan el rango inicial y final.
- `--max-terms N`: limita opcionalmente la red a los $N$ términos más frecuentes.

Ejemplo filtrando el último quinquenio:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/biblio_network_cli.py build-network \
  --input /ruta/al/corpus.parquet \
  --period 2020-2024 \
  --max-terms 50 \
  --output /ruta/a/red_2020_2024.json
```

---

### 2. Generación de Redes Secuenciales Longitudinales (`sequential-networks` o `period-networks`)
Descompone el corpus en periodos consecutivos o ventanas deslizantes, construye la red de cada periodo con comunidades Leiden y centralidades, y produce el manifiesto unificado para mapas autoorganizados (SOM):

```bash
/home/ambientesPy/revistaslatam/bin/python scripts/biblio_network_cli.py sequential-networks \
  --input /ruta/al/corpus.json \
  --output-dir ./longitudinal_networks \
  --network-type cooccurrence \
  --unit keywords \
  --window 10 \
  --max-terms 40 \
  --normalization association-strength
```

#### Opciones de Secuenciación:
- `--window N`: Tamaño de ventana en años (ej. `10` para décadas, `5` para lustros/quinquenios).
- `--step S`: Paso de desplazamiento (por defecto igual a `--window` para ventanas disjuntas; o menor para ventanas deslizantes / *rolling windows*, ej. `--window 5 --step 1`).
- `--periods "P1,P2,..."`: Lista explícita de periodos (ej. `--periods "1990-1999,2000-2009,2010-2019,2020-2024"`).
- `--max-terms M`: Número de términos prominentes retenidos en el **vocabulario canónico compartido** (garantiza matrices $M \times M$ alineadas en todos los periodos).
- `--algorithm leiden|louvain`: Algoritmo de detección de comunidades en cada red periódica (default: `leiden`).
- `--format gexf|pajek|vosviewer-json`: Exporta adicionalmente cada red periódica en formato visualizador externo.

#### Archivos Generados en `--output-dir`:
1. `network_{period_slug}.json`: Grafo individual de cada periodo con nodos, aristas normalizadas, comunidades Leiden y métricas de centralidad (PageRank, grado ponderado, intermediación).
2. `sequence_manifest.json`: Manifiesto consolidado con la evolución estructural de la red, el vocabulario compartido y las matrices `periods_data` formateadas para entrenamiento neuronal directo.

---

### 3. Conexión Directa con SOM Longitudinal (`neural-longitudinal-mapping`)
El archivo `sequence_manifest.json` emitido por `sequential-networks` es **100% compatible sin conversión intermedia** con el motor de encadenamiento temporal:

```bash
# 1. Entrenar secuencia longitudinal (Warm-Start Chaining)
/home/ambientesPy/revistaslatam/bin/python /home/labsom/knomap/engine/skills/neural-longitudinal-mapping/scripts/neural_longitudinal_cli.py train \
  --input ./longitudinal_networks/sequence_manifest.json \
  --rows 8 --cols 12 \
  --output ./longitudinal_results.json

# 2. Computar dinámicas Macro, Meso y Micro
/home/ambientesPy/revistaslatam/bin/python /home/labsom/knomap/engine/skills/neural-longitudinal-mapping/scripts/neural_longitudinal_cli.py analyze \
  --input ./longitudinal_results.json \
  --output ./dynamics_analysis.json

# 3. Generar reporte Markdown de publicación
/home/ambientesPy/revistaslatam/bin/python /home/labsom/knomap/engine/skills/neural-longitudinal-mapping/scripts/neural_longitudinal_cli.py report \
  --analysis ./dynamics_analysis.json \
  --output ./report_longitudinal.md
```

---

### 4. Detección de Comunidades Individual (`detect-communities`)
Ejecuta la partición modular sobre una red existente:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/biblio_network_cli.py detect-communities \
  --input /ruta/a/red_keywords.json \
  --algorithm leiden \
  --resolution 1.0 \
  --output /ruta/a/red_con_comunidades.json
```

---

### 5. Cálculo de Centralidades (`calculate-centralities`)
Calcula el grado ponderado, intermediación (*betweenness*) y PageRank:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/biblio_network_cli.py calculate-centralities \
  --input /ruta/a/red_con_comunidades.json \
  --output /ruta/a/centralidades.json
```

---

### 6. Exportación a Formatos Externos (`export-graph`)
Exporta el grafo para Gephi, Pajek o VOSviewer:
```bash
/home/ambientesPy/revistaslatam/bin/python scripts/biblio_network_cli.py export-graph \
  --input /ruta/a/red_con_comunidades.json \
  --format gexf \
  --output /ruta/al/mapa.gexf
```

---

## Workflow Steps
1. **Seleccionar Granularidad Temporal:**
   - Para estudiar un hito específico: `build-network --period YYYY-YYYY`.
   - Para analizar la trayectoria histórica evolutiva: `sequential-networks --window 5` (o `10`).
2. **Vocabulario Compartido:** `sequential-networks` aísla los $M$ conceptos dominantes para mantener la invarianza dimensional entre cortes temporales.
3. **Modelado Neurocomputacional:** Alimentar `sequence_manifest.json` a `neural-longitudinal-mapping` con encadenamiento Warm-Start ($W_t^{(0)} = W_{t-1}^*$).
4. **Inspección Visual:** Visualizar las redes individuales en KnoMap o Gephi, y explorar la dinámica de clusters y deriva sináptica ($\Delta W$).

---

## References
- [Tipologías de Redes e Indicadores](references/network_typologies_kpis.md)
- [Formulación de Association Strength](references/association_strength_formulation.md)
- Metodología SOM Longitudinal: *Jiménez-Andrade, Martí-Lahera & Carrillo-Calvet (2024)*, [IJSMC](https://doi.org/10.47909/ijsmc.92).

---

## Troubleshooting & Edge Cases
- **Años ausentes o heterogéneos:** El parser extrae automáticamente el año de `publication_year`, `year`, `PY`, `Date` o `anio`. Si no hay ningún año en el corpus, se emitirá una advertencia y se utilizará el rango global.
- **Redes Ralas por Periodo:** Si en las primeras décadas hay pocos documentos, algunas palabras del vocabulario pueden tener frecuencia cero en ese periodo; el manifest conserva la dimensión $M \times M$ con ceros en la fila/columna respectiva, asegurando estabilidad dimensional en el SOM.
- **Comunidades Desconectadas:** Louvain puede generar sub-comunidades inconexas en grafos dispersos; utilizar siempre `--algorithm leiden`.
