---
name: classical-bibliometrics-laws
description: >-
  Modelado matemático y validación empírica de leyes bibliométricas clásicas (Ley de Lotka con conteo full/frac y prueba KS, Ley de Bradford con formulación continua de Egghe, Índice de Price de obsolescencia y ajuste de curvas de crecimiento exponencial vs logístico).
metadata:
  python: ">=3.10"
  script: "scripts/bibliometric_laws_cli.py"
---

# Classical Bibliometrics Laws: Modelado Informétrico y Validación Empírica

## 1. Overview y Propósito

El módulo cuantitativo **`classical-bibliometrics-laws`** proporciona un entorno de cómputo riguroso para la contrastación empírica de los modelos matemáticos fundamentales de la ciencia de la información e informetría. Permite responder preguntas clave sobre la consolidación disciplinar, la concentración de autorías, la dispersión de revistas, el recambio teórico del conocimiento y las fases evolutivas de un paradigma científico.

---

## 2. Ámbito de Aplicación de cada Ley Bibliométrica

A continuación se detalla a qué entidad analítica aplica cada modelo, su formulación y su utilidad en la toma de decisiones cienciométricas:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      MATRIZ DE APLICABILIDAD DE LEYES CLÁSICAS                         │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ Ley Bibliométrica        │ Entidad a la que Aplica     │ Pregunta / Decisión que Resuelve│
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 1. Ley de Lotka (1926)   │ Autoras e Investigadores    │ ¿Qué tan concentrada o equi-   │
│                          │ (Población de autores)      │ tativa es la producción en la  │
│                          │                             │ disciplina? ¿Hay élite activa?│
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 2. Ley de Bradford (1934 │ Revistas Científicas        │ ¿Cuáles son las Core Journals  │
│    / Egghe 1990)         │ (Fuentes de publicación)    │ indispensables para suscrip-  │
│                          │                             │ ción o envío de manuscritos?  │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 3. Índice de Price (1965)│ Referencias Bibliográficas  │ ¿Es una ciencia dura o blanda?│
│    y Half-Life           │ (Aparato crítico citado)    │ ¿Con qué rapidez envejecen    │
│                          │                             │ los conceptos teóricos?       │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 4. Fases de Crecimiento  │ Producción Cronológica      │ ¿El campo está emergiendo, en │
│    de la Ciencia (1963)  │ (Series anuales de trabajos)│ expansión exponencial o en    │
│                          │                             │ saturación/madurez paradigmá- │
│                          │                             │ tica?                         │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

### 2.1 Ley de Lotka (Productividad de Autores, 1926)
* **A qué aplica:** A la frecuencia con la que investigadoras e investigadores publican $x$ trabajos ($x = 1, 2, 3, \dots$).
* **Fórmula:** $y_x = \frac{C}{x^c}$, con $c \approx 2.0$ y constante $C = \frac{1}{\zeta(c)}$.
* **Utilidad práctica y toma de decisiones:**
  - **Detección de estratificación:** Evalúa si la producción científica sigue el principio del cuadrado inverso (pequeña élite prolífica vs. 60% de autores ocasionales de un solo artículo).
  - **Diagnóstico institucional:** Mide si un departamento o instituto depende de unos pocos líderes consolidados o cuenta con masa crítica distribuida.
  - **Decisión metodológica:** Permite comparar el conteo completo (*full counting*, 1 crédito por coautoría) frente al conteo fraccional (*fractional counting*, $1/k$) para neutralizar el sesgo de hiper-coautoría.

### 2.2 Ley de Bradford (Dispersión de la Literatura en Fuentes, 1934 / Egghe 1990)
* **A qué aplica:** A la distribución de artículos entre las revistas o fuentes especializadas de un campo temático específico.
* **Fórmula:** División continua en $p=3$ zonas de igual producción ($A/3$), verificando la progresión geométrica $1 : k : k^2$.
* **Utilidad práctica y toma de decisiones:**
  - **Identificación del Núcleo (*Core Journals*):** Delimita la **Zona 1 (Núcleo)** que concentra un tercio de toda la literatura relevante en un grupo selecto de títulos.
  - **Optimización presupuestal:** Guía a consorcios y bibliotecas universitarias en la priorización de suscripciones indexadas indispensables, evitando el gasto en revistas periféricas de baja densidad (Zona 3).
  - **Estrategia de publicación:** Asesora a grupos de investigación sobre las revistas más canónicas para someter manuscritos.

