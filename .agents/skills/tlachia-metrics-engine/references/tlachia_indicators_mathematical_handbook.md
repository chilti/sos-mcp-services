# Manual Matemático de Indicadores Cienciométricos TlachIA

Este manual documenta las fórmulas matemáticas y definiciones operativas de los indicadores implementados en `tlachia_metrics_cli.py`.

---

## 1. Volumen y Citación

### Índice H (Hirsch, 2005)
$$h = \max \{ i \in \mathbb{N} : c_{(i)} \ge i \}$$
donde $c_{(i)}$ es el vector de citas ordenado descendentemente.

### Índice i10
Cantidad de documentos con al menos 10 citas acumuladas:
$$i10 = \sum_{k=1}^N \mathbb{I}(c_k \ge 10)$$

---

## 2. Impacto Normalizado y Excelencia

### FWCI (Field-Weighted Citation Impact)
Razón entre las citas reales recibidas por el artículo y el promedio esperado de citas para publicaciones del mismo año, tipo documental y disciplina:
$$\text{FWCI} = \frac{c_{\text{obs}}}{e_{\text{esp}}}$$
Un valor de $1.0$ representa el promedio mundial; valores $> 1.0$ denotan impacto por encima del estándar global.

### Percentiles y Excelencia (Top 10% y Top 1%)
- **Top 10%:** Documentos cuyo percentil normalizado $\ge 90.0$.
- **Top 1% Élite:** Documentos cuyo percentil normalizado $\ge 99.0$.

---

## 3. Ciencia Abierta (Las 6 Vías)

- **Gold:** Revista de acceso abierto con cobro de APC comercial.
- **Diamond (Diamante):** Revista de acceso abierto sin cobro a autores ni lectores (financiada por universidades u organismos públicos).
- **Hybrid:** Revista por suscripción donde el autor pagó un APC para liberar su artículo individual.
- **Green (Verde):** Auto-archivo del pre-print o post-print en un repositorio institucional o temático (e.g. arXiv).
- **Bronze:** Acceso libre temporal en la web del editor sin licencia abierta formal (Creative Commons).
- **Closed:** Cerrado tras muro de pago (*paywall*).

---

## 4. Economía de la Publicación

- **Gasto Estimado en APC (USD):** Suma directa de cargos de procesamiento pagados a editoriales comerciales.
- **Ahorro por Publicación Diamante:** Se cuantifica asumiendo un costo medio de mercado de \$1,800 USD por cada artículo publicado en revistas Diamante:
$$\text{Ahorro Diamante} = N_{\text{diamante}} \times \$1,800 \text{ USD}$$

---

## 5. Coeficiente de Gini Temático
$$G = \frac{\sum_{i=1}^n \sum_{j=1}^n |x_i - x_j|}{2 n \sum_{i=1}^n x_i}$$
Mide la concentración o diversificación de los tópicos de investigación en el corpus ($G \to 0$: diversificación homogénea; $G \to 1$: hiperespecialización monotemática).
