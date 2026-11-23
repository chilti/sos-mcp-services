"""
Phase 4: Graph-Augmented Gray Zone Adjudication (--judge-mode agent by default, or local_llm),
Cohen's Kappa Calibration, Dynamic Domain Rubric from Phase 0, and Optional 1-Hop Snowballing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_io import load_env_vars, load_or_create_config, norm_doi, norm_oa_id, phase_dir, resolve_workdir


def get_top3_green_neighbors(target_indices: np.ndarray, vecs: np.ndarray, df: pd.DataFrame) -> dict[int, list[str]]:
    green_idx = np.where((df["zona_triaje"].values == "ZONA_VERDE") & (np.linalg.norm(vecs, axis=1) > 0.1))[0]
    if len(green_idx) == 0 or len(target_indices) == 0:
        return {}
    X_g = vecs[green_idx]
    out: dict[int, list[str]] = {}
    k_top = min(3, len(green_idx))
    for s in range(0, len(target_indices), 512):
        bidx = target_indices[s : s + 512]
        sims = vecs[bidx] @ X_g.T
        top_pos = np.argpartition(sims, -k_top, axis=1)[:, -k_top:]
        for ri, di in enumerate(bidx):
            order = sorted(top_pos[ri], key=lambda gp: sims[ri, gp], reverse=True)
            out[int(di)] = [f"[{sims[ri, gp]:.2f}] {str(df.at[int(green_idx[gp]), 'title'])[:110]} ({df.at[int(green_idx[gp]), 'topic']})" for gp in order]
    return out


def build_dynamic_judge_prompt(cfg: dict, facets_init: dict) -> str:
    topic_en = cfg["domain"]["seed_topic_en"]
    topic_es = cfg["domain"]["seed_topic_es"]
    inc_rule = facets_init.get("scope_inclusion_criteria") or f"Direct theoretical, clinical, methodological, or empirical study centered on {topic_en}."
    exc_rule = facets_init.get("scope_exclusion_traps") or f"Homonyms or tangential mentions where {topic_en} is not the primary object of study."
    return (
        f"You are a senior domain & scientometrics expert performing boundary triage for the field '{topic_en}' / '{topic_es}'.\n"
        f"Classify EACH work_uid strictly into one of 3 classes:\n"
        f"- INCLUDE_CORE: {inc_rule} The target field ('{topic_en}' / '{topic_es}') MUST be the primary object, population, or system under investigation (not merely a secondary application example, background citation, or generic tool).\n"
        f"- INCLUDE_PERIPHERY: Legitimate interdisciplinary bridge where '{topic_en}' is substantively analyzed alongside another scientific discipline, but is not a pure single-domain study.\n"
        f"- EXCLUDE: {exc_rule} Also EXCLUDE works where terms appear only as lexical homonyms, incidental keywords, or unrelated disciplinary contexts.\n"
        "Use top3_green_neighbors carefully when abstract is '[NO ABSTRACT]'.\n"
        'Return strict JSON: {"decisions": {"WORK_UID": {"label": "INCLUDE_CORE|INCLUDE_PERIPHERY|EXCLUDE", "reason": "short phrase"}}}'
    )


def prepare_agent_triage_batches(df: pd.DataFrame, vecs: np.ndarray, cfg: dict, facets_init: dict, out_dir: Path, cache_jsonl: Path, max_docs: int = 100000, batch_size: int = 45) -> dict[str, Any]:
    gray_idx = np.where(df["zona_triaje"].values == "ZONA_GRIS")[0]
    if len(gray_idx) > max_docs:
        gray_idx = gray_idx[np.argsort(-df["rrf_score"].values[gray_idx])[:max_docs]]

    cached: dict[str, dict[str, str]] = {}
    if cache_jsonl.exists():
        for ln in cache_jsonl.read_text(encoding="utf-8", errors="ignore").splitlines():
            if ln.strip():
                try:
                    obj = json.loads(ln)
                    cached[obj["work_uid"]] = obj
                except Exception:
                    pass

    pending = [int(i) for i in gray_idx if df.at[int(i), "work_uid"] not in cached]
    bdir = out_dir / "agent_triage_batches"
    bdir.mkdir(parents=True, exist_ok=True)
    for old in list(bdir.glob("*.jsonl")) + list(bdir.glob("*.txt")):
        old.unlink()
    (bdir / "JUDGE_RUBRIC.txt").write_text(build_dynamic_judge_prompt(cfg, facets_init), encoding="utf-8")

    if not pending:
        return {"total_gray": int(len(gray_idx)), "cached": int(len(gray_idx)), "pending": 0, "n_batches": 0}

    no_abs = np.array([i for i in pending if not str(df.at[i, "abstract_final"] or "").strip()], dtype=np.int64)
    nbr_map = get_top3_green_neighbors(no_abs, vecs, df)
    pending_sorted = sorted(pending, key=lambda i: (int(df.at[i, "leiden_cluster"]), -float(df.at[i, "margin_score"])))

    n_batches = 0
    for s in range(0, len(pending_sorted), batch_size):
        bidx = pending_sorted[s : s + batch_size]
        items = []
        for i in bidx:
            ab = str(df.at[i, "abstract_final"] or "").strip()
            rec = {
                "work_uid": df.at[i, "work_uid"], "leiden_cluster": int(df.at[i, "leiden_cluster"]),
                "margin_score": round(float(df.at[i, "margin_score"]), 4),
                "title": str(df.at[i, "title"])[:260], "venue": str(df.at[i, "source_venue"])[:100],
                "topic": str(df.at[i, "topic"])[:100], "keywords": str(df.at[i, "keywords"])[:150],
                "abstract": ab[:280] if ab else "[NO ABSTRACT]",
            }
            if i in nbr_map:
                rec["top3_green_neighbors"] = nbr_map[i]
            items.append(rec)
        (bdir / f"batch_{n_batches:03d}.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in items) + "\n", encoding="utf-8")
        n_batches += 1

    return {"total_gray": int(len(gray_idx)), "cached": int(len(gray_idx) - len(pending)), "pending": int(len(pending)), "n_batches": n_batches, "batch_dir": str(bdir)}


def run_local_llm_triage(df: pd.DataFrame, vecs: np.ndarray, cfg: dict, facets_init: dict, api_key: str, cache_jsonl: Path, max_docs: int = 100000) -> pd.DataFrame:
    sys_p = build_dynamic_judge_prompt(cfg, facets_init)
    ep = cfg["endpoints"]
    all_gray_idx = np.where(df["zona_triaje"].values == "ZONA_GRIS")[0]
    gray_idx = all_gray_idx
    if len(gray_idx) > max_docs:
        gray_idx = gray_idx[np.argsort(-df["rrf_score"].values[gray_idx])[:max_docs]]

    cached = {}
    if cache_jsonl.exists():
        for ln in cache_jsonl.read_text(encoding="utf-8", errors="ignore").splitlines():
            if ln.strip():
                try:
                    obj = json.loads(ln)
                    cached[obj["work_uid"]] = obj
                except Exception:
                    pass
    pending = [int(i) for i in gray_idx if df.at[int(i), "work_uid"] not in cached]
    nbr_map = get_top3_green_neighbors(np.array([i for i in pending if not str(df.at[i, "abstract_final"] or "").strip()], dtype=np.int64), vecs, df)

    url = ep["llm_base_url"].rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    has_auth_kw = "author_keywords" in df.columns

    def _build_item(i: int) -> dict[str, Any]:
        kw_val = str(df.at[i, "author_keywords"] or "").strip() if has_auth_kw else ""
        if not kw_val:
            kw_val = str(df.at[i, "keywords"] or "").strip()
        return {
            "work_uid": df.at[i, "work_uid"],
            "title": str(df.at[i, "title"])[:260],
            "venue": str(df.at[i, "source_venue"])[:100],
            "topic": str(df.at[i, "topic"])[:100],
            "keywords": kw_val[:150],
            "abstract": str(df.at[i, "abstract_final"] or "")[:750] or "[NO ABSTRACT]",
            **({"top3_green_neighbors": nbr_map[i]} if i in nbr_map else {}),
        }

    def _parse_decisions(raw_txt: str, target_uids: list[str]) -> dict[str, dict[str, str]]:
        txt = re.sub(r"<think>.*?</think>", "", raw_txt or "", flags=re.DOTALL).strip()
        txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt, flags=re.IGNORECASE | re.DOTALL).strip()
        m = re.search(r"\{.*\}", txt, flags=re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
                if isinstance(parsed, dict):
                    decs = parsed.get("decisions", parsed)
                    if isinstance(decs, dict) and any(u in decs for u in target_uids):
                        return decs
            except Exception:
                pass
        # Regex salvage for single-item or partially truncated JSON
        salvaged: dict[str, dict[str, str]] = {}
        for uid in target_uids:
            pat = re.compile(rf'"{re.escape(uid)}"\s*:\s*\{{[^}}]*?"label"\s*:\s*"(INCLUDE_CORE|INCLUDE_PERIPHERY|EXCLUDE)"(?:[^}}]*?"reason"\s*:\s*"([^"]*)")?', re.IGNORECASE)
            hit = pat.search(txt)
            if hit:
                salvaged[uid] = {"label": hit.group(1).upper(), "reason": (hit.group(2) or "llm_regex_salvaged")[:180]}
        if not salvaged and len(target_uids) == 1:
            m_lbl = re.search(r"\b(INCLUDE_CORE|INCLUDE_PERIPHERY|EXCLUDE)\b", txt)
            if m_lbl:
                salvaged[target_uids[0]] = {"label": m_lbl.group(1), "reason": "llm_single_salvaged"}
        return salvaged

    def _query_batch_recursive(batch_idx: list[int]) -> dict[str, dict[str, str]]:
        if not batch_idx:
            return {}
        items = [_build_item(i) for i in batch_idx]
        target_uids = [df.at[i, "work_uid"] for i in batch_idx]
        for use_effort in (True, False):
            payload: dict[str, Any] = {
                "model": ep["llm_model"],
                "temperature": 0.0,
                "max_tokens": max(600, 260 * len(batch_idx)),
                "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": json.dumps(items, ensure_ascii=False)}],
            }
            if use_effort:
                payload["reasoning_effort"] = "low"
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=90)
                if r.status_code == 400 and use_effort:
                    continue
                if r.status_code == 200:
                    msg = r.json()["choices"][0]["message"]
                    decs = _parse_decisions(msg.get("content") or "", target_uids)
                    if decs:
                        return decs
                break
            except Exception:
                if not use_effort:
                    break
        if len(batch_idx) > 1:
            mid = len(batch_idx) // 2
            out_decs = _query_batch_recursive(batch_idx[:mid])
            out_decs.update(_query_batch_recursive(batch_idx[mid:]))
            return out_decs
        return {}

    with cache_jsonl.open("a", encoding="utf-8") as fout:
        for s in range(0, len(pending), 5):
            bidx = pending[s : s + 5]
            decs = _query_batch_recursive(bidx)
            for i in bidx:
                uid = df.at[i, "work_uid"]
                raw_d = decs.get(uid, {}) if isinstance(decs, dict) else {}
                if isinstance(raw_d, str):
                    d = {"label": raw_d.strip(), "reason": "llm_str_label"}
                elif isinstance(raw_d, dict):
                    d = raw_d
                else:
                    d = {}
                lbl = str(d.get("label", "")).upper().strip()
                is_valid = lbl in ("INCLUDE_CORE", "INCLUDE_PERIPHERY", "EXCLUDE")
                if not is_valid:
                    lbl = "INCLUDE_CORE" if df.at[i, "margin_score"] >= 0.055 and df.at[i, "title_free_hits"] >= 1 else ("INCLUDE_PERIPHERY" if df.at[i, "margin_score"] >= 0.032 else "EXCLUDE")
                rec = {
                    "work_uid": uid,
                    "label": lbl,
                    "reason": str(d.get("reason", "auto_margin_fallback") if is_valid else "auto_margin_fallback")[:180],
                    "judge": "local_llm" if is_valid else "auto_margin_fallback",
                }
                cached[uid] = rec
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            time.sleep(0.05)

    df["llm_decision"] = "NOT_EVALUATED"
    df["llm_reason"] = ""
    df["llm_judge_source"] = ""
    for i in all_gray_idx:
        idx = int(i)
        uid = df.at[idx, "work_uid"]
        if uid in cached:
            df.at[idx, "llm_decision"] = cached[uid]["label"]
            df.at[idx, "llm_reason"] = cached[uid].get("reason", "")
            df.at[idx, "llm_judge_source"] = cached[uid].get("judge", "local_llm")
        else:
            m_sc, lr_p = float(df.at[idx, "margin_score"]), float(df.at[idx, "logreg_prob"])
            tf_h, tt = int(df.at[idx, "title_free_hits"]), int(df.at[idx, "topic_tier"])
            hom = bool(df.at[idx, "homonym_hit"])
            if (not hom) and m_sc >= 0.055 and lr_p >= 0.78 and (tf_h >= 1 or tt == 2):
                lbl = "INCLUDE_CORE"
            elif (not hom) and m_sc >= 0.032 and lr_p >= 0.60 and (tf_h >= 1 or tt >= 1 or bool(df.at[idx, "coupled_match"])):
                lbl = "INCLUDE_PERIPHERY"
            else:
                lbl = "EXCLUDE"
            df.at[idx, "llm_decision"] = lbl
            df.at[idx, "llm_reason"] = "graph_margin_consensus"
            df.at[idx, "llm_judge_source"] = "graph_margin_consensus"
    return df


def apply_cached_decisions(df: pd.DataFrame, cache_jsonl: Path) -> pd.DataFrame:
    cached: dict[str, dict[str, str]] = {}
    if cache_jsonl.exists():
        for ln in cache_jsonl.read_text(encoding="utf-8", errors="ignore").splitlines():
            if ln.strip():
                try:
                    obj = json.loads(ln)
                    cached[obj["work_uid"]] = obj
                except Exception:
                    pass
    df["llm_decision"] = "NOT_EVALUATED"
    df["llm_reason"] = ""
    df["llm_judge_source"] = ""
    for i in df.index:
        uid = df.at[i, "work_uid"]
        if uid in cached:
            lbl = str(cached[uid].get("label", "EXCLUDE")).upper()
            df.at[i, "llm_decision"] = lbl if lbl in ("INCLUDE_CORE", "INCLUDE_PERIPHERY", "EXCLUDE") else "EXCLUDE"
            df.at[i, "llm_reason"] = str(cached[uid].get("reason", ""))[:180]
            df.at[i, "llm_judge_source"] = str(cached[uid].get("judge", "agent"))
        elif df.at[i, "zona_triaje"] == "ZONA_GRIS":
            m_sc, lr_p = float(df.at[i, "margin_score"]), float(df.at[i, "logreg_prob"])
            tf_h, tt = int(df.at[i, "title_free_hits"]), int(df.at[i, "topic_tier"])
            hom = bool(df.at[i, "homonym_hit"])
            if (not hom) and m_sc >= 0.055 and lr_p >= 0.78 and (tf_h >= 1 or tt == 2):
                lbl = "INCLUDE_CORE"
            elif (not hom) and m_sc >= 0.032 and lr_p >= 0.60 and (tf_h >= 1 or tt >= 1 or bool(df.at[i, "coupled_match"])):
                lbl = "INCLUDE_PERIPHERY"
            else:
                lbl = "EXCLUDE"
            df.at[i, "llm_decision"] = lbl
            df.at[i, "llm_reason"] = "graph_margin_consensus"
            df.at[i, "llm_judge_source"] = "graph_margin_consensus"
    return df


def fetch_clickhouse_references_batched(df: pd.DataFrame, env: dict[str, str] | None) -> pd.DataFrame | None:
    """Query rag.works_flat.referenced_works in batches via id IN (...) with ZERO JOINs."""
    if not env or not env.get("CLICKHOUSE_HOST"):
        return None
    raw_ids = sorted({str(x).strip() for x in df.get("oa_id", pd.Series(dtype=str)).dropna() if str(x).strip()})
    if not raw_ids:
        return None
    full_ids: list[str] = []
    for oid in raw_ids:
        short = oid.replace("https://openalex.org/", "").strip()
        if short:
            full_ids.append(f"https://openalex.org/{short}")
    if not full_ids:
        return None
    try:
        import clickhouse_connect

        ch_pass = env.get("CLICKHOUSE_PASSWORD", "").replace("$$", "$")
        client = clickhouse_connect.get_client(
            host=env.get("CLICKHOUSE_HOST", "localhost"),
            port=int(env.get("CLICKHOUSE_PORT", 8123)),
            username=env.get("CLICKHOUSE_USER", "default"),
            password=ch_pass,
            database=env.get("CLICKHOUSE_DATABASE", "rag"),
        )
        chunks: list[pd.DataFrame] = []
        for s in range(0, len(full_ids), 5000):
            batch = full_ids[s : s + 5000]
            in_list = ", ".join("'" + x.replace("'", "''") + "'" for x in batch)
            q = f"SELECT id, doi, referenced_works FROM rag.works_flat WHERE id IN ({in_list})"
            cdf = client.query_df(q)
            if not cdf.empty:
                chunks.append(cdf)
        return pd.concat(chunks, ignore_index=True) if chunks else None
    except Exception as exc:
        print(f"  [Snowball ClickHouse warning] {exc}")
        return None


def run_snowballing(df: pd.DataFrame, cfg: dict, refs_parquet: Path | None = None, env: dict[str, str] | None = None) -> tuple[pd.DataFrame, int]:
    df["snowball_green_links"] = 0
    df["snowball_rescued"] = False
    if refs_parquet is not None and refs_parquet.exists():
        oa = pd.read_parquet(refs_parquet, columns=["id", "doi", "referenced_works"])
    else:
        oa = fetch_clickhouse_references_batched(df, env)
        if oa is None or oa.empty:
            return df, 0
    oa["oa_id"] = oa["id"].map(norm_oa_id)
    oa["doi_n"] = oa["doi"].map(norm_doi)
    oid_by_doi = {d: o for o, d in zip(oa["oa_id"], oa["doi_n"]) if o and d}
    refs_by_oid = {o: [str(x).split("/")[-1].upper() for x in rw if x] for o, rw in zip(oa["oa_id"], oa["referenced_works"]) if o and isinstance(rw, (list, np.ndarray))}
    resolved = [r.oa_id or oid_by_doi.get(str(r.doi_norm or ""), "") for r in df.itertuples(index=False)]
    green = {o for o, z in zip(resolved, df["zona_triaje"]) if o and z == "ZONA_VERDE"}
    link_cnt: dict[str, int] = {}
    for o in green:
        for ref in refs_by_oid.get(o, []):
            link_cnt[ref] = link_cnt.get(ref, 0) + 1
    min_l, min_m = int(cfg["thresholds"]["snowball_min_core_links"]), float(cfg["thresholds"]["snowball_min_margin"])
    rescued = 0
    for i, r in enumerate(df.itertuples(index=False)):
        o = resolved[i]
        if not o or r.zona_triaje == "ZONA_VERDE":
            continue
        tot = sum(1 for ref in refs_by_oid.get(o, []) if ref in green) + link_cnt.get(o, 0)
        df.at[i, "snowball_green_links"] = tot
        if tot >= min_l and r.margin_score >= min_m and r.llm_decision != "EXCLUDE":
            df.at[i, "snowball_rescued"] = True
            rescued += 1
    return df, rescued


def assign_final_layers(df: pd.DataFrame) -> pd.DataFrame:
    layers = []
    for r in df.itertuples(index=False):
        if r.zona_triaje == "ZONA_VERDE":
            layers.append("STRICT_CORE")
        elif r.zona_triaje == "ZONA_GRIS":
            if r.llm_decision == "INCLUDE_CORE":
                layers.append("STRICT_CORE")
            elif r.llm_decision == "INCLUDE_PERIPHERY" or r.snowball_rescued:
                layers.append("EXTENDED_INTERDISCIPLINARY")
            else:
                layers.append("EXCLUDED")
        else:
            layers.append("EXTENDED_INTERDISCIPLINARY" if r.snowball_rescued else "EXCLUDED")
    df["final_corpus_layer"] = layers
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=str, default=".")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--judge-mode", choices=["local_llm", "agent"], default="local_llm", help="local_llm (default): evaluate Gray Zone with configured local OpenAI-compatible model; agent: prepare JSONL batches for host agent")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--max-llm-docs", type=int, default=100000)
    parser.add_argument("--batch-size", type=int, default=45)
    parser.add_argument("--refs-parquet", type=str, default=None, help="Optional Parquet with OpenAlex referenced_works for 1-hop snowballing")
    parser.add_argument("--human-calibration-csv", type=str, default=None)
    args = parser.parse_args()

    wd = resolve_workdir(args.workdir)
    cfg, _ = load_or_create_config(wd, config_path=args.config)
    env = load_env_vars(wd, cfg)
    api_key = env.get("LLM_API_KEY", "lm-studio")

    f0_dir = phase_dir(wd, "fase0_estrategia")
    f1_dir = phase_dir(wd, "fase1_corpus")
    f3_dir = phase_dir(wd, "fase3_manifold")
    out_dir = phase_dir(wd, "fase4_llm_snowball")

    df = pd.read_parquet(f3_dir / "corpus_triaged_leiden.parquet")
    vecs = np.load(f1_dir / "embeddings_dense.npy")
    facets_init = json.loads((f0_dir / "facets_init.json").read_text(encoding="utf-8")) if (f0_dir / "facets_init.json").exists() else {}
    cache_jsonl = out_dir / "cache_llm_gris.jsonl"

    if args.judge_mode == "agent" and not args.finalize:
        prep = prepare_agent_triage_batches(df, vecs, cfg, facets_init, out_dir, cache_jsonl, max_docs=args.max_llm_docs, batch_size=args.batch_size)
        print("[Agent Judge Preparation]", json.dumps(prep, ensure_ascii=False))
        if prep["pending"] > 0:
            print("-> Evaluate batch_*.jsonl into cache_llm_gris.jsonl and run again with --finalize (or run --finalize to use graph-margin consensus fallback).")
            return

    if args.judge_mode == "local_llm":
        df = run_local_llm_triage(df, vecs, cfg, facets_init, api_key, cache_jsonl, max_docs=args.max_llm_docs)
    else:
        df = apply_cached_decisions(df, cache_jsonl)

    kappa = None
    if args.human_calibration_csv and Path(args.human_calibration_csv).exists():
        cal = pd.read_csv(args.human_calibration_csv)
        cal = cal[cal["human_label"].isin(["INCLUDE_CORE", "INCLUDE_PERIPHERY", "EXCLUDE"])]
        if len(cal) >= 20:
            kappa = float(cohen_kappa_score(cal["human_label"], cal["llm_decision"]))

    df, rescued = run_snowballing(df, cfg, Path(args.refs_parquet) if args.refs_parquet else None, env=env)
    df = assign_final_layers(df)
    df.to_parquet(out_dir / "corpus_triage_completo.parquet", index=False)

    gray_df = df[df["zona_triaje"] == "ZONA_GRIS"]
    evaluated_gray = gray_df[gray_df["llm_decision"] != "NOT_EVALUATED"]
    fb_count = int((evaluated_gray["llm_reason"] == "auto_margin_fallback").sum()) if not evaluated_gray.empty else 0
    summary = {
        "judge_mode": args.judge_mode,
        "zona_gris_total": int(len(gray_df)),
        "zona_gris_evaluated": int(len(evaluated_gray)),
        "fallback_count": fb_count,
        "fallback_rate": round(fb_count / max(1, len(evaluated_gray)), 4),
        "zona_gris_llm_counts": gray_df["llm_decision"].value_counts().to_dict(),
        "snowball_rescued": rescued,
        "kappa_calibrated": kappa,
        "final_layer_counts": df["final_corpus_layer"].value_counts().to_dict(),
    }
    (out_dir / "fase4_llm_metrics.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    from visual_artifacts import generate_phase_visuals
    generate_phase_visuals(4, wd, cfg)


if __name__ == "__main__":
    main()
