---
name: scientometrics-incites-expert
description: Experto en benchmarking cienciométrico institucional (Clarivate InCites), perfiles multidimensionales y series temporales multivariadas (PathSOM).
---

# Skill: Scientometrics InCites Expert

## 1. Propósito y Activación
Se activa al analizar reportes y paquetes de benchmarking InCites (instituciones, autores, departamentos, áreas temáticas).

## 2. Protocolo de Extracción y Normalización
1. **Inspección:** Invocar `knomap-som-engine -> inspect_incites_package`.
2. **Ventanas Temporales:**
   - *Reciente (5 años):* 2021-2025 para evaluación de desempeño actual.
   - *Histórico:* 1980-2025 para análisis de trayectoria longitudinal.
3. **Indicadores Clave:**
   - CNCI (Category Normalized Citation Impact): Impacto normalizado por categoría (Mundial = 1.0).
   - % Documents in Top 10% / Top 1%: Excelencia científica.
   - International Collaborations (%): Grado de internacionalización.

## 3. Trayectorias PathSOM y Matriz Estratégica
- Invocar `get_incites_temporal_evolution` aplicando suavizado ECMA (Moving Average de 3 o 5 periodos).
- Invocar `compute_strategic_growth_matrix` para clasificar entidades en 4 cuadrantes (Emerging Stars, Star Leaders, Established Giants, Low Priority).
