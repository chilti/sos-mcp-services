# Guía de Análisis Temporal y Longitudinal por Periodos en TlachIA

El motor de métricas cienciométricas de TlachIA permite analizar la evolución histórica de un corpus científico en tres escalas temporales:
1. **Series anuales continuas** (`annual-series`)
2. **Periodos únicos focalizados** (`calculate-summary --last-years 5` o `--period 2019-2024`)
3. **Periodos consecutivos y ventanas deslizantes** (`period-series`)

---

## 1. Modos de Partición Temporal

### A. Ventanas Fijas Consecutivas (`--window N`)
Divide el intervalo total del corpus en bloques no superpuestos de $N$ años:
- Si el corpus va de 2000 a 2024 con `--window 5`:
  `[2000-2004, 2005-2009, 2010-2014, 2015-2019, 2020-2024]`
- Si el corpus va de 2005 a 2024 con `--window 10`:
  `[2005-2014, 2015-2024]`

### B. Ventanas Deslizantes / Rodantes (`--window N --step S`)
Permite capturar dinámicas de transición suave con superposición:
- `--window 5 --step 1`:
  `[2015-2019, 2016-2020, 2017-2021, 2018-2022, 2019-2023, 2020-2024]`

### C. Lista Explícita de Periodos (`--periods "P1,P2,..."`)
Permite definir hitos institucionales o sexenales:
- `--periods "2006-2012,2012-2018,2018-2024"`

### D. Periodo Único o Más Reciente (`--single-period` o `--last-years`)
- `--single-period "2020-2024"`: evalúa exclusivamente ese quinquenio.
- `--last-years 5`: calcula el lustro más reciente de forma dinámica sin necesidad de conocer el año máximo de antemano.

---

## 2. Tasas de Variación y Crecimiento Inter-Periodo

En cada transición temporal de $t-1$ a $t$, el motor cuantifica:
- **Crecimiento de Producción ($\Delta \text{Docs}$):**
  $$\text{doc\_growth\_pct} = \frac{\text{Docs}_t - \text{Docs}_{t-1}}{\text{Docs}_{t-1}} \times 100$$
- **Variación de Citación ($\Delta \text{Citas}$):**
  $$\text{cite\_growth\_pct} = \frac{\text{Citas}_t - \text{Citas}_{t-1}}{\text{Citas}_{t-1}} \times 100$$

---

## 3. Matrices Longitudinales de Entidades para SOM (`--level`)

Al combinar `period-series` con `--level researcher` o `--level institution`, el motor genera una estructura longitudinal:
- Cada fila representa una entidad en un periodo específico con sus métricas (`num_documents`, `times_cited`, `cites_per_doc`, `h_index`, `pct_oa`).
- Esta matriz longitudinal puede exportarse a `.parquet` o `.csv` y alimentar directamente los algoritmos de encadenamiento temporal Warm-Start del skill [`neural-longitudinal-mapping`](file:///home/labsom/knomap/.agents/skills/neural-longitudinal-mapping/SKILL.md).
