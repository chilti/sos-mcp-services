---
name: template-policy-brief-gobernanza
description: >-
  Elaboración de resúmenes ejecutivos de política científica y tecnológica (Policy Briefs de 2 a 4 páginas) para rectorías, ministerios de ciencia (SECIHTI), comisiones legislativas y agencias de financiamiento. Guía al agente en el protocolo canónico de 5 fases: 1) Síntesis ejecutiva para decisores e Indicadores diagnósticos clave (Tabla 1), 2) Evidencia Multidimensional SOM contra el reduccionismo de los rankings (la falacia del pesar y sumar, con Tabla 2 de Clusters Institucionales), 3) Dilemas y trade-offs de gobernanza (APC vs Diamante, Hiperautoría vs Autonomía), 4) Evaluación prospectiva de escenarios, y 5) Matriz de recomendaciones prioritarias accionables (Tabla 3).
---

# Plantilla Maestra: Policy Brief de Gobernanza, Políticas de Ciencia y Tecnología (C&T) y Evidencia Multidimensional SOM
### *Especializada en síntesis ejecutiva para tomadores de decisiones de alta dirección (2 a 4 páginas)*

Esta plantilla está diseñada para que un **agente único** en LibreChat / `agentic-data-stack` o entornos de automatización elabore un **POLICY BRIEF** conciso, de máximo impacto institucional y rigurosamente fundamentado en evidencia cuantitativa, dirigido a titulares de rectorías, la Secretaría de Ciencia, Humanidades, Tecnología e Innovación (SECIHTI), consejos de investigación y comisiones legislativas.

Aporta como argumento científico central el **marco neurocomputacional de Mapas Autoorganizados de Kohonen (SOM)** (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025; Villaseñor-García et al., 2017) para evidenciar el error de diseñar políticas públicas y asignaciones presupuestales basadas en rankings unidimensionales (*pesar y sumar*), demostrando que el sistema científico se organiza en clusters con perfiles y misiones cualitativas diferenciadas.

---

## Directivas Operativas para el Agente (Protocolo MCP Real)

Antes de redactar el policy brief, debes cosechar los datos cuantitativos mediante las herramientas MCP disponibles:

1. **Diagnóstico Cuantitativo del Sector o Institución:**
   - Extraer agregaciones de producción, FWCI autónomo ($\le 20$ autores) y gasto comercial en APC mediante `sos_openalex` (`openalex_aggregate_mexico`) o consultas directas a `ClickHouse-OpenAlex` (CERO JOINs).
2. **Censo Oficial del Claustro en el Padrón SNII:**
   - Invocar `sos_sinapsisai` (`query_snii_census_overview`) para cuantificar la distribución del claustro por niveles (Candidato a Emérito) y detectar riesgos de envejecimiento o falta de relevo generacional.
3. **Evidencia de Perfiles Diferenciados con Redes SOM (`sos_knomap`):**
   - Evidenciar la partición de las instituciones en clusters funcionales mediante `sos_knomap` (`train_som`, `evaluate_som_clusters`), demostrando que comparar entidades de distinta vocación bajo un mismo escalar perjudica la diversidad y las necesidades locales.
4. **Focalización Estricta en Trade-Offs de Política Pública:**
   - Destacar los dilemas centrales: fuga en cuotas APC comerciales en USD vs. inversión en revistas Diamante públicas; hiperautoría pasiva vs. liderazgo intelectual de correspondencia; concentración centralizada vs. descentralización territorial.
5. **Brevedad, Claridad y Contundencia:**
   - Longitud objetivo: 2 a 4 páginas. Estructura modular ejecutiva con viñetas analíticas y tablas de acción inmediata.

---

## Reglas Editoriales Estrictas

