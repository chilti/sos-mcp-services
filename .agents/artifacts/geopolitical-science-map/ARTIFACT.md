---
name: geopolitical-science-map
title: Cartografía Geopolítica de la Ciencia & Acceso Abierto
version: 1.0.0
content_type: text/html
description: Tablero geopolítico interactivo que combina mapa de coautoría internacional (Índice de Salton y FWCI por país aliado), desglose de las 6 vías de Acceso Abierto (Diamante vs APC) y alineación con los 17 Objetivos de Desarrollo Sostenible (ODS).
input_schema:
  type: object
  required: [anchor_country, partner_countries]
  properties:
    anchor_country: { type: string, description: "Código o nombre del país ancla (ej. 'MX')" }
    partner_countries:
      type: array
      items:
        type: object
        required: [country_code, country_name, coauthored_papers]
        properties:
          country_code: { type: string }
          country_name: { type: string }
          coauthored_papers: { type: integer }
          mean_fwci: { type: number }
    oa_breakdown:
      type: object
      properties:
        diamond: { type: number }
        gold_apc: { type: number }
        green_repository: { type: number }
        hybrid: { type: number }
        bronze: { type: number }
        closed_paywall: { type: number }
    top_sdgs:
      type: array
      items:
        type: object
        properties:
          sdg_number: { type: integer }
          sdg_title: { type: string }
          aligned_papers_count: { type: integer }
          pct_share: { type: number }
---

# Instrucciones de Uso:
Invoca este artefacto al utilizar `topics-mcp` (`get_geopolitical_collaboration_matrix`, `get_open_access_transition_data`, `get_sdg_impact_matrix`) para responder consultas sobre diplomacia científica, mandatos de acceso abierto y contribución a los ODS.
