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
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

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
    parser.add_argument("--rows", type=int, default=None, help="Filas de la malla SOM")
    parser.add_argument("--cols", type=int, default=None, help="Columnas de la malla SOM")
    parser.add_argument("--clusters", type=int, default=4, help="Número de clusters k (default: 4)")
    parser.add_argument("--title", default="KnoMap SOM Trajectory Intelligence Dashboard", help="Título del dashboard")
    parser.add_argument("--state-out", default="./reports/som_trajectory_state.json", help="Ruta de salida del estado SOM (.json)")
    parser.add_argument("--html-out", default="./reports/som_trajectories.html", help="Ruta del dashboard interactivo (.html)")
    parser.add_argument("--json-out", default="./reports/som_trajectories.json", help="Ruta del reporte analítico de trayectorias (.json)")

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
        rec = suggestion.get("small_som_recommendation", {"rows": 6, "cols": 6})
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

    report_payload = {
        "input_series": args.input,
        "focal_entities_count": len(focal_entities),
        "focal_entities": focal_entities,
        "indicators_used": indicator_cols,
        "grid_shape": {"rows": rows, "cols": cols, "total_neurons": rows * cols},
        "artifacts": {
            "som_state_json": state_out_abs,
            "som_trajectories_html": html_out_abs,
        },
        "trajectories": analytical_trajectories,
    }
    json_out_abs = str(Path(args.json_out).resolve())
    Path(json_out_abs).parent.mkdir(parents=True, exist_ok=True)
    with open(json_out_abs, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2, ensure_ascii=False)

    print(f"[SOM Trajectory Mapping] {len(viz_trajectories)} trayectorias trazadas en malla {rows}x{cols} ({len(indicator_cols)} dimensiones).")
    print(f"  - Dashboard HTML: {html_out_abs}")
    print(f"  - Reporte JSON:   {json_out_abs}")


if __name__ == "__main__":
    main()