- **LENGUAJE MODERADO Y SOBRIO (PROHIBICIÓN ABSOLUTA DE SUPERLATIVOS):** Estilo directo, propositivo, neutro y libre de retórica mercadotécnica o superlativos (*"revolucionario"*, *"sin precedentes"*, *"extraordinario"*).
- **ZERO-SCAFFOLDING LEAKAGE:** Redacción formal institucional apta para presentación ante órganos de gobierno universitario o comisiones de estado.
- **TABLAS EN EL CHAT:** Las Tablas 1, 2 y 3 deben desplegarse íntegramente en Markdown.

---

# [Título del Policy Brief: Desafíos Estratégicos, Evidencia Multidimensional y Opciones de Política Científica para [Tema / Institución]: Recomendaciones de Gobernanza Basadas en Evidencia]

> ## SÍNTESIS EJECUTIVA PARA DECISORES
> - **El Problema Crítico:** Resumen ejecutivo de 1 párrafo sobre la tensión estructural o brecha detectada en el sistema o institución.
> - **La Evidencia Central:** 3 datos cuantitativos irrefutables derivados del análisis cienciométrico y neurocomputacional SOM.
> - **La Recomendación Principal:** Curso de acción inmediato con mayor retorno social, epistémico y presupuestal.

---

## 1. CONTEXTO Y MAGNITUD CUANTITATIVA DEL PROBLEMA

- **1.1. Antecedentes del Fenómeno:**
  * Descripción sucinta del entorno institucional o nacional en que se enmarca la problemática.
- **1.2. Tabla 1: Indicadores Diagnósticos Clave:**

| Variable Estratégica | Cifra Actual | Parámetro de Comparación | Brecha Detectada | Diagnóstico Operativo |
| :--- | :--- | :--- | :--- | :--- |
| **Producción e Impacto Normalizado** | [X.XX] FWCI Régimen B | 1.00 (Media mundial) | [Déficit / Superávit] | Desempeño autónomo de la comunidad local |
| **Autonomía Científica (% Primer Autor / Corresp.)** | [XX.X]% / [XX.X]% | [XX.X]% (Media nacional) | [Asimetría detectada] | Capacidad de formulación y conducción |
| **Costo Comercial en APC (USD)** | $[XXX,XXX] USD | Presupuesto institucional | [Fuga financiera estimada] | Drenaje hacia conglomerados editoriales |
| **Masa Crítica en Padrón SNII** | [XX.X]% senior (N2, N3, Em.) | [XX.X]% jóvenes (Cand., N1) | [Riesgo de relevo generacional] | Sostenibilidad de las líneas a mediano plazo |

---

## 2. EVIDENCIA MULTIDIMENSIONAL SOM CONTRA EL REDUCCIONISMO DE LOS RANKINGS

*La falacia del "pesar y sumar": por qué un solo indicador escalar distorsiona las políticas públicas (Carrillo-Calvet, Jiménez-Andrade & Arencibia-Jorge, 2025).*

- **2.1. El Error Metodológico de los Rankings Comerciales:**
  * Los rankings internacionales (ARWU, QS, THE) combinan indicadores heterogéneos mediante ponderaciones lineales arbitrarias, forzando a todas las instituciones a competir bajo un único modelo anglosajón intensivo en recursos.
  * Este reduccionismo castiga la investigación orientada a problemas nacionales, las publicaciones en lenguas locales y el acceso abierto comunitario.
- **2.2. Demostración Neurocomputacional con Redes SOM:**
  * El modelado en espacios de estados con redes de Kohonen demuestra que las instituciones se agrupan en clusters cualitativamente distintos: no son "mejores o peores" en una escala unidimensional, sino que cumplen funciones y misiones académicas diferenciadas.
- **2.3. Tabla 2: Tipología de Clusters Institucionales Revelados por el SOM:**

