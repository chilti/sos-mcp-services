# Mathematical Handbook of TlachIA Scientometric Indicators

This handbook documents the mathematical formulas and operational definitions of the indicators implemented in `tlachia_metrics_cli.py`.

---

## 1. Volume and Citation

### H-Index (Hirsch, 2005)
$$h = \max \{ i \in \mathbb{N} : c_{(i)} \ge i \}$$
where $c_{(i)}$ is the vector of citations sorted in descending order.

### i10-Index
Number of documents with at least 10 cumulative citations:
$$i10 = \sum_{k=1}^N \mathbb{I}(c_k \ge 10)$$

---

## 2. Normalized Impact and Excellence

### FWCI (Field-Weighted Citation Impact)
Ratio between the actual citations received by an article and the expected average citations for publications of the same year, document type, and discipline:
$$\text{FWCI} = \frac{c_{\text{obs}}}{e_{\text{exp}}}$$
A value of $1.0$ represents the world average; values $> 1.0$ denote impact above the global benchmark.

### Percentiles and Excellence (Top 10% and Top 1%)
- **Top 10%:** Documents whose normalized percentile $\ge 90.0$.
- **Top 1% Elite:** Documents whose normalized percentile $\ge 99.0$.

---

## 3. Open Science (The 6 Pathways)

- **Gold:** Open access journal charging a commercial APC.
- **Diamond:** Open access journal charging neither authors nor readers (funded by universities or public organizations).
- **Hybrid:** Subscription journal where the author paid an APC to make an individual article open access.
- **Green:** Self-archiving of a preprint or postprint in an institutional or thematic repository (e.g., arXiv).
- **Bronze:** Free-to-read access on the publisher's website without a formal open license (Creative Commons).
- **Closed:** Restricted behind a paywall.

---

## 4. Publication Economics

- **Estimated APC Expenditure (USD):** Direct sum of article processing charges paid to commercial publishers.
- **Diamond Publishing Savings:** Quantified assuming an average market cost of \$1,800 USD per article published in Diamond journals:
$$\text{Diamond Savings} = N_{\text{diamond}} \times \$1,800 \text{ USD}$$

---

## 5. Thematic Gini Coefficient
$$G = \frac{\sum_{i=1}^n \sum_{j=1}^n |x_i - x_j|}{2 n \sum_{i=1}^n x_i}$$
Measures the concentration or diversification of research topics in the corpus ($G \to 0$: homogeneous diversification; $G \to 1$: monothematic hyper-specialization).
