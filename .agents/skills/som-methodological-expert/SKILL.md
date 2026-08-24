---
name: som-methodological-expert
description: Experto en redes neuronales de Kohonen (SOM), cálculo de tamaño de malla espectral SVD, U-Matrix, calibración de clusters y métricas topológicas.
---

# Skill: SOM Methodological Expert

## 1. Propósito y Activación
Se activa cuando el usuario entrena, calibra o interpreta Mapas Auto-Organizados (Self-Organizing Maps) sobre datos multidimensionales.

## 2. Reglas de Dimensionamiento de Malla
1. **Ratio Espectral SVD:**
   - Calcular la descomposición en valores singulares: $\sigma_1 / \sigma_2$.
   - La relación de aspecto de la malla `rows:cols` debe coincidir con este ratio.
2. **Tamaño de Malla:**
   - *Small SOM:* $5 \times \sqrt{N}$ neuronas (ideal para agrupamiento denso y visualización rápida).
   - *Big SOM:* $10 \times N$ neuronas (ideal para análisis topológico continuo y U-Matrix de alta resolución).

## 3. Protocolo de Invocación MCP
1. Invocar `knomap-som-engine -> suggest_grid_size` pasando la matriz de datos.
2. Invocar `knomap-som-engine -> train_som` con inicialización PCA y topología hexagonal.
3. Invocar `knomap-som-engine -> evaluate_som_clusters` para sugerir el K óptimo vía Silhouette Score.
4. Invocar `knomap-som-engine -> recluster_som` si el usuario ajusta K sin reentrenar.
