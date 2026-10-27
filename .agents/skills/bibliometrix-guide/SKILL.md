---
name: bibliometrix-guide
description: >-
  Mapeo científico, análisis de redes bibliométricas y cartografía temática mediante el paquete canónico R bibliometrix (Aria & Cuccurullo, 2017) y su interfaz web Biblioshiny. Orquesta importación multibase (Scopus, WoS, PubMed, Dimensions, OpenAlex), co-citación, acoplamiento, diagramas estratégicos de Callon (Centralidad vs Densidad) y evolución temática longitudinal.
metadata:
  language: "R / Python"
  r_package: "bibliometrix >=4.0"
  scripts:
    - "scripts/bibliometrix_cli.py"
    - "scripts/bibliometrix_runner.R"
---

# Bibliometrix Guide: Mapeo Científico y Cartografía Temática en R

## 1. Overview y Propósito

El ecosistema **`bibliometrix`** (Massimo Aria & Corrado Cuccurullo, 2017; *Journal of Informetrics*) es uno de los paquetes de código abierto más consolidados a nivel internacional para el análisis bibliométrico integral y la cartografía de la ciencia (*Science Mapping*).

Esta habilidad proporciona una guía operativa exhaustiva y herramientas de orquestación para agentes y analistas, cubriendo el ciclo de vida completo del descubrimiento de conocimiento en bases de datos bibliográficas (KDD):
1. **Ingesta y normalización multibase:** Conversión uniforme a dataframes canónicos con `convert2df()` desde Scopus, Web of Science, PubMed, Dimensions, Cochrane y OpenAlex.
2. **Análisis descriptivo y producción:** Métricas globales, tasas anuales de crecimiento, leyes de productividad y fuentes dominantes con `biblioAnalysis()`.
3. **Estructura Intelectual y Redes:** Co-citación de referencias/autores, acoplamiento bibliográfico y redes de colaboración con `biblioNetwork()`.
4. **Estructura Conceptual y Diagramas de Callon:** Coocurrencia de términos, análisis factorial (MCA/CA) y el **Diagrama Estratégico de Cuadrantes de Callon** (Centralidad vs. Densidad) con `thematicMap()`.
5. **Evolución Temática Longitudinal:** Mapeo de flujos aluviales (Sankey) entre cortes temporales con `thematicEvolution()`.
6. **Interfaz Web No-Code:** Despliegue interactivo en el navegador mediante `biblioshiny()`.

---

## 2. Ámbito de Aplicación y Preguntas Cienciométricas

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   TIPOLOGÍAS DE ANÁLISIS EN R BIBLIOMETRIX                             │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ Tipología de Análisis   │ Funciones R Canónicas       │ Pregunta / Decisión que Resuelve│
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 1. Estadística           │ `convert2df()`,             │ ¿Cuál es el volumen global, la│
│    Descriptiva           │ `biblioAnalysis()`,         │ tasa anual de crecimiento y   │
│                          │ `summary()`                 │ los autores y revistas top?   │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 2. Estructura            │ `citations()`,              │ ¿Cuáles son los documentos y  │
│    Intelectual           │ `biblioNetwork(co-citation)`│ autores fundacionales citados │
│                          │ `histNetwork()` (HistCite)  │ conjuntamente en la base?     │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 3. Estructura Social     │ `biblioNetwork(collab)`     │ ¿Cómo se agrupan los autores, │
│                          │ `networkPlot(kamada)`       │ instituciones y países en     │
│                          │ `metaTagExtraction()`       │ colegios invisibles?          │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 4. Estructura Conceptual │ `thematicMap()`             │ ¿Cuáles son los temas motores,│
│    (Diagrama de Callon)  │ (Centralidad vs Densidad)   │ especializados de nicho, bási-│
│                          │ `biblioNetwork(co-occur)`   │ cos o emergentes/declinantes? │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 5. Evolución Temática    │ `thematicEvolution()`       │ ¿Cómo se fusionan o escinden  │
│    Longitudinal          │ `plotThematicEvolution()`   │ los frentes temáticos a lo    │
│                          │                             │ largo de periodos históricos? │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

### 2.1 El Diagrama Estratégico de Callon (1991)
El paquete clasifica los clusters temáticos en 4 cuadrantes analíticos basándose en dos coordenadas ortogonales centradas en sus medianas:
* **Centralidad de Callon (Eje X - Enlaces Externos):** Mide la transversalidad e interconexión del cluster con el resto de la disciplina.
* **Densidad de Callon (Eje Y - Enlaces Internos):** Mide la cohesión conceptual y madurez interna del cluster.

1. **Cuadrante I: Temas Motores (*Motor Themes*, Alta Centralidad, Alta Densidad):** Líneas consolidadas e influyentes que estructuran la disciplina.
2. **Cuadrante II: Temas de Nicho (*Niche Themes*, Baja Centralidad, Alta Densidad):** Especialidades altamente desarrolladas pero marginales o aisladas.
3. **Cuadrante III: Temas Emergentes o Declinantes (*Emerging or Declining Themes*, Baja Centralidad, Baja Densidad):** Frentes embrionarios o líneas de investigación obsoletas.
4. **Cuadrante IV: Temas Básicos y Transversales (*Basic Themes*, Alta Centralidad, Baja Densidad):** Conceptos nodales compartidos por todo el corpus pero sin híper-especialización interna.

