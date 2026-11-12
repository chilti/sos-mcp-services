---
name: research-fronts-detection-expert
description: Methodological expert in multimodal research front detection (bibliographic coupling, co-citation, direct citation, and OpenAlex Topics), Leiden CPM partitioning, and longitudinal alluvial evolution with Adjusted Mutual Information (AMI). Delegates execution to topics-research-fronts-intelligence. Respond and label outputs in the user's language.
---

# Research Fronts Detection Expert

> **Language Rule:** Respond and label outputs in the user's language (default to English for script plots/labels, or pass `--lang es` when the user interacts in Spanish).

This skill provides the methodological framework for identifying and tracking **Research Fronts** and acts as a direct bridge to the full implementation in [`topics-research-fronts-intelligence`](file:///mnt/expansion/desplegados/sos-mcp-services/.agents/skills/topics-research-fronts-intelligence/SKILL.md).

## 1. Position in the Value Chain (Workspace-First)

1. **Primary Input:** Reads the corpus previously harvested into the Workspace (`./corpus.parquet`, `.csv`, or `.json`) generated in Stage 1 by `openalex-search-engineer`, `openalex-mexico-works-search`, or `openalex-harvester`.
2. **Operational Execution (Delegated to `topics-research-fronts-intelligence`):**
   - **Bibliometric Network Detection (Bottom-Up with Leiden CPM):**
     ```bash
     /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/topics-research-fronts-intelligence/scripts/build_bibliometric_fronts.py \
       --input ./corpus.parquet \
       --modality coupling \
       --normalization association_strength \
       --gamma 0.05 \
       --output ./reports/fronts_coupling.json \
       --export-vosviewer ./reports/fronts_vosviewer.json
     ```
   - **Macro/Meso OpenAlex Topics Profiling (Top-Down CWTS):**
     ```bash
     /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/topics-research-fronts-intelligence/scripts/extract_openalex_topics.py \
       --input ./corpus.parquet \
       --output ./reports/topics_profile.json
     ```
   - **Longitudinal Lineage Tracking with AMI and Interactive Alluvial Diagram:**
     ```bash
     /home/ambientesPy/revistaslatam/bin/python /mnt/expansion/desplegados/sos-mcp-services/.agents/skills/topics-research-fronts-intelligence/scripts/track_longitudinal_lineages.py \
       --input ./corpus.parquet \
       --windows 3 \
       --modality coupling \
       --output ./reports/lineages_ami.json \
       --html-out ./reports/alluvial_fronts.html
     ```
3. **Downstream Connections:**
   - Network visualization in `bibliometric-network-analyst` (`--export-vosviewer`).
   - Mapping of fronts onto SOMs in `som-methodological-expert` (aggregating the corpus by `topic` or `subfield` via `tlachia-metrics-engine`).
