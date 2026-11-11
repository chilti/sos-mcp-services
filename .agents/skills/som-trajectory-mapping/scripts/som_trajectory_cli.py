#!/usr/bin/env python3
"""
SOM Trajectory Mapping CLI (som_trajectory_cli.py)
--------------------------------------------------
Mapeo de Trayectorias en el Espacio de Estados con Redes Autoorganizadas de Kohonen (SOM),
suavizado con Medias Móviles Centradas (CMA) e interpolación continua con Splines Cúbicos
(Jiménez-Andrade, Arencibia-Jorge & Carrillo-Calvet, 2025).

Características:
- Lee series longitudinales por entidad (.parquet, .csv, .json) desde el Workspace
  (ej. ./matrices/series_cma_som.parquet generado por tlachia_metrics_cli.py annual-series --level ... --cma-window 3).
- Aplica la restricción ergonómica de KnoMap de máximo 5 entidades simultáneas en visualización
  (--entities o --top-entities <= 5), mientras entrena el SOM sobre el universo completo de pares.
- Permite elegir cualquier subconjunto de indicadores (--indicator-cols) o usar todas las columnas
  numéricas de indicadores sin truncar.
- Detecta Puntos de Inflexión Temporal (saltos topológicos inter-cluster o velocidad máxima) y
  Fases de Maduración Comunitaria (% Top 10% >= 10.0%).
- Genera el dashboard interactivo con controles de trayectorias (./reports/som_trajectories.html)
  y el manifiesto analítico (./reports/som_trajectories.json).
"""

import os
import sys
import json
import math
import colorsys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch
import matplotlib.patheffects as pe

CURRENT_DIR = Path(__file__).resolve().parent
SOS_ROOT = CURRENT_DIR.parents[3]
if str(SOS_ROOT) not in sys.path:
    sys.path.insert(0, str(SOS_ROOT))

from services.knomap.tools.som_tools import suggest_grid_size, train_som, evaluate_som_clusters, recluster_som
from services.knomap.tools.viz_tools import render_knomap_som_dashboard

NON_INDICATOR_META_COLS = {
    "entity", "level", "country", "country_code", "is_global_south",
    "period", "start_year", "end_year", "year", "publication_year",
    "first_year", "last_year", "id", "ror", "orcid"
}

TRAJECTORY_PALETTE = ["#38bdf8", "#fbbf24", "#ec4899", "#a855f7", "#34d399"]


