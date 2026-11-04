---
name: research-fronts-detection-expert
description: Experto metodológico en detección multimodal de frentes de investigación (acoplamiento bibliográfico, cocitación, citación directa y OpenAlex Topics), partición Leiden CPM y evolución longitudinal aluvial con Información Mutua Ajustada (AMI). Delega la ejecución en topics-research-fronts-intelligence.
---

# Research Fronts Detection Expert

Esta skill provee el marco metodológico para la identificación y seguimiento de **frentes de investigación (Research Fronts)** y actúa como puente directo hacia la implementación completa en [`topics-research-fronts-intelligence`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/topics-research-fronts-intelligence/SKILL.md).

## 1. Posición en la Cadena de Valor (Workspace-First)

1. **Entrada Principal:** Lee el corpus previamente cosechado en el Workspace (`./corpus.parquet`, `.csv` o `.json`) generado en la Etapa 1 por `openalex-search-engineer`, `openalex-mexico-works-search` o `openalex-harvester`.
2. **Ejecución Operativa (Delegación a `topics-research-fronts-intelligence`):**
   - **Detección por Redes Bibliométricas (Bottom-Up con Leiden CPM):**
     ```bash
     /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/topics-research-fronts-intelligence/scripts/build_bibliometric_fronts.py \
       --input ./corpus.parquet \
       --modality coupling \
       --normalization association_strength \
       --gamma 0.05 \
       --output ./reports/fronts_coupling.json \
       --export-vosviewer ./reports/fronts_vosviewer.json
     ```
   - **Perfilado Macro/Meso de Topics de OpenAlex (Top-Down CWTS):**
     ```bash
     /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/topics-research-fronts-intelligence/scripts/extract_openalex_topics.py \
       --input ./corpus.parquet \
       --output ./reports/topics_profile.json
     ```
   - **Seguimiento Longitudinal de Linajes con AMI y Diagrama Aluvial Interactivo:**
     ```bash
     /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/topics-research-fronts-intelligence/scripts/track_longitudinal_lineages.py \
       --input ./corpus.parquet \
       --windows 3 \
       --modality coupling \
       --output ./reports/lineages_ami.json \
       --html-out ./reports/alluvial_fronts.html
     ```
3. **Conexión Downstream:**
   - Visualización de redes en `bibliometric-network-analyst` (`--export-vosviewer`).
   - Cartografía de frentes sobre SOM en `som-methodological-expert` (agregando el corpus por `topic` o `subfield` mediante `tlachia-metrics-engine`).
