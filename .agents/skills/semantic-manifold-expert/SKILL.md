---
name: semantic-manifold-expert
description: Experto en análisis de variedades semánticas, estimación de dimensión intrínseca local (MLE al percentil 95) y compresión topológica no lineal (UMAP).
---

# Skill: Semantic Manifold Expert

## 1. Propósito y Activación
Se activa al procesar textos de artículos científicos (título + resumen + keywords) en espacios vectoriales densos (embeddings SPECTER2/Nomic).

## 2. Metodología de Variedades
1. **Techo de Información (Percentil 95):**
   - Estimar la dimensión intrínseca local con MLE (Maximum Likelihood Estimation).
   - Utilizar el percentil 95 como límite de compresión sin pérdida de topología.
2. **Protocolo MCP:**
   - `knomap-som-engine -> generate_document_embeddings`
   - `knomap-som-engine -> estimate_intrinsic_dimension`
   - `knomap-som-engine -> reduce_semantic_dimension` (UMAP a espacio intrínseco o 2D)
   - `knomap-som-engine -> cluster_semantic_documents` (Extracción TF-IDF jerárquica)
