# Guía de Aplicación de la Lista de Verificación PRESS 2015

Basado en: McGowan, J., Sampson, M., Salzwedel, D. M., Cogo, E., Foerster, V., & Lefebvre, C. (2016). *PRESS Peer Review of Electronic Search Strategies: 2015 Guideline Explanation and Elaboration (E&E)*. Journal of Clinical Epidemiology, 75, 40-46.

---

## Introducción

El instrumento **PRESS 2015** es el estándar metodológico internacional para evaluar y auditar estrategias de búsqueda electrónica estructuradas en revisiones sistemáticas, metaanálisis y estudios bibliométricos exhaustivos. Su aplicación previene errores de diseño que comprometen la validez de la investigación.

---

## Los 6 Dominios de Auditoría PRESS

### 1. Traducción de la Pregunta de Investigación (Translation of the Research Question)
- **Objetivo:** Asegurar que cada concepto esencial de la pregunta de investigación (p. ej., PICO o PCC) esté fielmente representado en la estrategia.
- **Puntos críticos:**
  - ¿Se han omitido conceptos clave que causan sobre-recuperación masiva?
  - ¿Se han agregado demasiados conceptos que estrangulan el recall (silencio bibliográfico)?
  - ¿Las facetas son ortogonales e independientes?

### 2. Operadores Booleanos y de Proximidad (Boolean and Proximity Operators)
- **Objetivo:** Verificar la lógica de conjuntos y precedencia de evaluación.
- **Puntos críticos:**
  - **Paréntesis anidados:** `A AND (B OR C)` es completamente diferente de `A AND B OR C`. Sin paréntesis, la precedencia estándar (`AND` tiene mayor prioridad que `OR` en la mayoría de los motores) agrupa como `(A AND B) OR C`, recuperando todo el universo de `C` sin filtrar por `A`.
  - **Uso de `NOT`:** El operador `NOT` debe evitarse en la medida de lo posible. Si un artículo discute *"Why pediatric models differ from adult paradigms"*, una búsqueda con `NOT adult*` descartará dicho estudio pediátrico.
  - **Proximidad vs AND:** En resúmenes largos, `termA AND termB` puede coincidir porque `termA` está en los antecedentes y `termB` en las conclusiones, sin existir relación conceptual. Usar `NEAR/n` (WoS) o `W/n` (Scopus) asegura co-ocurrencia contextual.

### 3. Vocabulario Controlado (Subject Headings)
- **Objetivo:** Explotar la tesaurización formal de las bases indexadas.
- **Puntos críticos:**
  - ¿Se identificaron los descriptores MeSH (PubMed), Emtree (Embase), Subject Categories (WoS) o Topics (OpenAlex)?
  - ¿Se evaluó si el término debe expandirse jerárquicamente (*Explode*) o restringirse a foco mayor (*Major Concept / [majr]*)?
  - ¿Los términos del tesauro son actuales o están obsoletos?

### 4. Búsqueda en Texto Libre (Text Word Searching)
- **Objetivo:** Capturar la terminología contemporánea, variantes naturales y literatura no indizada aún en tesauros.
- **Puntos críticos:**
  - **Sinonimia exhaustiva:** Términos coloquiales vs formales, marcas comerciales vs nombres genéricos.
  - **Variaciones ortográficas:** Británica vs Americana (`tumour` vs `tumor`, `anaesthesia` vs `anesthesia`, `centre` vs `center`).
  - **Acrónimos:** Evaluar colisión semántica (p. ej., `NLP` puede significar *Natural Language Processing* o *Neuro-Linguistic Programming*).

### 5. Ortografía, Truncamiento y Comodines (Spelling, Truncation, and Wildcards)
- **Objetivo:** Prevenir errores tipográficos y desbordamiento léxico.
- **Puntos críticos:**
  - **Comodines peligrosos:** Truncamientos de menos de 4 letras (p. ej., `pol*` recupera *policy, polish, politics, polymer, police, pollen*).
  - **Comillas desbalanceadas:** Ocasionan fallos silenciosos en APIs o interpretaciones erróneas.
  - **Plurales irregulares:** Comprobar que `child*` cubra *children*, pero atender casos como `matrix`/`matrices` o `criterion`/`criteria`.

### 6. Filtros y Límites (Limits and Filters)
- **Objetivo:** Garantizar que las restricciones aplicadas sean deliberadas y metodológicamente defendibles.
- **Puntos críticos:**
  - ¿El filtro temporal está justificado por un hito histórico o regulatorio (p. ej., año de descubrimiento o publicación de una ley)?
  - ¿Los filtros de idioma sesgan la evidencia hacia el hemisferio anglosajón, omitiendo aportes clave de Iberoamérica o Asia?
  - ¿El filtro de tipo de documento (`doctype`) descarta revisiones o *conference papers* que contienen síntesis fundamentales?