def load_series_df(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo de series: {path}")
    ext = p.suffix.lower()
    if ext == ".parquet":
        return pd.read_parquet(p)
    elif ext == ".csv":
        return pd.read_csv(p)
    elif ext == ".json":
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            return pd.DataFrame(raw)
        elif isinstance(raw, dict):
            for k in ("records", "series", "data"):
                if isinstance(raw.get(k), list):
                    return pd.DataFrame(raw[k])
        return pd.read_json(p)
    return pd.read_parquet(p)


def normalize_matrix(X: np.ndarray, method: str = "zscore") -> np.ndarray:
    X = np.nan_to_num(X.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
    if method == "none":
        return X
    elif method == "minmax":
        mn = X.min(axis=0)
        mx = X.max(axis=0)
        rng = np.where((mx - mn) == 0, 1.0, mx - mn)
        return (X - mn) / rng
    else:
        mean = X.mean(axis=0)
        std = X.std(axis=0)
        std = np.where(std < 1e-9, 1.0, std)
        return (X - mean) / std


INDICATOR_NAMES_ES = {
    "num_documents": "Volumen de Artículos (N)",
    "share_pct": "Participación (%)",
    "times_cited": "Citas Acumuladas",
    "cites_per_doc": "Citas por Artículo",
    "cited_docs": "Artículos Citados",
    "uncited_docs": "Artículos No Citados",
    "pct_docs_cited": "% Artículos Citados",
    "pct_uncited": "% Artículos No Citados",
    "h_index": "Índice H",
    "g_index": "Índice G",
    "m_index": "Índice M (H/Edad)",
    "i10_index": "Índice i10",
    "fwci_avg": "FWCI Promedio",
    "fwci_median": "FWCI Mediana",
    "avg_percentile": "Percentil Promedio",
    "top_10_pct_docs": "Artículos Top 10%",
    "pct_top_10": "% Artículos Top 10%",
    "top_1_pct_docs": "Artículos Top 1%",
    "pct_top_1": "% Artículos Top 1%",
    "oa_docs": "Artículos en Acceso Abierto",
    "pct_oa": "% Acceso Abierto",
    "pct_oa_total": "% Acceso Abierto Total",
    "pct_oa_diamond": "% OA Diamante",
    "pct_oa_gold": "% OA Dorada APC",
    "pct_oa_hybrid": "% OA Híbrida",
    "pct_oa_green": "% OA Verde",
    "pct_oa_bronze": "% OA Bronce",
    "pct_oa_closed": "% Acceso Cerrado",
    "apc_list_usd": "Gasto APC Lista (USD)",
    "estimated_apc_paid_usd": "Gasto APC Estimado (USD)",
    "avg_apc_per_doc_usd": "APC Promedio por Doc (USD)",
    "estimated_diamond_savings_usd": "Ahorro Estimado Diamante (USD)",
    "pct_international": "% Coautoría Internacional",
    "pct_domestic": "% Coautoría Nacional",
    "pct_global_south": "% Coautoría Sur Global",
    "pct_single_authored": "% Autoría Única",
    "avg_authors_per_doc": "Autores por Doc",
    "avg_countries_per_doc": "Países por Doc",
    "collaboration_index": "Índice de Colaboración",
    "active_years": "Años Activos"
}

INDICATOR_NAMES_EN = {
    "num_documents": "Documents Volume (N)",
    "share_pct": "Share (%)",
    "times_cited": "Times Cited",
    "cites_per_doc": "Citations per Doc",
    "cited_docs": "Cited Documents",
    "uncited_docs": "Uncited Documents",
    "pct_docs_cited": "% Cited Documents",
    "pct_uncited": "% Uncited Documents",
    "h_index": "H-Index",
    "g_index": "G-Index",
    "m_index": "M-Index (H/Years)",
    "i10_index": "i10-Index",
    "fwci_avg": "Average FWCI",
    "fwci_median": "Median FWCI",
    "avg_percentile": "Average Percentile",
    "top_10_pct_docs": "Top 10% Documents",
    "pct_top_10": "% Top 10% Documents",
    "top_1_pct_docs": "Top 1% Documents",
    "pct_top_1": "% Top 1% Documents",
    "oa_docs": "Open Access Documents",
    "pct_oa": "% Open Access",
    "pct_oa_total": "% Total Open Access",
    "pct_oa_diamond": "% Diamond OA",
    "pct_oa_gold": "% Gold APC OA",
    "pct_oa_hybrid": "% Hybrid OA",
    "pct_oa_green": "% Green OA",
    "pct_oa_bronze": "% Bronze OA",
    "pct_oa_closed": "% Closed Access",
    "apc_list_usd": "List APC Expenditure ($)",
    "estimated_apc_paid_usd": "Est. APC Paid ($)",
    "avg_apc_per_doc_usd": "Avg. APC per Doc ($)",
    "estimated_diamond_savings_usd": "Est. Diamond Savings ($)",
    "pct_international": "% International Collab.",
    "pct_domestic": "% Domestic Collab.",
    "pct_global_south": "% Global South Collab.",
    "pct_single_authored": "% Single-Authored",
    "avg_authors_per_doc": "Authors per Doc",
    "avg_countries_per_doc": "Countries per Doc",
    "collaboration_index": "Collaboration Index",
    "active_years": "Active Years"
}


def render_trajectory_publication_figures(
    som_state: Dict[str, Any],
    out_png_es: str,
    out_png_en: str,
    dpi: int = 300
):
    """
    Genera figuras estáticas limpias de alta resolución (300 DPI) para publicación científica:
    - Parte Superior: Mapa de Trayectorias Continuas (Splines) + Panel Lateral de Leyenda.
    - Parte Inferior: Rejilla completa de Mapas de Componentes (Component Planes) para todas
      las dimensiones con paleta LabSOM divergente (Verde -> Amarillo -> Rojo), preservando
      geometría isométrica estricta (set_aspect equal).
    """
    rows = int(som_state.get("rows", 6))
    cols = int(som_state.get("cols", 6))
    clustering = som_state.get("clustering", [0] * (rows * cols))
    trajectories = som_state.get("trajectories", [])
    weights = np.array(som_state.get("weights", []))
    indicators = som_state.get("indicators", [])
    n_ind = len(indicators)

    R = 1.0
    apotema = math.sqrt(3) / 2.0
    avanceX = 1.5 * R
    avanceY = 2.0 * apotema * R

    coords = []
    for i in range(rows):
        for j in range(cols):
            x = j * avanceX
            y = i * avanceY + (apotema if j % 2 != 0 else 0.0)
            coords.append((x, y))

    def get_hex_points(xc: float, yc: float) -> List[Tuple[float, float]]:
        return [
            (xc + R, yc),
            (xc + 0.5 * R, yc + apotema * R),
            (xc - 0.5 * R, yc + apotema * R),
            (xc - R, yc),
            (xc - 0.5 * R, yc - apotema * R),
            (xc + 0.5 * R, yc - apotema * R)
        ]

    def get_cluster_rgb(cid: int) -> Tuple[float, float, float]:
        if cid is None or cid == -1:
            return (0.18, 0.22, 0.28)
        hue = (int(cid) * 137.5) % 360
        r, g, b = colorsys.hls_to_rgb(hue / 360.0, 0.75, 0.65)
        return (r, g, b)

    # Fronteras de cluster
    border_lines = []
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
            cid = clustering[idx] if idx < len(clustering) else 0
            xc, yc = coords[idx]
            pts = get_hex_points(xc, yc)
            for k, fn in neighbors_map.items():
                nr, nc, edge = fn(i, j)
                out_of_bounds = nr < 0 or nr >= rows or nc < 0 or nc >= cols
                n_idx = nc + nr * cols if not out_of_bounds else -1
                is_diff = out_of_bounds or (clustering[n_idx] != cid if n_idx < len(clustering) else False)
                if is_diff:
                    border_lines.append((pts[edge[0]], pts[edge[1]]))

    min_x = min(c[0] for c in coords) - 1.5
    max_x = max(c[0] for c in coords) + 1.5
    min_y = min(c[1] for c in coords) - 1.5
    max_y = max(c[1] for c in coords) + 1.5
    aspect = (max_y - min_y) / (max_x - min_x) if (max_x - min_x) > 0 else 0.6

    # Colormap LabSOM
    cmap_comp = LinearSegmentedColormap.from_list("labsom_component", ["#38a169", "#ecc94b", "#e53e3e"])

    n_comp_cols = 5
    n_comp_rows = math.ceil(n_ind / n_comp_cols) if n_ind > 0 else 0

    fig_w = 16.0
    h_main = fig_w * aspect * 0.75
    h_per_comp_row = (fig_w / n_comp_cols) * aspect * 1.15
    fig_h = h_main + (n_comp_rows * h_per_comp_row) + (2.2 if n_comp_rows > 0 else 1.0)

    for lang, out_path in [("es", out_png_es), ("en", out_png_en)]:
        fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
        if n_comp_rows > 0:
            gs = fig.add_gridspec(2, 1, height_ratios=[h_main, n_comp_rows * h_per_comp_row], hspace=0.28)
            gs_top = gs[0].subgridspec(1, 2, width_ratios=[3.4, 1.2], wspace=0.08)
            gs_bottom = gs[1].subgridspec(n_comp_rows, n_comp_cols, hspace=0.38, wspace=0.12)
            ax = fig.add_subplot(gs_top[0, 0])
            ax_leg = fig.add_subplot(gs_top[0, 1])
        else:
            gs = fig.add_gridspec(1, 2, width_ratios=[3.4, 1.2], wspace=0.08)
            gs_bottom = None
            ax = fig.add_subplot(gs[0, 0])
            ax_leg = fig.add_subplot(gs[0, 1])

        ax_leg.set_xlim(0, 1)
        ax_leg.set_ylim(0, 1)
        ax_leg.axis("off")

        # Hexágonos de fondo con tinte suave de cluster
        patches = [Polygon(get_hex_points(xc, yc), closed=True) for xc, yc in coords]
        colors = [get_cluster_rgb(clustering[idx] if idx < len(clustering) else 0) for idx in range(len(coords))]
        p_coll = PatchCollection(patches, facecolors=colors, edgecolors="#cbd5e1", linewidths=0.5, alpha=0.50)
        ax.add_collection(p_coll)

        if border_lines:
            l_coll = LineCollection(border_lines, colors="#475569", linewidths=1.2, linestyle="--", alpha=0.7)
            ax.add_collection(l_coll)

        # Trazar splines Catmull-Rom para cada entidad
        legend_items = []
        for traj_idx, traj in enumerate(trajectories):
            pts_idx = traj.get("points", [])
            pts = [coords[p] for p in pts_idx if p < len(coords)]
            if len(pts) < 2:
                continue
            col = traj.get("color", TRAJECTORY_PALETTE[traj_idx % len(TRAJECTORY_PALETTE)])
            lbls = traj.get("labels", [])
            name = traj.get("name", f"Entity {traj_idx+1}")

            path_cmds = [MplPath.MOVETO]
            path_verts = [pts[0]]
            for i in range(len(pts) - 1):
                p0 = pts[i - 1] if i > 0 else pts[i]
                p1 = pts[i]
                p2 = pts[i + 1]
                p3 = pts[i + 2] if i + 2 < len(pts) else p2
                cp1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
                cp2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
                path_cmds.extend([MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])
                path_verts.extend([cp1, cp2, p2])

            mpl_path = MplPath(path_verts, path_cmds)
            patch = PathPatch(
                mpl_path, facecolor="none", edgecolor=col, linewidth=3.2, zorder=5,
                path_effects=[pe.withStroke(linewidth=5.5, foreground="#0f172a")]
            )
            ax.add_patch(patch)

            # Puntos y etiquetas temporales (sin recuadro oscuro, con contorno nítido)
            for pt_idx, (px, py) in enumerate(pts):
                is_end = (pt_idx == len(pts) - 1)
                is_start = (pt_idx == 0)
                r_pt = 0.20 if (is_start or is_end) else 0.11
                circle = Circle((px, py), r_pt, facecolor=col, edgecolor="white" if (is_start or is_end) else "#0f172a", linewidth=1.5, zorder=6)
                ax.add_patch(circle)
                # Etiquetas de año en puntos clave
                if lbls and pt_idx < len(lbls) and (is_start or is_end or pt_idx % 2 == 0):
                    y_off = -0.32 if pt_idx % 2 == 0 else 0.36
                    ax.text(
                        px, py + y_off, lbls[pt_idx],
                        color="white", fontsize=7.5, fontweight="bold", ha="center", va="center", zorder=7,
                        path_effects=[pe.withStroke(linewidth=2.5, foreground="#0f172a")]
                    )

            legend_items.append((name, col, lbls[0] if lbls else "", lbls[-1] if lbls else ""))

        title_str = (
            "Mapeo de Trayectorias Temporales (Splines) en el Espacio de Estados SOM"
            if lang == "es"
            else "Continuous State-Space Trajectory Mapping (Splines) on SOM Lattice"
        )
        ax.set_title(title_str, fontsize=12.5, fontweight="bold", pad=12, color="#0f172a")
        ax.set_aspect("equal")
        ax.set_xlim(min_x, max_x)
        ax.set_ylim(max_y, min_y)
        ax.axis("off")

        # Panel de leyenda lateral
        leg_title = "ENTIDADES FOCALES" if lang == "es" else "FOCAL ENTITIES"
        ax_leg.text(0.05, 0.95, leg_title, fontsize=10, fontweight="black", color="#0f172a", va="top")
        sub_title = "Trayectorias y Periodo" if lang == "es" else "Trajectories & Period"
        ax_leg.text(0.05, 0.91, sub_title, fontsize=8, color="#64748b", va="top")

        y_pos = 0.82
        for name, col, t_start, t_end in legend_items:
            ax_leg.plot([0.05, 0.18], [y_pos, y_pos], color=col, linewidth=3.5, solid_capstyle="round")
            ax_leg.plot(0.05, y_pos, marker="o", color=col, markeredgecolor="white", markersize=6)
            ax_leg.plot(0.18, y_pos, marker="o", color=col, markeredgecolor="white", markersize=6)
            clean_name = name[:26] + ("..." if len(name) > 26 else "")
            ax_leg.text(0.22, y_pos, clean_name, fontsize=8.2, fontweight="bold", color="#1e293b", va="center")
            period_str = f"{t_start} → {t_end}" if t_start and t_end else ""
            ax_leg.text(0.22, y_pos - 0.045, period_str, fontsize=7.2, color="#64748b", va="center")
            y_pos -= 0.14

        note_txt = (
            "● Punto inicial / ■ Punto final\nLíneas: Spline Cúbico Catmull-Rom\nFondo: Agrupamiento Vesanto"
            if lang == "es"
            else "● Start point / ■ End point\nLines: Catmull-Rom Cubic Spline\nBackground: Vesanto Clusters"
        )
        ax_leg.text(0.05, 0.10, note_txt, fontsize=7.2, color="#475569", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#f8fafc", edgecolor="#e2e8f0"))

        # Panel Inferior: Rejilla de Mapas de Componentes (Component Planes)
        if n_ind > 0 and len(weights) > 0 and gs_bottom is not None:
            for d_idx, ind_name in enumerate(indicators):
                r_sub = d_idx // n_comp_cols
                c_sub = d_idx % n_comp_cols
                ax_sub = fig.add_subplot(gs_bottom[r_sub, c_sub])

                w_col = weights[:, d_idx] if d_idx < weights.shape[1] else np.zeros(len(coords))
                patches_sub = [Polygon(get_hex_points(xc, yc), closed=True) for xc, yc in coords]
                norm_sub = plt.Normalize(vmin=float(np.min(w_col)), vmax=float(np.max(w_col)))
                p_sub = PatchCollection(patches_sub, cmap=cmap_comp, norm=norm_sub, edgecolors="#334155", linewidths=0.15, alpha=0.95)
                p_sub.set_array(w_col)
                ax_sub.add_collection(p_sub)

                if border_lines:
                    l_sub = LineCollection(border_lines, colors="#000000", linewidths=0.55, alpha=0.55, zorder=4)
                    ax_sub.add_collection(l_sub)

                # Aspect ratio isométrico estricto
                ax_sub.set_aspect("equal")
                ax_sub.set_xlim(min_x, max_x)
                ax_sub.set_ylim(max_y, min_y)
                ax_sub.axis("off")

                name_dict = INDICATOR_NAMES_ES if lang == "es" else INDICATOR_NAMES_EN
                clean_name = name_dict.get(ind_name, ind_name.replace("_", " ").title())
                ax_sub.set_title(clean_name, fontsize=7.2, fontweight="bold", pad=3.5, color="#1e293b")

            # Celdas vacías sobrantes
            total_grid_cells = n_comp_rows * n_comp_cols
            for empty_idx in range(n_ind, total_grid_cells):
                r_sub = empty_idx // n_comp_cols
                c_sub = empty_idx % n_comp_cols
                ax_empty = fig.add_subplot(gs_bottom[r_sub, c_sub])
                ax_empty.axis("off")

        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="SOM Trajectory Mapping CLI - Trayectorias Continuas sobre SOM")
    parser.add_argument("--input", "-i", required=True, help="Ruta a la matriz de series longitudinales (.parquet, .csv, .json)")
    parser.add_argument("--entity-col", default=None, help="Columna de entidad (default: entity)")
    parser.add_argument("--time-col", default=None, help="Columna temporal (default: year o period)")
    parser.add_argument(
        "--indicator-cols",
        default=None,
        help="Lista opcional de indicadores separados por coma (por defecto utiliza todos los indicadores numéricos sin truncar)",
    )
    parser.add_argument("--entities", default=None, help="Entidades focales separadas por coma para trazar trayectorias (máx. 5)")
    parser.add_argument("--top-entities", type=int, default=5, help="Número de entidades principales a trazar si no se especifica --entities (máx. 5)")
    parser.add_argument("--cma-window", type=int, default=0, help="Aplicar Media Móvil Centrada adicional si la entrada aún no está suavizada (ej. 3)")
    parser.add_argument(
        "--grid-type",
        choices=["small", "big"],
        default="big",
        help="Regla de dimensionamiento automático: big (10*N, estándar en KnoMap/cienciometría) o small (5*sqrt(N))",
    )
    parser.add_argument("--rows", type=int, default=None, help="Filas de la malla SOM (sobreescribe --grid-type)")
    parser.add_argument("--cols", type=int, default=None, help="Columnas de la malla SOM (sobreescribe --grid-type)")
    parser.add_argument("--clusters", type=int, default=4, help="Número de clusters k (default: 4)")
    parser.add_argument("--title", default="KnoMap SOM Trajectory Intelligence Dashboard", help="Título del dashboard")
    parser.add_argument("--state-out", default="./reports/som_trajectory_state.json", help="Ruta de salida del estado SOM (.json)")
    parser.add_argument("--html-out", default="./reports/som_trajectories.html", help="Ruta del dashboard interactivo (.html)")
    parser.add_argument("--json-out", default="./reports/som_trajectories.json", help="Ruta del reporte analítico de trayectorias (.json)")
    parser.add_argument("--png-es", default="./reports/som_trajectories_es.png", help="Ruta PNG de trayectorias en español (300 DPI)")
    parser.add_argument("--png-en", default="./reports/som_trajectories_en.png", help="Ruta PNG de trayectorias en inglés (300 DPI)")
    parser.add_argument("--dpi", type=int, default=300, help="Resolución DPI para publicación (default: 300)")

    args = parser.parse_args()
    df = load_series_df(args.input)
    if df.empty:
        sys.stderr.write("Error: El archivo de series longitudinales está vacío.\n")
        sys.exit(1)

    entity_col = args.entity_col or next((c for c in df.columns if c.lower() in ("entity", "institution", "researcher", "author", "country")), df.columns[0])
    time_col = args.time_col or next((c for c in df.columns if c.lower() in ("year", "period", "publication_year")), df.columns[1])

    if args.indicator_cols:
        requested = [c.strip() for c in args.indicator_cols.split(",") if c.strip()]
        indicator_cols = [c for c in requested if c in df.columns]
    else:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        indicator_cols = [c for c in num_cols if c not in NON_INDICATOR_META_COLS and c.lower() not in NON_INDICATOR_META_COLS and c not in (entity_col, time_col)]

    if not indicator_cols:
        sys.stderr.write("Error: No se encontraron columnas numéricas de indicadores.\n")
        sys.exit(1)

    df = df.sort_values(by=[entity_col, time_col]).reset_index(drop=True)
    if args.cma_window and args.cma_window > 1:
        for col in indicator_cols:
            df[col] = (
                df.groupby(entity_col)[col]
                .transform(lambda s: pd.to_numeric(s, errors="coerce").rolling(window=args.cma_window, center=True, min_periods=1).mean())
                .fillna(0.0)
            )

    # Seleccionar hasta 5 entidades focales (límite cognitivo de KnoMap)
    if args.entities:
        focal_entities = [e.strip() for e in args.entities.split(",") if e.strip()][:5]
    else:
        k_top = min(5, max(1, args.top_entities))
        if "num_documents" in df.columns:
            vol_s = df.groupby(entity_col)["num_documents"].sum().sort_values(ascending=False)
            focal_entities = vol_s.head(k_top).index.tolist()
        else:
            focal_entities = df[entity_col].unique()[:k_top].tolist()

    # Etiquetas de fila (Entity @ Time) para entrenar el espacio de estados conjunto
    row_labels = [f"{r[entity_col]} ({r[time_col]})" for _, r in df.iterrows()]
    raw_X = df[indicator_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).values
    norm_X = normalize_matrix(raw_X, method="zscore")

    suggestion = suggest_grid_size(norm_X.tolist())
    if args.rows and args.cols:
        rows, cols = args.rows, args.cols
    else:
        rec_key = "big_som_recommendation" if args.grid_type == "big" else "small_som_recommendation"
        rec = suggestion.get(rec_key, {"rows": 6, "cols": 6})
        rows, cols = int(rec.get("rows", 6)), int(rec.get("cols", 6))

    state_out_abs = str(Path(args.state_out).resolve())
    Path(state_out_abs).parent.mkdir(parents=True, exist_ok=True)

    train_som(
        data=norm_X.tolist(),
        labels=row_labels,
        rows=rows,
        cols=cols,
        method="batch",
        init="pca",
        iterations=200,
        clustering_algorithm="hierarchical",
        n_clusters=args.clusters,
        run_umap=True,
        output_state_path=state_out_abs,
        indicator_names=indicator_cols,
    )

    with open(state_out_abs, "r", encoding="utf-8") as f:
        som_state = json.load(f)

    weights_np = np.array(som_state.get("weights", []))
    clustering = som_state.get("clustering", [0] * (rows * cols))

    # Calcular BMU exacto para cada fila (entidad, tiempo)
    bmu_indices = []
    for x_vec in norm_X:
        dists = np.linalg.norm(weights_np - x_vec, axis=1)
        bmu_indices.append(int(np.argmin(dists)))
    df["_bmu_idx"] = bmu_indices
    df["_cluster_id"] = [int(clustering[b]) if b < len(clustering) else 0 for b in bmu_indices]

    # Construir objetos de trayectoria y diagnóstico de inflexión / maduración
    viz_trajectories = []
    analytical_trajectories = []

    for idx_e, ent in enumerate(focal_entities):
        sub = df[df[entity_col] == ent].sort_values(by=time_col).reset_index(drop=True)
        if sub.empty:
            continue
        pts = sub["_bmu_idx"].tolist()
        t_labels = [str(t) for t in sub[time_col].tolist()]
        clusters_seq = sub["_cluster_id"].tolist()
        short_id = ent[:18].replace(" ", "_")
        color = TRAJECTORY_PALETTE[idx_e % len(TRAJECTORY_PALETTE)]

        viz_trajectories.append({
            "id": short_id,
            "country": short_id,
            "name": ent,
            "points": pts,
            "labels": t_labels,
            "color": color,
            "width": 2.2,
        })

        # Detectar puntos de inflexión (transiciones de cluster o saltos topológicos máximos)
        inflection_points = []
        for step_i in range(1, len(pts)):
            r1, c1 = pts[step_i - 1] // cols, pts[step_i - 1] % cols
            r2, c2 = pts[step_i] // cols, pts[step_i] % cols
            step_dist = math.hypot(r2 - r1, c2 - c1)
            cluster_changed = clusters_seq[step_i] != clusters_seq[step_i - 1]
            if cluster_changed or step_dist >= 2.0:
                inflection_points.append({
                    "from_time": t_labels[step_i - 1],
                    "to_time": t_labels[step_i],
                    "from_bmu": [r1, c1],
                    "to_bmu": [r2, c2],
                    "from_cluster": clusters_seq[step_i - 1],
                    "to_cluster": clusters_seq[step_i],
                    "lattice_step_distance": round(step_dist, 3),
                    "regime_shift": cluster_changed,
                })

        # Fase de maduración comunitaria (% Top 10% >= 10%)
        maturation_years = []
        if "pct_top_10" in sub.columns:
            for _, srow in sub.iterrows():
                if float(srow.get("pct_top_10") or 0.0) >= 10.0:
                    maturation_years.append(str(srow[time_col]))

        analytical_trajectories.append({
            "entity": ent,
            "color": color,
            "time_steps": t_labels,
            "bmu_sequence": [[b // cols, b % cols] for b in pts],
            "cluster_sequence": clusters_seq,
            "inflection_points": inflection_points,
            "community_maturation_steps_top10_ge_10pct": maturation_years,
        })

    som_state["trajectories"] = viz_trajectories
    with open(state_out_abs, "w", encoding="utf-8") as f:
        json.dump(som_state, f, indent=2, ensure_ascii=False)

    html_out_abs = str(Path(args.html_out).resolve())
    Path(html_out_abs).parent.mkdir(parents=True, exist_ok=True)
    render_knomap_som_dashboard(
        som_state=som_state,
        output_path=html_out_abs,
        title=args.title,
        selected_trajectories=viz_trajectories,
    )

    # Generar Figuras Estáticas para Publicación Científica (300 DPI, ES y EN)
    png_es_abs = str(Path(args.png_es).resolve())
    png_en_abs = str(Path(args.png_en).resolve())
    render_trajectory_publication_figures(
        som_state=som_state,
        out_png_es=png_es_abs,
        out_png_en=png_en_abs,
        dpi=args.dpi
    )

    report_payload = {
        "input_series": args.input,
        "focal_entities_count": len(focal_entities),
        "focal_entities": focal_entities,
        "indicators_used": indicator_cols,
        "grid_shape": {"rows": rows, "cols": cols, "total_neurons": rows * cols},
        "artifacts": {
            "som_state_json": state_out_abs,
            "som_trajectories_html": html_out_abs,
            "som_trajectories_es_png": png_es_abs,
            "som_trajectories_en_png": png_en_abs,
        },
        "trajectories": analytical_trajectories,
    }
    json_out_abs = str(Path(args.json_out).resolve())
    Path(json_out_abs).parent.mkdir(parents=True, exist_ok=True)
    with open(json_out_abs, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2, ensure_ascii=False)

    print(f"[SOM Trajectory Mapping] {len(viz_trajectories)} trayectorias trazadas en malla {rows}x{cols} ({len(indicator_cols)} dimensiones).")
    print(f"  - Dashboard HTML: {html_out_abs}")
    print(f"  - Trayectorias ES (300 DPI): {png_es_abs}")
    print(f"  - Trayectorias EN (300 DPI): {png_en_abs}")
    print(f"  - Reporte JSON:   {json_out_abs}")


if __name__ == "__main__":
    main()
