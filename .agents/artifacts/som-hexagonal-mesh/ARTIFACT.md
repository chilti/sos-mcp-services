---
name: som-hexagonal-mesh
title: Malla Hexagonal SOM & U-Matrix (knoMap)
version: 1.0.0
content_type: text/html
description: Visualizador interactivo de Mapas Auto-Organizados (SOM) hexagonales con vistas de U-Matrix, clusters K-Means, frecuencias de ocupación y trayectorias temporales PathSOM.
input_schema:
  type: object
  required: [grid_dimensions, u_matrix]
  properties:
    grid_dimensions:
      type: object
      required: [rows, cols]
      properties:
        rows: { type: integer, description: "Número de filas de la malla" }
        cols: { type: integer, description: "Número de columnas de la malla" }
    u_matrix:
      type: array
      description: "Matriz 2D de distancias topológicas entre neuronas (valores entre 0.0 y 1.0)"
      items: { type: array, items: { type: number } }
    sample_mappings:
      type: array
      description: "Lista de entidades (autores, instituciones, papers) mapeadas a sus neuronas ganadoras (BMUs)"
      items:
        type: object
        required: [label, bmu_row, bmu_col]
        properties:
          label: { type: string }
          bmu_row: { type: integer }
          bmu_col: { type: integer }
          cluster: { type: integer }
          weight: { type: number }
    cluster_labels:
      type: array
      description: "Lista plana o 2D de etiquetas de cluster K-Means por neurona"
      items: { type: integer }
    quantization_error: { type: number }
    topographic_error: { type: number }
    trajectories:
      type: array
      description: "Opcional: series temporales de posiciones de entidades a través de los años (PathSOM)"
      items:
        type: object
        properties:
          entity: { type: string }
          path: { type: array, items: { type: object, properties: { year: { type: integer }, row: { type: integer }, col: { type: integer } } } }
---

# Instrucciones de Uso:
Invoca este artefacto cuando hayas entrenado un mapa SOM con `knomap-mcp` (`train_som`) o cuando analices la topología de autores/instituciones. Proporciona la `u_matrix`, las dimensiones de la malla y los `sample_mappings` con las etiquetas de los investigadores o artículos analizados.
