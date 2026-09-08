# Fundamentos Matemáticos de las Leyes Bibliométricas Clásicas

Esta referencia formaliza los modelos informétricos de Lotka, Price y las fases de crecimiento científico.

---

## 1. Ley de Lotka (Productividad de Autores, 1926)

Describe la distribución de frecuencia del número de autores con $x$ publicaciones:

$$y_x = \frac{C}{x^c}, \quad x = 1, 2, 3, \dots$$

* $c \approx 2.0$: Exponente canónico de la ley del cuadrado inverso.
* $C = \left( \sum_{x=1}^\infty \frac{1}{x^c} \right)^{-1} = \frac{1}{\zeta(c)}$: Fracción teórica de autores con un solo artículo.
* **Bondad de Ajuste:** Se aplica la prueba no paramétrica de **Kolmogorov-Smirnov**:
  $$D = \max |F_{\text{empírica}}(x) - F_{\text{teórica}}(x)|$$
  Si $D \le \frac{1.36}{\sqrt{N}}$ (a $\alpha=0.05$), se acepta la hipótesis nula de que la disciplina obedece la Ley de Lotka.

---

## 2. Índice de Price (Obsolescencia de la Literatura, 1965)

Mide la proporción de referencias científicas publicadas en los últimos 5 años:

$$I_{\text{Price}} = \frac{R_{\le 5}}{R_{\text{total}}} \times 100\%$$

* $I_{\text{Price}} \ge 50\%$: Ciencias duras (*Hard Sciences*, e.g., Bioquímica, IA), caracterizadas por rápida obsolescencia y frentes efímeros.
* $I_{\text{Price}} \le 30\%$: Ciencias sociales y humanidades (*Soft Sciences*), con extensa longevidad citacional.
* **Citing Half-Life:** Mediana de la edad de las referencias citadas.

---

## 3. Fases de Crecimiento de la Ciencia (Price, 1963)

1. **Fase I (Emergencia):** Inicio lento, precursores aislados, varianza alta.
2. **Fase II (Crecimiento Exponencial):** Duplicación periódica de la literatura ($N(t) = N_0 e^{bt}$, tiempo de duplicación $t_d = \frac{\ln 2}{b}$).
3. **Fase III (Madurez / Saturación Logística):** Desaceleración por agotamiento de recursos o estabilización paradigmática ($N(t) = \frac{K}{1 + e^{-r(t - t_0)}}$, donde $K$ es la capacidad de carga).
