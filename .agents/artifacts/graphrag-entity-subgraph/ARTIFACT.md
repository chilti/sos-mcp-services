---
name: graphrag-entity-subgraph
title: Subgrafo de Conocimiento Científico GraphRAG (Neo4j)
version: 1.0.0
content_type: text/html
description: Visualizador interactivo de subgrafos de conocimiento científico heterogéneo (Investigadores SNII, Trabajos, Instituciones, Temas y Patentes) extraídos mediante consultas Cypher en Neo4j y búsqueda híbrida vectorial en Qdrant.
input_schema:
  type: object
  required: [nodes, edges]
  properties:
    nodes:
      type: array
      items:
        type: object
        required: [id, label, entity_type]
        properties:
          id: { type: string }
          label: { type: string }
          entity_type:
            type: string
            enum: [Researcher, Work, Institution, Concept, Patent]
          snii_level: { type: string }
          orcid: { type: string }
          citations: { type: integer }
    edges:
      type: array
      items:
        type: object
        required: [source, target, relationship]
        properties:
          source: { type: string }
          target: { type: string }
          relationship: { type: string, description: "AUTHORED | AFFILIATED_WITH | CITES | HAS_TOPIC" }
---

# Instrucciones de Uso:
Invoca este artefacto al realizar consultas en `sinapsisai-mcp` (`query_knowledge_graph_cypher`, `resolve_snii_identity`) para explorar visualmente las conexiones relacionales de un investigador, institución o corpus temático.
