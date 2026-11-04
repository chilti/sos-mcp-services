# Guía de Reporte PRIBA (Preferred Reporting Items for Bibliometric Analysis)

Basado en: Koo, M., & Lin, S. C. (2022). *Preferred reporting items for bibliometric analysis (PRIBA): A proposal for reporting bibliometric reviews*. Journal of Medical Sciences, 42(3), 115-123.

---

## 1. Contexto Metodológico

**PRIBA** fue propuesto por la comunidad cienciométrica como una adaptación directa y formal de **PRISMA 2020** orientada a revisiones bibliométricas y mapeo de la ciencia. 

A diferencia del PRISMA médico tradicional (diseñado para evaluar sesgos de intervención clínica y metaanálisis estadístico), PRIBA reformula los ítems para auditar la validez estructural de los estudios basados en datos bibliográficos:

---

## 2. Los Componentes Esenciales de PRIBA

### A. Definición de la Pregunta y Unidad de Análisis
* Especificación clara de la unidad de análisis (autores, documentos, revistas, países, instituciones o palabras clave/conceptos).
* Declaración del tipo de análisis relacional:
  * **Co-ocurrencia:** Mapeo de términos y frentes conceptuales.
  * **Coautoría:** Redes sociales y colaboración institucional/geográfica.
  * **Co-citación:** Estructura intelectual fundacional y colegios invisibles.
  * **Acoplamiento Bibliográfico:** Frentes de investigación contemporáneos activos.
  * **Citación Directa:** Linajes genealógicos de ideas.

### B. Delimitación y Recolección de Datos
* Consulta exacta con etiquetas de campo y operadores de proximidad.
* Registro de fecha de acceso y versión de la base (OpenAlex, WoS, Scopus).
* Mapeo del flujo cuantitativo: registros brutos recuperados $\to$ duplicados eliminados $\to$ registros incluidos con metadatos completos.

### C. Normalización y Métricas de Similitud
* Declaración del método de normalización relacional:
  * **Association Strength** (Van Eck & Waltman, recomendada para clustering espacial).
  * **Coseno de Salton** (adecuado para afinidad bilateral internacional).
  * **Índice de Jaccard** o **Índice de Equivalencia**.
* Declaración del método de conteo: **conteo completo (*full counting*)** vs. **conteo fraccional (*fractional counting*)**.

### D. Visualización, Algoritmos y Robustez
* Algoritmo de partición comunitaria (Leiden, Louvain, Infomap) y parámetros de resolución ($\gamma$).
* Software empleado y versiones (VOSviewer, Bibliometrix, KnoMap, Python).
* Identificación y discusión de sesgos de cobertura lingüística o indexación de las bases.
