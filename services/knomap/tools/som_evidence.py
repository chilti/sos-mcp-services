"""
Shared Full Evidence-First helpers for SOM pipelines:
- Reproducible normalization (divmax, zscore, minmax, robust, none) with scale factor audit
- SVD spectral sizing audit
- Quantization Error (QE) and Topological Error (TE) on flat-topped hexagonal grids
- Complete clustering evaluation curve (K=2..max_k), local-max detection (K>2), and 300 DPI plot
- Detailed raw & normalized cluster statistical profiles + singular profiles
"""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .som_tools import evaluate_som_clusters


def get_hex_neighbors(r: int, c: int, rows: int, cols: int) -> List[Tuple[int, int]]:
    """Order-1 hexagonal neighborhood (flat-topped offset matching SOMSolver)."""
    if c % 2 == 0:
        deltas = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]
    else:
        deltas = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]
    out: List[Tuple[int, int]] = []
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            out.append((nr, nc))
    return out


def normalize_matrix_with_audit(
    raw_X: np.ndarray,
    indicator_cols: List[str],
    method: str = "divmax",
    raw_df_for_missing: Optional[pd.DataFrame] = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Normalize [N x D] numeric matrix and preserve raw stats and exact scale factors."""
    X_clean = np.nan_to_num(np.asarray(raw_X, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    n_rows, n_cols = X_clean.shape

    raw_stats: Dict[str, Dict[str, Any]] = {}
    scale_factors: Dict[str, Dict[str, float]] = {}

    for j, col_name in enumerate(indicator_cols):
        col = X_clean[:, j]
        missing_cnt = 0
        if raw_df_for_missing is not None and col_name in raw_df_for_missing.columns:
            missing_cnt = int(pd.to_numeric(raw_df_for_missing[col_name], errors="coerce").isna().sum())
        raw_stats[col_name] = {
            "min": round(float(np.min(col)), 6),
            "max": round(float(np.max(col)), 6),
            "mean": round(float(np.mean(col)), 6),
            "median": round(float(np.median(col)), 6),
            "std": round(float(np.std(col)), 6),
            "missing_count": missing_cnt,
            "zero_count": int(np.sum(col == 0.0)),
        }

    if method == "none":
        norm_X = X_clean.copy()
        for col_name in indicator_cols:
            scale_factors[col_name] = {"offset": 0.0, "divisor": 1.0}
    elif method == "divmax":
        mx = X_clean.max(axis=0)
        div = np.where(np.abs(mx) < 1e-12, 1.0, mx)
        norm_X = X_clean / div
        for j, col_name in enumerate(indicator_cols):
            scale_factors[col_name] = {"offset": 0.0, "divisor": round(float(div[j]), 8)}
    elif method == "minmax":
        mn = X_clean.min(axis=0)
        mx = X_clean.max(axis=0)
        rng = np.where((mx - mn) < 1e-12, 1.0, mx - mn)
        norm_X = (X_clean - mn) / rng
        for j, col_name in enumerate(indicator_cols):
            scale_factors[col_name] = {
                "min_offset": round(float(mn[j]), 8),
                "range_divisor": round(float(rng[j]), 8),
            }
    elif method == "robust":
        med = np.median(X_clean, axis=0)
        q75, q25 = np.percentile(X_clean, [75, 25], axis=0)
        iqr = np.where((q75 - q25) < 1e-12, 1.0, q75 - q25)
        norm_X = (X_clean - med) / iqr
        for j, col_name in enumerate(indicator_cols):
            scale_factors[col_name] = {
                "median_offset": round(float(med[j]), 8),
                "q25": round(float(q25[j]), 8),
                "q75": round(float(q75[j]), 8),
                "iqr_divisor": round(float(iqr[j]), 8),
            }
    else:  # zscore
        mean = X_clean.mean(axis=0)
        std = X_clean.std(axis=0)
        std_safe = np.where(std < 1e-12, 1.0, std)
        norm_X = (X_clean - mean) / std_safe
        for j, col_name in enumerate(indicator_cols):
            scale_factors[col_name] = {
                "mean_offset": round(float(mean[j]), 8),
                "std_divisor": round(float(std_safe[j]), 8),
            }

    audit = {
        "method": method,
        "n_rows": int(n_rows),
        "n_indicators": int(n_cols),
        "raw_statistics": raw_stats,
        "scale_factors": scale_factors,
    }
    return norm_X, audit


def build_svd_audit(
    data_norm: np.ndarray,
    suggestion: Dict[str, Any],
    grid_type: str,
    rows: int,
    cols: int,
    explicit_override: bool = False,
) -> Dict[str, Any]:
    """Capture full SVD singular values, aspect ratio, grid recommendations, and over-gridding."""
    n_samples = int(data_norm.shape[0]) if len(data_norm.shape) > 0 else 0
    singular_values = suggestion.get("singular_values") or []
    ratio = suggestion.get("spectral_aspect_ratio")
    if not singular_values and n_samples > 1:
        try:
            _, s, _ = np.linalg.svd(data_norm - np.mean(data_norm, axis=0), full_matrices=False)
            singular_values = [round(float(v), 6) for v in s[:2]]
            if len(s) > 1 and s[1] > 1e-9:
                ratio = round(float(min(5.0, max(0.2, s[0] / s[1]))), 4)
        except Exception:
            pass
    if ratio is None:
        ratio = round(cols / max(1, rows), 4)

    total_neurons = int(rows) * int(cols)
    return {
        "n_samples": n_samples,
        "singular_values": singular_values,
        "sigma_1": singular_values[0] if len(singular_values) >= 1 else None,
        "sigma_2": singular_values[1] if len(singular_values) >= 2 else None,
        "spectral_aspect_ratio": ratio,
        "small_som_recommendation": suggestion.get("small_som_recommendation"),
        "big_som_recommendation": suggestion.get("big_som_recommendation"),
        "grid_type_applied": "explicit_override" if explicit_override else grid_type,
        "final_rows": int(rows),
        "final_cols": int(cols),
        "total_neurons": total_neurons,
        "overgridding_ratio": round(total_neurons / max(1, n_samples), 3),
        "topology": "hexagonal",
    }


def compute_som_quality_metrics(
    data_norm: np.ndarray,
    weights: np.ndarray,
    rows: int,
    cols: int,
) -> Dict[str, Any]:
    """Compute Quantization Error (QE), Topological Error (TE), and 1st/2nd BMUs."""
    X = np.asarray(data_norm, dtype=float)
    W = np.asarray(weights, dtype=float)
    if X.size == 0 or W.size == 0:
        return {
            "mean_quantization_error": None,
            "median_quantization_error": None,
            "max_quantization_error": None,
            "topological_error": None,
            "topological_violations": 0,
            "total_samples": 0,
            "bmu_indices": [],
            "second_bmu_indices": [],
            "per_sample_qe": [],
        }

    # Squared distances -> Euclidean distances [N x M]
    diffs = X[:, None, :] - W[None, :, :]
    dists = np.linalg.norm(diffs, axis=2)
    order = np.argsort(dists, axis=1)
    bmu1 = order[:, 0].astype(int).tolist()
    bmu2 = (order[:, 1] if dists.shape[1] > 1 else order[:, 0]).astype(int).tolist()
    qe_vec = dists[np.arange(len(X)), bmu1].astype(float)

    violations = 0
    for idx1, idx2 in zip(bmu1, bmu2):
        r1, c1 = idx1 // cols, idx1 % cols
        r2, c2 = idx2 // cols, idx2 % cols
        neighbors = set(get_hex_neighbors(r1, c1, rows, cols))
        if (r2, c2) not in neighbors:
            violations += 1

    n_samples = len(X)
    te = violations / max(1, n_samples)
    return {
        "mean_quantization_error": round(float(np.mean(qe_vec)), 6),
        "median_quantization_error": round(float(np.median(qe_vec)), 6),
        "max_quantization_error": round(float(np.max(qe_vec)), 6),
        "topological_error": round(float(te), 6),
        "topological_violations": int(violations),
        "total_samples": int(n_samples),
        "bmu_indices": bmu1,
        "second_bmu_indices": bmu2,
        "per_sample_qe": [round(float(v), 6) for v in qe_vec],
    }


def evaluate_clustering_curve(
    weights: np.ndarray,
    max_k: int = 15,
    cluster_strategy: str = "global_max",
    min_clusters: int = 2,
    manual_k: int = 0,
    existing_evals: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Evaluate K=2..actual_max_k (Silhouette, Davies-Bouldin, Calinski-Harabasz),
    mark global max, local maxima (K > 2), and select K per strategy.
    """
    w_list = weights.tolist() if isinstance(weights, np.ndarray) else list(weights)
    n_neurons = len(w_list)
    actual_max_k = min(max(2, int(max_k)), max(2, n_neurons - 1))

    raw_evals = existing_evals
    if not raw_evals:
        eval_res = evaluate_som_clusters(weights=w_list, max_k=actual_max_k)
        raw_evals = eval_res.get("evaluations", []) if eval_res.get("status") == "success" else []

    if not raw_evals:
        return {
            "evaluations": [],
            "labels_by_k": {},
            "selected_k": manual_k if manual_k > 0 else 4,
            "selected_silhouette": 0.0,
            "global_max_k": None,
            "local_max_gt2_k": None,
            "strategy": cluster_strategy,
        }

    rows_sorted = sorted(raw_evals, key=lambda x: int(x.get("k", 0)))
    sil_by_k = {int(r["k"]): float(r.get("silhouette", 0.0)) for r in rows_sorted}
    ks = [int(r["k"]) for r in rows_sorted]
    global_max_k = max(ks, key=lambda k: sil_by_k[k])

    # Local maxima strictly for K > 2
    local_max_ks: List[int] = []
    for idx, k in enumerate(ks):
        if k <= 2:
            continue
        prev_sil = sil_by_k[ks[idx - 1]] if idx > 0 else -1e9
        next_sil = sil_by_k[ks[idx + 1]] if idx + 1 < len(ks) else -1e9
        if sil_by_k[k] >= prev_sil and (idx + 1 == len(ks) or sil_by_k[k] >= next_sil):
            local_max_ks.append(k)

    # Fallback if Silhouette decreases monotonically for K > 2: best K >= 3
    gt2_ks = [k for k in ks if k > 2]
    local_max_gt2_k = max(local_max_ks, key=lambda k: sil_by_k[k]) if local_max_ks else (
        max(gt2_ks, key=lambda k: sil_by_k[k]) if gt2_ks else global_max_k
    )

    if manual_k > 0:
        effective_strategy = "manual"
        selected_k = manual_k if manual_k in sil_by_k else min(ks, key=lambda k: abs(k - manual_k))
    elif cluster_strategy == "local_max_gt2" and gt2_ks:
        effective_strategy = "local_max_gt2"
        candidates = [k for k in local_max_ks if k >= max(3, min_clusters)]
        if not candidates:
            candidates = [k for k in ks if k >= max(3, min_clusters)] or gt2_ks
        selected_k = max(candidates, key=lambda k: sil_by_k[k])
    else:
        effective_strategy = "global_max"
        candidates = [k for k in ks if k >= max(2, min_clusters)] or ks
        selected_k = max(candidates, key=lambda k: sil_by_k[k])

    clean_evals: List[Dict[str, Any]] = []
    labels_by_k: Dict[str, List[int]] = {}
    for r in rows_sorted:
        k = int(r["k"])
        lbls = r.get("labels")
        if isinstance(lbls, list):
            labels_by_k[str(k)] = [int(v) for v in lbls]
        clean_evals.append({
            "k": k,
            "silhouette": round(float(r.get("silhouette", 0.0)), 6),
            "davies_bouldin": round(float(r.get("davies_bouldin", 0.0)), 6),
            "calinski_harabasz": round(float(r.get("calinski_harabasz", 0.0)), 4),
            "is_global_max_silhouette": (k == global_max_k),
            "is_local_max_silhouette": (k in local_max_ks) or (not local_max_ks and k == local_max_gt2_k and k > 2),
            "is_selected": (k == selected_k),
        })

    return {
        "evaluations": clean_evals,
        "labels_by_k": labels_by_k,
        "selected_k": int(selected_k),
        "selected_silhouette": round(sil_by_k.get(selected_k, 0.0), 6),
        "global_max_k": int(global_max_k),
        "local_max_gt2_k": int(local_max_gt2_k),
        "strategy": effective_strategy,
    }


def render_cluster_eval_figure(
    evaluations: List[Dict[str, Any]],
    out_path: str,
    lang: str = "en",
    dpi: int = 300,
) -> None:
    """Render 3-panel K-selection diagnostic plot (Silhouette, Davies-Bouldin, Calinski-Harabasz)."""
    if not evaluations:
        return

    ks = [int(r["k"]) for r in evaluations]
    sils = [float(r["silhouette"]) for r in evaluations]
    dbs = [float(r["davies_bouldin"]) for r in evaluations]
    chs = [float(r["calinski_harabasz"]) for r in evaluations]
    gmax_k = next((r["k"] for r in evaluations if r.get("is_global_max_silhouette")), None)
    lmax_k = next((r["k"] for r in evaluations if r.get("is_local_max_silhouette") and not r.get("is_global_max_silhouette")), None)
    sel_k = next((r["k"] for r in evaluations if r.get("is_selected")), None)

    is_es = (lang == "es")
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8), dpi=dpi, facecolor="white")

    panels = [
        (axes[0], sils, "Coeficiente Silhouette (↑ mejor)" if is_es else "Silhouette Score (↑ higher is better)", "#1d4ed8"),
        (axes[1], dbs, "Índice Davies-Bouldin (↓ mejor)" if is_es else "Davies-Bouldin Index (↓ lower is better)", "#b91c1c"),
        (axes[2], chs, "Índice Calinski-Harabasz (↑ mejor)" if is_es else "Calinski-Harabasz Index (↑ higher is better)", "#047857"),
    ]

    for ax, vals, ylabel, color in panels:
        ax.plot(ks, vals, marker="o", linewidth=2.0, markersize=5.5, color=color, zorder=3)
        if gmax_k is not None and gmax_k in ks:
            idx = ks.index(gmax_k)
            ax.axvline(gmax_k, color="#64748b", linestyle=":", linewidth=1.3, label=("Máx. global" if is_es else "Global max") + f" (K={gmax_k})")
            ax.scatter([gmax_k], [vals[idx]], s=90, facecolors="none", edgecolors="#0f172a", linewidths=2.0, zorder=5)
        if lmax_k is not None and lmax_k in ks:
            idx = ks.index(lmax_k)
            ax.axvline(lmax_k, color="#d97706", linestyle="--", linewidth=1.4, label=("Máx. local K>2" if is_es else "Local max K>2") + f" (K={lmax_k})")
            ax.scatter([lmax_k], [vals[idx]], s=95, marker="^", color="#d97706", zorder=5)
        if sel_k is not None and sel_k in ks:
            idx = ks.index(sel_k)
            ax.axvline(sel_k, color="#7c3aed", linestyle="-.", linewidth=1.6, label=("Seleccionado" if is_es else "Selected") + f" (K={sel_k})")
            ax.scatter([sel_k], [vals[idx]], s=110, marker="*", color="#7c3aed", zorder=6)

        ax.set_xlabel("K (clusters)", fontsize=10, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=9.5, fontweight="bold")
        ax.set_xticks(ks)
        ax.grid(alpha=0.28, linestyle="--")
        ax.legend(fontsize=7.8, loc="best", frameon=True)

    title = (
        "Evaluación Multi-Criterio de Partición Vesanto SOM (K = 2..Kmax)"
        if is_es else
        "Multi-Criteria Vesanto SOM Partition Evaluation (K = 2..Kmax)"
    )
    fig.suptitle(title, fontsize=12.5, fontweight="bold", color="#0f172a", y=1.02)
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def build_cluster_profiles(
    raw_X: np.ndarray,
    norm_X: np.ndarray,
    entity_labels: List[str],
    indicator_cols: List[str],
    bmu_indices: List[int],
    neuron_clusters: List[int],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Build statistical cluster profiles (raw and normalized mean/median/min/max)
    and detect singular profiles (|C_k| == 1).
    """
    raw_arr = np.asarray(raw_X, dtype=float)
    norm_arr = np.asarray(norm_X, dtype=float)

    cluster_indices: Dict[int, List[int]] = {}
    for row_idx, bmu in enumerate(bmu_indices):
        cid = int(neuron_clusters[bmu]) if bmu < len(neuron_clusters) else 0
        cluster_indices.setdefault(cid, []).append(row_idx)

    profiles: List[Dict[str, Any]] = []
    flat_rows: List[Dict[str, Any]] = []
    singular_profiles: List[Dict[str, Any]] = []

    for cid in sorted(cluster_indices.keys()):
        idxs = cluster_indices[cid]
        ents = [entity_labels[i] for i in idxs]
        is_sing = (len(ents) == 1)
        sub_raw = raw_arr[idxs]
        sub_norm = norm_arr[idxs]

        ind_stats: Dict[str, Dict[str, float]] = {}
        for j, ind in enumerate(indicator_cols):
            r_col = sub_raw[:, j]
            n_col = sub_norm[:, j]
            stats_obj = {
                "raw_mean": round(float(np.mean(r_col)), 4),
                "raw_median": round(float(np.median(r_col)), 4),
                "raw_min": round(float(np.min(r_col)), 4),
                "raw_max": round(float(np.max(r_col)), 4),
                "norm_mean": round(float(np.mean(n_col)), 4),
                "norm_median": round(float(np.median(n_col)), 4),
                "norm_min": round(float(np.min(n_col)), 4),
                "norm_max": round(float(np.max(n_col)), 4),
            }
            ind_stats[ind] = stats_obj
            flat_rows.append({
                "cluster_id": int(cid),
                "n_entities": len(ents),
                "is_singular": is_sing,
                "indicator": ind,
                **stats_obj,
                "entities": " | ".join(ents),
            })

        prof_entry = {
            "cluster_id": int(cid),
            "n_entities": len(ents),
            "is_singular": is_sing,
            "entities": ents,
            "indicators": ind_stats,
        }
        profiles.append(prof_entry)
        if is_sing:
            singular_profiles.append({"cluster_id": int(cid), "entity": ents[0]})

    return profiles, flat_rows, singular_profiles

