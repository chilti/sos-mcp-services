---
name: classical-bibliometrics-laws
description: >-
  Mathematical modeling and empirical validation of classical bibliometric laws (Lotka's Law with full/fractional counting and KS test, Bradford's Law with Egghe's continuous formulation, Price's Index of obsolescence, and exponential vs. logistic growth curve fitting). Respond and label outputs in the user's language.
metadata:
  python: ">=3.10"
  script: "scripts/bibliometric_laws_cli.py"
---

# Classical Bibliometrics Laws: Informetric Modeling and Empirical Validation

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

## 1. Overview and Purpose

The quantitative module **`classical-bibliometrics-laws`** provides a rigorous computing environment for empirically testing the foundational mathematical models of information science and informetrics. It answers key questions regarding disciplinary consolidation, authorship concentration, journal dispersion, theoretical turnover of knowledge, and the evolutionary phases of a scientific paradigm.

---

## 2. Scope of Application of Each Bibliometric Law

Below is a summary of which analytical entity each model applies to, its formulation, and its utility in scientometric decision-making:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      APPLICABILITY MATRIX OF CLASSICAL LAWS                            │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ Bibliometric Law         │ Target Entity               │ Question / Decision Answered  │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 1. Lotka's Law (1926)    │ Authors & Researchers       │ How concentrated or equitable │
│                          │ (Author population)         │ is production in the field?   │
│                          │                             │ Is there an active elite?     │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 2. Bradford's Law (1934  │ Scientific Journals         │ Which are the essential Core  │
│    / Egghe 1990)         │ (Publication sources)       │ Journals for subscriptions or │
│                          │                             │ manuscript submissions?       │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 3. Price's Index (1965)  │ Bibliographic References    │ Is it a hard or soft science? │
│    and Half-Life         │ (Cited reference apparatus) │ How quickly do theoretical    │
│                          │                             │ concepts become obsolete?     │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ 4. Growth Phases of      │ Chronological Production    │ Is the field emerging, in     │
│    Science (1963)        │ (Annual publication series) │ exponential expansion, or in  │
│                          │                             │ paradigmatic saturation/matu- │
│                          │                             │ rity?                         │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

### 2.1 Lotka's Law (Author Productivity, 1926)
* **Applies to:** The frequency with which researchers publish $x$ works ($x = 1, 2, 3, \dots$).
* **Formula:** $y_x = \frac{C}{x^c}$, with $c \approx 2.0$ and constant $C = \frac{1}{\zeta(c)}$.
* **Practical utility and decision-making:**
  - **Stratification detection:** Evaluates whether scientific output follows the inverse square principle (a small prolific elite vs. ~60% occasional one-time authors).
  - **Institutional diagnosis:** Measures whether a department or institute relies on a few established leaders or possesses distributed critical mass.
  - **Methodological decision:** Compares *full counting* (1 credit per co-authorship) against *fractional counting* ($1/k$) to neutralize hyper-authorship bias.

### 2.2 Bradford's Law (Literature Scattering Across Sources, 1934 / Egghe 1990)
* **Applies to:** The distribution of articles across specialized journals or sources in a specific thematic field.
* **Formula:** Continuous division into $p=3$ zones of equal output ($A/3$), verifying the geometric progression $1 : k : k^2$.
* **Practical utility and decision-making:**
  - **Core Journals identification:** Delineates **Zone 1 (Core)**, which concentrates one-third of all relevant literature in a select group of titles.
  - **Budget optimization:** Guides university consortia and libraries in prioritizing essential indexed subscriptions while avoiding expenditure on low-density peripheral journals (Zone 3).
  - **Publication strategy:** Advises research groups on the most canonical journals for manuscript submission.

### 2.3 Price's Index and Citing Half-Life (1965)
* **Applies to:** The publication dates of the cited references in the corpus articles.
* **Formula:** $I_{\text{Price}} = \frac{R_{\le 5}}{R_{\text{total}}} \times 100\%$, plus the chronological median of citation age.
* **Practical utility and decision-making:**
  - **Epistemological classification:** Discriminates between **Hard Sciences** ($I_{\text{Price}} \ge 50\%$, rapid obsolescence, fast-moving research fronts such as AI or Biomedicine) and **Social Sciences / Humanities (Soft Sciences)** ($I_{\text{Price}} \le 30\%$, long-term historical accumulation of knowledge).
  - **Pace of theoretical turnover:** Evaluates whether a discipline draws on recent frontier literature or rests on classical foundations.

