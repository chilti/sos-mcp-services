"""
Phase 3: Intrinsic Dimension Estimation (TwoNN / MLE p95), UMAP(d_ID -> 2D) Hierarchical Projection,
Multi-Resolution Leiden Partitioning (0% orphans), 2-Pass Cluster-Aware Active Seeding,
Red Zone Outlier Rescue, and English Interactive + Static Map Export.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import igraph as ig
import leidenalg
import numpy as np
import pandas as pd
import umap
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_io import load_or_create_config, phase_dir, resolve_workdir

SPANISH_STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
    "con", "no", "una", "su", "al", "lo", "como", "mas", "más", "pero", "sus", "le", "ya", "o",
    "este", "sí", "si", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre", "también",
    "tambien", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante",
    "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto",
    "mi", "antes", "algunos", "que", "unos", "yo", "otro", "otras", "otra", "él", "tanto",
    "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual", "poco", "ella", "estar",
    "estas", "algunas", "algo", "nosotros", "estudio", "analisis", "análisis", "mediante",
}
BILINGUAL_STOPWORDS = sorted(set(ENGLISH_STOP_WORDS) | SPANISH_STOPWORDS)


def estimate_intrinsic_dimensions(vecs: np.ndarray) -> dict[str, float]:
    valid = np.linalg.norm(vecs, axis=1) > 0.1
    X = vecs[valid]
    _, uniq_idx = np.unique(np.round(X, 5), axis=0, return_index=True)
    Xu = X[np.sort(uniq_idx)]
    if len(Xu) > 15000:
        Xu = Xu[np.random.default_rng(42).choice(len(Xu), size=15000, replace=False)]

    k_nn = min(21, max(4, len(Xu) - 1))
    nn = NearestNeighbors(n_neighbors=k_nn, metric="euclidean", n_jobs=-1).fit(Xu)
    dists, _ = nn.kneighbors(Xu)
    r1 = np.maximum(dists[:, 1], 1e-7)
    r2 = np.maximum(dists[:, min(2, k_nn - 1)], 1e-7)
    mu = np.sort(r2 / r1)
    cut = max(3, int(0.90 * len(mu)))
    F = np.arange(1, cut + 1, dtype=np.float64) / (len(mu) + 1.0)
    x_tw = np.log(np.maximum(mu[:cut], 1.000001))
    y_tw = -np.log(np.maximum(1.0 - F, 1e-9))
    d_twonn = float(np.dot(x_tw, y_tw) / np.maximum(np.dot(x_tw, x_tw), 1e-9))

    dk = np.maximum(dists[:, 1:], 1e-7)
    local_mle = (dk.shape[1] - 1) / np.maximum(np.log(dk[:, -1:] / dk[:, :-1]).sum(axis=1), 1e-6)
    d_mle_p95 = float(np.percentile(local_mle, 95))

    d_skdim = None
    if importlib.util.find_spec("skdim") is not None and len(Xu) >= 50:
        try:
            import skdim
            d_skdim = float(skdim.id.TwoNN().fit_transform(Xu))
        except Exception:
            pass

    chosen = int(np.clip(round(d_skdim if d_skdim else d_twonn), 8, min(32, max(8, len(Xu) - 2))))
    return {
        "n_unique_vectors_used": int(len(Xu)),
        "d_twonn": round(d_twonn, 2),
        "d_skdim_twonn": round(d_skdim, 2) if d_skdim else None,
        "d_mle_p95_k20": round(d_mle_p95, 2),
        "umap_d_id_selected": chosen,
    }


def build_knn_igraph(coords: np.ndarray, k: int = 30) -> ig.Graph:
    k_eff = min(k, max(2, len(coords) - 1))
    dists, idxs = NearestNeighbors(n_neighbors=k_eff + 1, metric="euclidean", n_jobs=-1).fit(coords).kneighbors(coords)
    dists, idxs = dists[:, 1:], idxs[:, 1:]
    sigma = float(np.median(dists)) or 1.0
    weights_mat = np.exp(- (dists ** 2) / (2.0 * (sigma ** 2)))

    seen: dict[tuple[int, int], float] = {}
    for i in range(len(coords)):
        for j_pos in range(k_eff):
            j = int(idxs[i, j_pos])
            if i == j:
                continue
            pair = (i, j) if i < j else (j, i)
            w = float(weights_mat[i, j_pos])
            if pair not in seen or w > seen[pair]:
                seen[pair] = w
    G = ig.Graph(n=len(coords), edges=list(seen.keys()), directed=False)
    G.es["weight"] = list(seen.values())
    return G


def select_optimal_leiden_gamma(G: ig.Graph, seed_roles: np.ndarray, gammas: list[float]) -> tuple[np.ndarray, pd.DataFrame, float]:
    rows, best_gamma, best_obj, best_labels = [], gammas[0], 1e9, None
    is_pos, is_neg = seed_roles == "S_POS", seed_roles == "S_NEG"

    for g in gammas:
        part = leidenalg.find_partition(G, leidenalg.RBConfigurationVertexPartition, resolution_parameter=float(g), weights="weight", seed=42)
        labels = np.array(part.membership, dtype=np.int32)
        sizes = np.bincount(labels)
        small_share = float(sizes[sizes < 20].sum() / len(labels))
        tot_s, cond_ent = 0, 0.0
        for cid in range(int(labels.max() + 1)):
            m = labels == cid
            np_c, nn_c = int(is_pos[m].sum()), int(is_neg[m].sum())
            ns = np_c + nn_c
            if ns == 0:
                continue
            tot_s += ns
            p = np_c / ns
            if 0.0 < p < 1.0:
                cond_ent += ns * (-(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p)))
        mean_ent = cond_ent / max(1, tot_s)
        obj = mean_ent + 0.15 * small_share
        rows.append({"gamma": float(g), "n_clusters": int(labels.max() + 1), "modularity": round(float(part.modularity), 4), "cond_entropy_S_pos_neg": round(mean_ent, 4), "small_clusters_share": round(small_share, 4), "objective": round(obj, 4)})
        if obj < best_obj:
            best_obj, best_gamma, best_labels = obj, float(g), labels
    assert best_labels is not None
    return best_labels, pd.DataFrame(rows), best_gamma


def extract_cluster_keywords(titles: pd.Series, labels: np.ndarray, top_k: int = 6) -> dict[int, str]:
    vec = TfidfVectorizer(max_features=3000, stop_words=BILINGUAL_STOPWORDS, ngram_range=(1, 2), min_df=2)
    try:
        X = vec.fit_transform(titles.fillna("").astype(str))
        terms = np.array(vec.get_feature_names_out())
    except Exception:
        return {}
    out: dict[int, str] = {}
    for cid in np.unique(labels):
        m = labels == cid
        mean_tf = np.asarray(X[m].mean(axis=0)).ravel()
        top_i = np.argsort(mean_tf)[::-1][:top_k]
        out[int(cid)] = ", ".join(terms[i] for i in top_i if mean_tf[i] > 0)
    return out


def triage_clusters_and_rescue(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    th = cfg["thresholds"]
    labels = df["leiden_cluster"].values
    kw_map = extract_cluster_keywords(df["title"], labels)

    seed_eff = df["seed_role"].astype(str).copy()
    p_prom = n_prom = 0
    for cid in sorted(np.unique(labels)):
        sub = df[labels == cid]
        if int(sub["seed_role"].isin(["S_POS", "S_NEG"]).sum()) >= 5:
            continue
        none_idx = sub.index[sub["seed_role"] == "NONE"]
        if len(none_idx) == 0:
            continue
        sn = df.loc[none_idx]
        p_idx = none_idx[((sn["logreg_prob"] >= 0.82) & (sn["margin_score"] >= 0.045) & (~sn["homonym_hit"]) & ((sn["title_free_hits"] >= 1) | (sn["topic_tier"] == 2) | sn["pure_venue_flag"])).values][:8]
        n_idx = none_idx[((sn["logreg_prob"] <= 0.18) & (sn["margin_score"] <= -0.015) & (sn["title_free_hits"] == 0) & (~sn["pure_venue_flag"]) & ((sn["topic_tier"] <= 0) | sn["homonym_hit"])).values][:8]
        if len(p_idx) > 0:
            seed_eff.loc[p_idx] = "S_POS"
            p_prom += len(p_idx)
        if len(n_idx) > 0:
            seed_eff.loc[n_idx] = "S_NEG"
            n_prom += len(n_idx)
    df["seed_role_cluster_aware"] = seed_eff
    print(f"   [Cluster-Aware Active Seeding] Promoted +{p_prom} S_POS, +{n_prom} S_NEG anchors.")

    cards, zone_by_cid = [], {}
    for cid in sorted(np.unique(labels)):
        sub = df[labels == cid]
        n_sp = int((sub["seed_role_cluster_aware"] == "S_POS").sum())
        n_sn = int((sub["seed_role_cluster_aware"] == "S_NEG").sum())
        ns = n_sp + n_sn
        pct_sp, pct_sn = 100.0 * n_sp / max(1, ns), 100.0 * n_sn / max(1, ns)
        med_m = float(sub["margin_score"].median())
        med_lr = float(sub["logreg_prob"].median()) if "logreg_prob" in sub.columns else 0.5
        pct_th = float((sub["title_free_hits"] >= 1).mean() * 100.0)
        pct_pv = float(sub["pure_venue_flag"].mean() * 100.0) if "pure_venue_flag" in sub.columns else 0.0

        if ns >= 5:
            is_green_seeds = (
                pct_sp >= th["green_zone_min_pos_pct"]
                and (pct_sn <= th["green_zone_max_neg_pct"] or n_sn <= 1)
                and med_m > 0.0
            ) or (pct_sp >= 78.0 and pct_sn <= 15.0 and med_m >= 0.06)
            is_green_anchored = (med_lr >= 0.68) and (pct_th >= 18.0 or pct_pv >= 12.0 or med_m >= 0.075)
            if is_green_seeds and is_green_anchored:
                zone = "ZONA_VERDE"
            elif (
                pct_sn >= th["red_zone_min_neg_pct"]
                and pct_sp <= th["red_zone_max_pos_pct"]
                and ((med_m < -0.015) or (med_m < 0.005 and pct_th < 12.0) or (med_lr <= 0.35 and pct_th < 12.0))
            ) or (pct_sp <= 15.0 and med_lr <= 0.25 and pct_th < 8.0 and pct_pv < 5.0):
                zone = "ZONA_ROJA"
            else:
                zone = "ZONA_GRIS"
        else:
            if med_m >= 0.055 and med_lr >= 0.72 and (pct_th >= 42.0 or pct_pv >= 25.0):
                zone = "ZONA_VERDE"
            elif (
                (pct_sn == 100.0 and med_m < -0.01)
                or (med_m <= 0.005 and pct_th < 10.0)
                or (med_m < -0.02)
                or (med_lr <= 0.25 and pct_th < 8.0 and pct_pv < 5.0)
            ):
                zone = "ZONA_ROJA"
            else:
                zone = "ZONA_GRIS"

        zone_by_cid[int(cid)] = zone
        cards.append({
            "leiden_cluster": int(cid), "zona_inicial": zone, "n_docs": int(len(sub)),
            "n_s_pos": n_sp, "n_s_neg": n_sn, "pct_s_pos_seeded": round(pct_sp, 1),
            "pct_s_neg_seeded": round(pct_sn, 1), "median_margin": round(med_m, 4),
            "median_logreg_prob": round(med_lr, 4),
            "median_rrf": round(float(sub["rrf_score"].median()), 6),
            "pct_title_free_hits": round(pct_th, 1),
            "pct_pure_venue": round(pct_pv, 1),
            "top_topics": json.dumps(sub["topic"].replace("", pd.NA).dropna().value_counts().head(3).to_dict(), ensure_ascii=False),
            "c_tfidf_terms": kw_map.get(int(cid), ""),
        })

    df["zona_cluster"] = df["leiden_cluster"].map(zone_by_cid)
    df["zona_triaje"] = df["zona_cluster"].copy()
    df["red_outlier_rescued"] = False
    rescue_mask = (df["zona_cluster"] == "ZONA_ROJA") & ((df["title_free_hits"] >= 1) | df["coupled_match"] | df["pure_venue_flag"]) & (df["margin_score"] > float(th["red_zone_outlier_rescue_margin"]))
    df.loc[rescue_mask, "zona_triaje"] = "ZONA_GRIS"
    df.loc[rescue_mask, "red_outlier_rescued"] = True
    return df, pd.DataFrame(cards)


def write_manifold_figures(df: pd.DataFrame, out_html: Path, d_id: int) -> None:
    zone_map = {"ZONA_VERDE": "GREEN ZONE", "ZONA_GRIS": "GRAY ZONE", "ZONA_ROJA": "RED ZONE"}
    df_p = df.copy()
    df_p["triage_zone"] = df_p["zona_triaje"].map(lambda z: zone_map.get(z, z))
    try:
        import plotly.express as px
        samp = df_p.sample(n=min(18000, len(df_p)), random_state=42) if len(df_p) > 18000 else df_p
        fig = px.scatter(
            samp, x="umap_x", y="umap_y", color="triage_zone",
            color_discrete_map={"GREEN ZONE": "#059669", "GRAY ZONE": "#eab308", "RED ZONE": "#dc2626"},
            labels={"umap_x": f"UMAP-1 (from {d_id}D manifold)", "umap_y": f"UMAP-2 (from {d_id}D manifold)", "triage_zone": "Triage Zone"},
            hover_data={"title": True, "topic": True, "language": True, "leiden_cluster": True, "margin_score": ":.3f", "via_captacion": True, "umap_x": False, "umap_y": False},
            title=f"UMAP(d_ID={d_id}D -> 2D) Manifold + Multi-Resolution Leiden — 3-Zone Triage",
            opacity=0.65, width=1200, height=780,
        )
        fig.update_traces(marker={"size": 4})
        fig.write_html(str(out_html), include_plotlyjs="cdn")
    except Exception as exc:
        print(f"  [Plotly warning] {exc}")
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10.5, 6.8), dpi=220)
        for z_raw, z_lbl, col, alp, sz in [("ZONA_GRIS", "GRAY ZONE", "#eab308", 0.35, 4), ("ZONA_ROJA", "RED ZONE", "#dc2626", 0.45, 5), ("ZONA_VERDE", "GREEN ZONE", "#059669", 0.55, 6)]:
            sub = df[df["zona_triaje"] == z_raw]
            ax.scatter(sub["umap_x"], sub["umap_y"], c=col, s=sz, alpha=alp, edgecolors="none", label=f"{z_lbl} (n={len(sub):,})")
        ax.set_title(f"UMAP(d_ID={d_id}D -> 2D) Manifold + Multi-Resolution Leiden — 3-Zone Triage", fontsize=12, fontweight="bold")
        ax.set_xlabel(f"UMAP-1 (from {d_id}D manifold)")
        ax.set_ylabel(f"UMAP-2 (from {d_id}D manifold)")
        ax.legend(markerscale=3, frameon=True, loc="best")
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.savefig(out_html.with_suffix(".png"), dpi=220)
        plt.close(fig)
    except Exception as exc:
        print(f"  [PNG warning] {exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=str, default=".")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--reuse-umap", action="store_true")
    args = parser.parse_args()

    wd = resolve_workdir(args.workdir)
    cfg, _ = load_or_create_config(wd, config_path=args.config)
    th = cfg["thresholds"]

    f1_dir = phase_dir(wd, "fase1_corpus")
    f2_dir = phase_dir(wd, "fase2_scoring")
    out_dir = phase_dir(wd, "fase3_manifold")
    rep_dir = wd / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(f2_dir / "corpus_scored_rrf.parquet")
    vecs = np.load(f1_dir / "embeddings_dense.npy")

    if args.reuse_umap and (out_dir / "fase3_manifold_metrics.json").exists():
        id_stats = json.loads((out_dir / "fase3_manifold_metrics.json").read_text(encoding="utf-8"))["intrinsic_dimension"]
        d_id = id_stats["umap_d_id_selected"]
        coords_id = np.load(out_dir / f"umap_{d_id}d_coords.npy")
        coords_2d = np.load(out_dir / f"umap_2d_from_{d_id}d_coords.npy")
    else:
        id_stats = estimate_intrinsic_dimensions(vecs)
        d_id = id_stats["umap_d_id_selected"]
        nn_eff = min(int(th["umap_n_neighbors"]), max(5, len(df) - 2))
        coords_id = umap.UMAP(n_components=min(d_id, max(2, len(df) - 2)), n_neighbors=nn_eff, min_dist=float(th["umap_min_dist"]), metric="cosine", random_state=42).fit_transform(vecs)
        np.save(out_dir / f"umap_{d_id}d_coords.npy", coords_id.astype(np.float32))
        coords_2d = umap.UMAP(n_components=2, n_neighbors=nn_eff, min_dist=0.12, metric="euclidean", random_state=42).fit_transform(coords_id)
        np.save(out_dir / f"umap_2d_from_{d_id}d_coords.npy", coords_2d.astype(np.float32))

    df["umap_x"] = coords_2d[:, 0].astype(np.float32)
    df["umap_y"] = coords_2d[:, 1].astype(np.float32)

    G = build_knn_igraph(coords_id, k=30)
    labels, gamma_df, best_gamma = select_optimal_leiden_gamma(G, df["seed_role"].values, th["leiden_resolutions"])
    df["leiden_cluster"] = labels
    gamma_df.to_csv(out_dir / "leiden_multigamma_selection.csv", index=False)

    df, cards_df = triage_clusters_and_rescue(df, cfg)
    cards_df.to_csv(out_dir / "leiden_cluster_cards.csv", index=False)
    df.to_parquet(out_dir / "corpus_triaged_leiden.parquet", index=False)
    write_manifold_figures(df, rep_dir / "fase3_manifold_zones.html", d_id)

    summary = {
        "intrinsic_dimension": id_stats,
        "best_gamma": best_gamma,
        "n_clusters": int(len(np.unique(labels))),
        "orphans_pct": 0.0,
        "red_zone_outliers_rescued": int(df["red_outlier_rescued"].sum()),
        "zone_counts": df["zona_triaje"].value_counts().to_dict(),
    }
    (out_dir / "fase3_manifold_metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    from visual_artifacts import generate_phase_visuals
    generate_phase_visuals(3, wd, cfg)


if __name__ == "__main__":
    main()