| Cluster SOM ($K^*$) | Perfil Funcional Dominante | Misión Académica Legítima | Indicadores Cardinales en el SOM | Política Pública Diferenciada Recomendada |
| :--- | :--- | :--- | :--- | :--- |
| **Cluster Élite Global** | Investigación intensiva en frontera tecnológica | Liderazgo científico internacional y atracción de fondos | Alto FWCI, Top 1%, Colaboración internacional | Financiamiento de laboratorios centrales de vanguardia |
| **Cluster Soberanía y Pertinencia Social** | Fuerte anclaje territorial, liderazgo autoral y OA Diamante | Resolución de problemas regionales y vinculación comunitaria | Elevada tasa primer autor, 100% Diamante, alineación ODS | Evaluación cualitativa de impacto social y regional |
| **Cluster Formación y Docencia Avanzada** | Masa crítica orientada a posgrado y docencia | Formación de recursos humanos y extensión | Volumen constante, publicaciones orientadas a docencia | Estímulos a la titulación y desarrollo de material pedagógico |

---

## 3. DILEMAS Y DISYUNTIVAS DE GOBERNANZA (TRADE-OFFS)

- **3.1. Dilema 1: Visibilidad Global vs. Soberanía Epistémica:**
  * Contrastar el incentivo de publicar en mega-consorcios con miles de autores frente a la necesidad de respaldar proyectos endógenos con autoría de correspondencia local.
- **3.2. Dilema 2: Cuotas Comerciales (APC) vs. Acceso Abierto Diamante:**
  * Análisis del costo de oportunidad: el desvío de presupuestos públicos hacia pagos de cuotas APC corporativas (USD) frente a la inversión en infraestructura editorial pública, regional y sostenible.
- **3.3. Dilema 3: Concentración Centralizada vs. Descentralización Territorial:**
  * Riesgos de polarizar los recursos en unos pocos centros de la capital frente al fomento de capacidades científicas en las entidades federativas.

---

## 4. EVALUACIÓN DE ESCENARIOS PROSPECTIVOS

- **4.1. Escenario Inercial (Status Quo / Inacción):**
  * Consecuencias proyectadas a 3 y 5 años: profundización de la fuga en APC, estancamiento del impacto autónomo y crisis de relevo en el SNII.
- **4.2. Escenario Proactivo (Intervención Basada en Evidencia Multidimensional):**
  * Beneficios proyectados: reorientación de fondos hacia infraestructura propia, fortalecimiento de la soberanía autoral y consolidación de clusters de desarrollo tecnológico.

---

## 5. MATRIZ DE RECOMENDACIONES PRIORITARIAS Y CURSOS DE ACCIÓN

Presentar la **Tabla 3: Matriz de Recomendaciones Accionables para Decisores**:

| Nivel de Decisión | Acción de Política Recomendada | Plazo de Implementación | Indicador de Éxito / Meta Verificable |
| :--- | :--- | :--- | :--- |
| **Alta Dirección / Rectoría / SECIHTI** | Regular el pago institucional de cuotas APC comerciales y fortalecer la vía Diamante. | Inmediato (0–6 meses) | Ahorro del [XX]% en divisas transferidas por APC en USD. |
| **Consejos Técnicos / Comités de Evaluación** | Adoptar el modelo de evaluación por pares comparables del SOM, erradicando rankings escalares. | Corto Plazo (6–12 meses) | Normativa aprobada con perfiles cualitativos diferenciados. |
| **Coordinaciones de Investigación** | Fondo concursable de apoyo exclusivo a proyectos con liderazgo de correspondencia institucional. | Mediano Plazo (1–3 años) | Incremento de [X]% en la tasa de autor de correspondencia. |

---

## FUENTES Y METADATOS AUDITABLES

- Clúster ClickHouse OpenAlex México (`rag.works_academic_all`, filtro ROR).
- Padrón Oficial SNII vía `sos_sinapsisai`.
- Metodología neurocomputacional: Carrillo-Calvet, H., Jiménez-Andrade, J. L., & Arencibia-Jorge, R. (2025). Redes neuronales autoorganizadas y mapeos de la ciencia. UNAM, IIBI.