### 2.3 Índice de Price y Vida Media Citacional (*Citing Half-Life*, 1965)
* **A qué aplica:** A las fechas de publicación del aparato crítico (referencias citadas) de los artículos del corpus.
* **Fórmula:** $I_{\text{Price}} = \frac{R_{\le 5}}{R_{\text{total}}} \times 100\%$, y mediana cronológica de la edad de citación.
* **Utilidad práctica y toma de decisiones:**
  - **Clasificación epistemológica:** Discrimina entre **Ciencias Duras (*Hard Sciences*)** ($I_{\text{Price}} \ge 50\%$, rápida obsolescencia, frentes de investigación efímeros como IA o Biomedicina) y **Ciencias Sociales / Humanidades (*Soft Sciences*)** ($I_{\text{Price}} \le 30\%$, conocimiento de larga acumulación histórica).
  - **Ritmo de recambio teórico:** Evalúa si una disciplina está recurriendo a literatura de frontera reciente o si reposa en fundamentos clásicos.

### 2.4 Fases de Crecimiento de la Ciencia (Price, Modelos Exponencial vs. Logístico, 1963)
* **A qué aplica:** A las series anuales no acumuladas de publicaciones de un campo o línea de investigación.
* **Fórmulas:** Exponencial $N(t) = a e^{bt}$ vs. Logística $N(t) = \frac{K}{1 + e^{-r(t - t_0)}}$.
* **Utilidad práctica y toma de decisiones:**
  - **Fase I (Emergencia):** Inicio lento y fluctuante de un área pionera.
  - **Fase II (Expansión Exponencial):** Crecimiento vigoroso sin restricciones; calcula el **tiempo de duplicación (*doubling time*)**, p. ej.: "la literatura en IA se duplica cada 2.1 años".
  - **Fase III (Madurez / Saturación Logística):** Desaceleración por límites de financiamiento o estabilización paradigmática; estima la **capacidad de carga ($K$)**, alertando sobre la saturación de una línea de investigación.

---

## 3. Dependencies y Cadena de Valor

```
┌─────────────────────────────────┐
│     Habilidades Upstream        │
│ • openalex-mexico-works-search  │──┐
│ • openalex-harvester / scopus   │  │  Corpus tabular estructurado
│ • tlachia-metrics-handler (ZIP) │  │  (.parquet, .csv, .json)
└─────────────────────────────────┘  │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │      classical-bibliometrics-laws   │
                  │  (Lotka, Bradford, Price, Crecim.)  │
                  └─────────────────────────────────────┘
                                     │
                                     ▼  Resultados JSON y gráficos PNG
┌────────────────────────────────────┴────────────────────────────────────┐
│                       Habilidades Downstream                            │
│ • som-methodological-expert (U-Matrix y perfiles de productividad)       │
│ • bibliometric-network-analyst (Acoplamiento de revistas en el Core)    │
│ • Reportes cienciométricos institucionales y de política científica    │
└─────────────────────────────────────────────────────────────────────────┘
```

* **Habilidades Upstream (Proveedores del corpus):**
  - [`openalex-mexico-works-search`](../openalex-mexico-clickhouse/openalex-mexico-works-search/SKILL.md): Extracción de corpus de publicaciones de México en formato Parquet/JSON.
  - [`openalex-harvester`](../openalex-harvester/SKILL.md) / [`scopus-harvester`](../scopus-harvester/SKILL.md) / [`arxiv-harvester`](../arxiv-harvester/SKILL.md): Descarga normalizada de literatura científica.
  - [`tlachia-metrics-handler`](../tlachia-metrics-handler/SKILL.md): Extracción de paquetes canónicos de metadatos de documentos.
