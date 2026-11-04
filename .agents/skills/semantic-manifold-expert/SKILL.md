---
name: semantic-manifold-expert
description: Análisis de variedades semánticas (Semantic Manifolds), estimación de dimensión intrínseca local (MLE al percentil 95, TwoNN) sobre matrices de indicadores o embeddings vectoriales (768d) y compresión topológica no lineal UMAP acoplada al SOM.
---

# Semantic Manifold Expert (MLE Intrinsic Dimension & UMAP Topology)

Esta skill modela la geometría de variedades de datos cienciométricos y embeddings semánticos antes o en paralelo al entrenamiento del Mapa Autoorganizado de Kohonen (SOM).

## 1. Integración en la Cadena de Valor (Workspace-First)

1. **Entradas desde el Workspace:**
   - Matrices multidimensionales `./matrices/indicadores_som.parquet` generadas por `tlachia-metrics-engine` (con 35+ indicadores).
   - Vectores de pesos sinápticos entrenados en `./reports/som_state.json`.
   - Embeddings semánticos de 768 dimensiones (`embedding_nomic`) recuperados por `openalex-mexico-semantic-search`.

2. **Funciones Metodológicas Clave:**
   - **Estimación de Dimensión Intrínseca Local ($d_{MLE}$ al percentil 95):** Cuantifica cuántos grados de libertad reales gobiernan la variedad de indicadores antes de proyectarla a la retícula 2D del SOM.
   - **Proyección UMAP acoplada al SOM (`run_umap=True` en `som_tools.py`):** Todo entrenamiento ejecutado mediante `som-methodological-expert` (`scripts/som_pipeline_cli.py`) calcula y almacena las coordenadas UMAP 2D de los prototipos neuronales en `./reports/som_state.json`, permitiendo contrastar la preservación topológica de la malla hexagonal frente a la variedad continua UMAP.
