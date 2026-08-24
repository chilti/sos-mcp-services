"""
visualizer_agent.py - Agente Especialista en Composición y Auto-Síntesis de Artefactos Interactivos
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from agent.swarm.base_agent import BaseSpecialistAgent
from agent.artifact_manager import artifact_manager
from lib.episodic_memory import episodic_memory

try:
    from smolagents import tool
except ImportError:
    def tool(fn): return fn


def get_visualizer_tools(session_id: Optional[str] = None, emitted_collector: Optional[List[Dict[str, Any]]] = None) -> List[Any]:
    tools = []

    # 1. Emit Existing Catalog Artifact
    @tool
    def emit_standard_artifact(artifact_id: str, title: str, data_json_str: str) -> str:
        """
        Renderiza un artefacto interactivo del catálogo existente (som-hexagonal-mesh, bibliometric-force-network, etc.).
        Args:
            artifact_id: ID del artefacto ('som-hexagonal-mesh', 'bibliometric-force-network', 'umap-density-contours', 'research-fronts-evolution', 'geopolitical-science-map', 'bibliometric-laws-curves', 'journal-benchmark-matrix', 'institutional-benchmarking-profile', 'graphrag-entity-subgraph', 'scientific-executive-report').
            title: Título descriptivo de la visualización.
            data_json_str: Estructura de datos en formato JSON requerida por el artefacto.
        """
        try:
            data = json.loads(data_json_str) if isinstance(data_json_str, str) else data_json_str
            html = artifact_manager.render_artifact(artifact_id, data, title=title)
            if html:
                item = {"artifact_id": artifact_id, "title": title, "data": data, "html": html}
                if emitted_collector is not None:
                    emitted_collector.append(item)
                if session_id:
                    episodic_memory.record_evidence(
                        session_id=session_id,
                        claim_type="conclusion",
                        claim_text=f"Artefacto Emitido: {title} ({artifact_id})",
                        evidence_source=f"artifact_{artifact_id}",
                        evidence_payload={"title": title, "data_keys": list(data.keys())}
                    )
                return f"✅ Artefacto '{title}' ({artifact_id}) generado exitosamente."
            return f"❌ Error: Artefacto '{artifact_id}' no encontrado en el catálogo."
        except Exception as e:
            return f"❌ Error renderizando artefacto: {str(e)}"
    tools.append(emit_standard_artifact)

    # 2. SINTETIZAR NUEVO ARTEFACTO AL VUELO (Self-Synthesized Artifacts)
    @tool
    def synthesize_new_artifact(
        artifact_id: str,
        title: str,
        description: str,
        input_schema_json: str,
        template_html_code: str,
        data_json_str: str
    ) -> str:
        """
        Crea, persiste y renderiza un NUEVO artefacto interactivo al vuelo (HTML/D3/Plotly/Canvas) cuando ninguna plantilla existente cubre la necesidad.
        El nuevo artefacto queda guardado en .agents/artifacts/ para siempre y disponible para todos los sistemas.
        Args:
            artifact_id: Identificador kebab-case único (ej. 'citation-chord-diagram', '3d-spatial-scatter').
            title: Nombre legible del artefacto.
            description: Descripción metodológica y visual del nuevo gráfico.
            input_schema_json: Schema JSON de entrada esperado.
            template_html_code: Código HTML/JS autónomo completo que consuma 'window.__ARTIFACT_DATA__ = {{ DATA_JSON }}'.
            data_json_str: Datos JSON a inyectar y renderizar de inmediato.
        """
        try:
            artifacts_dir = Path("/mnt/expansion/desplegados/sos-mcp-services/.agents/artifacts")
            target_dir = artifacts_dir / artifact_id
            target_dir.mkdir(parents=True, exist_ok=True)

            # 1. Escribir ARTIFACT.md
            md_content = f"""---
name: {artifact_id}
title: {title}
version: 1.0.0
content_type: text/html
description: {description}
input_schema:
{input_schema_json}
---

# Artefacto Auto-Sintetizado por el Enjambre Científico
Generado autónomamente por VisualizerAgent para cubrir nuevas necesidades de visualización.
"""
            (target_dir / "ARTIFACT.md").write_text(md_content, encoding="utf-8")

            # 2. Escribir template.html
            (target_dir / "template.html").write_text(template_html_code, encoding="utf-8")

            # 3. Re-escanear catálogo en caliente
            artifact_manager.artifacts = artifact_manager._load_all_artifacts()

            # 4. Renderizar de inmediato
            data = json.loads(data_json_str) if isinstance(data_json_str, str) else data_json_str
            html = artifact_manager.render_artifact(artifact_id, data, title=title)
            
            if html:
                item = {"artifact_id": artifact_id, "title": title, "data": data, "html": html, "is_newly_synthesized": True}
                if emitted_collector is not None:
                    emitted_collector.append(item)
                if session_id:
                    episodic_memory.record_evidence(
                        session_id=session_id,
                        claim_type="conclusion",
                        claim_text=f"Nuevo Artefacto Sintetizado: {title} ({artifact_id})",
                        evidence_source=f"new_artifact_{artifact_id}",
                        evidence_payload={"title": title, "schema": input_schema_json}
                    )
                return f"🎉 ¡Nuevo artefacto '{title}' ({artifact_id}) auto-sintetizado, persistido y renderizado exitosamente!"
            return f"❌ Error al renderizar la nueva plantilla de '{artifact_id}'."
        except Exception as e:
            return f"❌ Error en auto-síntesis de artefacto: {str(e)}"
    tools.append(synthesize_new_artifact)

    return tools


class InteractiveVisualizerAgent(BaseSpecialistAgent):
    """Agente especialista en renderizado y auto-síntesis de artefactos visuales interactivos."""
    def __init__(self, session_id: Optional[str] = None, emitted_collector: Optional[List[Dict[str, Any]]] = None, **kwargs):
        self.emitted_collector = emitted_collector if emitted_collector is not None else []
        tools = get_visualizer_tools(session_id=session_id, emitted_collector=self.emitted_collector)
        role = ("Experto en visualización científica e interfaces interactivas D3.js, SVG, Canvas y Plotly. "
                "Emite artefactos del catálogo universal y posee la capacidad de AUTO-SINTETIZAR nuevos artefactos "
                "interactivos en tiempo de ejecución (`synthesize_new_artifact`) si se requiere un gráfico no contemplado.")
        super().__init__(name="InteractiveVisualizerAgent", role_description=role, tools=tools, **kwargs)
