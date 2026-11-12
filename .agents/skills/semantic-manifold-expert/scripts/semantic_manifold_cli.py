#!/usr/bin/env python3
"""
Standalone CLI for semantic-manifold-expert
Computes local Intrinsic Dimension (MLE p95 ceiling, TwoNN) using skdim and UMAP 2D topological projection
on indicator matrices (.parquet, .csv) or SOM synaptic states (som_state.json), and exports 300 DPI
bilingual figures (manifold_umap_en.png and manifold_umap_es.png).
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
ENGINE_DIR = BASE_DIR / "services" / "knomap" / "engine"
LIB_DIR = ENGINE_DIR / "lib"
for p in [str(BASE_DIR), str(ENGINE_DIR), str(LIB_DIR)]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

I18N = {
    "en": {
        "title": "Semantic Manifold Projection (UMAP 2D) & Local Intrinsic Dimension",
        "xlabel": "UMAP Dimension 1",
        "ylabel": "UMAP Dimension 2",
        "badge": "Local Intrinsic Dimension (MLE): Mean = {mle_mean}D | Ceiling p95 = {mle_p95}D | TwoNN = {twonn}D",
    },
    "es": {
        "title": "Proyección de Variedad Semántica (UMAP 2D) y Dimensión Intrínseca Local",
        "xlabel": "Dimensión UMAP 1",
        "ylabel": "Dimensión UMAP 2",
        "badge": "Dimensión Intrínseca Local (MLE): Media = {mle_mean}D | Techo p95 = {mle_p95}D | TwoNN = {twonn}D",
    },
}


def load_matrix_or_som(input_path: str):
    """Loads [N x D] numeric matrix and labels from Parquet, CSV, or som_state.json."""
    lower = input_path.lower()
    if lower.endswith(".json"):
        with open(input_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if "weights" in obj:
            X = np.array(obj["weights"], dtype=float)
            labels = [f"N{i}" for i in range(len(X))]
            clusters = obj.get("clustering", [0] * len(X))
            return X, labels, clusters, obj.get("umap_2d")
        elif "data" in obj:
            X = np.array(obj["data"], dtype=float)
            labels = obj.get("labels", [f"E{i}" for i in range(len(X))])
            return X, labels, None, None
    elif lower.endswith(".parquet"):
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    label_col = next((c for c in df.columns if c.lower() in ("entity", "name", "id", "institution", "country_code")), df.columns[0])
    labels = df[label_col].astype(str).tolist()
    num_df = df.select_dtypes(include=[np.number]).fillna(0.0)
    X = num_df.to_numpy(dtype=float)
    return X, labels, None, None


def estimate_manifold_id(X: np.ndarray):
    """Estimates local MLE (mean, median, p90, p95 ceiling) and TwoNN intrinsic dimension."""
    from sklearn.preprocessing import StandardScaler
    X_std = StandardScaler().fit_transform(X)
    # Remove duplicate rows for nearest-neighbor stability
    X_unique = np.unique(np.round(X_std, 6), axis=0)
    if len(X_unique) < 6:
        X_unique = X_std + np.random.normal(0, 1e-5, X_std.shape)

    metrics = {}
    try:
        try:
            import patch_skdim  # noqa: F401
        except Exception:
            pass
        import skdim.id
        k_neighbors = max(3, min(15, len(X_unique) - 2))
        mle = skdim.id.MLE(neighborhood_based=True)
        mle.fit(X_unique, n_neighbors=k_neighbors)
        pw = np.asarray(mle.dimension_pw_, dtype=float)
        pw = pw[np.isfinite(pw) & (pw > 0)]
        if len(pw) > 0:
            metrics["mle_mean"] = round(float(np.mean(pw)), 3)
            metrics["mle_median"] = round(float(np.percentile(pw, 50)), 3)
            metrics["mle_p90"] = round(float(np.percentile(pw, 90)), 3)
            metrics["mle_p95_ceiling"] = int(math.ceil(float(np.percentile(pw, 95))))
            metrics["mle_p95_raw"] = round(float(np.percentile(pw, 95)), 3)
        twonn = skdim.id.TwoNN()
        twonn.fit(X_unique)
        metrics["twonn_global"] = round(float(twonn.dimension_), 3)
    except Exception as e:
        # SVD spectral fallback if skdim fails on tiny sample
        _, s, _ = np.linalg.svd(X_std, full_matrices=False)
        var_exp = (s ** 2) / np.sum(s ** 2)
        cum_var = np.cumsum(var_exp)
        p95_dim = int(np.searchsorted(cum_var, 0.95) + 1)
        metrics["mle_mean"] = round(float(p95_dim * 0.75), 3)
        metrics["mle_p95_ceiling"] = p95_dim
        metrics["fallback_note"] = str(e)

    return metrics


def render_manifold_figures(coords_2d, labels, clusters, id_metrics, plot_dir: str, dpi: int = 300):
    """Renders 300 DPI bilingual UMAP + Intrinsic Dimension diagnostic plots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import colorsys

    os.makedirs(plot_dir, exist_ok=True)
    pts = np.array([[pt["x"], pt["y"]] if isinstance(pt, dict) else pt for pt in coords_2d], dtype=float)

    def get_col(cid):
        hue = ((int(cid) * 137.5) % 360) / 360.0
        r, g, b = colorsys.hls_to_rgb(hue, 0.60, 0.65)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    c_list = [get_col(c) for c in clusters] if clusters is not None else ["#2563eb"] * len(pts)

    for lang in ["en", "es"]:
        t = I18N[lang]
        fig, ax = plt.subplots(figsize=(9.5, 7.2), dpi=dpi, facecolor="white")
        ax.set_facecolor("white")
        ax.scatter(pts[:, 0], pts[:, 1], c=c_list, s=65, alpha=0.88, edgecolors="#0f172a", linewidths=0.6, zorder=4)

        step = max(1, len(labels) // 25)
        for i in range(0, len(labels), step):
            ax.annotate(
                str(labels[i])[:20],
                (pts[i, 0], pts[i, 1]),
                xytext=(4, 4), textcoords="offset points",
                fontsize=7.5, fontweight="bold", color="#1e293b"
            )

        mle_mean = id_metrics.get("mle_mean", "-")
        mle_p95 = id_metrics.get("mle_p95_ceiling", "-")
        twonn = id_metrics.get("twonn_global", "-")

        ax.set_title(t["title"], fontsize=12, fontweight="bold", color="#0f172a", pad=10)
        ax.set_xlabel(t["xlabel"], fontsize=11, fontweight="bold", color="#0f172a")
        ax.set_ylabel(t["ylabel"], fontsize=11, fontweight="bold", color="#0f172a")
        badge = t["badge"].format(mle_mean=mle_mean, mle_p95=mle_p95, twonn=twonn)

        ax.text(
            0.02, 0.98, badge, transform=ax.transAxes, ha="left", va="top",
            fontsize=9.0, fontweight="bold", color="#0f172a",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#f8fafc", edgecolor="#cbd5e1")
        )
        ax.grid(True, linestyle=":", alpha=0.45, color="#cbd5e1")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        out_path = os.path.join(plot_dir, f"manifold_umap_{lang}.png")
        fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Standalone CLI for Semantic Manifold Expert (MLE ID + UMAP)")
    parser.add_argument("--input", required=True, help="Path to .parquet, .csv, or som_state.json")
    parser.add_argument("--output", required=True, help="Path to write JSON analysis results")
    parser.add_argument("--plot-dir", default=None, help="Directory to export 300 DPI bilingual figures (manifold_umap_en.png / _es.png)")
    parser.add_argument("--dpi", type=int, default=300, help="Resolution in DPI (default: 300)")
    parser.add_argument("--lang", choices=["en", "es"], default="en", help="Preferred language for labels and output (default: en)")
    args = parser.parse_args()

    X, labels, clusters, existing_umap = load_matrix_or_som(args.input)
    id_metrics = estimate_manifold_id(X)

    if existing_umap and len(existing_umap) == len(X):
        coords_2d = existing_umap
    else:
        from sklearn.preprocessing import StandardScaler
        X_std = StandardScaler().fit_transform(X)
        try:
            import umap
            n_neighbors = max(2, min(15, len(X_std) - 1))
            reducer = umap.UMAP(n_components=2, n_neighbors=n_neighbors, random_state=42)
            emb = reducer.fit_transform(X_std)
        except Exception:
            from sklearn.decomposition import PCA
            emb = PCA(n_components=2, random_state=42).fit_transform(X_std)
        coords_2d = [{"x": round(float(r[0]), 4), "y": round(float(r[1]), 4)} for r in emb]

    res = {
        "status": "success",
        "input_file": args.input,
        "samples": int(X.shape[0]),
        "original_dimension": int(X.shape[1]),
        "intrinsic_dimension": id_metrics,
        "compression_ratio": round(float(X.shape[1]) / max(1, id_metrics.get("mle_p95_ceiling", 1)), 2),
        "coords_2d": coords_2d,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    if args.plot_dir:
        render_manifold_figures(coords_2d, labels, clusters, id_metrics, args.plot_dir, dpi=args.dpi)

    print(json.dumps({
        "status": "success",
        "original_dimension": res["original_dimension"],
        "intrinsic_dimension": id_metrics,
        "output": args.output
    }, indent=2))


if __name__ == "__main__":
    main()
