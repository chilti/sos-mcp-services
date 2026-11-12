# Mathematical Foundations of Classical Bibliometric Laws

This reference formalizes the informetric models of Lotka, Price, and the phases of scientific growth.

---

## 1. Lotka's Law (Author Productivity, 1926)

Describes the frequency distribution of the number of authors with $x$ publications:

$$y_x = \frac{C}{x^c}, \quad x = 1, 2, 3, \dots$$

* $c \approx 2.0$: Canonical exponent of the inverse square law.
* $C = \left( \sum_{x=1}^\infty \frac{1}{x^c} \right)^{-1} = \frac{1}{\zeta(c)}$: Theoretical fraction of authors with a single article.
* **Goodness of Fit:** The non-parametric **Kolmogorov-Smirnov** test is applied:
  $$D = \max |F_{\text{empirical}}(x) - F_{\text{theoretical}}(x)|$$
  If $D \le \frac{1.36}{\sqrt{N}}$ (at $\alpha=0.05$), the null hypothesis that the discipline obeys Lotka's Law is accepted.

---

## 2. Price's Index (Literature Obsolescence, 1965)

Measures the proportion of scientific references published within the last 5 years:

$$I_{\text{Price}} = \frac{R_{\le 5}}{R_{\text{total}}} \times 100\%$$

* $I_{\text{Price}} \ge 50\%$: **Hard Sciences** (e.g., Biochemistry, AI), characterized by rapid obsolescence and fast-moving research fronts.
* $I_{\text{Price}} \le 30\%$: **Social Sciences and Humanities (Soft Sciences)**, with extended citation longevity.
* **Citing Half-Life:** Median age of the cited references.

---

## 3. Growth Phases of Science (Price, 1963)

1. **Phase I (Emergence):** Slow start, isolated precursors, high variance.
2. **Phase II (Exponential Growth):** Periodic doubling of the literature ($N(t) = N_0 e^{bt}$, doubling time $t_d = \frac{\ln 2}{b}$).
3. **Phase III (Logistic Maturity / Saturation):** Deceleration due to resource exhaustion or paradigmatic stabilization ($N(t) = \frac{K}{1 + e^{-r(t - t_0)}}$, where $K$ is the carrying capacity).
