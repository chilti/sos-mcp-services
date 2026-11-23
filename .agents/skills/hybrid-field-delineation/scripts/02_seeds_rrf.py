"""
Phase 2: Stratified Seed Co-Construction (S+ / S-), 5-Fold OOF Calibration,
Lexical + Continuous TF-IDF Scoring, Contrastive Margin, and RRF(k=60) Fusion.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_io import filter_safe_homonyms, load_or_create_config, phase_dir, resolve_workdir, strip_accents


def compile_term_pattern(terms: list[str]) -> re.Pattern:
    parts = []
    for t in terms:
        ts = strip_accents(t).lower().strip()
        if not ts:
            continue
        wc = ts.endswith("*")
        base = re.escape(ts[:-1] if wc else ts)
        has_cjk = bool(re.search(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", ts))
        if has_cjk:
            parts.append(base)
        else:
            parts.append(rf"\b{base}" + (r"\w*" if wc else r"\b"))
    return re.compile("(?:" + "|".join(dict.fromkeys(parts)) + ")", flags=re.IGNORECASE) if parts else re.compile(r"(?!x)x")


def knn_mean_cosine(X_q: np.ndarray, X_ref: np.ndarray, k: int = 15) -> np.ndarray:
    if len(X_ref) == 0:
        return np.zeros(len(X_q), dtype=np.float32)
    k_eff = min(k, len(X_ref))
    out = np.zeros(len(X_q), dtype=np.float32)
    for s in range(0, len(X_q), 2048):
        sims = X_q[s : s + 2048] @ X_ref.T
        top_k = np.partition(sims, -k_eff, axis=1)[:, -k_eff:] if sims.shape[1] > k_eff else sims
        out[s : s + 2048] = top_k.mean(axis=1)
    return out


def compute_damped_margin(
    X_q: np.ndarray,
    X_pos: np.ndarray,
    X_neg: np.ndarray,
    k: int = 15,
    neg_weight: float = 0.35,
) -> np.ndarray:
    """Contrastive k-NN cosine margin with variance-damped negative subtraction preserving zero-point scale."""
    sim_pos = knn_mean_cosine(X_q, X_pos, k=k)
    sim_neg = knn_mean_cosine(X_q, X_neg, k=k)
    neg_baseline = float(np.median(sim_neg)) if len(sim_neg) > 0 else 0.0
    w = float(np.clip(neg_weight, 0.0, 1.0))
    return (sim_pos - (w * sim_neg + (1.0 - w) * neg_baseline)).astype(np.float32)


def compute_lexical_signals(
    df: pd.DataFrame,
    audit_df: pd.DataFrame,
    facets_init: dict,
    topics_df: pd.DataFrame,
    sources_df: pd.DataFrame,
    cfg: dict | None = None,
    keyword_mode: str = "variant_b",
) -> pd.DataFrame:
    free_terms = audit_df[audit_df["final_action"] == "FREE_OR"]["term"].tolist()
    coup_terms = audit_df[audit_df["final_action"] == "COUPLE_PROXIMITY"]["term"].tolist()
    coup_set = set(coup_terms)
    anchors = [a for a in (facets_init.get("anatomical_anchors_en", []) + facets_init.get("anatomical_anchors_es", [])) if a not in coup_set]
    dom = (cfg or {}).get("domain") or {}
    protected = [dom.get("seed_topic_en", ""), dom.get("seed_topic_es", ""), *anchors, *free_terms]
    homonyms = filter_safe_homonyms(facets_init.get("lexical_homonyms_to_avoid", []), protected)

    indiv_rx = [compile_term_pattern([t]) for t in free_terms if str(t).strip()]
    rx_free_any = compile_term_pattern(free_terms)
    rx_coup = compile_term_pattern(coup_terms)
    rx_anc = compile_term_pattern(anchors)
    rx_hom = compile_term_pattern(homonyms)

    core_topics = set(topics_df[topics_df["llm_class"] == "INCLUDE_CORE"]["display_name"].dropna().astype(str).str.lower().tolist()) if not topics_df.empty else set()
    adj_topics = set(topics_df[topics_df["llm_class"] == "INCLUDE_ADJACENT"]["display_name"].dropna().astype(str).str.lower().tolist()) if not topics_df.empty else set()
    excl_topics = set(topics_df[topics_df["llm_class"] == "EXCLUDE"]["display_name"].dropna().astype(str).str.lower().tolist()) if not topics_df.empty else set()

    pure_src_df = sources_df[sources_df["source_class"] == "PURE_DOMAIN_JOURNAL"] if not sources_df.empty and "source_class" in sources_df.columns else pd.DataFrame()
    pure_venues = set(pure_src_df["display_name"].dropna().astype(str).str.lower().str.strip().tolist()) if not pure_src_df.empty and "display_name" in pure_src_df.columns else set()
    pure_source_ids: set[str] = set()
    if not pure_src_df.empty and "source_id" in pure_src_df.columns:
        for sid in pure_src_df["source_id"].dropna().astype(str).str.strip():
            s_short = sid.replace("https://openalex.org/", "").strip().lower()
            if s_short:
                pure_source_ids.add(s_short)
                pure_source_ids.add(f"https://openalex.org/{s_short}")

    titles_raw = df["title"].fillna("").astype(str).tolist()
    abs_raw = df["abstract_final"].fillna("").astype(str).tolist()
    kw_all_raw = df["keywords"].fillna("").astype(str).tolist()
    auth_kw_raw = df["author_keywords"].fillna("").astype(str).tolist() if "author_keywords" in df.columns else [""] * len(df)

    titles_clean = [strip_accents(t).lower() for t in titles_raw]
    if keyword_mode == "variant_b":
        # Variant B: include author_keywords always; include algorithmic keywords only when abstract is missing
        body_clean = [
            strip_accents(f"{t} {akw} {ab}" if ab.strip() else f"{t} {kw}").lower()
            for t, akw, kw, ab in zip(titles_raw, auth_kw_raw, kw_all_raw, abs_raw)
        ]
    else:
        body_clean = [strip_accents(f"{t} {kw} {ab}").lower() for t, kw, ab in zip(titles_raw, kw_all_raw, abs_raw)]

    topics_low = df["topic"].fillna("").astype(str).str.lower().str.strip().tolist()
    kw_low = [strip_accents(k).lower() for k in kw_all_raw]
    venues_low = df["source_venue"].fillna("").astype(str).str.lower().str.strip().tolist()
    sids_low = df["source_id"].fillna("").astype(str).str.lower().str.strip().tolist() if "source_id" in df.columns else [""] * len(df)

    n = len(df)
    title_hits = np.zeros(n, dtype=np.int32)
    body_hits = np.zeros(n, dtype=np.int32)
    coupled = np.zeros(n, dtype=bool)
    homonym_hit = np.zeros(n, dtype=bool)
    topic_tier = np.zeros(n, dtype=np.int32)
    pure_venue = np.zeros(n, dtype=bool)
    rx_anchor_tax = compile_term_pattern(anchors[:8])
    has_topic_catalog = bool(core_topics or adj_topics)

    for i in range(n):
        ti, bi = titles_clean[i], body_clean[i]
        if rx_free_any.search(ti):
            title_hits[i] = sum(1 for rx in indiv_rx if rx.search(ti))
        if rx_free_any.search(bi):
            body_hits[i] = sum(1 for rx in indiv_rx if rx.search(bi))
        coupled[i] = bool(rx_coup.search(bi) and rx_anc.search(bi))
        homonym_hit[i] = bool(rx_hom.search(bi))
        tl, vl = topics_low[i], venues_low[i]
        vl_short = vl.replace("https://openalex.org/", "").strip()
        sid_short = sids_low[i].replace("https://openalex.org/", "").strip()
        pure_venue[i] = (vl in pure_venues) or (vl_short in pure_source_ids) or (sid_short in pure_source_ids)
        if tl in core_topics:
            topic_tier[i] = 2
        elif tl in adj_topics:
            topic_tier[i] = 1
        elif tl in excl_topics:
            topic_tier[i] = -1
        elif tl and has_topic_catalog and not pure_venue[i]:
            topic_tier[i] = -1
        elif not tl and (pure_venue[i] or rx_anchor_tax.search(kw_low[i])):
            topic_tier[i] = 2

    vocab_seeds = [strip_accents(t).lower().replace("*", "") for t in free_terms if len(t.replace("*", "")) >= 4]
    try:
        tfv = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=4000, sublinear_tf=True)
        X_tf = tfv.fit_transform(body_clean)
        q_vec = tfv.transform([" ".join(vocab_seeds)])
        tfidf_sim = np.asarray((X_tf @ q_vec.T).todense()).ravel().astype(np.float32)
    except Exception:
        tfidf_sim = np.zeros(n, dtype=np.float32)

    lex_score = (
        2.5 * np.minimum(title_hits, 4)
        + 1.0 * np.minimum(body_hits, 6)
        + 1.5 * coupled.astype(float)
        + 2.2 * (topic_tier == 2).astype(float)
        + 1.0 * (topic_tier == 1).astype(float)
        + 2.5 * pure_venue.astype(float)
        + 1.8 * tfidf_sim
        - 1.8 * (topic_tier == -1).astype(float)
        - 3.0 * (homonym_hit & (title_hits == 0)).astype(float)
    )
    return pd.DataFrame({
        "title_free_hits": title_hits, "body_free_hits": body_hits, "coupled_match": coupled,
        "homonym_hit": homonym_hit, "topic_tier": topic_tier, "pure_venue_flag": pure_venue,
        "tfidf_pos_sim": np.round(tfidf_sim, 4), "lex_score": lex_score,
    })


def build_stratified_seeds(
    df: pd.DataFrame, lex_df: pd.DataFrame, vec_norms: np.ndarray, n_pos: int = 1200, n_neg: int = 1200, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    rng = np.random.default_rng(seed)
    valid = vec_norms > 0.1
    non_hom = ~lex_df["homonym_hit"].values
    pos_struct = valid & non_hom & (lex_df["topic_tier"].values == 2) & lex_df["pure_venue_flag"].values
    pos_lex = valid & non_hom & (((lex_df["topic_tier"].values == 2) & (lex_df["title_free_hits"].values >= 1)) | (lex_df["pure_venue_flag"].values & (lex_df["body_free_hits"].values >= 1)))
    pos_cands = np.where(pos_struct | pos_lex)[0]
    if len(pos_cands) < 50:
        pos_cands = np.where(valid & non_hom & ((lex_df["title_free_hits"].values >= 1) | (lex_df["topic_tier"].values == 2)))[0]

    pos_sel = rng.choice(pos_cands, size=min(n_pos, len(pos_cands)), replace=False).tolist() if len(pos_cands) > n_pos else pos_cands.tolist()
    n_pos_struct = int(pos_struct[pos_sel].sum()) if pos_sel else 0

    target_neg = min(n_neg, max(200, len(pos_sel)))
    all_idx = np.arange(len(df))
    not_pos = ~np.isin(all_idx, pos_sel)

    # Tier 1: Zero free/coupled hits in external topic or with homonym
    tier1_mask = (
        valid
        & not_pos
        & (lex_df["title_free_hits"].values == 0)
        & (lex_df["body_free_hits"].values == 0)
        & (~lex_df["coupled_match"].values)
        & (~lex_df["pure_venue_flag"].values)
        & ((lex_df["topic_tier"].values == -1) | lex_df["homonym_hit"].values)
    )
    t1_cands = np.where(tier1_mask)[0]
    neg_sel = rng.choice(t1_cands, size=min(target_neg, len(t1_cands)), replace=False).tolist() if len(t1_cands) > target_neg else t1_cands.tolist()
    n_t1 = len(neg_sel)

    # Tier 2: Hard negatives in Phase-1 pool (0 title hits, <=1 body hit, external topic or homonym, lowest lex_score)
    n_t2 = 0
    if len(neg_sel) < target_neg:
        rem = target_neg - len(neg_sel)
        tier2_mask = (
            valid
            & (~np.isin(all_idx, pos_sel + neg_sel))
            & (lex_df["title_free_hits"].values == 0)
            & (lex_df["body_free_hits"].values <= 1)
            & (~lex_df["coupled_match"].values)
            & (~lex_df["pure_venue_flag"].values)
            & ((lex_df["topic_tier"].values == -1) | lex_df["homonym_hit"].values)
        )
        t2_cands = np.where(tier2_mask)[0]
        if len(t2_cands) > 0:
            order = np.argsort(lex_df["lex_score"].values[t2_cands])
            take = t2_cands[order[:rem]].tolist()
            neg_sel.extend(take)
            n_t2 = len(take)

    # Tier 3: Lowest lexical score fallback with 0 title hits and topic_tier <= 0
    n_t3 = 0
    if len(neg_sel) < target_neg:
        rem = target_neg - len(neg_sel)
        tier3_mask = (
            valid
            & (~np.isin(all_idx, pos_sel + neg_sel))
            & (lex_df["title_free_hits"].values == 0)
            & (~lex_df["pure_venue_flag"].values)
            & (lex_df["topic_tier"].values <= 0)
        )
        t3_cands = np.where(tier3_mask)[0]
        if len(t3_cands) > 0:
            order = np.argsort(lex_df["lex_score"].values[t3_cands])
            take = t3_cands[order[:rem]].tolist()
            neg_sel.extend(take)
            n_t3 = len(take)

    meta = {
        "n_pos_structural_seeds": n_pos_struct,
        "n_neg_tier1_strict": n_t1,
        "n_neg_tier2_hard": n_t2,
        "n_neg_tier3_lowlex": n_t3,
    }
    return np.array(sorted(set(pos_sel)), dtype=np.int64), np.array(sorted(set(neg_sel)), dtype=np.int64), meta


def cross_lingual_bootstrap_seeds(
    df: pd.DataFrame,
    lex_df: pd.DataFrame,
    vecs: np.ndarray,
    vec_norms: np.ndarray,
    pos_idx: np.ndarray,
    neg_idx: np.ndarray,
    k_nn: int,
    n_pos_target: int,
    neg_weight: float = 0.35,
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    """Round-2 cross-lingual seed bootstrapping adding high-confidence non-EN/ES anchors in the shared embedding space."""
    if len(pos_idx) < 5 or len(neg_idx) < 5 or "language" not in df.columns:
        return pos_idx, neg_idx, {"n_pos_cross_lingual": 0, "n_neg_cross_lingual": 0}
    langs = df["language"].fillna("").astype(str).str.lower().str.strip().values
    third_lang = ~np.isin(langs, ["en", "es", ""])
    if not third_lang.any():
        return pos_idx, neg_idx, {"n_pos_cross_lingual": 0, "n_neg_cross_lingual": 0}

    valid = vec_norms > 0.1
    m0 = compute_damped_margin(vecs, vecs[pos_idx], vecs[neg_idx], k=k_nn, neg_weight=neg_weight)

    pos_set, neg_set = set(pos_idx.tolist()), set(neg_idx.tolist())
    cand_pos = np.where(
        third_lang
        & valid
        & (~lex_df["homonym_hit"].values)
        & (lex_df["topic_tier"].values >= 1)
        & (m0 > 0.05)
        & (~np.isin(np.arange(len(df)), list(pos_set | neg_set)))
    )[0]
    cap_pos = min(max(10, n_pos_target // 10), max(10, len(pos_idx) // 4))
    if len(cand_pos) > cap_pos:
        cand_pos = cand_pos[np.argsort(-m0[cand_pos])[:cap_pos]]

    cand_neg = np.where(
        third_lang
        & valid
        & (lex_df["topic_tier"].values == -1)
        & (lex_df["title_free_hits"].values == 0)
        & (lex_df["body_free_hits"].values == 0)
        & (m0 < -0.02)
        & (~np.isin(np.arange(len(df)), list(pos_set | neg_set | set(cand_pos.tolist()))))
    )[0]
    cap_neg = max(len(cand_pos), 0)
    if len(cand_neg) > cap_neg:
        cand_neg = cand_neg[np.argsort(m0[cand_neg])[:cap_neg]]

    new_pos = np.array(sorted(pos_set | set(cand_pos.tolist())), dtype=np.int64)
    new_neg = np.array(sorted(neg_set | set(cand_neg.tolist())), dtype=np.int64)
    if len(cand_pos) or len(cand_neg):
        print(f"  [Cross-Lingual Bootstrap] +{len(cand_pos)} S+ and +{len(cand_neg)} S- third-language anchors added.")
    return new_pos, new_neg, {"n_pos_cross_lingual": int(len(cand_pos)), "n_neg_cross_lingual": int(len(cand_neg))}


def run_oof_calibration(
    vecs: np.ndarray,
    pos_idx: np.ndarray,
    neg_idx: np.ndarray,
    k_nn: int,
    has_abs_all: np.ndarray,
    neg_weight: float = 0.35,
) -> dict[str, float]:
    X_s = np.vstack([vecs[pos_idx], vecs[neg_idx]])
    y_s = np.concatenate([np.ones(len(pos_idx), dtype=np.int32), np.zeros(len(neg_idx), dtype=np.int32)])
    abs_s = np.concatenate([has_abs_all[pos_idx], has_abs_all[neg_idx]])
    skf = StratifiedKFold(n_splits=min(5, len(pos_idx), len(neg_idx)), shuffle=True, random_state=42)
    oof_m, oof_lr = np.zeros(len(y_s), dtype=np.float32), np.zeros(len(y_s), dtype=np.float32)

    for tr, va in skf.split(X_s, y_s):
        X_tr, y_tr, X_va = X_s[tr], y_s[tr], X_s[va]
        oof_m[va] = compute_damped_margin(X_va, X_tr[y_tr == 1], X_tr[y_tr == 0], k=k_nn, neg_weight=neg_weight)
        clf = LogisticRegression(C=1.0, max_iter=500, class_weight="balanced").fit(X_tr, y_tr)
        oof_lr[va] = clf.predict_proba(X_va)[:, 1]

    def _fpr90(yt: np.ndarray, sc: np.ndarray) -> float:
        ps = np.sort(sc[yt == 1])[::-1]
        thr = ps[min(len(ps) - 1, int(np.floor(0.90 * len(ps))))]
        return float((sc[yt == 0] >= thr).mean())

    metrics = {
        "n_pos_seeds": int(len(pos_idx)), "n_neg_seeds": int(len(neg_idx)),
        "oof_margin_pr_auc": float(average_precision_score(y_s, oof_m)),
        "oof_margin_roc_auc": float(roc_auc_score(y_s, oof_m)),
        "oof_margin_fpr_at_rec90": _fpr90(y_s, oof_m),
        "oof_logreg_pr_auc": float(average_precision_score(y_s, oof_lr)),
        "oof_logreg_roc_auc": float(roc_auc_score(y_s, oof_lr)),
        "oof_abs_gap": float(abs(oof_m[abs_s & (y_s == 1)].mean() - oof_m[(~abs_s) & (y_s == 1)].mean())) if (abs_s & (y_s == 1)).any() and ((~abs_s) & (y_s == 1)).any() else 0.0,
    }
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=str, default=".")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--n-pos", type=int, default=1200)
    parser.add_argument("--n-neg", type=int, default=1200)
    parser.add_argument("--keyword-mode", choices=["variant_b", "variant_c"], default="variant_b", help="variant_b (default): use algorithmic keywords only when abstract is empty; variant_c: always concatenate all keywords")
    parser.add_argument("--neg-margin-weight", type=float, default=0.35, help="Damping weight on per-document negative k-NN similarity (default 0.35)")
    parser.add_argument("--no-cross-lingual-bootstrap", action="store_true")
    args = parser.parse_args()

    wd = resolve_workdir(args.workdir)
    cfg, _ = load_or_create_config(wd, config_path=args.config)
    k_nn = int(cfg["thresholds"]["knn_neighbors"])
    rrf_k = int(cfg["thresholds"]["rrf_k"])

    f0_dir = phase_dir(wd, "fase0_estrategia")
    f1_dir = phase_dir(wd, "fase1_corpus")
    out_dir = phase_dir(wd, "fase2_scoring")

    df = pd.read_parquet(f1_dir / "corpus_bruto_dedup.parquet")
    vecs = np.load(f1_dir / "embeddings_dense.npy")
    audit_df = pd.read_csv(f0_dir / "audit_terminos_especificidad.csv")
    facets_init = json.loads((f0_dir / "facets_init.json").read_text(encoding="utf-8"))
    topics_df = pd.read_csv(f0_dir / "propuesta_topics_descubiertos.csv") if (f0_dir / "propuesta_topics_descubiertos.csv").exists() else pd.DataFrame()
    sources_df = pd.read_csv(f0_dir / "propuesta_revistas_bradford.csv") if (f0_dir / "propuesta_revistas_bradford.csv").exists() else pd.DataFrame()

    lex_df = compute_lexical_signals(df, audit_df, facets_init, topics_df, sources_df, cfg=cfg, keyword_mode=args.keyword_mode)
    vec_norms = np.linalg.norm(vecs, axis=1)
    pos_idx, neg_idx, seed_meta = build_stratified_seeds(df, lex_df, vec_norms, n_pos=args.n_pos, n_neg=args.n_neg)
    if not args.no_cross_lingual_bootstrap:
        pos_idx, neg_idx, boot_meta = cross_lingual_bootstrap_seeds(df, lex_df, vecs, vec_norms, pos_idx, neg_idx, k_nn=k_nn, n_pos_target=args.n_pos, neg_weight=args.neg_margin_weight)
        seed_meta.update(boot_meta)
    oof_metrics = run_oof_calibration(vecs, pos_idx, neg_idx, k_nn=k_nn, has_abs_all=(df["abstract_final"].fillna("").str.strip() != "").to_numpy(), neg_weight=args.neg_margin_weight)
    oof_metrics.update(seed_meta)

    X_pos, X_neg = vecs[pos_idx], vecs[neg_idx]
    margin = compute_damped_margin(vecs, X_pos, X_neg, k=k_nn, neg_weight=args.neg_margin_weight)
    zero_vec = vec_norms == 0
    if zero_vec.any():
        strong_lex_zero = zero_vec & (
            ((lex_df["title_free_hits"].values >= 1) & (~lex_df["homonym_hit"].values))
            | ((lex_df["topic_tier"].values == 2) & (lex_df["body_free_hits"].values >= 2))
        )
        margin[zero_vec & (~strong_lex_zero)] = -0.25
        margin[strong_lex_zero] = 0.0
    clf = LogisticRegression(C=1.0, max_iter=500, class_weight="balanced").fit(np.vstack([X_pos, X_neg]), np.concatenate([np.ones(len(pos_idx)), np.zeros(len(neg_idx))]))
    lr_prob = clf.predict_proba(vecs)[:, 1]
    lr_prob[zero_vec] = 0.0

    df_sc = pd.concat([df.reset_index(drop=True), lex_df.reset_index(drop=True)], axis=1)
    df_sc["margin_score"] = margin
    df_sc["logreg_prob"] = lr_prob
    df_sc["seed_role"] = "NONE"
    df_sc.loc[pos_idx, "seed_role"] = "S_POS"
    df_sc.loc[neg_idx, "seed_role"] = "S_NEG"
    df_sc["rank_lex"] = df_sc["lex_score"].rank(ascending=False, method="min").astype(int)
    df_sc["rank_sem"] = df_sc["margin_score"].rank(ascending=False, method="min").astype(int)
    df_sc["rank_lr"] = df_sc["logreg_prob"].rank(ascending=False, method="min").astype(int)
    df_sc["rrf_score"] = (
        (1.0 / (rrf_k + df_sc["rank_lex"]))
        + (1.0 / (rrf_k + df_sc["rank_sem"]))
        + (1.0 / (rrf_k + df_sc["rank_lr"]))
    )

    lex_strong = (df_sc["title_free_hits"] >= 1) | (df_sc["body_free_hits"] >= 2) | df_sc["coupled_match"] | df_sc["pure_venue_flag"]
    sem_strong = df_sc["margin_score"] > 0.02
    df_sc["via_captacion"] = np.select([lex_strong & sem_strong, lex_strong & (~sem_strong), (~lex_strong) & sem_strong], ["BOTH_LEX_AND_SEM", "LEX_ONLY", "SEM_ONLY_RESCUE"], default="BORDERLINE_WEAK")

    all_metrics = {"oof_calibration": oof_metrics, "via_counts": df_sc["via_captacion"].value_counts().to_dict()}
    df_sc.to_parquet(out_dir / "corpus_scored_rrf.parquet", index=False)
    (out_dir / "fase2_oof_metrics.json").write_text(json.dumps(all_metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(all_metrics, indent=2, ensure_ascii=False))

    from visual_artifacts import generate_phase_visuals
    generate_phase_visuals(2, wd, cfg)


if __name__ == "__main__":
    main()
