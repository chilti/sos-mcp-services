---
name: bibliometric-laws-curves
title: Curvas de Leyes Bibliométricas & Madurez (PLMetrix)
version: 1.0.0
content_type: text/html
description: Visualizador de ajuste empírico y teórico para leyes bibliométricas clásicas (Ley de Lotka de productividad de autores, Zonas concéntricas de Bradford, Ley de Zipf y Modelo de Madurez Exponencial/Logístico de Price).
input_schema:
  type: object
  required: [law_type, empirical_points]
  properties:
    law_type:
      type: string
      enum: [lotka, bradford, price_maturity, zipf]
      description: "Tipo de ley bibliométrica modelada"
    empirical_points:
      type: array
      items:
        type: object
        properties:
          x: { type: number, description: "Número de papers (Lotka), rango de revista (Bradford), o año (Price)" }
          y: { type: number, description: "Número de autores (Lotka), citas acumuladas (Bradford), o producción anual (Price)" }
          label: { type: string }
    fitted_curve:
      type: array
      items:
        type: object
        properties:
          x: { type: number }
          y: { type: number }
    fit_metrics:
      type: object
      properties:
        r_squared: { type: number, description: "Coeficiente de determinación R^2 (ej. 0.96)" }
        alpha_exponent: { type: number, description: "Exponente alfa de Lotka (ej. 2.04)" }
        constant_c: { type: number }
        doubling_time_years: { type: number }
        phase: { type: string, description: "Fase de madurez (ej. 'Exponencial', 'Saturación', 'Emergencia')" }
---

# Instrucciones de Uso:
Invoca este artefacto al utilizar `plmetrix-mcp` para presentar el modelado matemático riguroso de la productividad, dispersión editorial y madurez del campo científico.