---

## 3. Dependencies y Cadena de Valor

```
┌─────────────────────────────────┐
│     Habilidades Upstream        │
│ • openalex-mexico-works-search  │──┐
│ • scopus-harvester / pubmed     │  │  Exportaciones tabulares
│ • tlachia-metrics-handler (ZIP) │  │  (CSV, BibTeX, TXT, Parquet)
└─────────────────────────────────┘  │
                                     ▼
                     ┌───────────────────────────────┐
                     │      bibliometrix-guide       │
                     │  (Mapeo de Ciencia R / Python)│
                     └───────────────────────────────┘
                                     │
                                     ▼  Matrices de red, JSON de clusters y figuras PNG
┌────────────────────────────────────┴────────────────────────────────────┐
│                       Habilidades Downstream                            │
│ • som-methodological-expert (Contraste con mapas autoorganizados SOM)   │
│ • bibliometric-network-analyst (Algoritmo Leiden y modularidad estricta)│
│ • classical-bibliometrics-laws (Validación empírica Lotka / Bradford)   │
│ • Informes ejecutivos de política científica y benchmarking             │
└─────────────────────────────────────────────────────────────────────────┘
```

* **Habilidades Upstream (Proveedores del corpus):**
  - [`scopus-harvester`](../scopus-harvester/SKILL.md) / [`pubmed-harvester`](../pubmed-harvester/SKILL.md): Descarga de literatura con aparato crítico.
  - [`openalex-mexico-works-search`](../openalex-mexico-clickhouse/openalex-mexico-works-search/SKILL.md): Publicaciones de México con identificadores DOI y campos normalizados.
  - [`tlachia-metrics-handler`](../tlachia-metrics-handler/SKILL.md): Paquetes ZIP de metadatos de documentos.
