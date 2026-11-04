---
name: graphrag-scientific-intelligence
description: Consultas híbridas GraphRAG combinando búsqueda semántica vectorial de 768 dimensiones (Nomic), exploración de redes de coautoría/citación y verificación en el Padrón Oficial SNII.
---

# GraphRAG Scientific Intelligence

Esta skill articula consultas híbridas **GraphRAG** (recuperación aumentada por grafos de conocimiento y vectores densos) sobre la infraestructura científica del ecosistema.

## 1. Flujo Operativo en el Ecosistema (Workspace-First)

1. **Recuperación Semántica Vectorial (768d Nomic):**
   - Delega en `openalex-mexico-semantic-search` (`openalex_mexico_cli.py semantic-search`) para recuperar obras y perfiles por similitud coseno conceptual sin depender de coincidencia léxica exacta.
2. **Resolución de Identidad y Padrón SNII:**
   - Delega en `snii-identity-resolver` (`snii_resolver_cli.py`) y `openalex-mexico-author-search` para vincular cada nodo de autor con su nivel SNII, ORCID y ROR institucional.
3. **Construcción del Subgrafo Relacional en el Workspace:**
   - Una vez exportado el corpus afín a `./corpus.parquet`, delega en `bibliometric-network-analyst` (`biblio_network_cli.py`) y `topics-research-fronts-intelligence` (`build_bibliometric_fronts.py`) para extraer la estructura comunitaria Leiden, centralidades de intermediación (*betweenness*) y puentes estructurales entre grupos de investigación.
