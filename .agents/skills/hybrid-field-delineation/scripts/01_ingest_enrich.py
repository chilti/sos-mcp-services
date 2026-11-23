"""
Phase 1: Workspace-First Multi-Source Clean-Room Harvest (OpenAlex API / Manual CSV / ClickHouse optional,
PubMed API, WoS exports, Scopus exports), Geographic Disambiguation, Open-Source Abstract Recovery Cascade
(Semantic Scholar Batch API + OpenAlex DOI fallback), 4-Level Hybrid Deduplication, and Local-First Embeddings.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import socket
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_io import (
    first_author_surname,
    load_env_vars,
    load_or_create_config,
    norm_doi,
    norm_oa_id,
    norm_pmid,
    norm_title,
    phase_dir,
    resolve_workdir,
    strip_accents,
)


def is_valid_geo_affiliation(aff_text: str, rx_pos: re.Pattern | None, rx_neg: re.Pattern | None, country_codes: str, target_iso: str) -> bool:
    if not target_iso:
        return True
    cc = str(country_codes or "").upper()
    if target_iso in re.split(r"[,;\s|]+", cc):
        return True
    if rx_pos is None:
        return True
    txt = strip_accents(aff_text or "")
    has_pos = bool(rx_pos.search(txt))
    has_neg = bool(rx_neg.search(txt)) if rx_neg else False
    return has_pos and not has_neg


def _extract_precomputed_vector(val: Any) -> list[float] | None:
    """Normalizes a precomputed embedding array/list into an L2-unit float list, or None if empty."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, str):
        s = val.strip()
        if not s or s == "[]":
            return None
        try:
            val = json.loads(s)
        except Exception:
            return None
    try:
        arr = np.asarray(val, dtype=np.float32).ravel()
    except Exception:
        return None
    if arr.size < 16 or not np.all(np.isfinite(arr)):
        return None
    nrm = float(np.linalg.norm(arr))
    if nrm <= 0.0:
        return None
    return (arr / nrm).astype(np.float32).tolist()


def _join_seq_cell(val: Any, sep: str = ", ") -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    if isinstance(val, (list, tuple, np.ndarray)):
        return sep.join(str(x).strip() for x in val if str(x).strip())
    return str(val).strip()


def standardize_columns(df: pd.DataFrame, source_tag: str) -> pd.DataFrame:
    cols = [
        "oa_id", "doi_norm", "pmid_norm", "pmcid", "title", "title_norm",
        "publication_year", "doc_type", "language", "source_venue", "topic",
        "subfield", "field", "domain", "keywords", "author_names", "first_surname",
        "affiliations_raw", "country_codes", "abstract_final", "abstract_source",
        "cited_by_count", "fwci", "is_oa", "oa_status", "apc_paid_usd", "source_origin",
    ]
    out = pd.DataFrame(index=df.index)
    for c in cols:
        out[c] = df[c] if c in df.columns else ""
    out["source_origin"] = source_tag
    out["publication_year"] = pd.to_numeric(out["publication_year"], errors="coerce").fillna(0).astype(int)
    out["cited_by_count"] = pd.to_numeric(out["cited_by_count"], errors="coerce").fillna(0).astype(int)
    out["fwci"] = pd.to_numeric(out["fwci"], errors="coerce").fillna(0.0).astype(float)
    out["apc_paid_usd"] = pd.to_numeric(out["apc_paid_usd"], errors="coerce").fillna(0.0).astype(float)
    out["doi_norm"] = out["doi_norm"].map(norm_doi)
    out["pmid_norm"] = out["pmid_norm"].map(norm_pmid)
    out["oa_id"] = out["oa_id"].map(norm_oa_id)
    out["title_norm"] = out["title"].map(norm_title)
    out["first_surname"] = out["author_names"].map(first_author_surname)
    if "_precomputed_vec" in df.columns:
        out["_precomputed_vec"] = df["_precomputed_vec"].values
    else:
        out["_precomputed_vec"] = None
    return out


def reconstruct_inv_idx(inv_idx: dict | None) -> str:
    if not isinstance(inv_idx, dict) or not inv_idx:
        return ""
    pairs = sorted((p, w) for w, poss in inv_idx.items() for p in poss)
    return " ".join(w for _, w in pairs)


