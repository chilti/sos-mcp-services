# Scientific Leadership Metrics, Bilateral Normalization, and North-South Asymmetry

Quantitative methodological foundations for evaluating intellectual sovereignty, epistemological direction, and symmetry in cross-border collaboration (Moya-Anegón et al., 2013; Chinchilla-Rodríguez et al., 2019; Scimago Lab).

---

## 1. Bilateral Collaboration Intensity Normalization

Raw co-authorship counts ($C_{ij}$) introduce a **massive size bias** toward large scientific superpowers (USA, China, UK), masking intense strategic relationships between countries with smaller aggregate output.

### A. Bilateral Salton's Cosine
Measures relative affinity by normalizing the number of joint collaborations by the geometric mean of the individual outputs of both countries:

$$\text{Salton}_{ij} = \frac{C_{ij}}{\sqrt{T_i \times T_j}}$$

Where:
* $C_{ij}$: Papers with at least one co-authorship between country $i$ and country $j$.
* $T_i, T_j$: Total document output of country $i$ and country $j$ in the corpus/topic.
* **Range:** $[0, 1]$. Values close to 1 indicate near-perfect bilateral association.

### B. Bilateral Jaccard Index
Normalizes the intersection over the union of output:

$$\text{Jaccard}_{ij} = \frac{C_{ij}}{T_i + T_j - C_{ij}}$$

---

## 2. Epistemological Sovereignty and Leadership Metrics

In internationally co-authored publications ($K \ge 2$ sovereign countries present in the affiliations), the leadership position of the anchor country is evaluated:

### A. First-Author Leadership Rate ($L_{\text{first}}$)
Quantifies the proportion where the principal investigator (first author) belongs to a domestic institution of the anchor country:

$$L_{\text{first}}(\text{anchor}) = \frac{N_{\text{domestic\_first\_author}}}{N_{\text{anchor\_international\_papers}}} \times 100\%$$

### B. Corresponding-Author Leadership Rate ($L_{\text{corr}}$)
Quantifies the proportion where corresponding authorship (responsible for experimental design, funding, journal correspondence, and submission) resides in the anchor country:

$$L_{\text{corr}}(\text{anchor}) = \frac{N_{\text{domestic\_corresponding\_author}}}{N_{\text{anchor\_international\_papers}}} \times 100\%$$

---

## 3. Scientific Sovereignty Classification Matrix

| Leadership Range | Scientometric Diagnosis | Science Policy Interpretation |
|:---:|:---|:---|
| **$L \ge 50\%$** | **Preponderant Leadership (Epistemological Sovereignty)** | The country acts as hypothesis generator, project director, and primary author, attracting international talent. |
| **$40\% \le L < 50\%$** | **Symmetrical Collaboration (Equitable)** | Equitable balance among international counterparts; mature consortia without subordination relationships. |
| **$30\% \le L < 40\%$** | **Secondary Participation (Shared Direction)** | Collaborations where initiative often originates abroad, but the country retains relevant co-direction or corresponding authorship. |
| **$L < 30\%$** | **Epistemological Asymmetry / North-South Subordination** | Phenomenon known as *"Helicopter Science"* or extractive science: the country provides fieldwork, clinical samples, or local primary data, while intellectual direction and primary writing reside in Global North centers. |

---

## 4. Strategic Bilateral Quadrants (Salton vs. Volume)

By contrasting co-authorship volume ($C_{ij}$) with Salton's Cosine ($\text{Salton}_{ij}$) relative to corpus medians:

1. **Quadrant I (Upper Right - High Affinity / High Volume):**
   * *Core Strategic Partners.* Solid and recurrent bilateral articulation.
2. **Quadrant II (Upper Left - High Affinity / Moderate Volume):**
   * *Specialized Strategic Allies.* High relative scientometric proximity that should be supported with dedicated bilateral funding.
3. **Quadrant III (Lower Right - Low Affinity / High Volume):**
   * *Global Inertia Partners.* High volumes driven by the partner's massive global size (e.g., scientific superpowers), but with low bilateral specialization.
4. **Quadrant IV (Lower Left - Low Affinity / Low Volume):**
   * *Peripheral or Emerging Collaborations.* Sporadic or individual ties.
