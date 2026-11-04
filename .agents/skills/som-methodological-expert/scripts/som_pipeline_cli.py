#!/usr/bin/env python3
"""
SOM Methodological Expert CLI (som_pipeline_cli.py)
---------------------------------------------------
Flujo neurocomputacional Workspace-First para entrenar Mapas Autoorganizados de Kohonen (SOM)
sobre matrices multidimensionales [N x D] generadas por tlachia-metrics-engine,
tlachia-metrics-handler o scientometrics-incites-expert.

Características:
- Lee directamente archivos .parquet, .csv o .json del Workspace (ej. ./matrices/indicadores_som.parquet).
- Permite seleccionar cualquier subconjunto de dimensiones (--indicator-cols) o usar todas las columnas
  numéricas de indicadores disponibles sin truncar.
- Normalización Z-score / MinMax / Robust antes del entrenamiento.
- Dimensionamiento espectral SVD automático (Small SOM 5*sqrt(N) o Big SOM 10*N) o explícito (--rows, --cols).
- Meta-clustering jerárquico de Vesanto con selección automática de k por Silhouette Score (o --clusters k).
- Diagnóstico automático de Pares Comparables (misma BMU o neuronas adyacentes) y detección de la
  Paradoja FWCI vs. Average Percentile.
- Persistencia en ./reports/som_state.json y renderizado interactivo ./reports/som_dashboard.html.
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

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


def load_matrix_df(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo de matriz: {path}")
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
            for k in ("records", "entities", "data", "works"):
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
    elif method == "robust":
        med = np.median(X, axis=0)
        q75, q25 = np.percentile(X, [75, 25], axis=0)
        iqr = np.where((q75 - q25) == 0, 1.0, q75 - q25)
        return (X - med) / iqr
    else:  # zscore
        mean = X.mean(axis=0)
        std = X.std(axis=0)
        std = np.where(std < 1e-9, 1.0, std)
        return (X - mean) / std


def get_hex_neighbors(r: int, c: int, rows: int, cols: int) -> List[Tuple[int, int]]:
    """Vecindad hexagonal de orden 1 (flat-topped offset)."""
    if c % 2 == 0:
        deltas = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]
    else:
        deltas = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]
    out = []
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            out.append((nr, nc))
    return out


def main():
    parser = argparse.ArgumentParser(description="SOM Methodological Expert CLI - Entrenamiento y Diagnóstico SOM")
    parser.add_argument("--input", "-i", required=True, help="Ruta a la matriz de indicadores (.parquet, .csv, .json)")
    parser.add_argument("--entity-col", default=None, help="Columna de identidad de la entidad (default: auto)")
    parser.add_argument(
        "--indicator-cols",
        default=None,
        help="Lista opcional de indicadores separados por coma (si se omite, utiliza todos los indicadores numéricos de la matriz sin truncar)",
    )
    parser.add_argument("--norm", choices=["zscore", "minmax", "robust", "none"], default="zscore", help="Normalización (default: zscore)")
    parser.add_argument("--grid-type", choices=["small", "big"], default="small", help="Regla de dimensionamiento automático: small (5*sqrt(N)) o big (10*N)")
    parser.add_argument("--rows", type=int, default=None, help="Filas de la malla SOM (sobreescribe --grid-type)")
    parser.add_argument("--cols", type=int, default=None, help="Columnas de la malla SOM (sobreescribe --grid-type)")
    parser.add_argument("--iterations", type=int, default=200, help="Épocas de entrenamiento (default: 200)")
    parser.add_argument("--clusters", type=int, default=0, help="Número de clusters k (0 = selección óptima automática por Silhouette)")
    parser.add_argument("--title", default="KnoMap SOM Scientometric Dashboard", help="Título del dashboard HTML")
    parser.add_argument("--state-out", default="./reports/som_state.json", help="Ruta de salida del estado SOM (.json)")
    parser.add_argument("--html-out", default="./reports/som_dashboard.html", help="Ruta de salida del dashboard interactivo (.html)")
    parser.add_argument("--diagnosis-out", default="./reports/som_diagnosis.json", help="Ruta del diagnóstico cienciométrico (.json)")

    args = parser.parse_args()
    df = load_matrix_df(args.input)
    if df.empty:
        sys.stderr.write("Error: La matriz de entrada está vacía.\n")
        sys.exit(1)

    entity_col = args.entity_col or next(
        (c for c in df.columns if c.lower() in ("entity", "institution", "researcher", "author", "country", "name", "source")),
        df.columns[0],
    )
    labels = df[entity_col].astype(str).tolist()

    if args.indicator_cols:
        requested = [c.strip() for c in args.indicator_cols.split(",") if c.strip()]
        indicator_cols = [c for c in requested if c in df.columns]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            sys.stderr.write(f"[Aviso] Columnas solicitadas no encontradas en la matriz: {missing}\n")
    else:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        indicator_cols = [c for c in num_cols if c not in NON_INDICATOR_META_COLS and c.lower() not in NON_INDICATOR_META_COLS]

    if not indicator_cols:
        sys.stderr.write("Error: No se encontraron columnas numéricas de indicadores para entrenar el SOM.\n")
        sys.exit(1)

    raw_X = df[indicator_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).values
    norm_X = normalize_matrix(raw_X, method=args.norm)

    # Dimensionamiento espectral SVD
    suggestion = suggest_grid_size(norm_X.tolist())
    if args.rows and args.cols:
        rows, cols = args.rows, args.cols
    else:
        rec_key = "big_som_recommendation" if args.grid_type == "big" else "small_som_recommendation"
        rec = suggestion.get(rec_key, {"rows": 6, "cols": 6})
        rows, cols = int(rec.get("rows", 6)), int(rec.get("cols", 6))

    # Selección de k (automática por Silhouette entre k=3..min(8, rows*cols-1) o fija)
    state_out_abs = str(Path(args.state_out).resolve())
    Path(state_out_abs).parent.mkdir(parents=True, exist_ok=True)

    train_res = train_som(
        data=norm_X.tolist(),
        labels=labels,
        rows=rows,
        cols=cols,
        method="batch",
        init="pca",
        iterations=args.iterations,
        clustering_algorithm="hierarchical",
        n_clusters=args.clusters if args.clusters > 0 else 4,
        run_umap=True,
        output_state_path=state_out_abs,
        indicator_names=indicator_cols,
    )

    with open(state_out_abs, "r", encoding="utf-8") as f:
        som_state = json.load(f)

    best_k = args.clusters if args.clusters > 0 else 4
    best_sil = -1.0
    weights_list = som_state.get("weights", [])
    eval_res = evaluate_som_clusters(weights=weights_list, max_k=min(8, max(3, len(weights_list) // 3)))
    if args.clusters <= 0 and eval_res.get("status") == "success":
        best_k = int(eval_res.get("recommended_k") or 4)
        for ev in eval_res.get("evaluations", []):
            if ev.get("k") == best_k:
                best_sil = float(ev.get("silhouette", 0.0))
        rec_res = recluster_som(weights=weights_list, algorithm="hierarchical", n_clusters=best_k)
        if rec_res.get("status") == "success":
            som_state["clustering"] = rec_res.get("cluster_assignments", som_state.get("clustering", []))
    else:
        for ev in eval_res.get("evaluations", []):
            if ev.get("k") == best_k:
                best_sil = float(ev.get("silhouette", 0.0))
        rec_res = recluster_som(weights=weights_list, algorithm="hierarchical", n_clusters=best_k)
        if rec_res.get("status") == "success":
            som_state["clustering"] = rec_res.get("cluster_assignments", som_state.get("clustering", []))
    som_state["silhouette_score"] = round(best_sil, 4)
    som_state["n_clusters"] = best_k
    with open(state_out_abs, "w", encoding="utf-8") as f:
        json.dump(som_state, f, indent=2, ensure_ascii=False)

    # Renderizar Dashboard HTML
    html_out_abs = str(Path(args.html_out).resolve())
    Path(html_out_abs).parent.mkdir(parents=True, exist_ok=True)
    render_knomap_som_dashboard(som_state=som_state, output_path=html_out_abs, title=args.title)

    # Construir diagnóstico de Pares Comparables y Paradojas Métricas
    mapped_labels = som_state.get("mapped_labels", [])
    clustering = som_state.get("clustering", [])
    entity_bmu: Dict[str, Tuple[int, int, int]] = {}
    neuron_entities: Dict[int, List[str]] = {}
    for n_idx, ent_list in enumerate(mapped_labels):
        r, c = n_idx // cols, n_idx % cols
        neuron_entities[n_idx] = list(ent_list or [])
        for ent in (ent_list or []):
            entity_bmu[ent] = (n_idx, r, c)

    entity_diagnostics = []
    for idx_row, ent in enumerate(labels):
        n_idx, r, c = entity_bmu.get(ent, (0, 0, 0))
        cid = clustering[n_idx] if n_idx < len(clustering) else 0
        same_bmu_peers = [e for e in neuron_entities.get(n_idx, []) if e != ent]
        adj_peers = []
        for nr, nc in get_hex_neighbors(r, c, rows, cols):
            adj_idx = nr * cols + nc
            adj_peers.extend(neuron_entities.get(adj_idx, []))

        row_dict = df.iloc[idx_row].to_dict()
        fwci_val = float(row_dict.get("fwci_avg") or 0.0)
        perc_val = float(row_dict.get("avg_percentile") or 0.0)
        paradox_type = None
        if fwci_val >= 1.5 and 0 < perc_val < 55.0:
            paradox_type = "A_OUTLIER_INFLATION (High FWCI driven by outlier paper, moderate Average Percentile)"
        elif 0 < fwci_val < 1.1 and perc_val >= 65.0:
            paradox_type = "B_CONSISTENT_CONSOLIDATION (High Average Percentile across portfolio without extreme outlier)"

        entity_diagnostics.append({
            "entity": ent,
            "bmu_index": n_idx,
            "bmu_row": r,
            "bmu_col": c,
            "cluster_id": int(cid),
            "exact_bmu_peers": same_bmu_peers,
            "adjacent_topological_peers": adj_peers[:15],
            "paradox_diagnosis": paradox_type,
        })

    diagnosis = {
        "input_matrix": args.input,
        "n_entities": len(labels),
        "n_indicators": len(indicator_cols),
        "indicators_used": indicator_cols,
        "normalization": args.norm,
        "grid_shape": {"rows": rows, "cols": cols, "total_neurons": rows * cols, "topology": "hexagonal"},
        "quantization_error": train_res.get("quantization_error"),
        "clustering": {"algorithm": "vesanto_hierarchical", "n_clusters": best_k, "silhouette_score": round(best_sil, 4)},
        "artifacts": {
            "som_state_json": state_out_abs,
            "som_dashboard_html": html_out_abs,
        },
        "entities": entity_diagnostics,
    }

    diag_out_abs = str(Path(args.diagnosis_out).resolve())
    Path(diag_out_abs).parent.mkdir(parents=True, exist_ok=True)
    with open(diag_out_abs, "w", encoding="utf-8") as f:
        json.dump(diagnosis, f, indent=2, ensure_ascii=False)

    print(f"[SOM Methodological Expert] Entrenamiento exitoso ({rows}x{cols} neuronas, {len(indicator_cols)} dimensiones, k={best_k}, Silhouette={best_sil:.3f}).")
    print(f"  - Estado SOM: {state_out_abs}")
    print(f"  - Dashboard HTML: {html_out_abs}")
    print(f"  - Diagnóstico y Pares: {diag_out_abs}")


if __name__ == "__main__":
    main()