def load_wos_folder(wos_dir: Path, y0: int, y1: int, rx_pos: re.Pattern | None, rx_neg: re.Pattern | None, target_iso: str) -> tuple[pd.DataFrame, int]:
    files = sorted(wos_dir.glob("*.txt")) if wos_dir.exists() else []
    if not files:
        return pd.DataFrame(), 0
    csv.field_size_limit(10_000_000)
    rows, hdr = [], None
    for p in files:
        with p.open(encoding="utf-8-sig", errors="ignore") as f:
            rdr = csv.reader((ln.replace("\0", "") for ln in f), delimiter="\t", quoting=csv.QUOTE_NONE)
            h = next(rdr)
            hdr = hdr or h
            for row in rdr:
                if len(row) >= len(h):
                    rows.append(row[: len(h)])
    if not rows or not hdr:
        return pd.DataFrame(), 0
    raw = pd.DataFrame(rows, columns=hdr)
    df = pd.DataFrame()
    df["doi_norm"] = raw["DI"].map(norm_doi) if "DI" in raw else ""
    df["pmid_norm"] = raw["PM"].map(norm_pmid) if "PM" in raw else ""
    df["title"] = raw["TI"].fillna("").astype(str)
    df["publication_year"] = pd.to_numeric(raw.get("PY", 0), errors="coerce").fillna(0).astype(int)
    df["doc_type"] = raw.get("DT", pd.Series("", index=raw.index)).fillna("").astype(str).str.lower()
    df["source_venue"] = raw.get("SO", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["topic"] = raw.get("WC", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["keywords"] = raw.get("AK", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["author_names"] = raw.get("AU", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["affiliations_raw"] = raw.get("C1", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["abstract_final"] = raw.get("AB", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["abstract_source"] = np.where(df["abstract_final"].str.strip() != "", "wos_export", "")
    df["cited_by_count"] = pd.to_numeric(raw.get("TC", 0), errors="coerce").fillna(0).astype(int)
    df["country_codes"] = target_iso
    df = df[(df["publication_year"] >= y0) & (df["publication_year"] <= y1)].copy()
    mask = [True if (not target_iso or not str(a).strip()) else is_valid_geo_affiliation(a, rx_pos, rx_neg, "", target_iso) for a in df["affiliations_raw"]]
    dropped = int((~np.array(mask, dtype=bool)).sum())
    df = df[mask].copy()
    print(f"  [WoS Export] {len(df)} records ({y0}-{y1}), dropped non-target geo={dropped}.")
    return standardize_columns(df, "wos_cleanroom"), dropped


def load_scopus_folder(scopus_dir: Path, y0: int, y1: int, target_iso: str) -> pd.DataFrame:
    files = sorted(scopus_dir.glob("*.csv")) if scopus_dir.exists() else []
    if not files:
        return pd.DataFrame()
    raw = pd.concat([pd.read_csv(p, low_memory=False) for p in files], ignore_index=True)
    if "EID" in raw.columns:
        raw = raw.drop_duplicates(subset=["EID"]).reset_index(drop=True)
    df = pd.DataFrame()
    df["doi_norm"] = raw.get("DOI", pd.Series("", index=raw.index)).map(norm_doi)
    df["title"] = raw.get("Title", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["publication_year"] = pd.to_numeric(raw.get("Year", 0), errors="coerce").fillna(0).astype(int)
    df["doc_type"] = raw.get("Document Type", pd.Series("", index=raw.index)).fillna("").astype(str).str.lower()
    df["source_venue"] = raw.get("Source title", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["keywords"] = raw.get("Author Keywords", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["abstract_final"] = raw.get("Abstract", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["abstract_source"] = np.where((df["abstract_final"].str.strip() != "") & (~df["abstract_final"].str.contains("No abstract available", case=False)), "scopus_export", "")
    df.loc[df["abstract_source"] == "", "abstract_final"] = ""
    df["author_names"] = raw.get("Authors", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["cited_by_count"] = pd.to_numeric(raw.get("Cited by", 0), errors="coerce").fillna(0).astype(int)
    df["is_oa"] = raw.get("Open Access", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["country_codes"] = target_iso
    df = df[(df["publication_year"] >= y0) & (df["publication_year"] <= y1)].copy()
    print(f"  [Scopus Export] {len(df)} unique records ({y0}-{y1}).")
    return standardize_columns(df, "scopus_cleanroom")


def load_oa_manual_folder(oa_dir: Path, y0: int, y1: int, rx_pos: re.Pattern | None, rx_neg: re.Pattern | None, target_iso: str) -> pd.DataFrame:
    if not oa_dir.exists():
        return pd.DataFrame()
    files = sorted(oa_dir.glob("*.csv")) + sorted(oa_dir.glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    raw = pd.concat([pd.read_parquet(p) if p.suffix.lower() == ".parquet" else pd.read_csv(p, low_memory=False) for p in files], ignore_index=True)
    df = pd.DataFrame(index=raw.index)
    if "Title" in raw.columns and "title" not in raw.columns:
        df["title"] = raw["Title"].fillna("").astype(str)
        df["author_names"] = raw.get("Author", pd.Series("", index=raw.index)).fillna("").astype(str)
        df["publication_year"] = pd.to_numeric(raw.get("Year", 0), errors="coerce").fillna(0).astype(int)
        df["cited_by_count"] = pd.to_numeric(raw.get("Citation count", 0), errors="coerce").fillna(0).astype(int)
        df["is_oa"] = raw.get("Open access", pd.Series("", index=raw.index)).astype(str)
        df["doi_norm"] = raw.get("DOI", pd.Series("", index=raw.index)).map(norm_doi)
        sids = raw.get("Source IDs", pd.Series("", index=raw.index)).fillna("").astype(str)
        df["oa_id"] = sids.str.extract(r"https://openalex\.org/(W\d+)", expand=False).fillna("")
        df["pmid_norm"] = sids.str.extract(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", expand=False).fillna("")
        ctry = raw.get("Country", pd.Series(target_iso, index=raw.index)).fillna("").astype(str)
    else:
        df["oa_id"] = raw.get("id", pd.Series("", index=raw.index)).map(norm_oa_id)
        df["doi_norm"] = raw.get("doi", pd.Series("", index=raw.index)).map(norm_doi)
        df["pmid_norm"] = raw.get("ids.pmid", raw.get("pmid", pd.Series("", index=raw.index))).map(norm_pmid)
        df["title"] = raw.get("title", raw.get("display_name", pd.Series("", index=raw.index))).fillna("").astype(str)
        df["publication_year"] = pd.to_numeric(raw.get("publication_year", 0), errors="coerce").fillna(0).astype(int)
        df["doc_type"] = raw.get("type", pd.Series("", index=raw.index)).fillna("").astype(str).str.lower()
        df["language"] = raw.get("language", pd.Series("", index=raw.index)).fillna("").astype(str).str.lower()
        df["source_venue"] = raw.get("primary_location.source.display_name", pd.Series("", index=raw.index)).fillna("").astype(str)
        df["topic"] = raw.get("primary_topic.display_name", pd.Series("", index=raw.index)).fillna("").astype(str)
        df["subfield"] = raw.get("primary_topic.subfield.display_name", pd.Series("", index=raw.index)).fillna("").astype(str)
        df["field"] = raw.get("primary_topic.field.display_name", pd.Series("", index=raw.index)).fillna("").astype(str)
        df["domain"] = raw.get("primary_topic.domain.display_name", pd.Series("", index=raw.index)).fillna("").astype(str)
        df["author_names"] = raw.get("authorships.author.display_name", pd.Series("", index=raw.index)).fillna("").astype(str)
        df["cited_by_count"] = pd.to_numeric(raw.get("cited_by_count", 0), errors="coerce").fillna(0).astype(int)
        df["is_oa"] = raw.get("open_access.is_oa", pd.Series("", index=raw.index)).astype(str)
        ctry = raw.get("authorships.countries", pd.Series(target_iso, index=raw.index)).fillna("").astype(str)
    df["country_codes"] = np.where(ctry.str.strip() != "", ctry, target_iso)
    df = df[(df["publication_year"] >= y0) & (df["publication_year"] <= y1)].copy()
    print(f"  [OpenAlex Manual Export] {len(df)} records loaded from {oa_dir.name}/.")
    return standardize_columns(df, "oa_cleanroom_manual")


def _resolve_precomputed_col(df: pd.DataFrame, preferred: str = "auto") -> str | None:
    if preferred == "none":
        return None
    if preferred != "auto":
        return preferred if preferred in df.columns else None
    for cand in ("embedding_qwen", "embedding_nomic", "embedding", "dense_vector", "_precomputed_vec"):
        if cand in df.columns:
            return cand
    return None


def normalize_clickhouse_df(raw: pd.DataFrame, y0: int, y1: int, target_iso: str, source_tag: str = "clickhouse_mx_enriched", precomputed_col: str = "auto") -> pd.DataFrame:
    """Normalizes ClickHouse works_mexico_abstracts_enriched / works_flat exports and retains precomputed dense vectors."""
    if raw.empty:
        return pd.DataFrame()
    raw = raw.copy()
    if "is_retracted" in raw.columns:
        raw = raw[pd.to_numeric(raw["is_retracted"], errors="coerce").fillna(0) == 0]
    if "is_paratext" in raw.columns:
        raw = raw[pd.to_numeric(raw["is_paratext"], errors="coerce").fillna(0) == 0]
    raw["publication_year"] = pd.to_numeric(raw.get("publication_year", 0), errors="coerce").fillna(0).astype(int)
    raw = raw[(raw["publication_year"] >= y0) & (raw["publication_year"] <= y1)].copy()
    if raw.empty:
        return pd.DataFrame()

    df = pd.DataFrame(index=raw.index)
    df["oa_id"] = raw.get("id", raw.get("oa_id", pd.Series("", index=raw.index))).map(norm_oa_id)
    df["doi_norm"] = raw.get("doi", raw.get("doi_norm", pd.Series("", index=raw.index))).map(norm_doi)
    df["pmid_norm"] = raw.get("pmid", raw.get("pmid_norm", pd.Series("", index=raw.index))).map(norm_pmid)
    df["pmcid"] = raw.get("pmcid", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["title"] = raw.get("title", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["publication_year"] = raw["publication_year"]
    df["doc_type"] = raw.get("type", raw.get("doc_type", pd.Series("", index=raw.index))).fillna("").astype(str).str.lower()
    df["language"] = raw.get("language", pd.Series("", index=raw.index)).fillna("").astype(str).str.lower()
    df["source_id"] = raw.get("source_id", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["source_venue"] = raw.get("source_venue", raw.get("source_name", raw.get("source_id", pd.Series("", index=raw.index)))).fillna("").astype(str)
    df["topic"] = raw.get("topic", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["subfield"] = raw.get("subfield", raw.get("subfield_name", pd.Series("", index=raw.index))).fillna("").astype(str)
    df["field"] = raw.get("field", raw.get("field_name", pd.Series("", index=raw.index))).fillna("").astype(str)
    df["domain"] = raw.get("domain", raw.get("domain_name", pd.Series("", index=raw.index))).fillna("").astype(str)

    akw = raw["author_keywords"].map(lambda v: _join_seq_cell(v, ", ")) if "author_keywords" in raw.columns else pd.Series("", index=raw.index)
    okw = raw["keywords"].map(lambda v: _join_seq_cell(v, ", ")) if "keywords" in raw.columns else pd.Series("", index=raw.index)
    df["author_keywords"] = akw
    df["oa_keywords"] = okw
    df["keywords"] = [
        ", ".join(dict.fromkeys([t.strip() for t in f"{a}, {k}".split(",") if t.strip()]))
        for a, k in zip(akw, okw)
    ]
    df["author_names"] = raw["author_names"].map(lambda v: _join_seq_cell(v, "; ")) if "author_names" in raw.columns else ""
    if "country_codes" in raw.columns:
        cc_vals = raw["country_codes"].map(lambda v: _join_seq_cell(v, ","))
        df["country_codes"] = np.where(cc_vals.str.strip() != "", cc_vals, target_iso)
    else:
        df["country_codes"] = target_iso
    df["abstract_final"] = raw.get("abstract_final", raw.get("abstract", pd.Series("", index=raw.index))).fillna("").astype(str)
    df["abstract_source"] = raw.get("abstract_source", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["cited_by_count"] = pd.to_numeric(raw.get("cited_by_count", pd.Series(0, index=raw.index)), errors="coerce").fillna(0).astype(int)
    df["fwci"] = pd.to_numeric(raw.get("fwci", pd.Series(0.0, index=raw.index)), errors="coerce").fillna(0.0).astype(float)
    df["is_oa"] = raw.get("is_oa", pd.Series("", index=raw.index)).astype(str)
    df["oa_status"] = raw.get("oa_status", pd.Series("", index=raw.index)).fillna("").astype(str)
    df["apc_paid_usd"] = pd.to_numeric(raw.get("apc_paid_usd", pd.Series(0.0, index=raw.index)), errors="coerce").fillna(0.0).astype(float)

    vec_col = _resolve_precomputed_col(raw, precomputed_col)
    if vec_col:
        df["_precomputed_vec"] = [_extract_precomputed_vector(v) for v in raw[vec_col].tolist()]
        n_vec = sum(v is not None for v in df["_precomputed_vec"])
        print(f"  [ClickHouse Precomputed Vectors] Column '{vec_col}' retained for {n_vec}/{len(df)} works.")
    return standardize_columns(df, source_tag)


def load_clickhouse_parquet_inputs(ch_path: Path | None, default_dir: Path, y0: int, y1: int, target_iso: str, precomputed_col: str) -> pd.DataFrame:
    files: list[Path] = []
    if ch_path is not None:
        if ch_path.is_file():
            files = [ch_path]
        elif ch_path.is_dir():
            files = sorted(ch_path.glob("*.parquet"))
    elif default_dir.exists():
        files = sorted(default_dir.glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    raw = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)
    if "id" in raw.columns:
        raw = raw.drop_duplicates(subset=["id"]).reset_index(drop=True)
    df = normalize_clickhouse_df(raw, y0, y1, target_iso, source_tag="clickhouse_mx_enriched", precomputed_col=precomputed_col)
    print(f"  [ClickHouse Parquet] {len(df)} records loaded from {len(files)} file(s).")
    return df


def harvest_clickhouse(spec_path: Path, cache_pq: Path, y0: int, y1: int, target_iso: str, env: dict[str, str], precomputed_col: str = "auto") -> pd.DataFrame:
    """Executes ZERO-JOIN ClickHouse harvest reading precomputed MX vectors when available."""
    if cache_pq.exists():
        cached = pd.read_parquet(cache_pq)
        if precomputed_col != "none" and precomputed_col != "auto" and precomputed_col in cached.columns:
            cached["_precomputed_vec"] = [_extract_precomputed_vector(v) for v in cached[precomputed_col].tolist()]
        print(f"  [ClickHouse Cache] {len(cached)} records loaded.")
        return cached
    if not spec_path.exists():
        return pd.DataFrame()
    try:
        import clickhouse_connect
    except ImportError as exc:
        raise RuntimeError("clickhouse_connect is required for --openalex-cleanroom clickhouse (or pass --clickhouse-parquet).") from exc

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    ch_spec = spec.get("clickhouse") or {}
    if not ch_spec.get("enriched_where"):
        raise RuntimeError("Phase 0 clickhouse specification missing in openalex_api_broad.json; re-run 00_build_strategy.py.")

    client = clickhouse_connect.get_client(
        host=env.get("CLICKHOUSE_HOST") or env.get("CH_HOST") or "localhost",
        port=int(env.get("CLICKHOUSE_PORT") or 8123),
        username=env.get("CLICKHOUSE_USER") or "default",
        password=(env.get("CLICKHOUSE_PASSWORD") or env.get("CLICKHOUSE_CLEAN_PASSWORD") or "").replace("$$", "$"),
        database=env.get("CLICKHOUSE_DATABASE") or "rag",
        connect_timeout=10,
        send_receive_timeout=300,
    )
    is_mx = bool(ch_spec.get("is_mx_enriched"))
    vec_col = "embedding_nomic" if precomputed_col == "embedding_nomic" else "embedding_qwen"
    if is_mx:
        sel_cols = "id, doi, pmid, pmcid, publication_year, type, language, is_oa, source_id, title, author_keywords, keywords, abstract_final, abstract_source"
        if precomputed_col != "none":
            sel_cols += f", {vec_col}"
        q1 = f"SELECT {sel_cols} FROM rag.works_mexico_abstracts_enriched FINAL WHERE {ch_spec['enriched_where']}"
        df_base = client.query_df(q1)
        flat_topics_where = ch_spec.get("flat_topics_where") or ""
        if flat_topics_where:
            df_tids = client.query_df(f"SELECT id FROM rag.works_flat WHERE {flat_topics_where}")
            extra_ids = sorted(set(df_tids["id"].astype(str)) - set(df_base["id"].astype(str))) if not df_tids.empty else []
            extra_chunks = []
            for s in range(0, len(extra_ids), 5000):
                batch_ids = ", ".join("'" + x.replace("'", "") + "'" for x in extra_ids[s : s + 5000])
                extra_chunks.append(client.query_df(f"SELECT {sel_cols} FROM rag.works_mexico_abstracts_enriched FINAL WHERE id IN ({batch_ids})"))
            if extra_chunks:
                df_base = pd.concat([df_base] + extra_chunks, ignore_index=True).drop_duplicates(subset=["id"])

        # ZERO-JOIN metadata enrichment from rag.works_flat by batched id IN (...)
        all_ids = df_base["id"].dropna().astype(str).unique().tolist()
        meta_chunks = []
        for s in range(0, len(all_ids), 5000):
            batch_ids = ", ".join("'" + x.replace("'", "") + "'" for x in all_ids[s : s + 5000])
            qm = (
                "SELECT id, topic, subfield, field, domain, author_names, country_codes, "
                "cited_by_count, fwci, oa_status, apc_paid_usd, is_retracted, is_paratext "
                f"FROM rag.works_flat WHERE id IN ({batch_ids})"
            )
            meta_chunks.append(client.query_df(qm))
        if meta_chunks:
            df_meta = pd.concat(meta_chunks, ignore_index=True).drop_duplicates(subset=["id"])
            df_base = df_base.merge(df_meta, on="id", how="left")
        # Resolve source_id -> display_name from rag.sources in Python (ZERO JOINs)
        if "source_id" in df_base.columns:
            uniq_sids = sorted({str(s).split("/")[-1].strip() for s in df_base["source_id"].dropna().unique() if str(s).strip()})
            src_map: dict[str, str] = {}
            for s in range(0, len(uniq_sids), 5000):
                b_sids = ", ".join("'" + x.replace("'", "") + "'" for x in uniq_sids[s : s + 5000])
                try:
                    qs = f"SELECT replaceOne(id, 'https://openalex.org/', '') AS sid, display_name FROM rag.sources WHERE replaceOne(id, 'https://openalex.org/', '') IN ({b_sids})"
                    for r_sid, r_name in client.query(qs).result_rows:
                        if r_sid and r_name:
                            src_map[str(r_sid)] = str(r_name)
                            src_map[f"https://openalex.org/{r_sid}"] = str(r_name)
                except Exception:
                    break
            if src_map:
                df_base["source_name"] = [src_map.get(str(x).strip(), src_map.get(str(x).split("/")[-1].strip(), str(x))) for x in df_base["source_id"].fillna("")]
        out_df = normalize_clickhouse_df(df_base, y0, y1, target_iso, source_tag="clickhouse_mx_enriched", precomputed_col=vec_col if precomputed_col != "none" else "none")
    else:
        qf = (
            "SELECT id, doi, pmid, publication_year, type, language, is_oa, source_id, title, "
            "keywords, abstract, topic, subfield, field, domain, author_names, country_codes, "
            "cited_by_count, fwci, oa_status, apc_paid_usd, is_retracted, is_paratext "
            f"FROM rag.works_flat WHERE {ch_spec['enriched_where']}"
        )
        raw_flat = client.query_df(qf)
        out_df = normalize_clickhouse_df(raw_flat, y0, y1, target_iso, source_tag="clickhouse_flat", precomputed_col="none")

    if not out_df.empty:
        out_df.to_parquet(cache_pq, index=False)
    print(f"  [ClickHouse Direct] {len(out_df)} works harvested (ZERO JOINs).")
    return out_df


def harvest_pubmed(query_file: Path, y0: int, y1: int, cache_pq: Path, rx_pos: re.Pattern | None, rx_neg: re.Pattern | None, target_iso: str, c_name: str, refresh: bool = False) -> tuple[pd.DataFrame, int]:
    if cache_pq.exists() and not refresh:
        cached = pd.read_parquet(cache_pq)
        print(f"  [PubMed Cache] {len(cached)} records loaded.")
        return cached, 0
    if not query_file.exists():
        return pd.DataFrame(), 0

    raw_q = query_file.read_text(encoding="utf-8")
    core_q = re.sub(r"\nAND\s+\(\d{4}:\d{4}\[dp\]\)[\s\S]*$", "", raw_q).strip()
    aff_clause = f" AND {c_name}[Affiliation]" if (target_iso and c_name) else ""
    all_records, seen_pmids, dropped = [], set(), 0
    for wa in range(y0, y1 + 1, 5):
        wb = min(wa + 4, y1)
        full_q = f"{core_q} AND ({wa}:{wb}[dp]){aff_clause}"
        try:
            r = requests.post("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", data={"db": "pubmed", "term": full_q, "usehistory": "y", "retmax": "0", "retmode": "json"}, timeout=30)
            r.raise_for_status()
            es = r.json().get("esearchresult", {})
            count, webenv, qkey = int(es.get("count", 0) or 0), es.get("webenv", ""), es.get("querykey", "")
        except Exception:
            time.sleep(1.0)
            continue
        if count == 0 or not webenv:
            continue
        for retstart in range(0, min(count, 15000), 200):
            try:
                ef = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", params={"db": "pubmed", "query_key": qkey, "WebEnv": webenv, "retstart": str(retstart), "retmax": "200", "retmode": "xml"}, timeout=45)
                ef.raise_for_status()
                root = ET.fromstring(ef.text)
            except Exception:
                time.sleep(1.0)
                continue
            for art in root.findall(".//PubmedArticle"):
                pmid = (art.findtext(".//MedlineCitation/PMID") or "").strip()
                if not pmid or pmid in seen_pmids:
                    continue
                seen_pmids.add(pmid)
                aff_str = " | ".join("".join(a.itertext()).strip() for a in art.findall(".//AffiliationInfo/Affiliation"))
                if target_iso and not is_valid_geo_affiliation(aff_str, rx_pos, rx_neg, "", target_iso):
                    dropped += 1
                    continue
                doi, pmcid = "", ""
                for aid in art.findall(".//PubmedData/ArticleIdList/ArticleId"):
                    if aid.attrib.get("IdType") == "doi" and not doi:
                        doi = (aid.text or "").strip()
                    elif aid.attrib.get("IdType") == "pmc" and not pmcid:
                        pmcid = (aid.text or "").strip()
                t_el = art.find(".//Article/ArticleTitle")
                title = "".join(t_el.itertext()).strip() if t_el is not None else ""
                abstract = " ".join("".join(ab.itertext()).strip() for ab in art.findall(".//Article/Abstract/AbstractText"))
                pub_yr = art.findtext(".//Article/Journal/JournalIssue/PubDate/Year") or art.findtext(".//Article/Journal/JournalIssue/PubDate/MedlineDate") or str(wa)
                yr_m = re.search(r"(19\d{2}|20\d{2})", pub_yr)
                mesh = [m.text.strip() for m in art.findall(".//MeshHeadingList/MeshHeading/DescriptorName") if m.text]
                kws = [k.text.strip() for k in art.findall(".//KeywordList/Keyword") if k.text]
                auths = [f"{(au.findtext('LastName') or '').strip()}, {(au.findtext('ForeName') or '').strip()}".strip(", ") for au in art.findall(".//AuthorList/Author") if (au.findtext("LastName") or "").strip()]
                lang = (art.findtext(".//Article/Language") or "eng").strip().lower()
                ptypes = [pt.text.lower() for pt in art.findall(".//Article/PublicationTypeList/PublicationType") if pt.text]
                dtype = "review" if any("review" in p for p in ptypes) else ("letter" if "letter" in ptypes else ("editorial" if "editorial" in ptypes else "article"))
                all_records.append({
                    "oa_id": "", "doi_norm": norm_doi(doi), "pmid_norm": norm_pmid(pmid), "pmcid": pmcid,
                    "title": title, "publication_year": int(yr_m.group(1)) if yr_m else wa, "doc_type": dtype,
                    "language": {"eng": "en", "spa": "es", "por": "pt", "fre": "fr"}.get(lang, lang[:2]),
                    "source_venue": (art.findtext(".//Article/Journal/Title") or "").strip(),
                    "keywords": ", ".join(dict.fromkeys(mesh + kws)), "author_names": "; ".join(auths),
                    "affiliations_raw": aff_str, "country_codes": target_iso,
                    "abstract_final": abstract, "abstract_source": "pubmed_api" if abstract else "",
                })
            time.sleep(0.36)
    df = standardize_columns(pd.DataFrame(all_records), "pubmed_broad") if all_records else pd.DataFrame()
    if not df.empty:
        df.to_parquet(cache_pq, index=False)
    print(f"  [PubMed API] {len(df)} records retained (dropped geo mismatch={dropped}).")
    return df, dropped


def harvest_openalex_api(spec_path: Path, cache_pq: Path, email: str, oa_key: str | None, max_pages: int = 80) -> pd.DataFrame:
    if cache_pq.exists():
        cached = pd.read_parquet(cache_pq)
        print(f"  [OpenAlex API Cache] {len(cached)} records loaded.")
        return cached
    if not spec_path.exists():
        return pd.DataFrame()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    tids = spec.get("topic_ids", [])
    base_flt = spec.get("base_filter", "publication_year:2000-2025")
    rows, seen, calls = [], set(), 0

    def _pull_filter(flt: str) -> None:
        nonlocal calls
        cursor = "*"
        while cursor and calls < max_pages:
            params: dict[str, str] = {"filter": flt, "per-page": "200", "cursor": cursor, "select": "id,doi,ids,title,publication_year,type,language,primary_location,primary_topic,keywords,authorships,abstract_inverted_index,cited_by_count,fwci,open_access,apc_paid", "mailto": email}
            if oa_key:
                params["api_key"] = oa_key
            try:
                r = requests.get("https://api.openalex.org/works", params=params, timeout=30)
                if r.status_code == 429 and "api_key" in params:
                    params.pop("api_key", None)
                    r = requests.get("https://api.openalex.org/works", params=params, timeout=30)
                if r.status_code != 200:
                    break
                calls += 1
                data = r.json()
                res = data.get("results", [])
                if not res:
                    break
                for w in res:
                    oid = norm_oa_id(w.get("id"))
                    if not oid or oid in seen:
                        continue
                    seen.add(oid)
                    pt = w.get("primary_topic") or {}
                    src = (w.get("primary_location") or {}).get("source") or {}
                    kws = [k.get("display_name", "") for k in (w.get("keywords") or []) if k.get("display_name")]
                    auths = [((a.get("author") or {}).get("display_name") or "") for a in (w.get("authorships") or [])]
                    rows.append({
                        "oa_id": oid, "doi_norm": norm_doi(w.get("doi")), "pmid_norm": norm_pmid((w.get("ids") or {}).get("pmid")),
                        "pmcid": str((w.get("ids") or {}).get("pmcid") or ""), "title": str(w.get("title") or ""),
                        "publication_year": int(w.get("publication_year") or 0), "doc_type": str(w.get("type") or "").lower(),
                        "language": str(w.get("language") or "").lower(), "source_venue": str(src.get("display_name") or ""),
                        "topic": str(pt.get("display_name") or ""), "subfield": str((pt.get("subfield") or {}).get("display_name") or ""),
                        "field": str((pt.get("field") or {}).get("display_name") or ""), "domain": str((pt.get("domain") or {}).get("display_name") or ""),
                        "keywords": ", ".join(kws), "author_names": "; ".join([a for a in auths if a]),
                        "abstract_final": reconstruct_inv_idx(w.get("abstract_inverted_index")), "abstract_source": "oa_cleanroom_api",
                        "cited_by_count": int(w.get("cited_by_count") or 0), "fwci": float(w.get("fwci") or 0.0),
                        "is_oa": str((w.get("open_access") or {}).get("is_oa") or ""), "oa_status": str((w.get("open_access") or {}).get("oa_status") or ""),
                        "apc_paid_usd": float((w.get("apc_paid") or {}).get("value_usd") or 0.0),
                    })
                cursor = (data.get("meta") or {}).get("next_cursor")
                time.sleep(0.12)
            except Exception:
                break

    for s in range(0, len(tids), 25):
        _pull_filter(f"{base_flt},primary_topic.id:{'|'.join(tids[s:s+25])}")
    def _oa_fmt(term: str) -> str:
        c = term.replace("*", "").strip()
        return f'"{c}"' if " " in c else c

    free_q = [_oa_fmt(t) for t in (spec.get("free_terms_en", [])[:20] + spec.get("free_terms_es", [])[:10]) if len(t.replace("*", "").strip()) >= 4]
    if free_q:
        _pull_filter(f"{base_flt},title_and_abstract.search:({' OR '.join(free_q)})")
    extra_map = spec.get("free_terms_extra") or {}
    if isinstance(extra_map, dict):
        extra_terms = [_oa_fmt(t) for ts in extra_map.values() for t in (ts or []) if len(str(t).replace("*", "").strip()) >= 2]
        for s in range(0, len(extra_terms), 15):
            _pull_filter(f"{base_flt},title_and_abstract.search:({' OR '.join(extra_terms[s:s+15])})")
    out_df = standardize_columns(pd.DataFrame(rows), "oa_cleanroom_api") if rows else pd.DataFrame()
    if not out_df.empty:
        out_df.to_parquet(cache_pq, index=False)
    print(f"  [OpenAlex REST API] {len(out_df)} works harvested in {calls} cursor calls (est. ${calls*0.001:.3f} USD).")
    return out_df


def enrich_abstract_cascade(df: pd.DataFrame, email: str, oa_key: str | None, cache_dir: Path) -> pd.DataFrame:
    """Open-source abstract & metadata recovery cascade: Semantic Scholar Batch API + OpenAlex DOI API."""
    s2_cache_pq = cache_dir / "s2_abstract_cache.parquet"
    s2_meta: dict[str, dict[str, str]] = pd.read_parquet(s2_cache_pq).set_index("doi_norm").to_dict("index") if s2_cache_pq.exists() else {}
    need_s2 = df[(df["doi_norm"] != "") & (df["abstract_final"].fillna("").str.strip() == "")]
    s2_dois = [d for d in dict.fromkeys(need_s2["doi_norm"].tolist()) if d not in s2_meta][:3200]
    if s2_dois:
        print(f"  [Open Cascade - Semantic Scholar Batch] Querying {len(s2_dois)} DOIs...")
        for start in range(0, len(s2_dois), 400):
            batch = s2_dois[start : start + 400]
            try:
                r = requests.post("https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,abstract,externalIds", json={"ids": [f"DOI:{d}" for d in batch]}, timeout=25)
                if r.status_code != 200:
                    break
                found = set()
                for it in (r.json() or []):
                    if not isinstance(it, dict):
                        continue
                    ext = it.get("externalIds") or {}
                    dn = norm_doi(ext.get("DOI"))
                    if not dn:
                        continue
                    found.add(dn)
                    ab = str(it.get("abstract") or "").strip()
                    s2_meta[dn] = {"abstract_final": ab if len(ab) >= 40 else "", "pmid_norm": norm_pmid(ext.get("PubMed"))}
                for dn in batch:
                    s2_meta.setdefault(dn, {"abstract_final": "", "pmid_norm": ""})
                time.sleep(1.0)
            except Exception:
                break
        if s2_meta:
            pd.DataFrame([{"doi_norm": k, **v} for k, v in s2_meta.items()]).to_parquet(s2_cache_pq, index=False)

    for i in df[(df["doi_norm"] != "") & (df["abstract_final"].fillna("").str.strip() == "")].index:
        m = s2_meta.get(df.at[i, "doi_norm"])
        if m and m.get("abstract_final"):
            df.at[i, "abstract_final"] = m["abstract_final"]
            df.at[i, "abstract_source"] = "semantic_scholar_batch"

    oa_cache_pq = cache_dir / "oa_doi_metadata_cache.parquet"
    doi_meta: dict[str, dict[str, Any]] = pd.read_parquet(oa_cache_pq).set_index("doi_norm").to_dict("index") if oa_cache_pq.exists() else {}
    need_oa = df[(df["doi_norm"] != "") & ((df["abstract_final"] == "") | (df["topic"] == "") | (df["oa_id"] == ""))]
    oa_dois = [d for d in dict.fromkeys(need_oa["doi_norm"].tolist()) if d not in doi_meta][:2500]
    if oa_dois:
        print(f"  [Open Cascade - OpenAlex DOI Batch] Querying {len(oa_dois)} DOIs...")
        for start in range(0, len(oa_dois), 50):
            batch = oa_dois[start : start + 50]
            params: dict[str, str] = {"filter": "doi:" + "|".join(f"https://doi.org/{d}" for d in batch), "per-page": "50", "select": "id,doi,ids,language,primary_location,primary_topic,keywords,abstract_inverted_index,cited_by_count,open_access", "mailto": email}
            if oa_key:
                params["api_key"] = oa_key
            try:
                r = requests.get("https://api.openalex.org/works", params=params, timeout=20)
                if r.status_code == 429 and "api_key" in params:
                    params.pop("api_key", None)
                    r = requests.get("https://api.openalex.org/works", params=params, timeout=20)
                if r.status_code != 200:
                    break
                found = set()
                for w in r.json().get("results", []):
                    dn = norm_doi(w.get("doi"))
                    if not dn:
                        continue
                    found.add(dn)
                    pt = w.get("primary_topic") or {}
                    src = (w.get("primary_location") or {}).get("source") or {}
                    doi_meta[dn] = {
                        "oa_id": norm_oa_id(w.get("id")), "pmid_norm": norm_pmid((w.get("ids") or {}).get("pmid")),
                        "language": str(w.get("language") or "").lower(), "source_venue": str(src.get("display_name") or ""),
                        "topic": str(pt.get("display_name") or ""), "subfield": str((pt.get("subfield") or {}).get("display_name") or ""),
                        "field": str((pt.get("field") or {}).get("display_name") or ""), "domain": str((pt.get("domain") or {}).get("display_name") or ""),
                        "keywords": ", ".join(k.get("display_name", "") for k in (w.get("keywords") or []) if k.get("display_name")),
                        "abstract_final": reconstruct_inv_idx(w.get("abstract_inverted_index")),
                        "cited_by_count": int(w.get("cited_by_count") or 0),
                        "oa_status": str((w.get("open_access") or {}).get("oa_status") or ""),
                    }
                for dn in batch:
                    doi_meta.setdefault(dn, {})
                time.sleep(0.11)
            except Exception:
                break
        if doi_meta:
            pd.DataFrame([{"doi_norm": k, **v} for k, v in doi_meta.items()]).to_parquet(oa_cache_pq, index=False)

    for i in need_oa.index:
        m = doi_meta.get(df.at[i, "doi_norm"]) or {}
        for c in ["oa_id", "pmid_norm", "language", "source_venue", "topic", "subfield", "field", "domain", "keywords", "oa_status"]:
            if not str(df.at[i, c] or "").strip() and m.get(c):
                df.at[i, c] = m[c]
        if not str(df.at[i, "abstract_final"] or "").strip() and m.get("abstract_final"):
            df.at[i, "abstract_final"] = m["abstract_final"]
            df.at[i, "abstract_source"] = "oa_api_doi"
    return df


def compute_embeddings(
    df: pd.DataFrame, cfg: dict, env: dict[str, str], cache_dir: Path, backend: str = "auto", precomputed_mode: str = "auto"
) -> tuple[np.ndarray, dict[str, int]]:
    """Reuses precomputed ClickHouse/Parquet vectors first, computing dense embeddings only for missing rows."""
    cache_path = cache_dir / "dense_embeddings_cache.npz"
    texts = [
        " | ".join([f"Title: {r.title}"] + ([f"Venue: {r.source_venue}"] if str(r.source_venue).strip() else []) + ([f"Topic: {r.topic}"] if str(r.topic).strip() else []) + ([f"Keywords: {r.keywords}"] if str(r.keywords).strip() else []) + ([f"Abstract: {str(r.abstract_final)[:3000]}"] if str(r.abstract_final).strip() else []))
        for r in df.itertuples(index=False)
    ]
    hashes = [hashlib.sha1(t.encode("utf-8", errors="ignore")).hexdigest() for t in texts]
    vec_by_hash: dict[str, np.ndarray] = {}

    n_pre = 0
    pre_dim: int | None = None
    if precomputed_mode != "none" and "_precomputed_vec" in df.columns:
        valid_dims: dict[int, int] = {}
        pre_arrs: dict[int, np.ndarray] = {}
        for idx, raw_v in enumerate(df["_precomputed_vec"].tolist()):
            arr = _extract_precomputed_vector(raw_v)
            if arr is not None:
                v = np.asarray(arr, dtype=np.float32)
                pre_arrs[idx] = v
                valid_dims[len(v)] = valid_dims.get(len(v), 0) + 1
        if valid_dims:
            pre_dim = max(valid_dims, key=valid_dims.get)
            for idx, v in pre_arrs.items():
                if len(v) == pre_dim:
                    vec_by_hash[hashes[idx]] = v
                    n_pre += 1
            print(f"  [Precomputed Embeddings] Reused {n_pre}/{len(df)} vectors (dim={pre_dim}; 0 inference calls).")

    if cache_path.exists():
        npz = np.load(cache_path, allow_pickle=False)
        for h, v in zip(npz["hashes"], npz["vectors"]):
            if str(h) not in vec_by_hash and (pre_dim is None or len(v) == pre_dim):
                vec_by_hash[str(h)] = v.astype(np.float32)

    missing = [i for i, h in enumerate(hashes) if h not in vec_by_hash]
    base_url = cfg["endpoints"]["embedding_base_url"].rstrip("/")
    api_key = env.get("LLM_API_KEY") or env.get("OPENAI_API_KEY") or "lm-studio"
    model = cfg["endpoints"]["embedding_model"]

    use_http = False
    if backend in ("auto", "openai_api") and missing:
        try:
            r = requests.get(base_url + "/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=5)
            use_http = r.status_code == 200
        except Exception:
            use_http = False

    n_computed = 0
    if missing and use_http:
        print(f"  [Embeddings HTTP {base_url}] Computing {len(missing)} missing vectors (reused={len(df)-len(missing)})...")
        bs = 48
        for s in range(0, len(missing), bs):
            bidx = missing[s : s + bs]
            btxt = [texts[i][:5000] for i in bidx]
            for att in range(3):
                try:
                    resp = requests.post(base_url + "/embeddings", headers={"Authorization": f"Bearer {api_key}"}, json={"model": model, "input": btxt}, timeout=90)
                    if resp.status_code == 200:
                        data = sorted(resp.json()["data"], key=lambda x: x["index"])
                        for li, it in zip(bidx, data):
                            v = np.asarray(it["embedding"], dtype=np.float32)
                            if pre_dim is not None and len(v) != pre_dim:
                                continue
                            nrm = np.linalg.norm(v)
                            vec_by_hash[hashes[li]] = (v / nrm) if nrm > 0 else v
                            n_computed += 1
                        break
                except Exception:
                    time.sleep(2.0 * (att + 1))
            if (s // bs + 1) % 10 == 0 and vec_by_hash:
                np.savez_compressed(cache_path, hashes=np.array(list(vec_by_hash.keys())), vectors=np.vstack(list(vec_by_hash.values())))
    elif missing and backend in ("auto", "sentence_transformers"):
        hf_candidates = [
            cfg["endpoints"].get("local_hf_embedding_model", "Qwen/Qwen3-Embedding-0.6B"),
            "nomic-ai/nomic-embed-text-v2-moe",
            "sentence-transformers/all-MiniLM-L6-v2",
        ]
        encoded_ok = False
        try:
            from sentence_transformers import SentenceTransformer
            for hf_model in hf_candidates:
                try:
                    print(f"  [Embeddings Local HF Cache: {hf_model}] Encoding {len(missing)} missing works...")
                    st = SentenceTransformer(hf_model, local_files_only=True, trust_remote_code=True)
                    embs = st.encode([texts[i][:4000] for i in missing], batch_size=32, normalize_embeddings=True, show_progress_bar=False)
                    if pre_dim is not None and len(embs) and len(embs[0]) != pre_dim:
                        continue
                    for li, v in zip(missing, embs):
                        vec_by_hash[hashes[li]] = np.asarray(v, dtype=np.float32)
                        n_computed += 1
                    encoded_ok = True
                    break
                except Exception:
                    continue
        except Exception:
            pass
        if not encoded_ok and n_pre == 0:
            print("  [Embeddings Fallback SVD-TFIDF] No cached local HF/HTTP embedding model available; using dense SVD-TFIDF projection.")
            from sklearn.decomposition import TruncatedSVD
            from sklearn.feature_extraction.text import TfidfVectorizer
            X_tf = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), sublinear_tf=True).fit_transform(texts)
            dim_svd = min(256, max(16, X_tf.shape[1] - 1), max(16, len(texts) - 1))
            X_svd = TruncatedSVD(n_components=dim_svd, random_state=42).fit_transform(X_tf).astype(np.float32)
            for li in range(len(df)):
                v = X_svd[li]
                nrm = np.linalg.norm(v)
                vec_by_hash[hashes[li]] = (v / nrm) if nrm > 0 else v
                n_computed += 1
        elif not encoded_ok and n_pre > 0:
            print(f"  [Precomputed Guard] {len(missing)} rows lack precomputed {pre_dim}d vector and HTTP/HF is offline; preserving {pre_dim}d space cleanly.")

    dim = pre_dim or (len(next(iter(vec_by_hash.values()))) if vec_by_hash else 1024)
    compat = {h: v for h, v in vec_by_hash.items() if len(v) == dim}
    if compat:
        np.savez_compressed(cache_path, hashes=np.array(list(compat.keys())), vectors=np.vstack(list(compat.values())))

    mat = np.zeros((len(df), dim), dtype=np.float32)
    for i, h in enumerate(hashes):
        if h in compat:
            mat[i] = compat[h]
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (mat / norms).astype(np.float32), {"precomputed_vectors_reused": n_pre, "newly_computed_vectors": n_computed, "embed_dim": int(dim)}


def deduplicate_4_levels(
    raw_df: pd.DataFrame, cfg: dict, env: dict[str, str], cache_dir: Path, out_dir: Path, embed_backend: str, precomputed_mode: str = "auto"
) -> tuple[pd.DataFrame, np.ndarray, dict[str, int]]:
    n_raw = len(raw_df)
    raw_df = raw_df.reset_index(drop=True)
    parent = list(range(n_raw))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> bool:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
            return True
        return False

    l1 = l2 = l3 = 0
    s_doi, s_pmid, s_ty = {}, {}, {}
    for idx, r in enumerate(raw_df.itertuples(index=False)):
        if r.doi_norm:
            if r.doi_norm in s_doi and union(s_doi[r.doi_norm], idx):
                l1 += 1
            else:
                s_doi.setdefault(r.doi_norm, idx)
        if r.pmid_norm:
            if r.pmid_norm in s_pmid and union(s_pmid[r.pmid_norm], idx):
                l2 += 1
            else:
                s_pmid.setdefault(r.pmid_norm, idx)
        if len(r.title_norm) >= 12 and r.publication_year > 0:
            k = (r.title_norm, int(r.publication_year))
            if k in s_ty and union(s_ty[k], idx):
                l3 += 1
            else:
                s_ty.setdefault(k, idx)

    groups: dict[int, list[int]] = {}
    for i in range(n_raw):
        groups.setdefault(find(i), []).append(i)

    prio = {"clickhouse_mx_enriched": 5, "clickhouse_flat": 4, "oa_cleanroom_api": 4, "wos_cleanroom": 4, "pubmed_broad": 3, "scopus_cleanroom": 3, "oa_cleanroom_manual": 2}
    recs = raw_df.to_dict("records")

    def _merge(rows: list[dict[str, Any]], origs: list[str]) -> dict[str, Any]:
        rs = sorted(rows, key=lambda r: (1 if str(r.get("abstract_final", "")).strip() else 0, prio.get(r.get("source_origin", ""), 0)), reverse=True)
        base = dict(rs[0])
        for r in rs[1:]:
            for k in ["oa_id", "doi_norm", "pmid_norm", "pmcid", "language", "source_venue", "topic", "subfield", "field", "domain", "keywords", "author_names", "affiliations_raw", "country_codes", "abstract_final", "abstract_source", "oa_status"]:
                if not str(base.get(k, "") or "").strip() and str(r.get(k, "") or "").strip():
                    base[k] = r[k]
            if base.get("_precomputed_vec") is None and r.get("_precomputed_vec") is not None:
                base["_precomputed_vec"] = r["_precomputed_vec"]
            if int(r.get("cited_by_count", 0) or 0) > int(base.get("cited_by_count", 0) or 0):
                base["cited_by_count"] = r["cited_by_count"]
        oset = sorted(set(origs))
        base["n_sources"] = len(oset)
        base["sources_list"] = "|".join(oset)
        return base

    df3 = pd.DataFrame([_merge([recs[i] for i in idxs], [recs[i]["source_origin"] for i in idxs]) for idxs in groups.values()]).reset_index(drop=True)
    vecs, embed_stats = compute_embeddings(df3, cfg, env, cache_dir, backend=embed_backend, precomputed_mode=precomputed_mode)

    # Level 4: Bilingual semantic deduplication (cos >= 0.95 inside author/venue year blocks)
    p4 = list(range(len(df3)))

    def find4(x: int) -> int:
        while p4[x] != x:
            p4[x] = p4[p4[x]]
            x = p4[x]
        return x

    vnorms = np.linalg.norm(vecs, axis=1)
    blocks: dict[tuple[str, str, int], list[int]] = {}
    for i, r in enumerate(df3.itertuples(index=False)):
        if vnorms[i] == 0 or r.publication_year <= 0:
            continue
        yr = int(r.publication_year)
        if r.first_surname and len(r.first_surname) >= 3:
            blocks.setdefault(("au", r.first_surname, yr), []).append(i)
            blocks.setdefault(("au", r.first_surname, yr - 1), []).append(i)

    l4, pairs_log, seen_pairs = 0, [], set()
    for b_idxs in blocks.values():
        if not (2 <= len(b_idxs) <= 40):
            continue
        for ii in range(len(b_idxs)):
            for jj in range(ii + 1, len(b_idxs)):
                pa, pb = sorted((b_idxs[ii], b_idxs[jj]))
                if (pa, pb) in seen_pairs:
                    continue
                seen_pairs.add((pa, pb))
                da, db = df3.at[pa, "doi_norm"], df3.at[pb, "doi_norm"]
                if da and db and da != db:
                    continue
                if abs(int(df3.at[pa, "publication_year"]) - int(df3.at[pb, "publication_year"])) > 1:
                    continue
                sim = float(np.dot(vecs[pa], vecs[pb]))
                if sim >= 0.95:
                    ra, rb = find4(pa), find4(pb)
                    if ra != rb:
                        p4[rb] = ra
                        l4 += 1
                        pairs_log.append({"cos_sim": round(sim, 4), "title_a": df3.at[pa, "title"], "title_b": df3.at[pb, "title"]})

    if pairs_log:
        pd.DataFrame(pairs_log).to_csv(out_dir / "dedup_nivel4_pares_bilingues.csv", index=False)

    g4: dict[int, list[int]] = {}
    for i in range(len(df3)):
        g4.setdefault(find4(i), []).append(i)

    df3_recs = df3.to_dict("records")
    final_recs, keep_v = [], []
    for idxs in g4.values():
        if len(idxs) == 1:
            final_recs.append(df3_recs[idxs[0]])
            keep_v.append(idxs[0])
        else:
            origs = [o for i in idxs for o in str(df3_recs[i].get("sources_list", "")).split("|") if o]
            final_recs.append(_merge([df3_recs[i] for i in idxs], origs))
            keep_v.append(max(idxs, key=lambda i: (1 if str(df3.at[i, "abstract_final"]).strip() else 0, float(vnorms[i]))))

    df_final = pd.DataFrame(final_recs).reset_index(drop=True)
    if "_precomputed_vec" in df_final.columns:
        df_final = df_final.drop(columns=["_precomputed_vec"])
    slug = cfg["domain"].get("project_slug", "work").upper()[:6]
    df_final.insert(0, "work_uid", [f"{slug}_{i:06d}" for i in range(len(df_final))])
    stats = {
        "raw_total": n_raw,
        "level1_doi_merges": l1,
        "level2_pmid_merges": l2,
        "level3_title_year_merges": l3,
        "level4_bilingual_semantic_merges": l4,
        "dedup_total": len(df_final),
        **embed_stats,
    }
    return df_final, vecs[keep_v].astype(np.float32), stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=str, default=".")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--openalex-cleanroom", choices=["api", "manual", "clickhouse", "none"], default="api")
    parser.add_argument("--clickhouse-parquet", type=str, default=None, help="Optional pre-exported ClickHouse Parquet file/dir with precomputed embedding_qwen/embedding_nomic")
    parser.add_argument("--precomputed-embed-col", choices=["auto", "embedding_qwen", "embedding_nomic", "none"], default="auto")
    parser.add_argument("--wos-dir", type=str, default=None)
    parser.add_argument("--scopus-dir", type=str, default=None)
    parser.add_argument("--oa-manual-dir", type=str, default=None)
    parser.add_argument("--embed-backend", choices=["auto", "openai_api", "sentence_transformers"], default="auto")
    parser.add_argument("--include-pubmed", action="store_true", help="Force PubMed harvest even when is_biomedical is false")
    parser.add_argument("--skip-abstract-cascade", action="store_true")
    parser.add_argument("--force-abstract-cascade", action="store_true")
    parser.add_argument("--refresh-pubmed", action="store_true")
    parser.add_argument("--max-oa-pages", type=int, default=80)
    args = parser.parse_args()

    wd = resolve_workdir(args.workdir)
    cfg, _ = load_or_create_config(wd, config_path=args.config)
    env = load_env_vars(wd, cfg)
    oa_key = env.get("OPENALEX_API_KEY")
    email = cfg["endpoints"]["openalex_mailto"]
    y0, y1 = cfg["scope"]["year_start"], cfg["scope"]["year_end"]
    cc = (cfg["scope"].get("geo_country_code") or "").strip().upper()
    c_name = (cfg["scope"].get("geo_country_name") or cc).strip()
    pos_rx_s = cfg["geography_rescue"].get("positive_affiliation_regex") or (rf"\b{re.escape(c_name)}\b" if c_name else "")
    neg_rx_s = cfg["geography_rescue"].get("negative_affiliation_regex") or ""
    rx_pos = re.compile(pos_rx_s, flags=re.IGNORECASE) if pos_rx_s else None
    rx_neg = re.compile(neg_rx_s, flags=re.IGNORECASE) if neg_rx_s else None

    f0_dir = phase_dir(wd, "fase0_estrategia")
    out_dir = phase_dir(wd, "fase1_corpus")
    cache_dir = phase_dir(wd, "cache")
    in_root = wd / "delineation" / "inputs"

    q_geo = "country" if (cc and (f0_dir / "queries" / "country").exists()) else "global"
    parts: list[pd.DataFrame] = []

    df_wos, drop_wos = load_wos_folder(Path(args.wos_dir) if args.wos_dir else (in_root / "wos"), y0, y1, rx_pos, rx_neg, cc)
    if not df_wos.empty:
        parts.append(df_wos)
    df_scp = load_scopus_folder(Path(args.scopus_dir) if args.scopus_dir else (in_root / "scopus"), y0, y1, cc)
    if not df_scp.empty:
        parts.append(df_scp)
    df_oam = load_oa_manual_folder(Path(args.oa_manual_dir) if args.oa_manual_dir else (in_root / "openalex"), y0, y1, rx_pos, rx_neg, cc)
    if not df_oam.empty:
        parts.append(df_oam)

    df_chp = load_clickhouse_parquet_inputs(Path(args.clickhouse_parquet) if args.clickhouse_parquet else None, in_root / "clickhouse", y0, y1, cc, args.precomputed_embed_col)
    if not df_chp.empty:
        parts.append(df_chp)

    if args.openalex_cleanroom == "clickhouse":
        ch_cache_pq = out_dir / f"cache_clickhouse_{args.precomputed_embed_col}.parquet"
        df_ch = harvest_clickhouse(f0_dir / "queries" / q_geo / "openalex_api_broad.json", ch_cache_pq, y0, y1, cc, env, args.precomputed_embed_col)
        if not df_ch.empty:
            parts.append(df_ch)

    if (cfg["domain"].get("is_biomedical", False) or args.include_pubmed) and args.openalex_cleanroom != "clickhouse":
        df_pm, drop_pm = harvest_pubmed(f0_dir / "queries" / q_geo / "pubmed_broad.txt", y0, y1, out_dir / "cache_pubmed_broad.parquet", rx_pos, rx_neg, cc, c_name, refresh=args.refresh_pubmed)
        if not df_pm.empty:
            parts.append(df_pm)
    else:
        drop_pm = 0
        if args.openalex_cleanroom == "clickhouse":
            print("  [PubMed] Skipped (ClickHouse MX snapshot mode preserves frozen 1.2M scope).")
        else:
            print("  [PubMed] Skipped (is_biomedical=false; pass --include-pubmed to override).")

    if args.openalex_cleanroom == "api":
        df_oaa = harvest_openalex_api(f0_dir / "queries" / q_geo / "openalex_api_broad.json", out_dir / "cache_openalex_api.parquet", email, oa_key, max_pages=args.max_oa_pages)
        if not df_oaa.empty:
            parts.append(df_oaa)

    if not parts:
        raise RuntimeError("No Phase 1 sources produced records. Check query specs or drop exports into delineation/inputs/.")

    raw_union = pd.concat(parts, ignore_index=True)
    pure_ch_mx = set(raw_union["source_origin"].unique()) <= {"clickhouse_mx_enriched"}
    if args.force_abstract_cascade or (not args.skip_abstract_cascade and not pure_ch_mx):
        raw_union = enrich_abstract_cascade(raw_union, email, oa_key, cache_dir)
    else:
        print("  [Open Cascade] Skipped (frozen ClickHouse MX abstracts_enriched already populated / --skip-abstract-cascade).")
    corpus_df, vecs_mat, dedup_stats = deduplicate_4_levels(raw_union, cfg, env, cache_dir, out_dir, args.embed_backend, precomputed_mode=args.precomputed_embed_col)
    corpus_df.to_parquet(out_dir / "corpus_bruto_dedup.parquet", index=False)
    np.save(out_dir / "embeddings_dense.npy", vecs_mat)

    manifest = {
        "scope_year_range": [y0, y1],
        "geo_country": cc or "GLOBAL",
        "dropped_geo_wos": drop_wos,
        "dropped_geo_pubmed": drop_pm,
        "abstract_coverage": round(float((corpus_df["abstract_final"].fillna("").str.strip() != "").mean()), 4),
        "source_counts_raw": raw_union["source_origin"].value_counts().to_dict(),
        "dedup_stats": dedup_stats,
    }
    (out_dir / "fase1_ingesta_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))

    from visual_artifacts import generate_phase_visuals
    generate_phase_visuals(1, wd, cfg)


if __name__ == "__main__":
    main()
