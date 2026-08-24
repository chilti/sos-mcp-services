---
name: journal-benchmark-matrix
title: Matriz de Inteligencia Editorial & Revistas Iberoamericanas
version: 1.0.0
content_type: text/html
description: Evaluación cienciométrica y benchmarking de revistas científicas iberoamericanas con radar de indexación (DOAJ, SciELO, Redalyc, Latindex Catálogo 2.0), políticas de APC (Acceso Abierto Diamante vs Cobro APC) y perfil multilingüe.
input_schema:
  type: object
  required: [journal_name, indexes]
  properties:
    journal_name: { type: string }
    issn: { type: string }
    publisher: { type: string }
    diamond_oa: { type: boolean, description: "True si es Acceso Abierto Diamante (sin APCs para autor ni lector)" }
    apc_usd: { type: number, description: "Costo de APC en USD ($0 si es Diamante)" }
    indexes:
      type: object
      description: "Estado de indización en bases de datos"
      properties:
        doaj: { type: boolean }
        scielo: { type: boolean }
        redalyc: { type: boolean }
        latindex_catalogo_2: { type: boolean }
        scopus: { type: boolean }
        wos_esci_scie: { type: boolean }
    multilingualism:
      type: array
      items: { type: object, properties: { language: { type: string }, pct_articles: { type: number } } }
    scimago_quartile: { type: string, description: "Q1 | Q2 | Q3 | Q4 | No indexada" }
---

# Instrucciones de Uso:
Invoca este artefacto al utilizar `revistaslatam-mcp` para asesorar a investigadores o comités editoriales sobre indexación, políticas de acceso abierto y visibilidad regional/global.
