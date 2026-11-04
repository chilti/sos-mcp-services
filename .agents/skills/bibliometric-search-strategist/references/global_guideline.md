# Guía de Aplicación de la Lista de Verificación GLOBAL (ISSI)

Basado en: International Society for Scientometrics and Informetrics (ISSI) / ScholCommLab (Sugimoto, C. R., Larivière, V., Haustein, S., Vanderbilt, et al., 2023–2024). *GLOBAL: Guidance List for repOrting Bibliometric AnaLyses*.

---

## 1. Fundamentos y Necesidad en Cienciometría

A diferencia de las revisiones sistemáticas médicas (diseñadas bajo PRISMA para evaluar ensayos clínicos individuales y metaanálisis farmacológicos), los estudios cienciométricos y bibliométricos analizan **estructuras macroscópicas de la ciencia**, dinámicas de colaboración, linajes de citas y frentes de investigación.

La guía **GLOBAL** surge del consenso de la comunidad académica internacional de cienciometría para superar la crisis de reproducibilidad en los estudios bibliométricos, estableciendo un estándar explícito para reportar cómo se delimita el corpus, cómo se limpian los datos y cómo se configuran los algoritmos de redes.

---

## 2. Los 7 Dominios de la Lista de Verificación GLOBAL

### Dominio 1: Justificación Teórica y Preguntas de Investigación
- **Delimitación del Problema:** Justificación epistemológica del campo o temática bajo estudio.
- **Alcance Cienciométrico:** Especificación clara de si el estudio es evaluativo (indicadores de rendimiento), relacional (mapeo científico de redes) o longitudinal (trayectorias temporales).

### Dominio 2: Fuentes de Información y Snapshot Temporal
- **Bases de Datos Seleccionadas:** Declarar explícitamente las plataformas consultadas (OpenAlex, Web of Science Core Collection, Scopus, PubMed, Dimensions).
- **Snapshot y Fecha de Consulta:** Fecha exacta y huso horario de la extracción de datos. Dado que bases como OpenAlex, Scopus y WoS actualizan citas e indexaciones a diario, la fecha exacta es indispensable para la replicabilidad.
- **Edición y Suscripción:** Índices exactos consultados (p. ej., SCIE, SSCI, AHCI, ESCI en WoS) para evitar discrepancias por coberturas institucionales distintas.

### Dominio 3: Delimitación del Corpus (Field Delineation)
- **Ecuación de Búsqueda Completa:** Publicar la sintaxis literal y exacta utilizada en cada base, con etiquetas de campo (`TS=`, `TITLE-ABS-KEY()`, `[tiab]`).
- **Enfoque de Delimitación:** Indicar si la delimitación fue léxica pura (palabras clave/operadores booleanos), basada en citaciones (acoplamiento bibliográfico, clusters de co-citación) o híbrida (núcleo léxico + expansión por red).
- **Justificación de Términos:** Procedimiento para seleccionar palabras clave (tesauros MeSH/Emtree, Topics, o método iterativo *Pearl Growing*).
- **Límites Documentales y Temporales:** Justificación explícita del rango de años (`PY`) y de los tipos de documentos incluidos (`DT=Article/Review`).

### Dominio 4: Limpieza de Datos y Desambiguación de Entidades
- **Desduplicación:** Protocolo de detección de duplicados entre bases (normalización de DOI, concordancia de título/año).
- **Desambiguación Autoral:** Algoritmos o identificadores persistentes empleados para resolver homónimos (ORCID, OpenAlex Author IDs, Scopus Author ID).
- **Armonización Institucional:** Normalización de variantes organizacionales a través de vocabularios controlados (códigos ROR, subdependencias universitarias).
- **Tesauro de Palabras Clave:** Fusión de sinónimos, lemas, acrónimos y eliminación de palabras vacías (*stopwords*) o términos metodológicos genéricos.

### Dominio 5: Indicadores y Métricas Seleccionadas
- **Indicadores de Rendimiento:** Volumen de producción ($P$), citas totales ($C$), citas por documento ($C/P$), citas normalizadas por campo (FWCI / CNCI), decil de excelencia (Top 10%).
- **Indicadores Relacionales:** Conteo completo vs. conteo fraccional (*fractional counting*, Perianes-Rodriguez et al., 2016) para coautoría y acoplamiento bibliográfico.
- **Normalización de Similitud:** Especificación de la función de asociación empleada: *Association Strength* (Van Eck & Waltman), Coseno de Salton, Jaccard o Índice de Equivalencia.

### Dominio 6: Algoritmos, Software y Parámetros
- **Herramientas de Software:** Nombres y versiones exactas de las herramientas empleadas (VOSviewer, Bibliometrix en R, KnoMap, SciMAT, Gephi, Python NetworkX).
- **Umbrales Mínimos:** Frecuencia mínima de ocurrencia para nodos (palabras clave $\ge n$, citas mínimas $\ge c$).
- **Algoritmo de Clustering y Resolución:** Algoritmo de partición comunitaria (Leiden, Louvain, Infomap) y parámetro de resolución modular ($\gamma$).

### Dominio 7: Ciencia Abierta y Disponibilidad de Datos y Código
- **Disponibilidad de Datos:** Repositorio público (Zenodo, OSF, Figshare, GitHub) con el archivo canónico de metadatos (Parquet, CSV, RIS).
- **Scripts de Reproducibilidad:** Código fuente documentado con semillas fijas (`random_state=42`) para que cualquier investigador pueda regenerar las redes y tablas.
