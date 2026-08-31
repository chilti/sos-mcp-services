---
name: knomap-unified-orchestrator
description: Orquestador integral del ecosistema UNAM; coordina pipelines multi-fase desde extracción de datos masivos hasta modelado topológico y reportes.
---

# Skill: knoMap Unified Orchestrator

## 1. Propósito y Activación
Se activa cuando el usuario formula una meta de investigación integral (por ejemplo: "Analizar el estado de la Inteligencia Artificial en la UNAM durante los últimos 10 años").

## 2. Flujo de Orquestación en 5 Fases
1. **Fase 1 (Datos):** Extraer corpus y autores con `openalex-clickhouse-gateway`.
2. **Fase 2 (Validación Social/SNII):** Cruzar autores con `sinapsisai-graphrag-engine` y verificar padrón SNII.
3. **Fase 3 (Leyes y Frentes):** Ajustar Ley de Lotka con `plmetrix-laws-engine` y detectar frentes con `topics-research-fronts-engine`. **Crucial**: Ilustrar la evolución temporal de los frentes invocando `knomap_render_alluvial_diagram()`.
4. **Fase 4 (Topología SOM):** Reducir a espacio intrínseco y entrenar mapa de Kohonen con `knomap-som-engine`.
5. **Fase 5 (Síntesis):** Generar reporte con hallazgos, fortalezas, brechas (evidenciadas gráficamente invocando `knomap_render_dumbbell_chart()`) y recomendaciones de política científica (ilustradas con `knomap_render_connection_map()`).
