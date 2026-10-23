---
name: tlachia-metrics-handler
description: >-
  Gestor integral de paquetes exportados de TlachIA Metrics (.zip y directorios). Inspecciona inventarios de unidades (Locations, Organizations, Sources, Topics), extrae matrices de indicadores cienciométricos listas para el entrenamiento del SOM y recupera el archivo canónico de metadatos de documentos para análisis de redes bibliométricas (coautoría, acoplamiento y coocurrencia).
---

# TlachIA Metrics Handler: Gestor de Paquetes y Extracción Analítica

## 1. Propósito y Activación

Esta skill se activa cuando el usuario proporciona un **paquete exportado desde TlachIA Metrics** (archivo `.zip` o directorio descomprimido, por ejemplo `Artificial_Intelligence_in_Education.zip`) y requiere:

1. **Inspeccionar el Inventario del Paquete:** Identificar las unidades analíticas disponibles (`Locations`, `Organizations`, `Publication Sources`, `Research Areas Topic`, `Corpus`), los periodos temporales y los metadatos generales del corpus.
2. **Extraer Matrices Multidimensionales para el SOM:** Extraer perfiles tabulares limpios $[N \times D]$ de entidades específicas (ej. países en `Locations`, universidades en `Organizations`) seleccionando los indicadores cienciométricos deseados para enviarlos a [`som-methodological-expert`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md), [`neural-longitudinal-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md) o [`som-trajectory-mapping`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md).
3. **Localizar y Preparar el Archivo de Metadatos de Obras (`works_file`):** Extraer y validar el archivo canónico de documentos (`*_openalex_works.csv` o `.parquet`) para su posterior consumo en análisis de redes complejas con [`bibliometric-network-analyst`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/bibliometric-network-analyst/SKILL.md) (coautoría, acoplamiento bibliográfico, cocitación y coocurrencia de palabras clave).

---

## 2. Anatomía de un Paquete TlachIA Metrics

Los paquetes canónicos descargados de TlachIA Metrics contienen una arquitectura estandarizada en 5 niveles:

```
[Paquete TlachIA Metrics / .zip]
├── manifest.json                                # Metadatos del corpus, fecha y parámetros de consulta
├── LEEME_ESTRUCTURA.txt                         # Documentación de estructura y campos
├── 01_Matrices_Desempeño_Longitudinal/          # Matrices con variaciones interperiódicas (Δ% Docs, Δ FWCI)
│   ├── Locations Performance Matrix.csv
│   └── Organizations Performance Matrix.csv
├── 02_Periodos_Consecutivos/                    # Tablas desagregadas por lustros o ventanas fijas
│   ├── Locations 2016-2020.csv
│   └── Locations 2021-2026.csv
├── 03_Historico_Completo/                       # Perfil acumulado de todo el horizonte temporal
│   ├── Locations.csv                            # (150+ países con 30+ indicadores)
│   └── Organizations.csv                        # (Universidades e institutos)
├── 04_Tendencias_Anuales/                       # Series temporales año por año
│   └── Locations Trend.csv                      # (Mediciones anuales para suavizado y trayectorias)
└── 05_Tablas_Parquet_y_Datos/                   # Datos columnares y obras completas
    ├── <Nombre_Corpus>_openalex_works.csv       # Archivo canónico de documentos enriquecidos
    └── locations_full.parquet                   # Versión binaria de alta velocidad
```

---

## 3. Correspondencia con la Interfaz de Usuario en KnoMap

Cuando este archivo se carga visualmente en la interfaz de KnoMap, el comportamiento del agente debe emular la experiencia del usuario en la plataforma:

| Pestaña en KnoMap | Entidad Canónica (`unit_name`) | Objeto de Análisis |
| :--- | :--- | :--- |
| **Locations** | `Locations` | Países y territorios (código ISO-2 / ISO-3) |
| **Organizations** | `Organizations` | Universidades, centros de investigación y dependencias |
| **Sources** | `Publication Sources` | Revistas científicas, conferencias y repositorios |
| **Topics / Areas** | `Research Areas Topic` | Líneas de investigación temáticas (Topics OpenAlex) |
| **Subfields / Fields**| `Research Areas Subfield` / `Field`| Taxonomía disciplinar superior |
| **SDG** | `Research Areas SDG` | Objetivos de Desarrollo Sostenible (ODS 1–17) |
| **Corpus** | `Corpus` | Indicadores macro agregados del campo completo |

* **Acción *«Send to SOM»*:** En KnoMap, al seleccionar una entidad y un conjunto de columnas numéricas en la tabla, el frontend envía los datos al motor SOM. El agente reproduce este flujo programáticamente mediante las herramientas MCP.

---

## 4. Protocolo MCP de Extracción y Modelado

El agente ejecuta el siguiente flujo paso a paso:

```
+-------------------------------------------------------------------------------+
|                       FLUJO DE TRABAJO TLACHIA -> SOM & REDES                 |
+-------------------------------------------------------------------------------+
| 1. inspect_tlachia_package(package_path="...")                                |
|       ↓ (Retorna unidades disponibles, session_dir y works_file)              |
| 2. DECISIÓN DEL USUARIO:                                                      |
|       ├─ A. Modelado de Perfiles SOM:                                         |
|       │     get_tlachia_unit_matrix(unit_name="Locations", indicators=[...])  |
|       │     ↓ (Pasa data & labels a suggest_grid_size y train_som)            |
|       │     Aplicar metodología en som-methodological-expert                  |
|       │                                                                       |
|       ├─ B. Trayectorias Temporales (Órbita de Países):                       |
|       │     get_tlachia_temporal_evolution(entities=["RU","US","CN",...])     |
|       │     ↓ (Aplicar splines cúbicos y medias móviles centradas)            |
|       │     Aplicar metodología en som-trajectory-mapping (máx. 5 entidades)   |
|       │                                                                       |
|       └─ C. Análisis de Redes Bibliométricas:                                 |
|             get_tlachia_works_metadata(session_dir="...")                     |
|             ↓ (Obtiene works_file_path con columnas de autores/referencias)   |
|             Transferir a bibliometric-network-analyst                         |
+-------------------------------------------------------------------------------+
```

### Paso 1: Inspeccionar el Paquete
Invocar `knomap-som-engine -> inspect_tlachia_package`:
```python
# Ejemplo de llamada MCP:
inspect_tlachia_package(
    package_path=r"C:\Users\jlja\Downloads\Artificial_Intelligence_in_Education.zip"
)
```
* **Respuesta:** Devuelve `session_dir` (directorio temporal indexado), lista de `available_units` y metadatos del archivo de obras/artículos (`document_count`).

### Paso 2: Extraer la Matriz de Desempeño (ej. Países en `Locations`)
Invocar `knomap-som-engine -> get_tlachia_unit_matrix`:
```python
# Extracción de países con indicadores balanceados:
get_tlachia_unit_matrix(
    session_dir_or_zip=session_dir,
    unit_name="Locations",
    period_mode="Whole",        # "Whole" (histórico) o "5Years" (reciente)
    selected_indicators=[
        "Field-Weighted Citation Impact (FWCI)",
        "Citation Impact",
        "% Documents in Top 10%",
        "% Documents in Top 1%",
        "Average Percentile",
        "% All Open Access Documents",
        "% Free to Read / Diamond Documents",
        "% International Collaborations",
        "% Industry Collaborations",
        "Share"
    ],
    limit_top_n=50,             # Top 50 países líderes por volumen
    min_documents=10.0          # Opcional: umbral mínimo de masa crítica
)
```
* **Respuesta:** Devuelve `labels` (códigos de país), `indicators` y `data` (matriz $[N \times D]$ de números reales limpios sin NaNs).

### Paso 3: Enviar al Pipeline SOM
Una vez obtenida la matriz `data` y las etiquetas `labels`:
1. **Calcular Dimensiones:** Invocar `knomap-som-engine -> suggest_grid_size(data=data)` para obtener el aspect ratio SVD ($\sigma_1/\sigma_2$) y la sobremalla ($20N\text{--}30N$ neuronas según [`som-methodological-expert`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)).
2. **Entrenar SOM:** Invocar `knomap-som-engine -> train_som(data=data, labels=labels, rows=rows, cols=cols, init="pca")`.
3. **Optimizar Clusters:** Invocar `knomap-som-engine -> evaluate_som_clusters` para calibrar el $K$ óptimo vía Silhouette Score.
4. **Interpretar Resultados:** Examinar la U-Matrix y los mapas de componentes para identificar clusters de países con perfiles análogos (pares legítimos), polos de excelencia y perfiles atípicos.

### Paso 4: Recuperar el Archivo de Obras para Redes Bibliométricas
Si el usuario desea analizar redes de colaboración científica entre autores, instituciones o países, o bien redes de co-ocurrencia temática o acoplamiento bibliográfico:
Invocar `knomap-som-engine -> get_tlachia_works_metadata`:
```python
get_tlachia_works_metadata(session_dir_or_zip=session_dir)
```
* **Respuesta:** Proporciona la ruta absoluta `works_file_path` (ej. `.../Artificial_Intelligence_in_Education_openalex_works.csv`), confirma el volumen de documentos (e.g. 38,657) y valida que cuenta con las columnas requeridas:
  * `author_names` / `author_ids` $\rightarrow$ Redes de coautoría.
  * `institution_names` / `country_codes` $\rightarrow$ Redes de colaboración institucional y geopolítica.
  * `referenced_works` $\rightarrow$ Acoplamiento bibliográfico y cocitación.
  * `keywords` / `concepts` $\rightarrow$ Redes de coocurrencia conceptual.
* Esta ruta queda lista para transferirse directamente a [`bibliometric-network-analyst`](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/bibliometric-network-analyst/SKILL.md).

---

## 5. Batería de Indicadores Canónicos para `Locations` (Países)

Al asesorar al usuario en la selección de indicadores para caracterizar el perfil de desempeño de los países, se recomienda la siguiente batería equilibrada de 4 dimensiones:

1. **Capacidad y Producción:**
   * `Documents`: Volumen absoluto de artículos del país en el tema.
   * `Share`: Porcentaje de participación sobre el total mundial del corpus.
2. **Impacto Normalizado y Visibilidad:**
   * `Field-Weighted Citation Impact (FWCI)`: Citas normalizadas por campo, año y tipo de documento (Mundial = 1.0).
   * `Citation Impact`: Citas promedio por documento.
   * `Average Percentile`: Percentil promedio en ranking de citas (Mundial = 50.0).
3. **Excelencia Científica:**
   * `% Documents in Top 10%`: Proporción de artículos en el decil superior mundial.
   * `% Documents in Top 1%`: Proporción en el percentil de élite internacional.
4. **Ciencia Abierta y Modalidad de Publicación:**
   * `% All Open Access Documents`: Grado de apertura general.
   * `% Free to Read / Diamond Documents`: Publicación en Acceso Abierto Diamante (sin cobro de APC).
   * `Estimated Diamond Savings (USD)`: Ahorro acumulado generado por la vía Diamante.
5. **Colaboración e Internacionalización:**
   * `% International Collaborations`: Grado de inserción en redes transnacionales.
   * `% Industry Collaborations`: Vínculo con empresas y sector productivo.
   * `% Global South Collaborations`: Colaboración intrarregional o con países del Sur Global.

---

## 6. Referencias Técnicas

- [SOM Methodological Expert](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-methodological-expert/SKILL.md)
- [SOM Trajectory Mapping](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/som-trajectory-mapping/SKILL.md)
- [Neural Longitudinal Mapping](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/neural-longitudinal-mapping/SKILL.md)
- [Bibliometric Network Analyst](file:///C:/Users/jlja/Documents/Proyectos/sos-mcp-services/.agents/skills/bibliometric-network-analyst/SKILL.md)
- [KnoMap Engine Tlachia Parser](file:///c:/Users/jlja/Documents/Proyectos/knomap/engine/tlachia_parser.py)
