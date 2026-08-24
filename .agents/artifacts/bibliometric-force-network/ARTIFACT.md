---
name: bibliometric-force-network
title: Red Bibliométrica Interactiva & Louvain (D3 Force)
version: 1.0.0
content_type: text/html
description: Visualizador de redes de coautoría, co-ocurrencia de palabras clave y acoplamiento bibliográfico con simulación de fuerzas D3, partición Louvain/Leiden, buscador de nodos y métricas de centralidad.
input_schema:
  type: object
  required: [nodes, links]
  properties:
    nodes:
      type: array
      description: "Lista de nodos del grafo (investigadores, instituciones o términos)"
      items:
        type: object
        required: [id, label]
        properties:
          id: { type: [string, integer] }
          label: { type: string }
          weight: { type: number, description: "Frecuencia, volumen de artículos o citas" }
          cluster: { type: integer, description: "Identificador de comunidad Louvain/Leiden" }
          fwci: { type: number, description: "Impacto normalizado (opcional)" }
          institution: { type: string }
    links:
      type: array
      description: "Lista de enlaces de coautoría o similitud"
      items:
        type: object
        required: [source, target]
        properties:
          source: { type: [string, integer] }
          target: { type: [string, integer] }
          strength: { type: number, description: "Fuerza de asociación de Salton o número de coautorías" }
    modularity_q: { type: number, description: "Modularidad Q de la partición (ej. 0.68)" }
    network_type: { type: string, description: "coauthorship | cooccurrence | bibliographic_coupling" }
---

# Instrucciones de Uso:
Invoca este artefacto cuando construyas o analices redes de colaboración científica, coautoría internacional o co-ocurrencia temática. Proporciona la lista de `nodes` y `links` generada por `knomap-mcp` (`parse_bibliographic_file`) o calculada con `networkx` en el sandbox.
