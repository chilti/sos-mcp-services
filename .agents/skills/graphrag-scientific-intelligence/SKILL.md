---
name: graphrag-scientific-intelligence
description: Experto en consultas híbridas GraphRAG cruzando el Grafo de Conocimiento Neo4j, búsqueda vectorial en Qdrant y el Padrón Oficial SNII.
---

# Skill: GraphRAG Scientific Intelligence

## 1. Propósito y Activación
Se activa para responder preguntas complejas sobre investigadores, colaboraciones institucionales y proyectos de la UNAM y México.

## 2. Protocolo de Razonamiento Híbrido
1. **Búsqueda Vectorial:** `sinapsisai-graphrag-engine -> search_scientific_papers_semantic`.
2. **Exploración de Grafo:** `sinapsisai-graphrag-engine -> query_knowledge_graph_cypher` para navegar relaciones `[:COAUTHORED_WITH]`, `[:AFFILIATED_WITH]`, `[:ALIGNED_WITH_SDG]`.
3. **Validación SNII:** `sinapsisai-graphrag-engine -> resolve_snii_identity` y `get_researcher_profile` para confirmar nivel y vigencia oficial.
