---
name: research-fronts-detection-expert
description: Experto en detección multimodal de frentes de investigación (Research Fronts v5.0), evolución longitudinal con AMI y análisis de linajes temáticos.
---

# Skill: Research Fronts Detection Expert

## 1. Propósito y Activación
Se activa para descubrir frentes de investigación emergentes en subcampos científicos mediante el pipeline triple.

## 2. Modalidades de Detección
- **Estructural:** Algoritmo Leiden sobre red de acoplamiento bibliográfico con similitud de Salton $\ge 0.1$.
- **Semántica:** Clustering HDBSCAN sobre embeddings SPECTER2.
- **Topológica:** FastRP sobre el grafo de citas.

## 3. Protocolo MCP
1. Invocar `topics-research-fronts-engine -> detect_research_fronts_multimodal`.
2. Invocar `topics-research-fronts-engine -> track_front_evolution_longitudinal` para evaluar persistencia, fusiones y divisiones entre ventanas temporales.
