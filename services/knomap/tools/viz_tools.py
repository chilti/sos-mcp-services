import sys
import os
import math
import json
import colorsys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Asegurar que el engine de knomap está en el path (Windows y Linux)
KNOMAP_CANDIDATES = [
    Path(r"c:\Users\jlja\Documents\Proyectos\knomap"),
    Path(__file__).resolve().parent.parent.parent.parent / "knomap",
    Path("/home/labsom/knomap")
]
for p in KNOMAP_CANDIDATES:
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))

try:
    from engine.viz_extensions.charts_evolution import render_alluvial_diagram, render_slope_chart
    from engine.viz_extensions.charts_comparisons import render_dumbbell_chart, render_diverging_bar
    from engine.viz_extensions.charts_maps import render_connection_map, render_dorling_cartogram
    from engine.viz_extensions.charts_exploration import render_exploration_dashboard
    from engine.viz_extensions.charts_som import render_umatrix_3d, render_component_planes
except ImportError as e:
    def render_alluvial_diagram(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_slope_chart(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_dumbbell_chart(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_diverging_bar(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_connection_map(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_dorling_cartogram(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_exploration_dashboard(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_umatrix_3d(*args, **kwargs): return {"error": "viz_extensions not available"}
    def render_component_planes(*args, **kwargs): return {"error": "viz_extensions not available"}


# ==============================================================================
# KNOMAP NATIVE HEXAGONAL VISUALIZATION ENGINE (SVG + HTML)
# Replicación fiel de MallaHexagonal.tsx, LabSOM palettes y cluster boundaries
# ==============================================================================

def get_cluster_color(cluster_id: Optional[int]) -> str:
    """Color de cluster HSL por paso áureo canónico de KnoMap (137.5 deg)."""
    if cluster_id is None or cluster_id == -1:
        return "#2d3748"  # Ruido DBSCAN
    hue = (int(cluster_id) * 137.5) % 360
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, 0.65, 0.75)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def get_component_color(val: float, min_val: float, max_val: float, mid_val: Optional[float] = None) -> str:
    """Paleta LabSOM estándar divergente: Verde (#38a169) -> Amarillo (#ecc94b) -> Rojo (#e53e3e)."""
    if max_val <= min_val:
        return "#ecc94b"
    if mid_val is None or mid_val <= min_val or mid_val >= max_val:
        mid_val = (min_val + max_val) / 2.0
    val = max(min_val, min(max_val, float(val)))
    
    c_green = (56, 161, 105)
    c_yellow = (236, 201, 75)
    c_red = (229, 62, 62)
    
    if val <= mid_val:
        t = (val - min_val) / (mid_val - min_val) if mid_val > min_val else 0.5
        r = int(c_green[0] + t * (c_yellow[0] - c_green[0]))
        g = int(c_green[1] + t * (c_yellow[1] - c_green[1]))
        b = int(c_green[2] + t * (c_yellow[2] - c_green[2]))
    else:
        t = (val - mid_val) / (max_val - mid_val) if max_val > mid_val else 0.5
        r = int(c_yellow[0] + t * (c_red[0] - c_yellow[0]))
        g = int(c_yellow[1] + t * (c_red[1] - c_yellow[1]))
        b = int(c_yellow[2] + t * (c_red[2] - c_yellow[2]))
    return f"#{r:02x}{g:02x}{b:02x}"


def get_umatrix_color(val: float, min_val: float, max_val: float) -> str:
    """Paleta LabSOM U-Matrix: Rojo (#e53e3e, valles/densidad) -> Amarillo (#ecc94b, crestas/fronteras)."""
    if max_val <= min_val:
        return "#e53e3e"
    t = max(0.0, min(1.0, (float(val) - min_val) / (max_val - min_val)))
    c_red = (229, 62, 62)
    c_yellow = (236, 201, 75)
    r = int(c_red[0] + t * (c_yellow[0] - c_red[0]))
    g = int(c_red[1] + t * (c_yellow[1] - c_red[1]))
    b = int(c_red[2] + t * (c_yellow[2] - c_red[2]))
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_hexagonal_som_svg(
    rows: int,
    cols: int,
    cell_colors: List[str],
    clustering: Optional[List[int]] = None,
    cluster_labels: Optional[Dict[int, str]] = None,
    mapped_labels: Optional[List[List[str]]] = None,
    trajectories: Optional[List[Dict[str, Any]]] = None,
    max_labels_per_neuron: int = 2,
    max_total_labels: int = 40,
    show_cluster_labels: bool = True,
    show_boundaries: bool = True,
    cell_stroke_color: str = "#334155",
    cell_stroke_width: float = 0.025,
    boundary_stroke_color: str = "#000000",
    boundary_stroke_width: float = 0.065,
    svg_id: str = "knomap-som-svg"
) -> str:
    """
    Genera el código SVG vectorial completo de la Malla Hexagonal idéntico a MallaHexagonal.tsx de KnoMap.
    Soporta hexágonos flat-topped, fronteras topológicas de cluster, insignias y splines de trayectorias.
    """
    R = 1.0
    apotema = math.sqrt(3) / 2.0
    avanceX = 1.5 * R
    avanceY = 2.0 * apotema * R
    
    # Coordenadas de los centros de los hexágonos
    coords = []
    for i in range(rows):
        for j in range(cols):
            x = j * avanceX
            y = i * avanceY + (apotema if j % 2 != 0 else 0.0)
            coords.append((x, y))
            
    minX = -1.2 * R
    minY = -1.2 * apotema * R
    maxX = max(c[0] for c in coords) + 1.2 * R
    maxY = max(c[1] for c in coords) + 1.2 * R
    gridWidth = maxX - minX
    gridHeight = maxY - minY
    viewbox = f"{minX:.3f} {minY:.3f} {gridWidth:.3f} {gridHeight:.3f}"
    
    def get_hex_points(xc: float, yc: float) -> List[Tuple[float, float]]:
        return [
            (xc + R, yc),                               # P1
            (xc + 0.5 * R, yc + apotema * R),           # P2
            (xc - 0.5 * R, yc + apotema * R),           # P3
            (xc - R, yc),                               # P4
            (xc - 0.5 * R, yc - apotema * R),           # P5
            (xc + 0.5 * R, yc - apotema * R)            # P6
        ]

    # Cálculo de fronteras entre clusters (vecinos n1..n6 basados en paridad de columnas)
    border_lines = []
    if show_boundaries and clustering and len(clustering) == rows * cols:
        neighbors_map = {
            "n1": lambda r, c: (r if c % 2 == 0 else r + 1, c + 1, (0, 1)),
            "n2": lambda r, c: (r + 1, c, (1, 2)),
            "n3": lambda r, c: (r if c % 2 == 0 else r + 1, c - 1, (2, 3)),
            "n4": lambda r, c: (r - 1 if c % 2 == 0 else r, c - 1, (3, 4)),
            "n5": lambda r, c: (r - 1, c, (4, 5)),
            "n6": lambda r, c: (r - 1 if c % 2 == 0 else r, c + 1, (5, 0))
        }
        for i in range(rows):
            for j in range(cols):
                idx = j + i * cols
                c_id = clustering[idx]
                xc, yc = coords[idx]
                pts = get_hex_points(xc, yc)
                for k, fn in neighbors_map.items():
                    nr, nc, edge = fn(i, j)
                    out_of_bounds = nr < 0 or nr >= rows or nc < 0 or nc >= cols
                    n_idx = nc + nr * cols if not out_of_bounds else -1
                    is_diff = out_of_bounds or (clustering[n_idx] != c_id)
                    if is_diff:
                        border_lines.append((pts[edge[0]], pts[edge[1]]))

    # Medoides de clusters para posicionar etiquetas centrales
    cluster_centroids = {}
    if show_cluster_labels and clustering:
        c_map: Dict[int, List[int]] = {}
        for idx, cid in enumerate(clustering):
            if cid == -1: continue
            c_map.setdefault(cid, []).append(idx)
        for cid, indices in c_map.items():
            avg_x = sum(coords[idx][0] for idx in indices) / len(indices)
            avg_y = sum(coords[idx][1] for idx in indices) / len(indices)
            best_idx = min(indices, key=lambda idx: (coords[idx][0] - avg_x)**2 + (coords[idx][1] - avg_y)**2)
            cluster_centroids[cid] = coords[best_idx]

    # Control de densidad de etiquetas (Regla de Legibilidad)
    # Si hay demasiadas etiquetas, priorizamos las más representativas para no saturar el mapa
    labels_to_render: List[Tuple[int, float, float, List[str]]] = []
    if mapped_labels:
        total_found = sum(len(docs) for docs in mapped_labels if docs)
        # Ordenamos las neuronas con más etiquetas primero si excede el máximo permitido
        neuron_indices = list(range(len(coords)))
        if total_found > max_total_labels:
            neuron_indices.sort(key=lambda idx: len(mapped_labels[idx]) if idx < len(mapped_labels) else 0, reverse=True)
        
        rendered_count = 0
        for idx in neuron_indices:
            docs = mapped_labels[idx] if idx < len(mapped_labels) else []
            if not docs: continue
            if rendered_count >= max_total_labels: break
            shown_docs = docs[:max_labels_per_neuron]
            xc, yc = coords[idx]
            labels_to_render.append((idx, xc, yc, shown_docs))
            rendered_count += len(shown_docs)

    svg_parts = [
        f'<svg id="{svg_id}" viewBox="{viewbox}" width="100%" height="100%" '
        'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" '
        'class="knomap-som-svg select-none" style="filter: drop-shadow(0 4px 6px rgba(0,0,0,0.4));">'
    ]
    svg_parts.append('<defs>')
    svg_parts.append('  <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto" markerUnits="strokeWidth">')
    svg_parts.append('    <path d="M 0,0 L 6,3 L 0,6 Z" fill="context-stroke" />')
    svg_parts.append('  </marker>')
    svg_parts.append('</defs>')
    
    # 1. Polígonos Hexagonales
    svg_parts.append('<g class="hex-cells">')
    for idx, (xc, yc) in enumerate(coords):
        color = cell_colors[idx] if idx < len(cell_colors) else "#4a5568"
        pts = get_hex_points(xc, yc)
        pts_str = " ".join(f"{px:.3f},{py:.3f}" for px, py in pts)
        svg_parts.append(
            f'  <polygon points="{pts_str}" fill="{color}" stroke="{cell_stroke_color}" '
            f'stroke-width="{cell_stroke_width:.4f}" opacity="0.95" data-idx="{idx}" class="som-hex-cell" />'
        )
    svg_parts.append('</g>')

    # 2. Fronteras Topológicas Negras
    if border_lines:
        svg_parts.append('<g class="cluster-frontiers" pointer-events="none">')
        for p1, p2 in border_lines:
            svg_parts.append(
                f'  <line x1="{p1[0]:.3f}" y1="{p1[1]:.3f}" x2="{p2[0]:.3f}" y2="{p2[1]:.3f}" '
                f'stroke="{boundary_stroke_color}" stroke-width="{boundary_stroke_width:.4f}" stroke-linecap="round" />'
            )
        svg_parts.append('</g>')

    # 3. Trayectorias Longitudinales Spline (Catmull-Rom)
    if trajectories:
        svg_parts.append('<g class="trajectories" pointer-events="none">')
        for traj_idx, traj in enumerate(trajectories):
            pts = [coords[p] for p in traj.get("points", []) if p < len(coords)]
            if len(pts) < 2: continue
            color = traj.get("color", ["#38bdf8", "#fbbf24", "#ec4899", "#a855f7", "#34d399"][traj_idx % 5])
            width = traj.get("width", 2)
            d_path = [f"M {pts[0][0]:.3f} {pts[0][1]:.3f}"]
            for i in range(len(pts) - 1):
                p0 = pts[i-1] if i > 0 else pts[i]
                p1 = pts[i]
                p2 = pts[i+1]
                p3 = pts[i+2] if i + 2 < len(pts) else p2
                cp1_x = p1[0] + (p2[0] - p0[0]) / 6.0
                cp1_y = p1[1] + (p2[1] - p0[1]) / 6.0
                cp2_x = p2[0] - (p3[0] - p1[0]) / 6.0
                cp2_y = p2[1] - (p3[1] - p1[1]) / 6.0
                d_path.append(f"C {cp1_x:.3f} {cp1_y:.3f}, {cp2_x:.3f} {cp2_y:.3f}, {p2[0]:.3f} {p2[1]:.3f}")
            svg_parts.append(
                f'  <path d="{" ".join(d_path)}" fill="none" stroke="{color}" '
                f'stroke-width="{width * 0.045:.3f}" stroke-linecap="round" stroke-linejoin="round" '
                f'marker-end="url(#arrowhead)" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.8));" />'
            )
            for pt in pts:
                svg_parts.append(
                    f'  <circle cx="{pt[0]:.3f}" cy="{pt[1]:.3f}" r="{width * 0.055:.3f}" '
                    f'fill="{color}" stroke="#000000" stroke-width="0.02" />'
                )
        svg_parts.append('</g>')

    # 4. Etiquetas de Documentos/Entidades Mapeadas (Legibilidad garantizada)
    if labels_to_render:
        svg_parts.append('<g class="cell-labels" pointer-events="none">')
        for idx, xc, yc, docs in labels_to_render:
            for l_idx, doc in enumerate(docs):
                offset_y = (l_idx - (len(docs) - 1) / 2.0) * 0.42
                clean_name = str(doc)[:16] + ("..." if len(str(doc)) > 16 else "")
                svg_parts.append(
                    f'  <text x="{xc:.3f}" y="{yc + offset_y:.3f}" text-anchor="middle" dominant-baseline="middle" '
                    f'fill="#ffffff" stroke="#050508" stroke-width="0.10" paint-order="stroke fill" '
                    f'font-size="0.36" font-weight="900" font-family="system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto">{clean_name}</text>'
                )
        svg_parts.append('</g>')

    # 5. Insignias / Centros de Clusters
    if cluster_centroids:
        svg_parts.append('<g class="cluster-badges" pointer-events="none">')
        for cid, (cx, cy) in cluster_centroids.items():
            name = cluster_labels.get(cid, f"CLUSTER {cid}") if cluster_labels else f"CLUSTER {cid}"
            svg_parts.append(
                f'  <text x="{cx:.3f}" y="{cy:.3f}" text-anchor="middle" dominant-baseline="middle" '
                f'fill="#ffffff" stroke="#000000" stroke-width="0.22" paint-order="stroke fill" '
                f'font-size="0.65" font-weight="900" font-family="system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto" '
                f'letter-spacing="0.06em">{name}</text>'
            )
        svg_parts.append('</g>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def generate_radar_chart_svg(
    indicators: List[str],
    cluster_profiles: List[Dict[str, Any]],
    selected_units: Optional[List[Dict[str, Any]]] = None,
    width: int = 460,
    height: int = 340
) -> str:
    """Genera el gráfico radar SVG idéntico al CLUSTER PROFILE RADAR de KnoMap."""
    cx = width / 2.0
    cy = height / 2.0 - 10
    radius = min(width, height) * 0.36
    num_axes = len(indicators)
    if num_axes < 3:
        return f'<svg width="{width}" height="{height}"><text x="{cx}" y="{cy}" fill="#fff">Mínimo 3 indicadores</text></svg>'

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'xmlns="http://www.w3.org/2000/svg" class="knomap-radar-svg select-none">'
    ]
    svg.append('<defs>')
    svg.append('  <radialGradient id="radar-bg" cx="50%" cy="50%" r="50%">')
    svg.append('    <stop offset="0%" stop-color="#1e293b" stop-opacity="0.3"/>')
    svg.append('    <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>')
    svg.append('  </radialGradient>')
    svg.append('</defs>')

    # Telaraña concéntrica
    angles = [i * 2.0 * math.pi / num_axes - math.pi / 2.0 for i in range(num_axes)]
    levels = [0.2, 0.4, 0.6, 0.8, 1.0]
    
    svg.append('<g class="radar-grid">')
    for lvl in levels:
        pts = [
            f"{cx + radius * lvl * math.cos(a):.2f},{cy + radius * lvl * math.sin(a):.2f}"
            for a in angles
        ]
        svg.append(f'  <polygon points="{" ".join(pts)}" fill="none" stroke="#334155" stroke-width="0.8" opacity="0.6" />')
    
    # Ejes radiales
    for i, a in enumerate(angles):
        x2 = cx + radius * math.cos(a)
        y2 = cy + radius * math.sin(a)
        svg.append(f'  <line x1="{cx:.2f}" y1="{cy:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#334155" stroke-width="0.8" opacity="0.7"/>')
        # Etiquetas de ejes
        label_dist = radius + 22
        lx = cx + label_dist * math.cos(a)
        ly = cy + label_dist * math.sin(a)
        align = "middle"
        if math.cos(a) > 0.3: align = "start"
        elif math.cos(a) < -0.3: align = "end"
        ind_label = indicators[i][:18]
        svg.append(
            f'  <text x="{lx:.2f}" y="{ly:.2f}" text-anchor="{align}" dominant-baseline="middle" '
            f'fill="#94a3b8" font-size="10" font-weight="600" font-family="system-ui, sans-serif">{ind_label}</text>'
        )
    svg.append('</g>')

    # Polígonos de Clusters
    svg.append('<g class="radar-polygons">')
    for profile in cluster_profiles:
        cid = profile.get("cluster_id", 0)
        c_color = get_cluster_color(cid)
        values = profile.get("normalized_values", [0.5] * num_axes)
        pts = []
        for i, val in enumerate(values):
            norm_val = max(0.05, min(1.0, float(val)))
            r_val = radius * norm_val
            a = angles[i]
            pts.append(f"{cx + r_val * math.cos(a):.2f},{cy + r_val * math.sin(a):.2f}")
        svg.append(
            f'  <polygon points="{" ".join(pts)}" fill="{c_color}" fill-opacity="0.30" '
            f'stroke="{c_color}" stroke-width="2.2" />'
        )
    
    # Trazas de unidades seleccionadas
    if selected_units:
        for unit_idx, unit in enumerate(selected_units[:3]):
            u_color = ["#38bdf8", "#fbbf24", "#a855f7"][unit_idx % 3]
            values = unit.get("normalized_values", [0.5] * num_axes)
            pts = []
            for i, val in enumerate(values):
                norm_val = max(0.05, min(1.0, float(val)))
                r_val = radius * norm_val
                a = angles[i]
                pts.append(f"{cx + r_val * math.cos(a):.2f},{cy + r_val * math.sin(a):.2f}")
            svg.append(
                f'  <polygon points="{" ".join(pts)}" fill="none" '
                f'stroke="{u_color}" stroke-width="1.8" stroke-dasharray="3,3" />'
            )
    svg.append('</g>')
    svg.append('</svg>')
    return "\n".join(svg)


def render_knomap_som_dashboard(
    som_state: Dict[str, Any],
    output_path: str,
    title: str = "KnoMap SOM Intelligence Dashboard",
    max_labels_per_neuron: int = 2,
    selected_trajectories: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Genera el Dashboard HTML completo con la interfaz oscura, controles y componentes
    exactamente como se ven en la aplicación oficial de KnoMap.
    """
    rows = som_state.get("rows", som_state.get("config", {}).get("rows", 10))
    cols = som_state.get("cols", som_state.get("config", {}).get("cols", 12))
    total_neurons = rows * cols
    
    weights = som_state.get("weights", [])
    umatrix = som_state.get("umatrix", [])
    clustering = som_state.get("clustering", [])
    frequencies = som_state.get("frequencies", [])
    mapped_labels = som_state.get("mapped_labels", [])
    indicators = som_state.get("indicators", [f"Var {i+1}" for i in range(len(weights[0]) if weights else 5)])
    trajectories = selected_trajectories or som_state.get("trajectories", [])

    # Asegurar arrays numéricos
    if isinstance(umatrix, list) and len(umatrix) > 0 and isinstance(umatrix[0], list):
        flat_u = [float(val) for row in umatrix for val in row]
    else:
        flat_u = [float(v) for v in umatrix] if umatrix else [0.5] * total_neurons

    # 1. Colores de la Malla de Clusters
    cluster_colors = [get_cluster_color(cid) for cid in clustering] if clustering else ["#4a5568"] * total_neurons
    svg_clusters = generate_hexagonal_som_svg(
        rows=rows,
        cols=cols,
        cell_colors=cluster_colors,
        clustering=clustering,
        cluster_labels=som_state.get("cluster_names"),
        mapped_labels=mapped_labels,
        trajectories=trajectories,
        max_labels_per_neuron=max_labels_per_neuron,
        show_cluster_labels=True,
        show_boundaries=True,
        svg_id="svg-cluster-map"
    )

    # 2. Generar Radar de Perfiles de Clusters
    cluster_profiles = []
    unique_clusters = sorted(list(set(c for c in clustering if c is not None and c != -1))) if clustering else [0]
    weights_np = np.array(weights) if weights else np.zeros((total_neurons, len(indicators)))
    
    # Normalización min-max por indicador para el radar [0.1, 0.95]
    ind_mins = weights_np.min(axis=0) if len(weights_np) > 0 else np.zeros(len(indicators))
    ind_maxs = weights_np.max(axis=0) if len(weights_np) > 0 else np.ones(len(indicators))
    ranges = ind_maxs - ind_mins
    ranges[ranges == 0] = 1.0

    for cid in unique_clusters:
        c_idxs = [i for i, c in enumerate(clustering) if c == cid]
        if c_idxs:
            centroid_raw = weights_np[c_idxs].mean(axis=0)
            norm_vals = 0.15 + 0.80 * (centroid_raw - ind_mins) / ranges
            cluster_profiles.append({
                "cluster_id": cid,
                "normalized_values": norm_vals.tolist(),
                "raw_values": centroid_raw.tolist()
            })

    # Unidades representativas para el radar
    sample_units = []
    all_mapped = []
    for idx, doc_list in enumerate(mapped_labels):
        for doc in doc_list:
            all_mapped.append((doc, idx))
    for doc, idx in all_mapped[:3]:
        raw_w = weights_np[idx] if idx < len(weights_np) else ind_mins
        sample_units.append({
            "name": doc,
            "normalized_values": (0.15 + 0.80 * (raw_w - ind_mins) / ranges).tolist()
        })

    svg_radar = generate_radar_chart_svg(
        indicators=indicators,
        cluster_profiles=cluster_profiles,
        selected_units=sample_units,
        width=480,
        height=320
    )

    # 3. Generar la Rejilla de Component Maps (2x3)
    component_cards = []
    for f_idx, ind_name in enumerate(indicators[:6]):
        comp_values = [weights[i][f_idx] for i in range(min(total_neurons, len(weights)))] if weights else [0.5]*total_neurons
        min_v = float(min(comp_values))
        max_v = float(max(comp_values))
        mean_v = float(sum(comp_values) / max(1, len(comp_values)))
        
        comp_colors = [get_component_color(v, min_v, max_v, mean_v) for v in comp_values]
        comp_svg = generate_hexagonal_som_svg(
            rows=rows,
            cols=cols,
            cell_colors=comp_colors,
            clustering=clustering,
            mapped_labels=None, # Limpio sin etiquetas para correlación visual clara
            show_cluster_labels=False,
            show_boundaries=True,
            cell_stroke_color="#1e293b",
            cell_stroke_width=0.015,
            boundary_stroke_color="rgba(0,0,0,0.75)",
            boundary_stroke_width=0.045,
            svg_id=f"svg-comp-{f_idx}"
        )
        component_cards.append({
            "name": ind_name.upper(),
            "min": min_v,
            "max": max_v,
            "mean": mean_v,
            "svg": comp_svg
        })

    # Template HTML completo estilo KnoMap Dark
    html_content = f"""<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-main: #07090e;
      --bg-card: #0d111d;
      --border-card: #1c2438;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-purple: #818cf8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg-main);
      color: var(--text-main);
      font-family: 'Outfit', sans-serif;
      padding: 24px;
      line-height: 1.5;
    }}
    .dashboard-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border-card);
    }}
    .header-title h1 {{
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #fff;
    }}
    .header-title p {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .badge-bar {{
      display: flex;
      gap: 12px;
    }}
    .stat-badge {{
      background: rgba(30, 41, 59, 0.6);
      border: 1px solid var(--border-card);
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
    }}
    .stat-badge span {{ color: var(--accent-blue); font-family: 'JetBrains Mono', monospace; }}

    /* Layout Superior: Split 2 Columnas */
    .top-split {{
      display: grid;
      grid-template-columns: 1.25fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }}
    .card {{
      background: var(--bg-card);
      border: 1px solid var(--border-card);
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    .card-header {{
      padding: 14px 20px;
      border-bottom: 1px solid var(--border-card);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(13, 17, 29, 0.8);
    }}
    .card-title {{
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #e2e8f0;
    }}
    .card-subtitle {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .controls-group {{
      display: flex;
      gap: 8px;
      align-items: center;
    }}
    .btn-ctrl {{
      background: #1e293b;
      border: 1px solid #334155;
      color: #cbd5e1;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
    }}
    .btn-ctrl:hover {{ background: #334155; color: #fff; }}

    .map-container {{
      padding: 20px;
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 380px;
      background: radial-gradient(circle at center, #0f172a 0%, #07090e 100%);
    }}

    /* Component Maps 2x3 Grid */
    .grid-section-header {{
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .grid-title {{
      font-size: 14px;
      font-weight: 800;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: #cbd5e1;
    }}
    .component-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
    }}
    @media (max-width: 1200px) {{
      .top-split {{ grid-template-columns: 1fr; }}
      .component-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    @media (max-width: 768px) {{
      .component-grid {{ grid-template-columns: 1fr; }}
    }}

    .comp-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-card);
      border-radius: 10px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .comp-header {{
      padding: 10px 16px;
      border-bottom: 1px solid var(--border-card);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .comp-title {{
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: #94a3b8;
    }}
    .comp-body {{
      display: flex;
      padding: 12px;
      background: #090c14;
      align-items: center;
      min-height: 220px;
    }}
    .comp-map {{ flex: 1; display: flex; justify-content: center; align-items: center; }}
    .colorbar {{
      width: 42px;
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-left: 8px;
    }}
    .color-gradient {{
      width: 10px;
      height: 120px;
      border-radius: 3px;
      background: linear-gradient(to bottom, #e53e3e, #ecc94b, #38a169);
      margin: 4px 0;
      border: 1px solid rgba(255,255,255,0.1);
    }}
    .cb-val {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 9px;
      color: #94a3b8;
      font-weight: 600;
    }}
    .cb-mean {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 8px;
      color: #ecc94b;
      font-weight: 700;
      text-align: center;
      line-height: 1.1;
    }}

    /* Tooltip */
    #som-tooltip {{
      position: fixed;
      display: none;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid #38bdf8;
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 11px;
      pointer-events: none;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.6);
      backdrop-filter: blur(8px);
    }}
  </style>
</head>
<body>
  <div class="dashboard-header">
    <div class="header-title">
      <h1>{title}</h1>
      <p>Representación geométrica vectorial oficial de KnoMap (Malla Hexagonal flat-topped, fronteras y paleta LabSOM)</p>
    </div>
    <div class="badge-bar">
      <div class="stat-badge">MALLA: <span>{rows}x{cols} ({total_neurons} neuronas)</span></div>
      <div class="stat-badge">CLUSTERS: <span>K={len(unique_clusters)}</span></div>
      <div class="stat-badge">MODO: <span>Hexagonal LabSOM</span></div>
    </div>
  </div>

  <!-- SECCIÓN SUPERIOR: CLUSTERING + RADAR -->
  <div class="top-split">
    <!-- Card Clusters -->
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">AGGLOMERATIVE CLUSTERS</div>
          <div class="card-subtitle">Partición de nodos de la malla basada en similitud multidimensional</div>
        </div>
        <div class="controls-group">
          <button class="btn-ctrl" onclick="toggleLabels()">🏷️ Labels</button>
          <button class="btn-ctrl" onclick="downloadSvg('svg-cluster-map', 'knomap_clusters.svg')">⬇ SVG</button>
        </div>
      </div>
      <div class="map-container">
        {svg_clusters}
      </div>
    </div>

    <!-- Card Radar -->
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">CLUSTER PROFILE RADAR</div>
          <div class="card-subtitle">Comparación de centroides de clusters vs. unidades representativas</div>
        </div>
      </div>
      <div class="map-container" style="padding: 10px;">
        {svg_radar}
      </div>
    </div>
  </div>

  <!-- SECCIÓN INFERIOR: COMPONENT MAPS GRID -->
  <div class="grid-section-header">
    <div class="grid-title">INDIVIDUAL VARIABLE COMPONENT MAPS (MALLA HEXAGONAL)</div>
    <div class="controls-group">
      <span style="font-size: 11px; color: #94a3b8; font-weight: 600;">PALETA: Standard (Green-Yellow-Red)</span>
    </div>
  </div>

  <div class="component-grid">
    {''.join(f'''
    <div class="comp-card">
      <div class="comp-header">
        <div class="comp-title">{c["name"]}</div>
      </div>
      <div class="comp-body">
        <div class="comp-map">
          {c["svg"]}
        </div>
        <div class="colorbar">
          <span class="cb-val">{c["max"]:.2f}</span>
          <div class="color-gradient"></div>
          <span class="cb-mean">MEAN<br>{c["mean"]:.2f}</span>
          <div class="color-gradient"></div>
          <span class="cb-val">{c["min"]:.2f}</span>
        </div>
      </div>
    </div>
    ''' for c in component_cards)}
  </div>

  <div id="som-tooltip"></div>

  <script>
    function toggleLabels() {{
      const labels = document.querySelectorAll('.cell-labels');
      labels.forEach(l => {{
        l.style.display = (l.style.display === 'none') ? 'block' : 'none';
      }});
    }}

    function downloadSvg(svgId, filename) {{
      const svg = document.getElementById(svgId);
      if (!svg) return;
      const serializer = new XMLSerializer();
      const source = serializer.serializeToString(svg);
      const blob = new Blob([source], {{ type: 'image/svg+xml;charset=utf-8' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}
  </script>
</body>
</html>
"""
    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return {
        "status": "success",
        "visual_artifact_path": output_path,
        "grid": f"{rows}x{cols}",
        "components_rendered": len(component_cards),
        "trajectories_rendered": len(trajectories),
        "summary": f"Dashboard SOM KnoMap con malla hexagonal ({rows}x{cols}), radar de clusters y {len(component_cards)} planos de componentes generado en {output_path}."
    }


def knomap_render_som_dashboard(
    som_state_path: str,
    output_path: str,
    title: str = "KnoMap SOM Intelligence Dashboard",
    max_labels_per_neuron: int = 2
) -> Dict[str, Any]:
    """
    Herramienta MCP para generar el Dashboard SOM interactivo con estética y geometría nativa de KnoMap.
    
    Args:
        som_state_path: Ruta al archivo JSON con el estado del SOM entrenado (debe contener weights, umatrix, clustering, etc.).
        output_path: Ruta del artefacto HTML de salida.
        title: Título descriptivo para la cabecera del dashboard.
        max_labels_per_neuron: Máximo de etiquetas de texto dibujadas por hexágono para legibilidad.
    """
    try:
        with open(som_state_path, "r", encoding="utf-8") as f:
            som_state = json.load(f)
        return render_knomap_som_dashboard(
            som_state=som_state,
            output_path=output_path,
            title=title,
            max_labels_per_neuron=max_labels_per_neuron
        )
    except Exception as e:
        import traceback
        return {"error": f"Error renderizando Dashboard SOM KnoMap: {str(e)}", "traceback": traceback.format_exc()}


# ==============================================================================
# EXISTING ENGINE VIZ EXTENSIONS WRAPPERS
# ==============================================================================

def knomap_render_alluvial_diagram(data_path: str, output_path: str) -> dict:
    """Genera un diagrama aluvial (Sankey) temporal de los frentes de investigación."""
    try:
        df = pd.DataFrame()
        return render_alluvial_diagram(df, output_path)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_dumbbell_chart(data_path: str, metric: str, output_path: str) -> dict:
    """Genera un Dumbbell chart para evidenciar brechas en indicadores cienciométricos."""
    try:
        df = pd.DataFrame()
        return render_dumbbell_chart(df, metric, output_path)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_connection_map(data_path: str, output_path: str) -> dict:
    """Genera un mapa geopolítico de conexiones transfronterizas de coautoría."""
    try:
        df = pd.DataFrame()
        return render_connection_map(df, output_path)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_exploration_dashboard(data_path: str, output_path: str) -> dict:
    """Genera un panel exploratorio (Profiler) para el Paso 1, con distribuciones y series temporales."""
    try:
        filename = os.path.basename(data_path)
        if data_path.lower().endswith('.xlsx') or data_path.lower().endswith('.xls'):
            df = pd.read_excel(data_path, engine='openpyxl')
        else:
            df = pd.read_csv(data_path)
        return render_exploration_dashboard(df, output_path, filename_hint=filename)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_umatrix_3d(som_state_path: str, output_path: str) -> dict:
    """Genera un mapa topológico interactivo 3D de la U-Matrix."""
    try:
        with open(som_state_path, 'r', encoding='utf-8') as f:
            som_state = json.load(f)
        return render_umatrix_3d(som_state, output_path)
    except Exception as e:
        return {"error": str(e)}

def knomap_render_component_planes(som_state_path: str, output_path: str) -> dict:
    """Genera múltiples mapas de calor (Component Planes) para analizar correlaciones entre indicadores."""
    try:
        with open(som_state_path, 'r', encoding='utf-8') as f:
            som_state = json.load(f)
        return render_component_planes(som_state, output_path)
    except Exception as e:
        return {"error": str(e)}
