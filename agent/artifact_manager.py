"""
artifact_manager.py - Gestor Universal de Artefactos Visuales e Interactivos
Descubre dinámicamente artefactos en .agents/artifacts/, valida schemas e inyecta datos en plantillas HTML/JS.
"""
import os
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

class ArtifactDefinition:
    def __init__(self, artifact_id: str, directory: Path, metadata: Dict[str, Any], template_content: str, instructions: str):
        self.artifact_id = artifact_id
        self.directory = directory
        self.metadata = metadata
        self.name = metadata.get("name", artifact_id)
        self.title = metadata.get("title", self.name)
        self.version = metadata.get("version", "1.0.0")
        self.content_type = metadata.get("content_type", "text/html")
        self.description = metadata.get("description", "")
        self.input_schema = metadata.get("input_schema", {})
        self.template_content = template_content
        self.instructions = instructions

    def render(self, data: Dict[str, Any], title_override: Optional[str] = None) -> str:
        """
        Inyecta el payload JSON de datos en la plantilla HTML.
        """
        title = title_override or self.title
        data_json = json.dumps(data, ensure_ascii=False)
        meta_json = json.dumps({
            "artifact_id": self.artifact_id,
            "name": self.name,
            "title": title,
            "version": self.version
        }, ensure_ascii=False)

        rendered = self.template_content
        rendered = rendered.replace("{{ DATA_JSON }}", data_json)
        rendered = rendered.replace("{{ META_JSON }}", meta_json)
        rendered = rendered.replace("{{ TITLE }}", title)
        return rendered


