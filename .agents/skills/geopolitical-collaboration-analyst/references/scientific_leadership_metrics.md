# Métricas de Liderazgo Científico, Normalización Bilateral y Asimetría Norte-Sur

Fundamentos metodológicos cuantitativos para evaluar la soberanía intelectual, dirección epistemológica y simetría en la colaboración transfronteriza (Moya-Anegón et al., 2013; Chinchilla-Rodríguez et al., 2019; Scimago Lab).

---

## 1. Normalización de Intensidad de Colaboración Bilateral

El mero recuento absoluto de coautorías ($C_{ij}$) introduce un **sesgo de tamaño masivo** hacia las grandes superpotencias científicas (EE. UU., China, Reino Unido), enmascarando relaciones estratégicas intensas entre países con menor producción agregada.

### A. Coseno de Salton Bilateral
Mide la afinidad relativa normalizando el número de colaboraciones conjuntas por la media geométrica de las producciones individuales de ambos países:

$$\text{Salton}_{ij} = \frac{C_{ij}}{\sqrt{T_i \times T_j}}$$

Donde:
* $C_{ij}$: Artículos con al menos una coautoría entre el país $i$ y el país $j$.
* $T_i, T_j$: Producción total de documentos del país $i$ y el país $j$ en el corpus/tema.
* **Rango:** $[0, 1]$. Valores cercanos a 1 indican una asociación bilateral casi perfecta.

### B. Índice de Jaccard Bilateral
Normaliza la intersección sobre la unión de la producción:

$$\text{Jaccard}_{ij} = \frac{C_{ij}}{T_i + T_j - C_{ij}}$$

---

## 2. Métricas de Soberanía y Liderazgo Epistemológico

En publicaciones en coautoría internacional ($K \ge 2$ países soberanos presentes en las afiliaciones), se evalúa la posición de liderazgo del país ancla:

### A. Tasa de Liderazgo de Primer Autor ($L_{\text{first}}$)
Cuantifica la proporción donde el investigador principal (primer autor) pertenece a una institución nacional del país ancla:

$$L_{\text{first}}(\text{ancla}) = \frac{N_{\text{primer\_autor\_nacional}}}{N_{\text{artículos\_internacionales\_ancla}}} \times 100\%$$

### B. Tasa de Liderazgo de Autor de Correspondencia ($L_{\text{corr}}$)
Cuantifica la proporción donde la autoría de correspondencia (responsable del diseño experimental, financiamiento, correspondencia con la revista y envío) recae en el país ancla:

$$L_{\text{corr}}(\text{ancla}) = \frac{N_{\text{autor\_correspondencia\_nacional}}}{N_{\text{artículos\_internacionales\_ancla}}} \times 100\%$$

---

## 3. Matriz de Clasificación de Soberanía Científica

| Rango de Liderazgo | Diagnóstico Cienciométrico | Interpretación de Política Científica |
|:---:|:---|:---|
| **$L \ge 50\%$** | **Liderazgo Preponderante (Soberanía Epistemológica)** | El país actúa como generador de hipótesis, director del proyecto y redactor principal. Ejerce atracción de talento internacional. |
| **$40\% \le L < 50\%$** | **Colaboración Simétrica (Equitativa)** | Balance equitativo entre contrapartes internacionales. Consorcios maduros sin relaciones de subordinación. |
| **$30\% \le L < 40\%$** | **Participación Secundaria (Dirección Compartida)** | Colaboraciones donde la iniciativa suele originarse en el exterior, pero el país mantiene co-dirección o autoría de correspondencia relevante. |
| **$L < 30\%$** | **Asimetría Epistemológica / Subordinación Norte-Sur** | Fenómeno conocido como *"Ciencia Helicóptero"* o extractiva: el país aporta trabajo de campo, muestras clínicas o datos primarios locales, pero la dirección y redacción principal recae en centros del Norte Global. |

---

## 4. Cuadrantes Estratégicos Bilaterales (Salton vs. Volumen)

Al contrastar el volumen de coautorías ($C_{ij}$) con el Coseno de Salton ($\text{Salton}_{ij}$) respecto a las medianas del corpus:

1. **Cuadrante I (Superior Derecho - Alta Afinidad / Alto Volumen):**
   * *Socios Estratégicos Nucleares.* Articulación bilateral sólida y recurrente.
2. **Cuadrante II (Superior Izquierdo - Alta Afinidad / Volumen Moderado):**
   * *Aliados Estratégicos de Especialización.* Alta cercanía cienciométrica relativa que debe ser protegida con fondos bilaterales dedicados.
3. **Cuadrante III (Inferior Derecho - Baja Afinidad / Alto Volumen):**
   * *Socios por Inercia Global.* Volúmenes elevados debidos al gran tamaño global del socio (ej. superpotencias científicas), pero con baja especialización bilateral.
4. **Cuadrante IV (Inferior Izquierdo - Baja Afinidad / Bajo Volumen):**
   * *Colaboraciones Periféricas o Emergentes.* Lazos esporádicos o individuales.
