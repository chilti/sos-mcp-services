---
name: geopolitical-collaboration-analyst
description: Cartografía geopolítica de la ciencia, matrices de coautoría internacional normalizadas con ISO-3166-1 alpha-3, afinidad bilateral con Coseno de Salton y Jaccard, benchmarking por bloques regionales (Iberoamérica, Sur Global, OCDE, BRICS, UE), evaluación de soberanía epistemológica (ratios de primer autor y autor de correspondencia) y generación de dashboards interactivos autónomos (Plotly HTML con mapas mundiales, diagramas Sankey y matrices de cuadrantes).
dependencies:
  - python: ">=3.10"
  - script: "scripts/geopolitical_collab_cli.py"
  - references:
      - "references/iso_3166_alpha3_dictionary.md"
      - "references/scientific_leadership_metrics.md"
---

# Geopolitical Collaboration Analyst

Módulo cuantitativo y motor analítico de cartografía geopolítica de la ciencia y diplomacia científica internacional para analizar flujos transfronterizos de conocimiento, evaluar afinidades estratégicas y diagnosticar la soberanía epistemológica nacional.

---

## 1. Visión General y Alcance

Desacoplado de bases de datos externas y optimizado para ejecutarse de manera autónoma sobre cualquier corpus científico (Web of Science en texto plano `.txt`, `.csv`, `.parquet`, `.json` u OpenAlex), este módulo resuelve preguntas estratégicas de política científica:
* **¿Con quién investiga un país o institución?** Matrices de coautoría estandarizadas en códigos canónicos [ISO-3166-1 alpha-3](references/iso_3166_alpha3_dictionary.md).
* **¿Cuál es la afinidad bilateral real?** Normalización con el **Coseno de Salton** y el **Índice de Jaccard**, mitigando el sesgo de tamaño que favorece a las superpotencias.
* **¿Hacia qué bloques geopolíticos gravita la producción?** Cuantificación porcentual de la cooperación hacia **Iberoamérica**, el **Sur Global**, la **OCDE**, los **BRICS** y la **Unión Europea**.
* **¿Quién ejerce el liderazgo intelectual?** Diagnóstico de soberanía epistemológica mediante la posición de primer autor ($L_{\text{first}}$) y autor de correspondencia ($L_{\text{corr}}$), diferenciando consorcios simétricos de esquemas asimétricos o de *"ciencia helicóptero"*.

---

## 2. Artefactos Generados por la Skill

La skill produce artefactos analíticos y visuales de nivel ejecutivo:

| Artefacto | Formato | Descripción |
|---|:---:|---|
| **Dashboard Geopolítico Interactivo** | HTML autónomo (Plotly) | Dashboard interactivo con tema oscuro cienciométrico: Mapa Coroplético mundial, diagrama de flujos Sankey (País $\to$ Bloques $\to$ Socios), matriz estratégica de cuadrantes (Salton vs. Volumen), barras de soberanía por contraparte y tabla dinámica filtrable. |
| **Matriz Consolidada de Países** | JSON | Desglose integral con totales de producción, conteos de coautoría, coeficientes de Salton/Jaccard, métricas de liderazgo y benchmarking regional. |
| **Tabla de Socios Bilaterales** | CSV | Exportación tabular lista para Excel, Gephi o R con rangos, códigos ISO-3, nombres oficiales, región, coautorías y balance de autoría. |

---

## 3. Comandos CLI y Flujo de Trabajo

El script ejecutable [`scripts/geopolitical_collab_cli.py`](scripts/geopolitical_collab_cli.py) ofrece una interfaz CLI modular:

### 3.1 Flujo Integral Todo-en-Uno (`analyze-all`)
Ejecuta la extracción de afiliaciones, cálculo de Salton, benchmarking por bloques, evaluación de soberanía y exporta el dashboard HTML y datos estructurados:

```powershell
python .agents/skills/geopolitical-collaboration-analyst/scripts/geopolitical_collab_cli.py analyze-all \
  --input "C:\ruta\al\corpus.txt" \
  --anchor-country MEX \
  --top-n 30 \
  --output-json "reports/analisis_geopolitico_mexico.json" \
  --output-csv "reports/socios_bilaterales_mexico.csv" \
  --html "reports/dashboard_geopolitico_mexico.html" \
  --title "Cartografía Geopolítica de México (2020-2025)"
```

### 3.2 Matriz País-País y Afinidad de Salton (`country-matrix`)
Calcula la red bilateral y las métricas de proximidad cienciométrica respecto al país ancla:

```powershell
python .agents/skills/geopolitical-collaboration-analyst/scripts/geopolitical_collab_cli.py country-matrix \
  --input "corpus.parquet" \
  --anchor-country MEX \
  --top-n 25 \
  --output "matriz_paises.json" \
  --html "mapa_colaboracion.html"
```

### 3.3 Benchmarking por Bloque Regional (`regional-benchmark`)
Audita la intensidad de colaboración capturada por una región estratégica específica:

```powershell
python .agents/skills/geopolitical-collaboration-analyst/scripts/geopolitical_collab_cli.py regional-benchmark \
  --matrix-file "matriz_paises.json" \
  --region Iberoamerica \
  --anchor-country MEX \
  --output "benchmark_iberoamerica.json"
```
*Regiones disponibles:* `iberoamerica`, `globalsouth`, `oecd`, `brics`, `european_union`.

### 3.4 Diagnóstico de Soberanía Epistemológica (`scientific-leadership`)
Evalúa los porcentajes de primer autor y correspondencia nacional en artículos internacionales:

```powershell
python .agents/skills/geopolitical-collaboration-analyst/scripts/geopolitical_collab_cli.py scientific-leadership \
  --input "corpus.csv" \
  --country MEX \
  --output "liderazgo_mexico.json"
```

---

## 4. Fundamentos Metodológicos y Fórmulas

### 4.1 Coseno de Salton Bilateral
Normaliza la coautoría considerando las capacidades relativas de ambos países:

$$\text{Salton}_{ij} = \frac{C_{ij}}{\sqrt{T_i \times T_j}}$$

* $C_{ij}$: Artículos en coautoría conjunta entre el país ancla $i$ y el socio $j$.
* $T_i, T_j$: Producción total individual del país $i$ y del país $j$ en el corpus.

### 4.2 Matriz Estratégica de Cuadrantes (Salton vs. Volumen)
Permite categorizar a los socios en 4 cuadrantes respecto a las medianas del corpus:
1. **Socios Estratégicos Nucleares (Cuadrante I - Alto Salton / Alto Volumen):** Vínculos consolidados y estructurales.
2. **Aliados de Especialización (Cuadrante II - Alto Salton / Volumen Moderado):** Relaciones de alta afinidad relativa que maximizan la cercanía temática por sobre el tamaño bruto.
3. **Socios por Inercia Global (Cuadrante III - Bajo Salton / Alto Volumen):** Grandes potencias con las que se colabora por su enorme masa crítica global, sin reflejar necesariamente una afinidad preferencial.
4. **Colaboraciones Periféricas (Cuadrante IV - Bajo Salton / Bajo Volumen):** Contactos esporádicos.

### 4.3 Tasa de Liderazgo y Asimetría Norte-Sur

$$L_{\text{first}}(\text{ancla}) = \frac{N_{\text{primer\_autor\_ancla}}}{N_{\text{artículos\_internacionales}}} \times 100\%$$

| Nivel de Liderazgo | Diagnóstico | Significado de Política Científica |
|:---:|:---|:---|
| **$L \ge 50\%$** | **Soberano / Preponderante** | El país formula las preguntas de investigación, dirige los experimentos y redacta los manuscritos principales. |
| **$40\% \le L < 50\%$** | **Simétrico / Equitativo** | Cooperación horizontal con distribución balanceada de responsabilidades. |
| **$30\% \le L < 40\%$** | **Intermedio / Compartido** | Participación activa con co-dirección frecuente. |
| **$L < 30\%$** | **Asimétrico / Subordinado** | *"Ciencia Helicóptero"*: el país local suele actuar como proveedor de muestras, trabajo de campo o datos primarios, mientras la dirección intelectual recae en centros del Norte Global. |

---

## 5. Anti-Patrones y Buenas Prácticas Metodológicas

| Anti-Patrón | Riesgo Metodológico | Corrección Canónica en la Skill |
|---|---|---|
| **Conteo Crudo de Coautorías:** Reportar únicamente $C_{ij}$ sin normalizar. | Sesgo de tamaño: Estados Unidos y China siempre encabezan cualquier ranking, ocultando afinidades estratégicas latinoamericanas o ibéricas. | Calcular siempre el **Coseno de Salton** y el **Índice de Jaccard** para ponderar la intensidad relativa. |
| **Truncación Ciega de 3 Caracteres:** Truncar textos desconocidos a sus primeros 3 caracteres. | Provincias, ciudades chinas (Xiamen $\to$ `XIA`, Qingdao $\to$ `QIA`) o códigos postales se convierten en falsos países soberanos. | Uso estricto de catálogo canónico ISO-3166-1 (249 países) y descarte de cadenas no identificadas como país soberano. |
| **Confusión Primer Autor vs. Autor de Correspondencia:** Asumir que son siempre idénticos. | En muchas disciplinas biomédicas el último autor o el autor de correspondencia es el líder senior del laboratorio. | Extraer de forma independiente $L_{\text{first}}$ (campo `C1`/primer bloque) y $L_{\text{corr}}$ (campo `RP`/Reprint author). |
| **Ignorar Megaciencia y Ensayos Clínicos Multicéntricos:** No advertir sobre artículos con >50 autores o física de altas energías. | En consorcios masivos (CERN, ATLAS, ensayos clínicos globales) el ratio de primer autor nacional puede descender al <10% sin implicar subordinación extractiva. | Contextualizar los indicadores de liderazgo filtrando o advirtiendo sobre hiperautorías. |
| **Mezcla de ISO-2 con ISO-3:** Usar indistintamente códigos de 2 y 3 letras. | Inconsistencia en visualizadores geográficos y bases de datos tabulares. | Homogeneización automática a **ISO-3166-1 alpha-3** como clave canónica única. |

---

## 6. Referencias y Documentación Técnica

* [`references/iso_3166_alpha3_dictionary.md`](references/iso_3166_alpha3_dictionary.md): Diccionario exhaustivo de normalización a códigos de tres letras y agrupación regional.
* [`references/scientific_leadership_metrics.md`](references/scientific_leadership_metrics.md): Fundamentos matemáticos de las métricas de soberanía cienciométrica y asimetría Norte-Sur.
* Moya-Anegón, F., et al. (2013). *A new technique for building mapping of science: combining co-citation and bibliographic coupling*. Journal of Informetrics.
* Chinchilla-Rodríguez, Z., et al. (2019). *The role of scientific leadership in international scientific collaboration*. Scientometrics.
