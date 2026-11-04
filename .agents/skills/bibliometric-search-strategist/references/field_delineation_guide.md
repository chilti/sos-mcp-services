# Guía Metodológica de Delimitación de Campos (Field Delineation) en Cienciometría

Basado en:
* Huang, C., Schiebel, E., & Porter, A. L. (2011). *A multi-stage approach to mapping emerging technologies: the case of DNA sequencing technology*. Scientometrics, 87(2), 241-260.
* Glänzel, W., Schlemmer, B., & Du Plessis, B. (2009). *A hybrid approach for addressing the problem of "field delineation" in scientometric studies*. Scientometrics, 79(1), 3-17.
* Zitt, M., & Bassecoulard, E. (2006). *Challenges for scientometric indicators: the data delimitation issue*. Scientometrics, 67(1), 145-160.

---

## 1. El Problema de la Delimitación de Campos Científicos

En cienciometría, delimitar el corpus de un campo de investigación (*Field Delineation*) es el paso más crítico de cualquier estudio bibliométrico. Una delimitación defectuosa produce:
* **Falso Silencio (Bajo *Recall*):** Omitir trabajos clave que utilizan vocabulario alternativo o metafórico, distorsionando las redes y subestimando el impacto.
* **Ruido Masivo (Baja *Precision*):** Incluir literatura irrelevante debido a términos polisémicos, falseando las métricas de colaboración y los clusters temáticos.

---

## 2. Los Tres Enfoques Canónicos de Delimitación

```mermaid
flowchart TD
    subgraph Enfoque1 ["1. Enfoque Léxico Modular (Huang & Porter, 2011)"]
        L1["Términos Núcleo (Core Search)"] --> L2["Expansión por Términos Afines"]
        L2 --> L3["Filtrado de Ruido por Co-ocurrencia"]
    end

    subgraph Enfoque2 ["2. Enfoque Topológico de Citaciones (Klavans & Boyack)"]
        C1["Artículos Semilla Canónicos"] --> C2["Acoplamiento Bibliográfico / Co-citación"]
        C2 --> C3["Partición por Grafos Globales (Leiden)"]
    end

    subgraph Enfoque3 ["3. Enfoque Híbrido Causal-Léxico (Glänzel et al., 2009)"]
        H1["Semilla / Núcleo Léxico Booleano"] --> H2["Expansión por Red de Citaciones (1er orden)"]
        H2 --> H3["Filtro de Densidad Núcleo (Cita a >= k semillas)"]
    end
```

---

## 3. Protocolo Multi-Etapa de Huang, Schiebel & Porter (2011)

Diseñado especialmente para dominios emergentes o interdisciplinarios, este protocolo consta de 4 etapas estructuradas:

### Etapa 1: Definición del Núcleo de Alta Precisión (Core Search)
- Selección de términos estrictos, inequívocos e indiscutibles que definen la tecnología o teoría (p. ej., nombres propios de algoritmos, ecuaciones formalizadas o construcciones léxicas exclusivas).
- Objetivo: Garantizar una precisión cercana al 100%, aunque el *recall* inicial sea moderado.

### Etapa 2: Expansión Sistemática (Modular Expansion)
- A partir del corpus núcleo, se analizan las palabras clave de autor y los esquemas de clasificación (Topics de OpenAlex, MeSH Headings, Categorías WoS).
- Se incorporan variantes tecnológicas, herramientas computacionales asociadas y terminología de subcampos conectados mediante bloques conceptuales (`OR`).

### Etapa 3: Filtrado y Exclusión de Ruido (Noise Removal)
- Se auditan las palabras polisémicas que provocan contaminación temática.
- **Regla cienciométrica:** No usar el operador `NOT` de forma aislada sin evaluar si elimina literatura seminal. En su lugar, se utilizan:
  1. Restricciones de categorías temáticas ajenas (`NOT WC="Surgery"` si el estudio es puramente informático).
  2. Umbrales de co-ocurrencia: el término ambiguo solo se admite si co-ocurre con al menos un término del núcleo conceptual.

### Etapa 4: Validación y Calibración
- Verificación del porcentaje de recuperación de las obras seminales (*golden standard*).
- Inspección manual del decil superior de publicaciones más citadas para confirmar que pertenecen al dominio.

---

## 4. El Enfoque Híbrido Causal-Léxico de Glänzel et al. (2009)

Para resolver el problema del desbordamiento en el rastreo de citas (*citation snowballing*):

$$\text{Criterio de Inclusión Híbrido}: \quad d \in \text{Corpus} \iff d \in \text{Core}_{\text{léxico}} \quad \lor \quad |\text{Citations}(d, \text{Core}_{\text{léxico}})| \ge k$$

Donde $k$ es el **umbral de densidad de citación núcleo** (típicamente $k=2$ o $k=3$):
* Si un documento externo fue descubierto por citar o ser citado por una semilla, **solo se retiene si se conecta simultáneamente con al menos $k$ documentos del núcleo inicial**.
* Esto actúa como una barrera topológica que impide que la búsqueda se fugue hacia disciplinas tangenciales.
