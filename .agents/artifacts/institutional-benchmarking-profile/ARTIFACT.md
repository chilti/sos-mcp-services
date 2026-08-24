---
name: institutional-benchmarking-profile
title: Perfil Institucional Multidimensional InCites (knoMap)
version: 1.0.0
content_type: text/html
description: Benchmarking cienciométrico institucional (estándar Clarivate InCites) con gráfico de radar multidimensional de impacto (FWCI, % Top 10%, % Colaboración Internacional, Citas/Doc por disciplina WoS) y comparación de pares.
input_schema:
  type: object
  required: [institution_name, metrics]
  properties:
    institution_name: { type: string }
    country: { type: string }
    time_period: { type: string }
    metrics:
      type: object
      properties:
        web_of_science_documents: { type: integer }
        mean_fwci: { type: number, description: "Category Normalized Citation Impact (CNCI / FWCI)" }
        pct_top_10_percent: { type: number, description: "% de papers en el top 10% más citado" }
        pct_international_collab: { type: number, description: "% de coautoría internacional" }
        citations_per_doc: { type: number }
    radar_disciplines:
      type: array
      items:
        type: object
        properties:
          discipline: { type: string }
          institution_score: { type: number }
          baseline_score: { type: number }
---

# Instrucciones de Uso:
Invoca este artefacto al realizar evaluaciones de desempeño institucional, comparaciones internacionales o diagnósticos cienciométricos con `knomap-mcp`.
