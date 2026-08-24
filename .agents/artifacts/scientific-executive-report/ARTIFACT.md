---
name: scientific-executive-report
title: Reporte Ejecutivo de Inteligencia Científica & Cienciometría
version: 1.0.0
content_type: text/html
description: Reporte cienciométrico integral de grado ejecutivo con tarjetas KPI, síntesis estructurada, tablas analíticas filtrables y exportables, y recomendaciones estratégicas.
input_schema:
  type: object
  required: [title, executive_summary, kpis]
  properties:
    title: { type: string }
    subtitle: { type: string }
    institution: { type: string }
    executive_summary: { type: string }
    kpis:
      type: array
      items:
        type: object
        required: [label, value]
        properties:
          label: { type: string }
          value: { type: [string, number] }
          detail: { type: string }
    sections:
      type: array
      items:
        type: object
        required: [title, content]
        properties:
          title: { type: string }
          content: { type: string }
          table:
            type: object
            properties:
              headers: { type: array, items: { type: string } }
              rows: { type: array, items: { type: array } }
    recommendations:
      type: array
      items: { type: string }
---

# Instrucciones de Uso:
Invoca este artefacto al finalizar investigaciones amplias, diagnósticos institucionales o comparativas nacionales para entregar un informe formal y exhaustivo al usuario.
