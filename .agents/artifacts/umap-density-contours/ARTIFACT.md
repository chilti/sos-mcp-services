---
name: umap-density-contours
title: Mapa Semántico UMAP & Densidad KDE (knoMap)
version: 1.0.0
content_type: text/html
description: Proyección topológica no lineal 2D (UMAP) de artículos científicos o investigadores sobre embeddings semánticos con isolíneas de densidad KDE continua, clusters temáticos y estimación de dimensión intrínseca local.
input_schema:
  type: object
  required: [points]
  properties:
    points:
      type: array
      description: "Puntos proyectados en 2D (artículos o investigadores)"
      items:
        type: object
        required: [x, y, label]
        properties:
          x: { type: number }
          y: { type: number }
          label: { type: string, description: "Título del artículo o nombre del autor" }
          cluster: { type: integer }
          topic: { type: string }
          citations: { type: integer }
          year: { type: integer }
    intrinsic_dimension_mle: { type: number, description: "Dimensión intrínseca local estimada (ej. 14.2 al percentil 95)" }
    umap_parameters:
      type: object
      properties:
        n_neighbors: { type: integer }
        min_dist: { type: number }
        metric: { type: string }
---

# Instrucciones de Uso:
Invoca este artefacto cuando realices análisis de variedades semánticas, compresión de embeddings (Nomic / SPECTER2) con UMAP o mapeo temático de producción científica masiva.