* **Habilidades Downstream (Consumidores del análisis):**
  - [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Proyección neurocomputacional SOM de perfiles cienciométricos.
  - [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md): Partición de redes complejas con algoritmo Leiden.
  - [`classical-bibliometrics-laws`](../classical-bibliometrics-laws/SKILL.md): Contraste con leyes de Lotka, Bradford y Price.
* **Entorno y Recursos de Software:**
  - **Entorno R (Primario):** R `>= 4.0` con librerías `bibliometrix` y `jsonlite`.
  - **Entorno Python (Orquestador / Fallback):** Python `>= 3.10` con `numpy`, `matplotlib`, `pandas`.
  - **Scripts CLI:**
    - [`scripts/bibliometrix_runner.R`](scripts/bibliometrix_runner.R): Script autónomo para ejecución R desatendida vía `Rscript`.
    - [`scripts/bibliometrix_cli.py`](scripts/bibliometrix_cli.py): Orquestador CLI en Python que genera recetas `.R`, ejecuta el runner o computa nativamente el diagrama de Callon.

---

## 4. Protocolo de Ejecución CLI (File-Output First)

### 4.1 Generación de Recetas R Reproducibles (`generate-script`)
Cuando el agente o el usuario requiera un script `.R` listo para ejecutar en RStudio o terminal:
```bash
python scripts/bibliometrix_cli.py generate-script \
  --input ./data/corpus_scopus.csv \
  --output ./scripts/analisis_tematico.R \
  --analysis thematic \
  --field DE
```
Opciones de `--analysis`: `summary`, `co-citation`, `collaboration`, `thematic`, `evolution`, `biblioshiny`.

### 4.2 Ejecución Nativa de Diagrama de Callon (`callon-map`)
Permite calcular el diagrama estratégico de Callon (Centralidad vs. Densidad) directamente sobre archivos `.parquet`, `.csv` o `.json`, sin necesidad obligatoria de Rscript:
```bash
python scripts/bibliometrix_cli.py callon-map \
  --input ./data/corpus_mexico.parquet \
  --field DE \
  --top-terms 50 \
  --min-freq 3 \
  --plot-output ./data/mapa_callon.png \
  --output ./data/clusters_callon.json
```

### 4.3 Ejecución Desatendida con Rscript (`run`)
Invoca el runner de R para análisis masivos en servidor o entornos con R instalado:
```bash
python scripts/bibliometrix_cli.py run \
  --command thematic \
  --input ./data/scopus_export.csv \
  --field DE \
  --plot-output ./data/callon_r.png \
  --output ./data/thematic_output.json
```

---

## 5. Recetas R Canónicas (Quick Reference)

### 5.1 Carga e Importación Multibase
```r
library(bibliometrix)

# Scopus CSV
M <- convert2df("scopus.csv", dbsource = "scopus", format = "csv")

# Web of Science Plain Text
M <- convert2df("savedrecs.txt", dbsource = "wos", format = "plaintext")

# PubMed MEDLINE format
M <- convert2df("pubmed-set.txt", dbsource = "pubmed", format = "pubmed")
```

### 5.2 Análisis Descriptivo Global
```r
results <- biblioAnalysis(M, sep = ";")
summary(results, k = 10, pause = FALSE)
plot(x = results, k = 10, pause = FALSE)
```

### 5.3 Redes Bibliométricas
```r
# 1. Co-citación de referencias
NetMatrix <- biblioNetwork(M, analysis = "co-citation", network = "references", sep = ";")
net <- networkPlot(NetMatrix, n = 40, Title = "Red de Co-citación", type = "fruchterman", size = TRUE)

# 2. Colaboración entre países
M <- metaTagExtraction(M, Field = "AU_CO", sep = ";")
NetMatrix <- biblioNetwork(M, analysis = "collaboration", network = "countries", sep = ";")
net <- networkPlot(NetMatrix, n = 30, Title = "Colaboración Internacional", type = "circle")

# 3. Coocurrencia de palabras clave de autor
NetMatrix <- biblioNetwork(M, analysis = "co-occurrences", network = "keywords", sep = ";")
net <- networkPlot(NetMatrix, n = 50, Title = "Red Conceptual", type = "kamada")
```

### 5.4 Mapa Temático de Cuadrantes de Callon
```r
Map <- thematicMap(M, field = "DE", n = 250, minfreq = 5,
                  stemming = FALSE, size = 0.5, n.labels = 3, repel = TRUE)
plot(Map$map)
```

### 5.5 Lanzamiento de Biblioshiny (Interfaz Web)
```r
biblioshiny()
```

---

## 6. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Mezclar exportaciones de Scopus y WoS sin deduplicación previa de DOIs**  
  Cargar archivos de múltiples bases con formatos cruzados sin unificar identificadores únicos (`DI` / `UT`). Se generan documentos duplicados que sesgan fuertemente las redes de co-citación e inflan la productividad.  
  **Solución:** Deduplicar con `bibliometrix::mergeDbSources()` o prefiltrar en Python por DOI normalizado antes de la conversión.
- ❌ **Anti-patrón 2: Umbrales mínimos de coocurrencia o co-citación demasiado bajos**  
  Ejecutar `biblioNetwork()` o `thematicMap()` con `minfreq = 1` o sin fijar `n`. Provoca la creación de grafos gigantescos con miles de aristas esporádicas que saturan la memoria de R y generan visualizaciones ilegibles de tipo "bola de estambre" (*hairball*).  
  **Solución:** Fijar siempre `n` acotado (p. ej. `n = 30` a `50` nodos) y `minfreq >= 3` a `5`.
- ❌ **Anti-patrón 3: Confundir Palabras Clave de Autor (`DE`) con Keywords Plus (`ID`)**  
  Usar `field = "ID"` para diagramas de Callon esperando capturar el vocabulario directo de los investigadores. Las Keywords Plus son generadas algorítmicamente a partir de títulos citados e introducen términos genéricos (p. ej. *system*, *model*, *performance*) que contaminan los temas motores.  
  **Solución:** Usar `field = "DE"` (Author Keywords) para frentes emergentes y análisis temático conceptual riguroso.
- ❌ **Anti-patrón 4: Omitir la fijación de semilla aleatoria (`set.seed`) en disposiciones de red**  
  Generar redes con algoritmos de fuerza dirigidos (*Fruchterman-Reingold* o *Kamada-Kawai*) sin fijar una semilla estocástica. Cada ejecución reordena los nodos en coordenadas distintas, impidiendo la reproducibilidad de informes científicos.  
  **Solución:** Invocar `set.seed(1234)` antes de cualquier `networkPlot()` o `thematicMap()`.
- ❌ **Anti-patrón 5: Falta de normalización de variantes de nombres o acrónimos institucionales**  
  Construir redes de coautoría o instituciones directamente desde datos crudos. Un mismo autor puede figurar como `GARCIA, J.`, `GARCIA, J.L.` y `GARCIA-ANDRADE, J.`, fragmentando su centralidad en la red.  
  **Solución:** Utilizar tablas de sinónimos (*thesaurus*) en `thematicMap(synonyms = ...)` o normalizar previamente las variantes hispanas.

---

## 7. Referencias Técnicas

- [Fundamentos Teóricos del Diagrama de Callon (1991)](references/callon_thematic_quadrants_theory.md)
- [Diccionario de Etiquetas de Campo Canónicas (`AU`, `DE`, `CR`, etc.)](references/bibliometrix_field_tags_guide.md)
- [Script Autónomo de Ejecución R](scripts/bibliometrix_runner.R)
- [Orquestador y Puente CLI Python](scripts/bibliometrix_cli.py)
- [Sitio Oficial de Bibliometrix](https://www.bibliometrix.org/)
- Aria, M. & Cuccurullo, C. (2017). "bibliometrix: An R-tool for comprehensive science mapping analysis." *Journal of Informetrics*, 11(4), 959–975. [DOI: 10.1016/j.joi.2017.08.007](https://doi.org/10.1016/j.joi.2017.08.007).
