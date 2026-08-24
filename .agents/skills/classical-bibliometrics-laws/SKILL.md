---
name: classical-bibliometrics-laws
description: Experto en modelado matemático de leyes bibliométricas clásicas (Lotka, Bradford, Zipf, Price) y fases de madurez científica.
---

# Skill: Classical Bibliometrics Laws

## 1. Propósito y Activación
Se activa para validar hipótesis cuantitativas sobre distribuciones de productividad, dispersión de literatura y tasas de envejecimiento.

## 2. Modelos y Criterios de Aceptación
- **Ley de Lotka (Productividad de Autores):** $A_n = A_1 / n^c$. Exponente canónico $c \approx 2.0$. Prueba Kolmogorov-Smirnov para bondad de ajuste.
- **Ley de Bradford (Dispersión de Revistas):** División en 3 zonas de igual producción ($1 : k : k^2$). Extracción del núcleo *Core*.
- **Índice de Price (Obsolescencia):** Porcentaje de referencias con $\le 5$ años de antigüedad.
- **Modelos de Crecimiento:** Comparación Exponencial vs Logístico para determinar fase de madurez.

## 3. Protocolo MCP
- `plmetrix-laws-engine -> analyze_lotka_law`
- `plmetrix-laws-engine -> analyze_bradford_law`
- `plmetrix-laws-engine -> analyze_price_index`
- `plmetrix-laws-engine -> analyze_scientific_growth_phases`