* **Habilidades Downstream (Consumidores del análisis):**
  - [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Incorporación de indicadores clásicos a perfiles multidimensionales para entrenamiento SOM.
  - [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md): Acoplamiento bibliográfico y redes de co-citación restringidas al Core de Bradford.
* **Entorno de Ejecución:**
  - Python `>=3.10` con paquetes requeridos: `numpy`, `scipy`, `matplotlib`, `pandas`.
  - Script CLI: [`scripts/bibliometric_laws_cli.py`](scripts/bibliometric_laws_cli.py).

---

## 4. Protocolo de Ejecución CLI (File-Output First)

Todos los comandos reciben un archivo estructurado de entrada (`--input <ruta>`) en formato `.parquet`, `.csv` o `.json` y requieren obligatoriamente una ruta de salida JSON (`--output <ruta>`), con opción de generar un gráfico de alta resolución en PNG (`--plot-output <ruta>`).

### 4.1 Ley de Lotka (`lotka`)
Ajusta la distribución de productividad autoral y calcula la prueba Kolmogorov-Smirnov:
```bash
python scripts/bibliometric_laws_cli.py lotka \
  --input ./data/corpus_cientifico.parquet \
  --counting full \
  --plot-output ./data/grafico_lotka.png \
  --output ./data/resultado_lotka.json
```
* **Opciones de `--counting`:**
  - `full`: Conteo completo (1 crédito por coautoría; estándar para sociología de la ciencia).
  - `fractional`: Conteo fraccional ($1/k$; recomendado ante hiper-coautoría o equipos extensos).

### 4.2 Ley de Bradford (`bradford`)
Divide las fuentes en 3 zonas de igual producción aplicando la formulación continua de Egghe:
```bash
python scripts/bibliometric_laws_cli.py bradford \
  --input ./data/corpus_cientifico.parquet \
  --output ./data/zonas_bradford.json
```

### 4.3 Índice de Price y Obsolescencia (`price-index`)
Calcula la proporción de referencias con $\le 5$ años y la vida media citacional:
```bash
python scripts/bibliometric_laws_cli.py price-index \
  --input ./data/corpus_cientifico.parquet \
  --output ./data/indice_price.json
```

### 4.4 Fases de Crecimiento de la Ciencia (`growth-phase`)
Compara el ajuste Exponencial vs. Logístico para diagnosticar la fase de madurez del campo:
```bash
python scripts/bibliometric_laws_cli.py growth-phase \
  --input ./data/corpus_cientifico.parquet \
  --plot-output ./data/grafico_crecimiento.png \
  --output ./data/diagnostico_fase.json
```

---

## 5. Especificación de Métricas y Contratos de Datos (JSON)

### 5.1 Salida de `lotka` (`resultado_lotka.json`)
```json
{
  "law": "Lotka's Law",
  "counting_mode": "full",
  "total_authors": 12450,
  "fitted_exponent_c": 2.154,
  "fitted_constant_C": 0.62,
  "r_squared": 0.965,
  "ks_statistic_d_max": 0.0142,
  "ks_critical_value_05": 0.0122,
  "goodness_of_fit_accepted": true,
  "empirical_distribution": [
    {"papers": 1, "authors": 7800},
    {"papers": 2, "authors": 1950}
  ],
  "plot_path": "./data/grafico_lotka.png"
}
```

### 5.2 Salida de `bradford` (`zonas_bradford.json`)
```json
{
  "law": "Bradford's Law (Egghe Demarcation)",
  "total_sources": 850,
  "total_articles": 4200,
  "zones": {
    "zone_1_core": {
      "description": "Núcleo de Revistas (Core)",
      "sources_count": 18,
      "articles_count": 1400,
      "top_sources": ["Journal of Informetrics", "Scientometrics"]
    },
    "zone_2_moderate": {
      "description": "Zona de Concentración Moderada",
      "sources_count": 95,
      "articles_count": 1400
    },
    "zone_3_peripheral": {
      "description": "Zona Periférica / Alta Dispersión",
      "sources_count": 737,
      "articles_count": 1400
    }
  },
  "bradford_multiplier_k": 5.4,
  "theoretical_proportion": "1 : 5.4 : 29.2"
}
```

### 5.3 Salida de `price-index` (`indice_price.json`)
```json
{
  "law": "Price's Index of Obsolescence",
  "total_analyzed_references": 54200,
  "references_le_5_years": 29810,
  "price_index_percentage": 55.0,
  "citing_half_life_years": 4.5,
  "interpretation": "Hard Science (Rápida obsolescencia)"
}
```

### 5.4 Salida de `growth-phase` (`diagnostico_fase.json`)
```json
{
  "law": "Scientific Growth Phases",
  "years_range": [2010, 2025],
  "exponential_fit": {
    "r_squared": 0.942,
    "doubling_time_years": 3.4
  },
  "logistic_fit": {
    "r_squared": 0.885,
    "estimated_saturation_carrying_capacity_K": 1250.0
  },
  "diagnosed_phase": "Fase II: Crecimiento Exponencial (Expansión Activa)",
  "plot_path": "./data/grafico_crecimiento.png"
}
```

---

## 6. Common Mistakes y Anti-Patrones (Evitar Errores Frecuentes)

- ❌ **Anti-patrón 1: Mezclar disciplinas heterogéneas al aplicar Bradford**  
  Aplicar el análisis de Bradford sobre un corpus multidisciplinario o institucional global (ej. toda la producción de una universidad que combina medicina, derecho, física y sociología) en lugar de un campo temático específico.  
  *Efecto:* Destruye la relación geométrica ($1 : k : k^2$), inflando artificialmente el tamaño del núcleo y falseando la dispersión.  
  **Solución:** Segmentar el corpus por dominio temático específico (vía `openalex-mexico-works-search --topic` o categorías normalizadas).
- ❌ **Anti-patrón 2: Asumir validez de Lotka sin prueba formal Kolmogorov-Smirnov**  
  Ajustar una regresión lineal sobre log(autores) vs. log(artículos) y reportar sólo $R^2$ alto, sin verificar el estadístico de prueba $D_{\max}$ frente al valor crítico $1.36/\sqrt{N}$.  
  *Efecto:* Aceptar erróneamente que una comunidad obedece la ley cuando la prueba estadística no paramétrica la rechaza a $\alpha=0.05$.  
  **Solución:** Inspeccionar siempre `"goodness_of_fit_accepted"` y `"ks_statistic_d_max"` en la salida JSON.
- ❌ **Anti-patrón 3: Omitir la distinción entre Conteo Completo (*Full*) y Fraccional (*Fractional*)**  
  Utilizar conteo completo por defecto en campos dominados por hiper-coautoría (e.g. física de partículas o medicina genómica con decenas o cientos de autores por trabajo).  
  *Efecto:* Se distorsiona la distribución, creando una falsa abundancia de autores hiperproductivos y alterando el exponente $c$.  
  **Solución:** Usar `--counting fractional` cuando el corpus presente promedio de coautores $> 5$, distribuyendo $1/k$ créditos por autor.
- ❌ **Anti-patrón 4: Sesgo temporal en Price por referencias no fechadas o anacrónicas**  
  Asumir que todas las referencias citadas contienen un año interpretable o incluir citas con fechas posteriores al artículo (citas anacrónicas o *in press* con edad negativa).  
  *Efecto:* Distorsión severa del porcentaje del índice de Price y de la vida media citacional.  
  **Solución:** Descartar referencias no parseables y filtrar referencias donde $\text{año}_{\text{referencia}} \le \text{año}_{\text{documento}}$, como implementa de forma segura el CLI.
- ❌ **Anti-patrón 5: Ajustar curvas de crecimiento sobre menos de 4 años o sobre series acumuladas**  
  Ejecutar `growth-phase` en rangos temporales demasiado estrechos (ej. 2023–2024) o acumular manualmente las publicaciones antes de pasarlas al script.  
  *Efecto:* El algoritmo de optimización no lineal de Levenberg-Marquardt para la curva logística diverge o falla (`Insufficient variation`).  
  **Solución:** Disponer de un mínimo de 4 a 5 años de producción anual no acumulada para evaluar la curvatura sigmoide y el punto de inflexión.

---

## 7. Referencias Técnicas

- [Fundamentos Matemáticos de Leyes Clásicas](references/classical_laws_mathematical_foundations.md)
- [Formulación Continua de Bradford (Egghe)](references/egghe_continuous_bradford.md)
- [Estándar Canónico de Diseño de Skills Científicas](../../docs/estandar_diseno_skills_cientificas.md)
- [Script CLI Canónico](scripts/bibliometric_laws_cli.py)
