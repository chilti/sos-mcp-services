---
name: research-fronts-evolution
title: Evolución Longitudinal de Frentes de Investigación v5.0
version: 1.0.0
content_type: text/html
description: Diagrama Aluvial / Sankey temporal de linajes científicos que rastrea la persistencia, división, fusión y emergencia de frentes de investigación a través de ventanas cronológicas con métricas de Información Mutua Ajustada (AMI).
input_schema:
  type: object
  required: [time_windows, fronts, flows]
  properties:
    time_windows:
      type: array
      description: "Lista de periodos o ventanas temporales (ej. ['2015-2017', '2018-2020', '2021-2023'])"
      items: { type: string }
    fronts:
      type: array
      description: "Nodos de frentes por cada ventana temporal"
      items:
        type: object
        required: [id, label, window]
        properties:
          id: { type: string }
          label: { type: string }
          window: { type: string }
          size: { type: integer, description: "Número de papers nucleares en el frente" }
          mean_citations: { type: number }
          top_terms: { type: array, items: { type: string } }
    flows:
      type: array
      description: "Transiciones y linajes entre frentes de ventanas consecutivas"
      items:
        type: object
        required: [source, target, value]
        properties:
          source: { type: string }
          target: { type: string }
          value: { type: number, description: "Intensidad del linaje o papers compartidos" }
          event_type: { type: string, description: "persisted | split | merged | emerged" }
          ami_score: { type: number }
---

# Instrucciones de Uso:
Invoca este artefacto al utilizar `topics-mcp` (`track_front_evolution_longitudinal`) para presentar la trayectoria histórica, maduración y ramificación de frentes temáticos.