class ArtifactManager:
    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths = search_paths or [
            Path("/mnt/expansion/desplegados/sos-mcp-services/.agents/artifacts"),
            Path("/home/sinapsisai/.agents/artifacts"),
            Path(".agents/artifacts")
        ]
        self.artifacts: Dict[str, ArtifactDefinition] = {}
        self.discover_artifacts()

    def discover_artifacts(self) -> Dict[str, ArtifactDefinition]:
        """
        Escanea las rutas de búsqueda y carga todas las definiciones de artefactos disponibles.
        """
        self.artifacts.clear()
        for base_path in self.search_paths:
            if not base_path.exists() or not base_path.is_dir():
                continue

            for item in base_path.iterdir():
                if item.is_dir():
                    artifact_file = item / "ARTIFACT.md"
                    template_file = item / "template.html"
                    
                    if artifact_file.exists():
                        try:
                            definition = self._load_artifact(item.name, item, artifact_file, template_file)
                            if definition:
                                self.artifacts[definition.artifact_id] = definition
                        except Exception as e:
                            print(f"[ArtifactManager] Error cargando artefacto {item.name}: {e}")

        return self.artifacts

    def _load_artifact(self, artifact_id: str, directory: Path, artifact_file: Path, template_file: Path) -> Optional[ArtifactDefinition]:
        content = artifact_file.read_text(encoding="utf-8")
        metadata = {}
        instructions = ""

        # Parse YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_text = parts[1]
                instructions = parts[2].strip()
                
                # Parse manual sencillo o con pyyaml si está disponible
                try:
                    import yaml
                    metadata = yaml.safe_load(yaml_text) or {}
                except ImportError:
                    for line in yaml_text.splitlines():
                        if ":" in line and not line.strip().startswith("#"):
                            k, v = line.split(":", 1)
                            metadata[k.strip()] = v.strip().strip("'\"")

        template_content = ""
        if template_file.exists():
            template_content = template_file.read_text(encoding="utf-8")
        else:
            # Plantilla por defecto con visor de datos JSON si no hay template.html
            template_content = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{{ TITLE }}</title>
  <style>
    body { font-family: monospace; background: #0f172a; color: #f8fafc; padding: 20px; }
    pre { background: #1e293b; padding: 15px; border-radius: 8px; overflow-x: auto; }
  </style>
</head>
<body>
  <h2>{{ TITLE }}</h2>
  <pre id="data-view"></pre>
  <script>
    const data = {{ DATA_JSON }};
    document.getElementById('data-view').textContent = JSON.stringify(data, null, 2);
  </script>
</body>
</html>"""

        return ArtifactDefinition(
            artifact_id=artifact_id,
            directory=directory,
            metadata=metadata,
            template_content=template_content,
            instructions=instructions
        )

    def list_artifacts(self) -> List[Dict[str, Any]]:
        """
        Retorna la lista estructurada de artefactos disponibles.
        """
        return [
            {
                "id": a.artifact_id,
                "name": a.name,
                "title": a.title,
                "description": a.description,
                "version": a.version,
                "content_type": a.content_type,
                "input_schema": a.input_schema
            }
            for a in self.artifacts.values()
        ]

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactDefinition]:
        return self.artifacts.get(artifact_id)

    def render_artifact(self, artifact_id: str, data: Dict[str, Any], title: Optional[str] = None) -> Optional[str]:
        """
        Genera el HTML final del artefacto inyectando el payload de datos.
        """
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            print(f"[ArtifactManager] Advertencia: Artefacto '{artifact_id}' no encontrado.")
            return None
        return artifact.render(data, title_override=title)

    def detect_and_render_artifacts_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Escanea el texto en busca de bloques JSON que coincidan con los schemas de artefactos conocidos
        y los renderiza automáticamente si no fueron emitidos vía herramienta.
        """
        emitted = []
        if not text:
            return emitted

        # 1. Extraer todos los objetos JSON balanceados
        json_objects = []
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    chunk = text[start:i+1]
                    try:
                        obj = json.loads(chunk)
                        if isinstance(obj, dict):
                            json_objects.append(obj)
                    except Exception:
                        pass
                    start = -1

        # 2. Clasificar y renderizar cada objeto contra los artefactos
        seen_types = set()
        for obj in json_objects:
            art_id = None
            title = None

            # Reglas de firma
            if "u_matrix" in obj or ("grid_dimensions" in obj and "sample_mappings" in obj):
                art_id = "som-hexagonal-mesh"
                title = "Mapa SOM Hexagonal (knoMap)"
            elif "nodes" in obj and "links" in obj:
                art_id = "bibliometric-force-network"
                title = "Red Bibliométrica Interactiva & Louvain"
            elif "nodes" in obj and "edges" in obj:
                art_id = "graphrag-entity-subgraph"
                title = "Subgrafo de Conocimiento GraphRAG"
            elif "partner_countries" in obj or "oa_breakdown" in obj or "top_sdgs" in obj:
                art_id = "geopolitical-science-map"
                title = "Cartografía Geopolítica & Acceso Abierto"
            elif "fronts" in obj and "flows" in obj:
                art_id = "research-fronts-evolution"
                title = "Evolución de Frentes de Investigación v5.0"
            elif "law_type" in obj or "empirical_points" in obj:
                art_id = "bibliometric-laws-curves"
                title = f"Curvas de Leyes Bibliométricas ({obj.get('law_type', '').upper()})"
            elif "journal_name" in obj and "indexes" in obj:
                art_id = "journal-benchmark-matrix"
                title = f"Matriz Editorial: {obj.get('journal_name')}"
            elif "radar_disciplines" in obj or ("metrics" in obj and "institution_name" in obj):
                art_id = "institutional-benchmarking-profile"
                title = f"Perfil Institucional InCites: {obj.get('institution_name', 'Institución')}"
            elif "executive_summary" in obj or ("kpis" in obj and ("sections" in obj or "title" in obj)):
                art_id = "scientific-executive-report"
                title = obj.get("title", "Reporte Ejecutivo Cienciométrico")

            if art_id and art_id not in seen_types:
                rendered_html = self.render_artifact(art_id, obj, title=title)
                if rendered_html:
                    seen_types.add(art_id)
                    emitted.append({
                        "artifact_id": art_id,
                        "title": title,
                        "data": obj,
                        "html": rendered_html
                    })

        return emitted

    def get_artifacts_prompt(self) -> str:
        """
        Genera las instrucciones de artefactos disponibles para inyectar en el prompt del LLM.
        """
        if not self.artifacts:
            return ""

        prompt_lines = [
            "## 🎨 CATÁLOGO DE ARTEFACTOS VISUALES INTERACTIVOS DISPONIBLES:",
            "Para que el usuario VEA los paneles interactivos vivos en el chat, DEBES invocar la herramienta `emit_scientific_artifact(artifact_id, title, data)` en tu bloque de código Python, pasando el diccionario `data` con la estructura correspondiente.",
            ""
        ]

        for art in self.artifacts.values():
            prompt_lines.append(f"### [Artefacto: `{art.artifact_id}`] - {art.title}")
            prompt_lines.append(f"**Descripción:** {art.description}")
            if art.input_schema:
                prompt_lines.append(f"**Estructura esperada de `data`:**\n```json\n{json.dumps(art.input_schema, indent=2, ensure_ascii=False)}\n```")
            prompt_lines.append("")

        return "\n".join(prompt_lines)


# Singleton global
artifact_manager = ArtifactManager()