### 2.4 Growth Phases of Science (Price, Exponential vs. Logistic Models, 1963)
* **Applies to:** Non-cumulative annual publication series of a field or research line.
* **Formulas:** Exponential $N(t) = a e^{bt}$ vs. Logistic $N(t) = \frac{K}{1 + e^{-r(t - t_0)}}$.
* **Practical utility and decision-making:**
  - **Phase I (Emergence):** Slow, fluctuating start of a pioneering area.
  - **Phase II (Exponential Expansion):** Vigorous, unconstrained growth; computes the **doubling time** (e.g., "AI literature doubles every 2.1 years").
  - **Phase III (Logistic Maturity / Saturation):** Deceleration due to funding limits or paradigmatic stabilization; estimates the **carrying capacity ($K$)**, signaling saturation of a research line.

---

## 3. Dependencies and Value Chain

```
┌─────────────────────────────────┐
│     Upstream Skills             │
│ • openalex-mexico-works-search  │──┐
│ • openalex-harvester / scopus   │  │  Structured tabular corpus
│ • tlachia-metrics-handler (ZIP) │  │  (.parquet, .csv, .json)
└─────────────────────────────────┘  │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │      classical-bibliometrics-laws   │
                  │  (Lotka, Bradford, Price, Growth)   │
                  └─────────────────────────────────────┘
                                     │
                                     ▼  JSON results and PNG charts
┌────────────────────────────────────┴────────────────────────────────────┐
│                       Downstream Skills                                 │
│ • som-methodological-expert (U-Matrix and productivity profiles)        │
│ • bibliometric-network-analyst (Journal coupling in Bradford's Core)    │
│ • Institutional scientometric and science policy reports                │
└─────────────────────────────────────────────────────────────────────────┘
```

* **Upstream Skills (Corpus Providers):**
  - [`openalex-mexico-works-search`](../openalex-mexico-clickhouse/openalex-mexico-works-search/SKILL.md): Extraction of Mexican publication corpora in Parquet/JSON format.
  - [`openalex-harvester`](../openalex-harvester/SKILL.md) / [`scopus-harvester`](../scopus-harvester/SKILL.md) / [`arxiv-harvester`](../arxiv-harvester/SKILL.md): Normalized scientific literature downloads.
  - [`tlachia-metrics-handler`](../tlachia-metrics-handler/SKILL.md): Extraction of canonical document metadata packages.
* **Downstream Skills (Analysis Consumers):**
  - [`som-methodological-expert`](../som-methodological-expert/SKILL.md): Incorporation of classical indicators into multidimensional profiles for SOM training.
  - [`bibliometric-network-analyst`](../bibliometric-network-analyst/SKILL.md): Bibliographic coupling and co-citation networks restricted to Bradford's Core.
* **Execution Environment:**
  - Python `>=3.10` with required packages: `numpy`, `scipy`, `matplotlib`, `pandas`.
  - CLI Script: [`scripts/bibliometric_laws_cli.py`](scripts/bibliometric_laws_cli.py).

---

## 4. CLI Execution Protocol (File-Output First)

All commands accept a structured input file (`--input <path>`) in `.parquet`, `.csv`, or `.json` format and strictly require a JSON output path (`--output <path>`), with options to generate high-resolution PNG charts (`--plot-output <path>`) and interactive HTML plots.

### 4.1 Lotka's Law (`lotka`)
Fits the author productivity distribution and computes the Kolmogorov-Smirnov test:
```bash
python scripts/bibliometric_laws_cli.py lotka \
  --input ./data/scientific_corpus.parquet \
  --counting full \
  --plot-es ./reports/lotka_distribution_es.png \
  --plot-en ./reports/lotka_distribution_en.png \
  --plotly-html ./reports/lotka_distribution.html \
  --output ./reports/lotka_result.json
```
* **Options for `--counting`:**
  - `full`: Full counting (1 credit per co-authorship; standard for sociology of science).
  - `fractional`: Fractional counting ($1/k$; recommended for hyper-authorship or large teams).

### 4.2 Bradford's Law (`bradford`)
Divides sources into 3 zones of equal output applying Egghe's continuous formulation:
```bash
python scripts/bibliometric_laws_cli.py bradford \
  --input ./data/scientific_corpus.parquet \
  --output ./data/bradford_zones.json
```

### 4.3 Price's Index and Obsolescence (`price-index`)
Computes the proportion of references $\le 5$ years old and the citing half-life:
```bash
python scripts/bibliometric_laws_cli.py price-index \
  --input ./data/scientific_corpus.parquet \
  --output ./data/price_index.json
```

### 4.4 Growth Phases of Science (`growth-phase`)
Compares Exponential vs. Logistic curve fits to diagnose the maturity phase of the field:
```bash
python scripts/bibliometric_laws_cli.py growth-phase \
  --input ./data/scientific_corpus.parquet \
  --plot-es ./reports/growth_kinetics_es.png \
  --plot-en ./reports/growth_kinetics_en.png \
  --plotly-html ./reports/growth_kinetics.html \
  --output ./reports/phase_diagnosis.json
```

