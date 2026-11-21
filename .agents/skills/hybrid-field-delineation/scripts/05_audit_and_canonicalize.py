"""
Phase 5: Canonical Export (./corpus.parquet matching sos-mcp-services CANONICAL_COLUMNS),
Separated Conference Annex (./corpus_conferences.parquet), Horvitz-Thompson Blind Audit,
Deterministic Language/Domain Fallback, and English GLOBAL/PRISMA-S Manifest & Visuals.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_io import load_or_create_config, phase_dir, resolve_workdir, to_canonical_corpus


def normalize_doc_type(dt: str, title: str = "") -> str:
    s = str(dt or "").lower().strip()
    t = str(title or "").lower().strip()
    if "retract" in s or t.startswith("retracted:") or t.startswith("[retracted"):
        return "retracted"
    if not s:
        return "article"
    if "meeting abstract" in s or s == "abstract":
        return "meeting_abstract"
    if "review" in s or "short survey" in s:
        return "review"
    if "letter" in s:
        return "letter"
    if "editorial" in s:
        return "editorial"
    if "proceedings" in s or "conference" in s:
        return "proceedings_paper"
    if "book chapter" in s or "book-chapter" in s or s == "book":
        return "book_chapter"
    if "note" in s or "erratum" in s or "correction" in s or "paratext" in s or "supplementary" in s:
        return "paratext_or_erratum"
    return "article"


def infer_missing_language_and_domain(df: pd.DataFrame) -> pd.DataFrame:
    rx_es = re.compile(r"\b(estudio|pacientes|tratamiento|enfermedad|enfermedades|analisis|resultados|mediante|desarrollo|evaluacion|casos|sistema)\b", flags=re.IGNORECASE)
    rx_phys = re.compile(r"\b(physics|quantum|optics|photonics|catalysis|polymer|material|nanoparticle|semiconductor|thermodynamics|astronomy|engineering|computing)\b", flags=re.IGNORECASE)
    rx_soc = re.compile(r"\b(education|economics|sociology|policy|governance|law|management|tourism|psychology|history|linguistics)\b", flags=re.IGNORECASE)
    rx_life = re.compile(r"\b(ecology|botany|zoology|genetics|biochemistry|microbiology|agriculture|agronomy|biodiversity|neuroscience|cell biology)\b", flags=re.IGNORECASE)
    rx_health = re.compile(r"\b(medicine|clinical|hospital|patient|disease|therapy|diagnosis|epidemiology|public health|surgery|pathology)\b", flags=re.IGNORECASE)

    new_langs, new_doms = [], []
    for r in df.itertuples(index=False):
        lg = str(r.language or "").strip().lower()
        if not lg or lg in ("unknown", "none", "und"):
            new_langs.append("es" if len(rx_es.findall(f"{r.title} {str(r.abstract_final)[:250]}")) >= 2 else "en")
        else:
            new_langs.append(lg)

        dm = str(r.domain or "").strip()
        if not dm or dm.lower() in ("unknown", "none", ""):
            meta = f"{r.topic} {r.source_venue} {r.keywords} {r.title}"
            if rx_health.search(meta):
                new_doms.append("Health Sciences")
            elif rx_phys.search(meta):
                new_doms.append("Physical Sciences")
            elif rx_soc.search(meta):
                new_doms.append("Social Sciences")
            elif rx_life.search(meta):
                new_doms.append("Life Sciences")
            else:
                new_doms.append("Multidisciplinary / General")
        else:
            new_doms.append(dm)

    df["language"] = new_langs
    df["domain"] = new_doms
    return df


def build_horvitz_thompson_sample(df: pd.DataFrame, out_dir: Path, seed: int = 42) -> dict[str, dict[str, int]]:
    rng = np.random.default_rng(seed)
    strata_defs = {
        "STRATUM_GREEN_LEX": (df["zona_triaje"] == "ZONA_VERDE") & (df["via_captacion"].isin(["BOTH_LEX_AND_SEM", "LEX_ONLY"])),
        "STRATUM_GREEN_SEM_RESCUE": (df["zona_triaje"] == "ZONA_VERDE") & (df["via_captacion"] == "SEM_ONLY_RESCUE"),
        "STRATUM_GRAY_ACCEPTED": (df["zona_triaje"] == "ZONA_GRIS") & (df["final_corpus_layer"].isin(["STRICT_CORE", "EXTENDED_INTERDISCIPLINARY"])),
        "STRATUM_GRAY_REJECTED": (df["zona_triaje"] == "ZONA_GRIS") & (df["final_corpus_layer"] == "EXCLUDED"),
        "STRATUM_RED_BORDERLINE": (df["zona_triaje"] == "ZONA_ROJA") & (df["final_corpus_layer"] == "EXCLUDED"),
    }
    targets = {"STRATUM_GREEN_LEX": 100, "STRATUM_GREEN_SEM_RESCUE": 70, "STRATUM_GRAY_ACCEPTED": 70, "STRATUM_GRAY_REJECTED": 60, "STRATUM_RED_BORDERLINE": 60}

    frames, meta = [], {}
    for sname, mask in strata_defs.items():
        idxs = np.where(mask.values)[0]
        N_h = len(idxs)
        n_h = min(targets[sname], N_h)
        meta[sname] = {"N_h": int(N_h), "n_h": int(n_h)}
        if n_h == 0:
            continue
        chosen = rng.choice(idxs[np.argsort(-df["margin_score"].values[idxs])][: max(n_h, len(idxs) // 2)], size=n_h, replace=False) if sname == "STRATUM_RED_BORDERLINE" else rng.choice(idxs, size=n_h, replace=False)
        sub = df.iloc[chosen].copy()
        sub["stratum_name"], sub["N_h"], sub["n_h"], sub["ht_weight"] = sname, N_h, n_h, float(N_h) / float(n_h)
        frames.append(sub)

    if not frames:
        return meta
    samp = pd.concat(frames, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    samp.insert(0, "blind_audit_id", [f"BLIND_{i:04d}" for i in range(len(samp))])
    blind_df = samp[["blind_audit_id", "title", "publication_year", "language", "source_venue", "topic", "keywords", "abstract_final"]].copy()
    blind_df["expert_decision"], blind_df["expert_notes"] = "", ""
    blind_df.to_csv(out_dir / "auditoria_ciega_muestra_n360.csv", index=False)
    samp[["blind_audit_id", "work_uid", "oa_id", "doi_norm", "stratum_name", "N_h", "n_h", "ht_weight", "final_corpus_layer", "zona_triaje", "via_captacion", "margin_score", "llm_decision"]].to_csv(out_dir / "auditoria_ciega_clave_interna.csv", index=False)
    return meta


def compute_ht_with_bootstrap(annotated_csv: Path, key_csv: Path, n_boot: int = 1000) -> dict[str, object]:
    ann, key = pd.read_csv(annotated_csv), pd.read_csv(key_csv)
    m = pd.merge(key, ann[["blind_audit_id", "expert_decision"]], on="blind_audit_id", how="inner")
    m = m[m["expert_decision"].isin(["INCLUDE_CORE", "INCLUDE_PERIPHERY", "EXCLUDE", "1", "0", 1, 0])].copy()
    if m.empty:
        return {"status": "no_annotated_rows"}
    m["is_pos"] = m["expert_decision"].astype(str).isin(["INCLUDE_CORE", "INCLUDE_PERIPHERY", "1"]).astype(float)
    m["is_pred"] = m["final_corpus_layer"].isin(["STRICT_CORE", "EXTENDED_INTERDISCIPLINARY"]).astype(float)

    def _est(sub: pd.DataFrame) -> tuple[float, float, float]:
        w = sub["ht_weight"].values
        tp = float(np.sum(w * sub["is_pos"].values * sub["is_pred"].values))
        prec = tp / max(1e-9, float(np.sum(w * sub["is_pred"].values)))
        rec = tp / max(1e-9, float(np.sum(w * sub["is_pos"].values)))
        return prec, rec, (2 * prec * rec / max(1e-9, prec + rec))

    p0, r0, f0 = _est(m)
    rng = np.random.default_rng(42)
    ps, rs, fs = [], [], []
    for _ in range(n_boot):
        pb, rb, fb = _est(pd.concat([grp.sample(n=len(grp), replace=True, random_state=int(rng.integers(0, 10**7))) for _, grp in m.groupby("stratum_name")], ignore_index=True))
        ps.append(pb); rs.append(rb); fs.append(fb)
    return {
        "n_evaluated": int(len(m)),
        "ht_precision": round(p0, 4), "ht_precision_ci95": [round(float(np.percentile(ps, 2.5)), 4), round(float(np.percentile(ps, 97.5)), 4)],
        "ht_recall": round(r0, 4), "ht_recall_ci95": [round(float(np.percentile(rs, 2.5)), 4), round(float(np.percentile(rs, 97.5)), 4)],
        "ht_f1": round(f0, 4), "ht_f1_ci95": [round(float(np.percentile(fs, 2.5)), 4), round(float(np.percentile(fs, 97.5)), 4)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=str, default=".")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--compute-ht", type=str, default=None)
    args = parser.parse_args()

    wd = resolve_workdir(args.workdir)
    cfg, _ = load_or_create_config(wd, config_path=args.config)
    f4_dir = phase_dir(wd, "fase4_llm_snowball")
    out_dir = phase_dir(wd, "fase5_corpus_final")
    rep_dir = wd / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)

    if args.compute_ht:
        res_ht = compute_ht_with_bootstrap(Path(args.compute_ht), out_dir / "auditoria_ciega_clave_interna.csv")
        (out_dir / "horvitz_thompson_results.json").write_text(json.dumps(res_ht, indent=2), encoding="utf-8")
        print(json.dumps(res_ht, indent=2))
        return

    df = pd.read_parquet(f4_dir / "corpus_triage_completo.parquet")
    df = infer_missing_language_and_domain(df)
    df["doc_type_norm"] = [normalize_doc_type(dt, ti) for dt, ti in zip(df["doc_type"], df["title"])]

    mask_ret = (df["final_corpus_layer"] != "EXCLUDED") & (df["doc_type_norm"].isin(["retracted", "paratext_or_erratum"]))
    df.loc[mask_ret, "final_corpus_layer"] = "EXCLUDED_RETRACTED"

    mask_conf = df["final_corpus_layer"].isin(["STRICT_CORE", "EXTENDED_INTERDISCIPLINARY"]) & df["doc_type_norm"].isin(["meeting_abstract", "proceedings_paper"])
    df.loc[mask_conf, "final_corpus_layer"] = "CONFERENCE_PROCEEDINGS"

    meta_strata = build_horvitz_thompson_sample(df, out_dir)
    corpus_citable = df[df["final_corpus_layer"].isin(["STRICT_CORE", "EXTENDED_INTERDISCIPLINARY"])].copy().reset_index(drop=True)
    corpus_strict = corpus_citable[corpus_citable["final_corpus_layer"] == "STRICT_CORE"].copy().reset_index(drop=True)
    corpus_ext = corpus_citable[corpus_citable["final_corpus_layer"] == "EXTENDED_INTERDISCIPLINARY"].copy().reset_index(drop=True)
    corpus_conf = df[df["final_corpus_layer"] == "CONFERENCE_PROCEEDINGS"].copy().reset_index(drop=True)

    # Canonical Workspace-First ./corpus.parquet + ./corpus_conferences.parquet for downstream sos-mcp-services skills
    canonical_df = to_canonical_corpus(corpus_citable)
    canonical_df.to_parquet(wd / "corpus.parquet", index=False)
    to_canonical_corpus(corpus_conf).to_parquet(wd / "corpus_conferences.parquet", index=False)

    corpus_citable.to_parquet(out_dir / "corpus_citable_full.parquet", index=False)
    corpus_strict.to_parquet(out_dir / "corpus_strict_core.parquet", index=False)
    corpus_ext.to_parquet(out_dir / "corpus_extended_interdisciplinary.parquet", index=False)
    corpus_conf.to_parquet(out_dir / "corpus_conferences_raw.parquet", index=False)

    pub_cols = [c for c in corpus_citable.columns if c not in ("abstract_final", "affiliations_raw")]
    corpus_citable[pub_cols].to_parquet(out_dir / "corpus_public_no_abstracts_copyright.parquet", index=False)

    m_f1 = json.loads((phase_dir(wd, "fase1_corpus") / "fase1_ingesta_manifest.json").read_text(encoding="utf-8")) if (phase_dir(wd, "fase1_corpus") / "fase1_ingesta_manifest.json").exists() else {}
    m_f2 = json.loads((phase_dir(wd, "fase2_scoring") / "fase2_oof_metrics.json").read_text(encoding="utf-8")) if (phase_dir(wd, "fase2_scoring") / "fase2_oof_metrics.json").exists() else {}
    m_f3 = json.loads((phase_dir(wd, "fase3_manifold") / "fase3_manifold_metrics.json").read_text(encoding="utf-8")) if (phase_dir(wd, "fase3_manifold") / "fase3_manifold_metrics.json").exists() else {}
    m_f4 = json.loads((phase_dir(wd, "fase4_llm_snowball") / "fase4_llm_metrics.json").read_text(encoding="utf-8")) if (phase_dir(wd, "fase4_llm_snowball") / "fase4_llm_metrics.json").exists() else {}

    global_manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed_topic_en": cfg["domain"]["seed_topic_en"],
        "geo_scope": cfg["scope"].get("geo_country_code") or "GLOBAL",
        "year_range": [cfg["scope"]["year_start"], cfg["scope"]["year_end"]],
        "counts": {
            "fase1_dedup_broad_candidates": int(len(df)),
            "final_corpus_total": int(len(corpus_citable)),
            "strict_core_count": int(len(corpus_strict)),
            "extended_interdisciplinary_count": int(len(corpus_ext)),
            "conference_proceedings_separated_count": int(len(corpus_conf)),
            "excluded_noise_count": int((df["final_corpus_layer"] == "EXCLUDED").sum()),
            "excluded_retracted_count": int((df["final_corpus_layer"] == "EXCLUDED_RETRACTED").sum()),
        },
        "languages_top": corpus_citable["language"].value_counts().head(8).to_dict(),
        "domains_represented_no_cutoff": corpus_citable["domain"].value_counts().to_dict(),
        "doc_types": corpus_citable["doc_type_norm"].value_counts().to_dict(),
        "conference_doc_types": corpus_conf["doc_type_norm"].value_counts().to_dict(),
        "horvitz_thompson_strata": meta_strata,
        "phase_summaries": {"fase1": m_f1, "fase2": m_f2, "fase3": m_f3, "fase4": m_f4},
    }
    (out_dir / "fase5_global_manifest.json").write_text(json.dumps(global_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        f"# Hybrid Scientific Field Delineation Manifest — {cfg['domain']['seed_topic_en']}",
        f"**UTC Timestamp:** {global_manifest['timestamp_utc']}  ",
        f"**Geographic Scope:** `{global_manifest['geo_scope']}` | **Years:** `{global_manifest['year_range'][0]}-{global_manifest['year_range'][1]}`",
        "",
        "## 1. Quantitative Flow (Phase 0 -> Phase 5)",
        f"- Unique deduplicated candidates (Phase 1): **{len(df):,}**",
        f"- **Canonical Citable Corpus (`./corpus.parquet`):** **{len(corpus_citable):,}** works",
        f"  - `STRICT_CORE` layer: **{len(corpus_strict):,}**",
        f"  - `EXTENDED_INTERDISCIPLINARY` layer: **{len(corpus_ext):,}**",
        f"- **Separated Conference Proceedings (`./corpus_conferences.parquet`):** **{len(corpus_conf):,}** works",
        f"- Pruned noise (`EXCLUDED`): **{(df['final_corpus_layer'] == 'EXCLUDED').sum():,}** | Retracted/paratext (`EXCLUDED_RETRACTED`): **{(df['final_corpus_layer'] == 'EXCLUDED_RETRACTED').sum():,}**",
        "",
        "## 2. Scientific Domain Distribution (Zero Blind Domains, No Cutoff)",
        *[f"- `{dom}`: **{cnt:,}**" for dom, cnt in global_manifest["domains_represented_no_cutoff"].items()],
        "",
        "## 3. Language & Document Type Breakdown",
        f"- Languages: `{json.dumps(global_manifest['languages_top'], ensure_ascii=False)}`",
        f"- Citable document types: `{json.dumps(global_manifest['doc_types'], ensure_ascii=False)}`",
        f"- Conference annex document types: `{json.dumps(global_manifest['conference_doc_types'], ensure_ascii=False)}`",
        "",
        "## 4. Horvitz-Thompson Stratified Blind Audit (n=360)",
        f"- Blind sample: `delineation/fase5_corpus_final/auditoria_ciega_muestra_n360.csv`",
        f"- Strata: `{json.dumps(meta_strata, ensure_ascii=False)}`",
    ]
    (rep_dir / "GLOBAL_PRISMA_S_MANIFEST.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(global_manifest["counts"], indent=2))

    from visual_artifacts import generate_phase_visuals
    generate_phase_visuals(5, wd, cfg)


if __name__ == "__main__":
    main()