---

## 5. Metrics Specification and Data Contracts (JSON)

### 5.1 Output of `lotka` (`lotka_result.json`)
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
  "plot_path": "./data/lotka_plot.png"
}
```

### 5.2 Output of `bradford` (`bradford_zones.json`)
```json
{
  "law": "Bradford's Law (Egghe Demarcation)",
  "total_sources": 850,
  "total_articles": 4200,
  "zones": {
    "zone_1_core": {
      "description": "Core Journals (Zone 1)",
      "sources_count": 18,
      "articles_count": 1400,
      "top_sources": ["Journal of Informetrics", "Scientometrics"]
    },
    "zone_2_moderate": {
      "description": "Moderate Concentration Zone",
      "sources_count": 95,
      "articles_count": 1400
    },
    "zone_3_peripheral": {
      "description": "Peripheral / High Dispersion Zone",
      "sources_count": 737,
      "articles_count": 1400
    }
  },
  "bradford_multiplier_k": 5.4,
  "theoretical_proportion": "1 : 5.4 : 29.2"
}
```

### 5.3 Output of `price-index` (`price_index.json`)
```json
{
  "law": "Price's Index of Obsolescence",
  "total_analyzed_references": 54200,
  "references_le_5_years": 29810,
  "price_index_percentage": 55.0,
  "citing_half_life_years": 4.5,
  "interpretation": "Hard Science (Fast obsolescence)"
}
```

### 5.4 Output of `growth-phase` (`phase_diagnosis.json`)
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
  "diagnosed_phase": "Phase II: Exponential Growth (Active Expansion)",
  "plot_path": "./data/growth_plot.png"
}
```

---

## 6. Common Mistakes and Anti-Patterns

- ❌ **Anti-pattern 1: Mixing heterogeneous disciplines when applying Bradford's Law**  
  Applying Bradford's analysis to a multidisciplinary or global institutional corpus (e.g., an entire university's output combining medicine, law, physics, and sociology) rather than a specific thematic field.  
  *Effect:* Destroys the geometric relationship ($1 : k : k^2$), artificially inflating the core size and distorting scattering estimates.  
  **Solution:** Segment the corpus by specific thematic domain (via `openalex-mexico-works-search --topic` or normalized categories).
- ❌ **Anti-pattern 2: Assuming Lotka's Law holds without a formal Kolmogorov-Smirnov test**  
  Fitting a linear regression on $\log(\text{authors})$ vs. $\log(\text{articles})$ and reporting only a high $R^2$, without checking the test statistic $D_{\max}$ against the critical value $1.36/\sqrt{N}$.  
  *Effect:* Erroneously accepting that a community obeys the law when the non-parametric statistical test rejects it at $\alpha=0.05$.  
  **Solution:** Always inspect `"goodness_of_fit_accepted"` and `"ks_statistic_d_max"` in the JSON output.
- ❌ **Anti-pattern 3: Ignoring the distinction between Full and Fractional Counting**  
  Using full counting by default in fields dominated by hyper-authorship (e.g., particle physics or genomic medicine with dozens or hundreds of authors per work).  
  *Effect:* Distorts the distribution, creating a false abundance of hyper-productive authors and altering the exponent $c$.  
  **Solution:** Use `--counting fractional` when the corpus exhibits an average co-author count $> 5$, distributing $1/k$ credits per author.
- ❌ **Anti-pattern 4: Temporal bias in Price's Index from undated or anachronistic references**  
  Assuming all cited references contain a valid year or including citations dated later than the citing article (anachronistic or *in press* citations with negative age).  
  *Effect:* Severe distortion of the Price Index percentage and citing half-life.  
  **Solution:** Discard unparseable references and filter references where $\text{year}_{\text{reference}} \le \text{year}_{\text{document}}$, as safely implemented by the CLI.
- ❌ **Anti-pattern 5: Fitting growth curves over fewer than 4 years or on cumulative series**  
  Running `growth-phase` on overly narrow time ranges (e.g., 2023–2024) or manually accumulating publications before passing them to the script.  
  *Effect:* The non-linear Levenberg-Marquardt optimization algorithm for the logistic curve diverges or fails (`Insufficient variation`).  
  **Solution:** Provide at least 4 to 5 years of non-cumulative annual output to evaluate sigmoid curvature and the inflection point.

---

## 7. Technical References

- [Mathematical Foundations of Classical Laws](references/classical_laws_mathematical_foundations.md)
- [Continuous Formulation of Bradford's Law (Egghe)](references/egghe_continuous_bradford.md)
- [Canonical Design Standard for Scientific Skills](../../docs/estandar_diseno_skills_cientificas.md)
- [Canonical CLI Script](scripts/bibliometric_laws_cli.py)
