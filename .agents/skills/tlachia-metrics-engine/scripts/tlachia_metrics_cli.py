#!/usr/bin/env python3
"""
TlachIA Metrics Engine CLI
--------------------------
Motor cienciométrico autónomo e independiente para el cálculo de más de 35 indicadores
de volumen, citación (H, G, M, i10), excelencia (FWCI, Percentil, Top 10%, Top 1%),
las 6 vías de Acceso Abierto, economía de la publicación (APC USD real/lista y ahorro Diamante),
colaboración internacional, estructura coautoral, coeficiente de Gini temático y análisis
temporal (anual con suavizado CMA y longitudinal por periodos) a nivel global o por entidad
(investigador/autor, institución, país, revista/fuente, subcampo o tópico) sin truncar columnas.
"""

import sys
import os
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

GLOBAL_SOUTH_COUNTRIES = {
    # América Latina y Caribe
    "MX", "BR", "AR", "CL", "CO", "PE", "UY", "VE", "EC", "BO", "PY", "CU", "DO", "CR", "PA", "GT", "HN", "SV", "NI", "JM", "TT",
    # África
    "ZA", "EG", "NG", "KE", "GH", "ET", "TZ", "UG", "DZ", "MA", "TN", "SN", "CM", "CI", "ZW",
    # Asia y Medio Oriente
    "IN", "ID", "PK", "BD", "PH", "VN", "TH", "MY", "IR", "IQ", "JO", "LB", "LK", "NP", "KZ", "UZ", "CN",
}

METADATA_NON_INDICATOR_COLS = {
    "entity", "level", "country", "period", "start_year", "end_year", "year",
    "first_year", "last_year", "is_global_south"
}


def _normalize_loaded_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza alias de columnas para garantizar interoperabilidad con todos los cosechadores y ClickHouse."""
    if df.empty:
        return df
    df = df.copy()
    if "year" not in df.columns and "publication_year" in df.columns:
        df["year"] = df["publication_year"]
    if "citations" not in df.columns and "cited_by_count" in df.columns:
        df["citations"] = df["cited_by_count"]
    if "authors" not in df.columns:
        for alt in ("author_names", "raw_author_names"):
            if alt in df.columns:
                df["authors"] = df[alt].apply(
                    lambda x: "; ".join(map(str, x)) if isinstance(x, (list, np.ndarray)) else str(x or "")
                )
                break
    if "affiliations" not in df.columns and "institution_names" in df.columns:
        df["affiliations"] = df["institution_names"].apply(
            lambda x: "; ".join(map(str, x)) if isinstance(x, (list, np.ndarray)) else str(x or "")
        )
    if "country_codes" not in df.columns:
        if "all_country_codes" in df.columns:
            df["country_codes"] = df["all_country_codes"].apply(
                lambda x: "; ".join(map(str, x)) if isinstance(x, (list, np.ndarray)) else str(x or "")
            )
        elif "countries" in df.columns:
            df["country_codes"] = df["countries"].apply(
                lambda x: "; ".join(map(str, x)) if isinstance(x, (list, np.ndarray)) else str(x or "")
            )
        elif "country_code" in df.columns:
            df["country_codes"] = df["country_code"].fillna("").astype(str)
    else:
        df["country_codes"] = df["country_codes"].apply(
            lambda x: "; ".join(map(str, x)) if isinstance(x, (list, np.ndarray)) else str(x or "")
        )
    if "source_title" not in df.columns:
        for alt in ("journal_name", "source_id", "venue"):
            if alt in df.columns:
                df["source_title"] = df[alt].fillna("").astype(str)
                break
    if "keywords_author" not in df.columns and "keywords" in df.columns:
        df["keywords_author"] = df["keywords"].apply(
            lambda x: "; ".join(map(str, x)) if isinstance(x, (list, np.ndarray)) else str(x or "")
        )
    if "keywords_plus" not in df.columns and "topic" in df.columns:
        df["keywords_plus"] = df["topic"].fillna("").astype(str)
    return df


def load_canonical_corpus(filepath: str) -> pd.DataFrame:
    """Carga un archivo bibliográfico tabular (.parquet, .csv, .json) en DataFrame normalizado."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")
    ext = p.suffix.lower()
    if ext == ".parquet":
        df = pd.read_parquet(p)
    elif ext == ".csv":
        df = pd.read_csv(p)
    elif ext == ".json":
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            df = pd.DataFrame(raw)
        elif isinstance(raw, dict):
            recs = raw.get("records") or raw.get("works") or raw.get("data") or raw.get("results")
            if isinstance(recs, list):
                df = pd.DataFrame(recs)
            else:
                df = pd.DataFrame([raw])
        else:
            df = pd.read_json(p)
    else:
        try:
            df = pd.read_parquet(p)
        except Exception:
            df = pd.read_csv(p)
    return _normalize_loaded_df(df)


def calculate_h_index(citations_series: pd.Series) -> int:
    """Calcula el índice H de Hirsch a partir de un arreglo de citas."""
    if citations_series is None or len(citations_series) == 0:
        return 0
    cits = np.sort(pd.to_numeric(citations_series, errors="coerce").fillna(0).values)[::-1]
    h = 0
    for i, c in enumerate(cits):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return int(h)


def calculate_g_index(citations_series: pd.Series) -> int:
    """Calcula el índice G de Egghe a partir de un arreglo de citas."""
    if citations_series is None or len(citations_series) == 0:
        return 0
    cits = np.sort(pd.to_numeric(citations_series, errors="coerce").fillna(0).values)[::-1]
    cumsum = np.cumsum(cits)
    g = 0
    for i, total in enumerate(cumsum):
        k = i + 1
        if total >= k * k:
            g = k
        else:
            break
    return int(g)


def calculate_i10_index(citations_series: pd.Series) -> int:
    """Calcula la cantidad de documentos con al menos 10 citas."""
    if citations_series is None or len(citations_series) == 0:
        return 0
    cits = pd.to_numeric(citations_series, errors="coerce").fillna(0)
    return int((cits >= 10).sum())


def compute_gini_coefficient(values: np.ndarray) -> float:
    """Calcula el coeficiente de concentración de Gini (0 = perfecta igualdad, 1 = máxima concentración)."""
    vals = np.asarray(values, dtype=float)
    vals = vals[vals >= 0]
    if len(vals) == 0 or np.sum(vals) == 0:
        return 0.0
    vals = np.sort(vals)
    n = len(vals)
    index = np.arange(1, n + 1)
    return float(((np.sum((2 * index - n - 1) * vals)) / (n * np.sum(vals))))


def _split_semicolon_items(val: Any) -> List[str]:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return []
    if isinstance(val, (list, np.ndarray)):
        return [str(x).strip() for x in val if str(x).strip() and str(x).strip().upper() != "NAN"]
    return [x.strip() for x in str(val).split(";") if x.strip() and x.strip().upper() != "NAN"]


def compute_summary_indicators(df: pd.DataFrame, total_corpus_docs: Optional[int] = None) -> Dict[str, Any]:
    """
    Calcula la suite completa de más de 35 indicadores cienciométricos de TlachIA
    sobre un DataFrame (sea el corpus global o el subconjunto de una entidad/periodo).
    """
    n_docs = len(df)
    denom_corpus = total_corpus_docs if (total_corpus_docs and total_corpus_docs > 0) else max(n_docs, 1)
    if n_docs == 0:
        return {
            "num_documents": 0, "share_pct": 0.0, "times_cited": 0, "cites_per_doc": 0.0,
            "cited_docs": 0, "uncited_docs": 0, "pct_docs_cited": 0.0, "pct_uncited": 0.0,
            "h_index": 0, "g_index": 0, "m_index": 0.0, "i10_index": 0,
            "fwci_avg": 0.0, "fwci_median": 0.0, "avg_percentile": 0.0,
            "top_10_pct_docs": 0, "pct_top_10": 0.0, "top_1_pct_docs": 0, "pct_top_1": 0.0,
            "oa_docs": 0, "pct_oa": 0.0, "pct_oa_total": 0.0,
            "pct_oa_diamond": 0.0, "pct_oa_gold": 0.0, "pct_oa_hybrid": 0.0,
            "pct_oa_green": 0.0, "pct_oa_bronze": 0.0, "pct_oa_closed": 100.0,
            "apc_list_usd": 0.0, "estimated_apc_paid_usd": 0.0, "avg_apc_per_doc_usd": 0.0,
            "estimated_diamond_savings_usd": 0.0,
            "pct_international": 0.0, "pct_domestic": 0.0, "pct_global_south": 0.0,
            "pct_single_authored": 0.0, "avg_authors_per_doc": 0.0, "avg_countries_per_doc": 0.0,
            "collaboration_index": 0.0, "active_years": 0, "first_year": None, "last_year": None,
        }

    # 1. Volumen, Ventana Temporal y Citas
    cits_col = "citations" if "citations" in df.columns else ("cited_by_count" if "cited_by_count" in df.columns else None)
    cits = pd.to_numeric(df[cits_col], errors="coerce").fillna(0) if cits_col else pd.Series([0] * n_docs)

    times_cited = int(cits.sum())
    cites_per_doc = float(times_cited / n_docs)
    cited_docs = int((cits > 0).sum())
    uncited_docs = int(n_docs - cited_docs)
    pct_docs_cited = float((cited_docs / n_docs) * 100.0)
    pct_uncited = float((uncited_docs / n_docs) * 100.0)
    h_idx = calculate_h_index(cits)
    g_idx = calculate_g_index(cits)
    i10_idx = calculate_i10_index(cits)

    first_year, last_year, active_years = None, None, 1
    if "year" in df.columns:
        yrs = pd.to_numeric(df["year"], errors="coerce").dropna()
        if len(yrs) > 0:
            first_year = int(yrs.min())
            last_year = int(yrs.max())
            active_years = max(1, last_year - first_year + 1)
    m_idx = float(h_idx / active_years)

    # 2. Impacto Normalizado (FWCI) y Percentiles / Top 10% / Top 1%
    fwci_avg = 0.0
    fwci_median = 0.0
    if "fwci" in df.columns and df["fwci"].notna().any():
        fwci_s = pd.to_numeric(df["fwci"], errors="coerce").dropna()
        if len(fwci_s) > 0:
            fwci_avg = float(fwci_s.mean())
            fwci_median = float(fwci_s.median())

    avg_percentile = 0.0
    top_10_docs = 0
    top_1_docs = 0
    if "percentile" in df.columns and df["percentile"].notna().any():
        perc_s = pd.to_numeric(df["percentile"], errors="coerce").dropna()
        if len(perc_s) > 0:
            if perc_s.max() <= 1.0 and perc_s.max() > 0:
                perc_s = perc_s * 100.0
            avg_percentile = float(perc_s.mean())
            top_10_docs = int((perc_s >= 90.0).sum())
            top_1_docs = int((perc_s >= 99.0).sum())
    if "is_top_10" in df.columns and top_10_docs == 0:
        top_10_docs = int(df["is_top_10"].isin([1, True, "1", "true", "True"]).sum())
    if "is_top_1" in df.columns and top_1_docs == 0:
        top_1_docs = int(df["is_top_1"].isin([1, True, "1", "true", "True"]).sum())

    pct_top_10 = float((top_10_docs / n_docs) * 100.0)
    pct_top_1 = float((top_1_docs / n_docs) * 100.0)

    # 3. Acceso Abierto y Ciencia Abierta (6 Vías)
    oa_status_s = df["oa_status"].fillna("closed").astype(str).str.lower() if "oa_status" in df.columns else pd.Series(["closed"] * n_docs)
    if "is_oa" in df.columns:
        is_oa_s = df["is_oa"].isin([1, True, "1", "true", "True"]) | oa_status_s.isin(["gold", "diamond", "green", "hybrid", "bronze"])
    else:
        is_oa_s = oa_status_s != "closed"

    oa_docs = int(is_oa_s.sum())
    pct_oa_total = float((oa_docs / n_docs) * 100.0)
    pct_oa_diamond = float(((oa_status_s == "diamond").sum() / n_docs) * 100.0)
    pct_oa_gold = float(((oa_status_s == "gold").sum() / n_docs) * 100.0)
    pct_oa_hybrid = float(((oa_status_s == "hybrid").sum() / n_docs) * 100.0)
    pct_oa_green = float(((oa_status_s == "green").sum() / n_docs) * 100.0)
    pct_oa_bronze = float(((oa_status_s == "bronze").sum() / n_docs) * 100.0)
    pct_oa_closed = float(((~is_oa_s).sum() / n_docs) * 100.0)

    # 4. Economía de la Publicación (APC USD y Ahorro Diamante)
    apc_list_usd = float(pd.to_numeric(df["apc_list_usd"], errors="coerce").fillna(0).sum()) if "apc_list_usd" in df.columns else 0.0
    if "apc_paid_usd" in df.columns:
        apc_s = pd.to_numeric(df["apc_paid_usd"], errors="coerce").fillna(0)
        est_apc_paid_usd = float(apc_s.sum())
        avg_apc_per_doc_usd = float(est_apc_paid_usd / n_docs)
    else:
        est_apc_paid_usd = 0.0
        avg_apc_per_doc_usd = 0.0

    diamond_count = int((oa_status_s == "diamond").sum())
    est_diamond_savings_usd = float(diamond_count * 1800.0)

    # 5. Colaboración Internacional, Sur Global y Coautoría
    n_intl = 0
    n_domestic = 0
    n_global_south = 0
    total_countries_count = 0

    if "country_codes" in df.columns:
        for val in df["country_codes"]:
            codes = [c.upper() for c in _split_semicolon_items(val)]
            uniq_c = set(codes)
            total_countries_count += max(len(uniq_c), 1) if uniq_c else 0
            if len(uniq_c) > 1:
                n_intl += 1
            elif len(uniq_c) == 1:
                n_domestic += 1
            if any(c in GLOBAL_SOUTH_COUNTRIES for c in uniq_c):
                n_global_south += 1

    pct_intl = float((n_intl / n_docs) * 100.0)
    pct_dom = float((n_domestic / n_docs) * 100.0)
    pct_south = float((n_global_south / n_docs) * 100.0)
    avg_countries_per_doc = float(total_countries_count / n_docs)

    single_author_docs = 0
    multi_author_docs = 0
    multi_author_total_authors = 0
    total_authors_count = 0
    if "authors" in df.columns:
        for val in df["authors"]:
            auth_list = _split_semicolon_items(val)
            k = len(auth_list)
            total_authors_count += k
            if k <= 1:
                single_author_docs += 1
            else:
                multi_author_docs += 1
                multi_author_total_authors += k

    pct_single_authored = float((single_author_docs / n_docs) * 100.0)
    avg_authors_per_doc = float(total_authors_count / n_docs)
    collaboration_index = float(multi_author_total_authors / multi_author_docs) if multi_author_docs > 0 else 1.0

    return {
        "num_documents": int(n_docs),
        "share_pct": round(float((n_docs / denom_corpus) * 100.0), 3),
        "times_cited": int(times_cited),
        "cites_per_doc": round(cites_per_doc, 2),
        "cited_docs": int(cited_docs),
        "uncited_docs": int(uncited_docs),
        "pct_docs_cited": round(pct_docs_cited, 2),
        "pct_uncited": round(pct_uncited, 2),
        "h_index": int(h_idx),
        "g_index": int(g_idx),
        "m_index": round(m_idx, 3),
        "i10_index": int(i10_idx),
        "fwci_avg": round(fwci_avg, 3),
        "fwci_median": round(fwci_median, 3),
        "avg_percentile": round(avg_percentile, 2),
        "top_10_pct_docs": int(top_10_docs),
        "pct_top_10": round(pct_top_10, 2),
        "top_1_pct_docs": int(top_1_docs),
        "pct_top_1": round(pct_top_1, 2),
        "oa_docs": int(oa_docs),
        "pct_oa": round(pct_oa_total, 2),
        "pct_oa_total": round(pct_oa_total, 2),
        "pct_oa_diamond": round(pct_oa_diamond, 2),
        "pct_oa_gold": round(pct_oa_gold, 2),
        "pct_oa_hybrid": round(pct_oa_hybrid, 2),
        "pct_oa_green": round(pct_oa_green, 2),
        "pct_oa_bronze": round(pct_oa_bronze, 2),
        "pct_oa_closed": round(pct_oa_closed, 2),
        "apc_list_usd": round(apc_list_usd, 2),
        "estimated_apc_paid_usd": round(est_apc_paid_usd, 2),
        "avg_apc_per_doc_usd": round(avg_apc_per_doc_usd, 2),
        "estimated_diamond_savings_usd": round(est_diamond_savings_usd, 2),
        "pct_international": round(pct_intl, 2),
        "pct_domestic": round(pct_dom, 2),
        "pct_global_south": round(pct_south, 2),
        "pct_single_authored": round(pct_single_authored, 2),
        "avg_authors_per_doc": round(avg_authors_per_doc, 2),
        "avg_countries_per_doc": round(avg_countries_per_doc, 2),
        "collaboration_index": round(collaboration_index, 2),
        "active_years": int(active_years),
        "first_year": first_year,
        "last_year": last_year,
    }


def _extract_entity_index_map(df: pd.DataFrame, level: str) -> Tuple[Dict[str, List[int]], Dict[str, List[str]]]:
    """Mapea cada entidad a los índices de fila de df donde participa y sus países asociados."""
    norm_level = level.lower().strip()
    if norm_level == "author":
        norm_level = "researcher"

    entity_indices: Dict[str, List[int]] = {}
    entity_countries: Dict[str, List[str]] = {}

    for idx, row in df.iterrows():
        cc_list = [c.upper() for c in _split_semicolon_items(row.get("country_codes", ""))]
        primary_cc = str(row.get("country_code", "") or (cc_list[0] if cc_list else "")).strip().upper()
        if primary_cc == "NAN":
            primary_cc = ""

        if norm_level == "researcher":
            items = _split_semicolon_items(row.get("authors", ""))
        elif norm_level == "institution":
            items = _split_semicolon_items(row.get("affiliations", ""))
        elif norm_level == "country":
            items = cc_list if cc_list else ([primary_cc] if primary_cc else [])
        elif norm_level == "source":
            st = str(row.get("source_title", "") or "").strip()
            items = [st] if st and st.upper() != "NAN" else []
        elif norm_level in ("subfield", "topic", "field", "domain"):
            val = str(row.get(norm_level, "") or "").strip()
            items = [val] if val and val.upper() != "NAN" else []
        else:
            raise ValueError(f"Nivel de entidad no soportado: {level}")

        for ent in set(items):
            if not ent:
                continue
            if ent not in entity_indices:
                entity_indices[ent] = []
                entity_countries[ent] = []
            entity_indices[ent].append(idx)
            if primary_cc:
                entity_countries[ent].append(primary_cc)

    return entity_indices, entity_countries


def aggregate_by_entity(
    df: pd.DataFrame,
    level: str,
    min_docs: int = 1,
    top_n: Optional[int] = None,
    indicators: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Agrega la batería completa de 35+ indicadores cienciométricos por entidad
    (researcher/author, institution, country, source, subfield, topic, field)
    sin truncar ninguna dimensión analítica.
    """
    norm_level = "researcher" if level.lower().strip() == "author" else level.lower().strip()
    df_reset = df.reset_index(drop=True)
    total_docs = len(df_reset)
    entity_indices, entity_countries = _extract_entity_index_map(df_reset, norm_level)

    # Filtrar por min_docs y ordenar por volumen antes de calcular indicadores detallados
    qualified = [(ent, idxs) for ent, idxs in entity_indices.items() if len(idxs) >= max(1, min_docs)]
    qualified.sort(key=lambda x: len(x[1]), reverse=True)
    if top_n is not None and top_n > 0:
        qualified = qualified[:top_n]

    records = []
    for ent, idxs in qualified:
        sub_df = df_reset.iloc[idxs]
        metrics = compute_summary_indicators(sub_df, total_corpus_docs=total_docs)
        ccs = entity_countries.get(ent, [])
        top_cc = ent if norm_level == "country" else (max(set(ccs), key=ccs.count) if ccs else "")
        row_out = {
            "entity": ent,
            "level": norm_level,
            "country": top_cc,
            "is_global_south": 1 if top_cc in GLOBAL_SOUTH_COUNTRIES else 0,
            **metrics,
        }
        records.append(row_out)

    res_df = pd.DataFrame(records)
    if not res_df.empty:
        res_df = res_df.sort_values(by=["num_documents", "times_cited"], ascending=[False, False]).reset_index(drop=True)
        if indicators:
            keep_meta = [c for c in ["entity", "level", "country", "is_global_south"] if c in res_df.columns]
            keep_ind = [c for c in indicators if c in res_df.columns and c not in keep_meta]
            res_df = res_df[keep_meta + keep_ind]
    return res_df


def build_periods(
    df: pd.DataFrame,
    periods_str: Optional[str] = None,
    window: Optional[int] = None,
    step: Optional[int] = None,
    last_years: Optional[int] = None,
    single_period: Optional[str] = None,
) -> List[Tuple[str, int, int]]:
    """Construye la lista de periodos (etiqueta, año_inicio, año_fin)."""
    periods = []
    years_s = pd.to_numeric(df.get("year"), errors="coerce").dropna()
    if len(years_s) == 0:
        return periods
    min_year = int(years_s.min())
    max_year = int(years_s.max())

    if single_period:
        parts = [p.strip() for p in single_period.split("-") if p.strip()]
        if len(parts) == 2:
            s_yr, e_yr = int(parts[0]), int(parts[1])
            periods.append((f"{s_yr}-{e_yr}", s_yr, e_yr))
        elif len(parts) == 1:
            s_yr = int(parts[0])
            periods.append((str(s_yr), s_yr, s_yr))
        return periods

    if last_years:
        s_yr = max(min_year, max_year - last_years + 1)
        periods.append((f"{s_yr}-{max_year}", s_yr, max_year))
        return periods

    if periods_str:
        for p_item in periods_str.split(","):
            p_clean = p_item.strip()
            if not p_clean:
                continue
            parts = [p.strip() for p in p_clean.split("-") if p.strip()]
            if len(parts) == 2:
                s_yr, e_yr = int(parts[0]), int(parts[1])
                periods.append((f"{s_yr}-{e_yr}", s_yr, e_yr))
            elif len(parts) == 1:
                s_yr = int(parts[0])
                periods.append((str(s_yr), s_yr, s_yr))
        return periods

    if window:
        w_step = step if step and step > 0 else window
        curr = min_year
        while curr <= max_year:
            end = min(curr + window - 1, max_year)
            label = f"{curr}-{end}" if curr != end else str(curr)
            periods.append((label, curr, end))
            if end == max_year and w_step == window:
                break
            curr += w_step
            if curr > max_year:
                break
        return periods

    curr = min_year
    while curr <= max_year:
        end = min(curr + 4, max_year)
        label = f"{curr}-{end}" if curr != end else str(curr)
        periods.append((label, curr, end))
        curr += 5
    return periods


def _apply_cma_smoothing(df_series: pd.DataFrame, cma_window: int, group_col: Optional[str] = None) -> pd.DataFrame:
    """
    Aplica Media Móvil Centrada (Centered Moving Average, CMA) de ventana cma_window
    sobre las columnas de indicadores numéricos para alimentar som-trajectory-mapping.
    """
    if df_series.empty or not cma_window or cma_window <= 1:
        return df_series
    df_out = df_series.copy()
    num_cols = [
        c for c in df_out.select_dtypes(include=[np.number]).columns
        if c not in METADATA_NON_INDICATOR_COLS
    ]
    if group_col and group_col in df_out.columns:
        df_out = df_out.sort_values(by=[group_col, "year"]).reset_index(drop=True)
        for col in num_cols:
            df_out[col] = (
                df_out.groupby(group_col)[col]
                .transform(lambda s: s.rolling(window=cma_window, center=True, min_periods=1).mean())
                .round(3)
            )
    else:
        df_out = df_out.sort_values(by="year").reset_index(drop=True)
        for col in num_cols:
            df_out[col] = df_out[col].rolling(window=cma_window, center=True, min_periods=1).mean().round(3)
    return df_out


def calculate_annual_series(
    df: pd.DataFrame,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    level: Optional[str] = None,
    min_docs: int = 1,
    top_n: Optional[int] = None,
    cma_window: Optional[int] = None,
    indicators: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Calcula la serie temporal año por año con los 35+ indicadores TlachIA.
    - Si level es None: serie anual agregada de todo el corpus.
    - Si level se especifica (institution, researcher/author, country, source, subfield, topic):
      serie anual longitudinal por entidad, con suavizado opcional CMA (--cma-window 3 o 5)
      lista para som-trajectory-mapping.
    """
    if "year" not in df.columns:
        raise ValueError("El corpus no contiene la columna 'year'.")

    df_clean = df.dropna(subset=["year"]).copy()
    df_clean["year"] = pd.to_numeric(df_clean["year"], errors="coerce")
    df_clean = df_clean.dropna(subset=["year"])
    df_clean["year"] = df_clean["year"].astype(int)

    if year_from is not None:
        df_clean = df_clean[df_clean["year"] >= year_from]
    if year_to is not None:
        df_clean = df_clean[df_clean["year"] <= year_to]

    years = sorted(df_clean["year"].unique())
    if not level:
        rows = []
        prev_docs = None
        prev_cites = None
        for yr in years:
            sub_df = df_clean[df_clean["year"] == yr]
            metrics = compute_summary_indicators(sub_df, total_corpus_docs=len(df_clean))
            curr_docs = metrics.get("num_documents", 0)
            curr_cites = metrics.get("times_cited", 0)
            doc_growth = round(((curr_docs - prev_docs) / prev_docs) * 100.0, 2) if (prev_docs and prev_docs > 0) else 0.0
            cite_growth = round(((curr_cites - prev_cites) / prev_cites) * 100.0, 2) if (prev_cites and prev_cites > 0) else 0.0
            rows.append({
                "year": int(yr),
                **metrics,
                "doc_growth_pct": doc_growth,
                "cite_growth_pct": cite_growth,
            })
            prev_docs = curr_docs
            prev_cites = curr_cites
        res_df = pd.DataFrame(rows)
        if cma_window and cma_window > 1:
            res_df = _apply_cma_smoothing(res_df, cma_window, group_col=None)
        return res_df

    # Serie anual por entidad (para som-trajectory-mapping)
    overall_entities = aggregate_by_entity(df_clean, level=level, min_docs=min_docs, top_n=top_n)
    if overall_entities.empty:
        return pd.DataFrame()
    selected_entities = set(overall_entities["entity"].tolist())

    entity_year_rows = []
    for yr in years:
        sub_df = df_clean[df_clean["year"] == yr]
        if sub_df.empty:
            continue
        yr_agg = aggregate_by_entity(sub_df, level=level, min_docs=1, top_n=None, indicators=indicators)
        if yr_agg.empty:
            continue
        yr_agg = yr_agg[yr_agg["entity"].isin(selected_entities)].copy()
        if not yr_agg.empty:
            yr_agg.insert(0, "year", int(yr))
            entity_year_rows.append(yr_agg)

    if not entity_year_rows:
        return pd.DataFrame()
    res_df = pd.concat(entity_year_rows, ignore_index=True)
    res_df = res_df.sort_values(by=["entity", "year"]).reset_index(drop=True)
    if cma_window and cma_window > 1:
        res_df = _apply_cma_smoothing(res_df, cma_window, group_col="entity")
    return res_df


def calculate_period_series(
    df: pd.DataFrame,
    periods: List[Tuple[str, int, int]],
    level: Optional[str] = None,
    min_docs: int = 1,
    top_n: Optional[int] = None,
    indicators: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Calcula los 35+ indicadores cienciométricos para una secuencia de periodos.
    - Si level es None: serie temporal agregada a nivel de corpus con tasas de crecimiento.
    - Si level se especifica: matriz longitudinal de entidades con todos los indicadores (para SOM / PathSOM).
    """
    if "year" not in df.columns:
        raise ValueError("El corpus no contiene la columna 'year'.")

    df_clean = df.dropna(subset=["year"]).copy()
    df_clean["year"] = pd.to_numeric(df_clean["year"], errors="coerce")
    df_clean = df_clean.dropna(subset=["year"])

    if level is None:
        rows = []
        prev_docs = None
        prev_cites = None
        for label, s_yr, e_yr in periods:
            sub_df = df_clean[(df_clean["year"] >= s_yr) & (df_clean["year"] <= e_yr)]
            metrics = compute_summary_indicators(sub_df, total_corpus_docs=len(df_clean))
            curr_docs = metrics.get("num_documents", 0)
            curr_cites = metrics.get("times_cited", 0)
            doc_growth = round(((curr_docs - prev_docs) / prev_docs) * 100.0, 2) if (prev_docs and prev_docs > 0) else 0.0
            cite_growth = round(((curr_cites - prev_cites) / prev_cites) * 100.0, 2) if (prev_cites and prev_cites > 0) else 0.0
            rows.append({
                "period": label,
                "start_year": s_yr,
                "end_year": e_yr,
                **metrics,
                "doc_growth_pct": doc_growth,
                "cite_growth_pct": cite_growth,
            })
            prev_docs = curr_docs
            prev_cites = curr_cites
        return pd.DataFrame(rows)
    else:
        overall_entities = aggregate_by_entity(df_clean, level=level, min_docs=min_docs, top_n=top_n)
        selected_entities = set(overall_entities["entity"].tolist()) if not overall_entities.empty else None

        entity_rows = []
        for label, s_yr, e_yr in periods:
            sub_df = df_clean[(df_clean["year"] >= s_yr) & (df_clean["year"] <= e_yr)]
            if len(sub_df) == 0:
                continue
            agg_df = aggregate_by_entity(sub_df, level=level, min_docs=1, top_n=None, indicators=indicators)
            if not agg_df.empty:
                if selected_entities is not None:
                    agg_df = agg_df[agg_df["entity"].isin(selected_entities)].copy()
                if not agg_df.empty:
                    agg_df.insert(0, "end_year", e_yr)
                    agg_df.insert(0, "start_year", s_yr)
                    agg_df.insert(0, "period", label)
                    entity_rows.append(agg_df)

        if entity_rows:
            return pd.concat(entity_rows, ignore_index=True)
        return pd.DataFrame()


def format_summary_markdown(metrics: Dict[str, Any], corpus_path: str, subtitle: str = "") -> str:
    """Genera un reporte legible en Markdown de los indicadores."""
    lines = [
        f"# Reporte Cienciométrico TlachIA: {Path(corpus_path).name}",
        f"*{subtitle}*" if subtitle else "",
        "",
        "## 1. Volumen, Citación e Índices de Hirsch/Egghe",
        f"- **Documentos Totales:** {metrics.get('num_documents', 0):,}",
        f"- **Citas Recibidas:** {metrics.get('times_cited', 0):,}",
        f"- **Citas Promedio por Documento:** {metrics.get('cites_per_doc', 0.0)}",
        f"- **Porcentaje de Documentos Citados:** {metrics.get('pct_docs_cited', 0.0)}%",
        f"- **Índice H del Corpus:** {metrics.get('h_index', 0)}",
        f"- **Índice G de Egghe:** {metrics.get('g_index', 0)}",
        f"- **Índice M (H / años activos):** {metrics.get('m_index', 0.0)}",
        f"- **Índice i10:** {metrics.get('i10_index', 0)}",
        "",
        "## 2. Impacto Normalizado y Excelencia",
        f"- **FWCI Promedio:** {metrics.get('fwci_avg', 0.0)}",
        f"- **FWCI Mediana:** {metrics.get('fwci_median', 0.0)}",
        f"- **Percentil Promedio:** {metrics.get('avg_percentile', 0.0)}",
        f"- **Porcentaje en Top 10% Más Citado:** {metrics.get('pct_top_10', 0.0)}% ({metrics.get('top_10_pct_docs', 0)} docs)",
        f"- **Porcentaje en Top 1% Élite:** {metrics.get('pct_top_1', 0.0)}% ({metrics.get('top_1_pct_docs', 0)} docs)",
        "",
        "## 3. Ciencia Abierta y Acceso (6 Vías)",
        f"- **Acceso Abierto Total:** {metrics.get('pct_oa_total', 0.0)}%",
        f"  - Diamond (Sin APC institucional): {metrics.get('pct_oa_diamond', 0.0)}%",
        f"  - Gold Comercial: {metrics.get('pct_oa_gold', 0.0)}%",
        f"  - Hybrid: {metrics.get('pct_oa_hybrid', 0.0)}%",
        f"  - Green (Auto-archivo / Repositorios): {metrics.get('pct_oa_green', 0.0)}%",
        f"  - Bronze: {metrics.get('pct_oa_bronze', 0.0)}%",
        f"  - Closed (Suscripción): {metrics.get('pct_oa_closed', 0.0)}%",
        "",
        "## 4. Economía de la Publicación",
        f"- **Gasto Observado en APC:** ${metrics.get('estimated_apc_paid_usd', 0.0):,.2f} USD",
        f"- **Gasto de Lista en APC:** ${metrics.get('apc_list_usd', 0.0):,.2f} USD",
        f"- **Gasto Medio en APC por Documento:** ${metrics.get('avg_apc_per_doc_usd', 0.0):,.2f} USD",
        f"- **Ahorro Estimado por Publicación Diamante:** ${metrics.get('estimated_diamond_savings_usd', 0.0):,.2f} USD",
        "",
        "## 5. Colaboración, Coautoría e Internacionalización",
        f"- **Colaboración Internacional:** {metrics.get('pct_international', 0.0)}%",
        f"- **Colaboración Doméstica:** {metrics.get('pct_domestic', 0.0)}%",
        f"- **Participación del Sur Global:** {metrics.get('pct_global_south', 0.0)}%",
        f"- **Autoría Única:** {metrics.get('pct_single_authored', 0.0)}%",
        f"- **Promedio de Autores por Documento:** {metrics.get('avg_authors_per_doc', 0.0)}",
        f"- **Índice de Colaboración (coautores en obras múltiples):** {metrics.get('collaboration_index', 0.0)}",
    ]
    return "\n".join([l for l in lines if l is not None])


def format_time_series_markdown(df_ts: pd.DataFrame, title: str, time_col: str = "period") -> str:
    """Genera una tabla comparativa Markdown limpia para series anuales o de periodos."""
    lines = [f"# {title}", ""]
    cols_to_show = [time_col, "entity", "num_documents", "times_cited", "cites_per_doc", "h_index", "fwci_avg", "pct_top_10", "pct_oa_total", "pct_international"]
    avail_cols = [c for c in cols_to_show if c in df_ts.columns]

    headers = {
        time_col: "Periodo" if time_col == "period" else "Año",
        "entity": "Entidad",
        "num_documents": "Docs",
        "times_cited": "Citas",
        "cites_per_doc": "Citas/Doc",
        "h_index": "H-Index",
        "fwci_avg": "FWCI",
        "pct_top_10": "% Top 10%",
        "pct_oa_total": "% OA",
        "pct_international": "% Intl",
    }

    header_row = "| " + " | ".join([headers.get(c, c) for c in avail_cols]) + " |"
    separator_row = "| " + " | ".join(["---"] * len(avail_cols)) + " |"
    lines.append(header_row)
    lines.append(separator_row)

    for _, row in df_ts.head(50).iterrows():
        vals = []
        for c in avail_cols:
            v = row.get(c)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                vals.append("-")
            elif c in ["pct_oa_total", "pct_top_10", "pct_international"]:
                vals.append(f"{v:.1f}%")
            elif isinstance(v, float):
                vals.append(f"{v:.2f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines)


def save_dataframe_output(df: pd.DataFrame, output_path: str) -> None:
    """Guarda un DataFrame según la extensión especificada."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ext = out.suffix.lower()
    if ext == ".parquet":
        df.to_parquet(out, index=False, engine="pyarrow")
    elif ext == ".csv":
        df.to_csv(out, index=False, encoding="utf-8")
    elif ext == ".json":
        df.to_json(out, orient="records", force_ascii=False, indent=2)
    elif ext == ".md":
        time_col = "year" if "year" in df.columns else ("period" if "period" in df.columns else df.columns[0])
        md_text = format_time_series_markdown(df, "Serie Cienciométrica TlachIA", time_col=time_col)
        with open(out, "w", encoding="utf-8") as f:
            f.write(md_text)
    else:
        df.to_parquet(out.with_suffix(".parquet"), index=False, engine="pyarrow")


def _add_corpus_arg(parser: argparse.ArgumentParser) -> None:
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--corpus", "--input", "-i", dest="corpus", type=str, help="Ruta al archivo tabular (.parquet, .json, .csv)")


def main():
    parser = argparse.ArgumentParser(
        description="TlachIA Metrics Engine CLI: Cálculo de 35+ indicadores cienciométricos, económicos y de ciencia abierta sin truncar dimensiones."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    level_choices = ["researcher", "author", "institution", "country", "source", "subfield", "topic", "field"]

    # 1. calculate-summary / summary
    for cmd_name in ("calculate-summary", "summary"):
        p_sum = subparsers.add_parser(cmd_name, help="Calcula los 35+ indicadores globales del corpus.")
        _add_corpus_arg(p_sum)
        p_sum.add_argument("--year", type=int, help="Filtrar por un año exacto")
        p_sum.add_argument("--year-from", type=int, help="Año de inicio")
        p_sum.add_argument("--year-to", type=int, help="Año de fin")
        p_sum.add_argument("--period", type=str, help="Filtrar por periodo (ej. '2019-2024')")
        p_sum.add_argument("--last-years", type=int, help="Filtrar por los últimos N años del corpus")
        p_sum.add_argument("--output", "-o", type=str, help="Ruta para guardar el reporte (.json o .md)")

    # 2. annual-series
    p_ann = subparsers.add_parser("annual-series", help="Genera la serie temporal anual (del corpus o por entidad con suavizado CMA).")
    _add_corpus_arg(p_ann)
    p_ann.add_argument("--year-from", type=int, help="Año inicial opcional")
    p_ann.add_argument("--year-to", type=int, help="Año final opcional")
    p_ann.add_argument("--level", type=str, choices=level_choices, help="Opcional: desagregar serie anual por entidad (para som-trajectory-mapping)")
    p_ann.add_argument("--min-docs", type=int, default=1, help="Mínimo de documentos acumulados por entidad (default: 1)")
    p_ann.add_argument("--top", type=int, default=None, help="Limitar a las Top N entidades por volumen")
    p_ann.add_argument("--cma-window", type=int, default=None, help="Ventana de Media Móvil Centrada (ej. 3 o 5) para suavizar trayectorias SOM")
    p_ann.add_argument("--indicators", type=str, default=None, help="Lista opcional de indicadores separados por coma (por defecto conserva TODOS)")
    p_ann.add_argument("--output", "-o", type=str, help="Ruta de guardado (.parquet, .csv, .json, .md)")

    # 3. period-series
    p_per = subparsers.add_parser("period-series", help="Calcula indicadores por periodos consecutivos o ventanas deslizantes.")
    _add_corpus_arg(p_per)
    p_per.add_argument("--window", type=int, help="Tamaño de ventana en años (ej. 5 o 10)")
    p_per.add_argument("--step", type=int, help="Paso de desplazamiento en años (default: igual a --window)")
    p_per.add_argument("--periods", type=str, help="Lista explícita de periodos separados por coma (ej. '2020-2022,2023-2026')")
    p_per.add_argument("--single-period", type=str, help="Un solo periodo específico (ej. '2020-2024')")
    p_per.add_argument("--last-years", type=int, help="Evaluar únicamente el último bloque de N años")
    p_per.add_argument("--level", type=str, choices=level_choices, help="Generar matriz longitudinal por entidad a través de periodos (para SOM / PathSOM)")
    p_per.add_argument("--min-docs", type=int, default=1, help="Mínimo de documentos acumulados por entidad")
    p_per.add_argument("--top", type=int, default=None, help="Limitar a las Top N entidades por volumen")
    p_per.add_argument("--indicators", type=str, default=None, help="Lista opcional de indicadores separados por coma (por defecto conserva TODOS)")
    p_per.add_argument("--output", "-o", type=str, help="Ruta de guardado (.parquet, .csv, .json, .md)")

    # 4. aggregate-by / by-entity
    for cmd_name in ("aggregate-by", "by-entity"):
        p_agg = subparsers.add_parser(cmd_name, help="Genera matriz [N x D] completa con los 35+ indicadores por entidad (para SOM).")
        _add_corpus_arg(p_agg)
        p_agg.add_argument("--level", type=str, choices=level_choices, required=True, help="Nivel de agregación")
        p_agg.add_argument("--min-docs", type=int, default=1, help="Mínimo de documentos por entidad (default: 1)")
        p_agg.add_argument("--top", type=int, default=None, help="Limitar a las Top N entidades por volumen")
        p_agg.add_argument("--indicators", type=str, default=None, help="Lista opcional de indicadores separados por coma (por defecto conserva TODOS)")
        p_agg.add_argument("--output", "-o", type=str, required=True, help="Ruta del archivo de salida (.parquet, .csv, .json)")

    # 5. gini-diversity
    p_gini = subparsers.add_parser("gini-diversity", help="Calcula el coeficiente de concentración de Gini temático.")
    _add_corpus_arg(p_gini)
    p_gini.add_argument("--column", type=str, default="keywords_plus", help="Columna para analizar frecuencias (default: keywords_plus)")

    args = parser.parse_args()
    df = load_canonical_corpus(args.corpus)

    ind_list = [x.strip() for x in args.indicators.split(",") if x.strip()] if getattr(args, "indicators", None) else None

    if args.command in ("calculate-summary", "summary"):
        subtitle_parts = []
        filtered_df = df.copy()

        if "year" in filtered_df.columns:
            years_s = pd.to_numeric(filtered_df["year"], errors="coerce").dropna()
            if len(years_s) > 0:
                max_yr = int(years_s.max())
                min_yr = int(years_s.min())

                if args.year:
                    filtered_df = filtered_df[filtered_df["year"] == args.year]
                    subtitle_parts.append(f"Año: {args.year}")
                elif args.period:
                    p_parts = [int(x.strip()) for x in args.period.split("-") if x.strip()]
                    if len(p_parts) == 2:
                        filtered_df = filtered_df[(filtered_df["year"] >= p_parts[0]) & (filtered_df["year"] <= p_parts[1])]
                        subtitle_parts.append(f"Periodo: {p_parts[0]}-{p_parts[1]}")
                elif args.last_years:
                    s_yr = max(min_yr, max_yr - args.last_years + 1)
                    filtered_df = filtered_df[(filtered_df["year"] >= s_yr) & (filtered_df["year"] <= max_yr)]
                    subtitle_parts.append(f"Últimos {args.last_years} años ({s_yr}-{max_yr})")
                else:
                    if args.year_from:
                        filtered_df = filtered_df[filtered_df["year"] >= args.year_from]
                        subtitle_parts.append(f"Desde {args.year_from}")
                    if args.year_to:
                        filtered_df = filtered_df[filtered_df["year"] <= args.year_to]
                        subtitle_parts.append(f"Hasta {args.year_to}")

        metrics = compute_summary_indicators(filtered_df)
        sub_str = " | ".join(subtitle_parts)
        md_report = format_summary_markdown(metrics, args.corpus, subtitle=sub_str)

        if args.output:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.suffix.lower() == ".json":
                with open(out, "w", encoding="utf-8") as f:
                    json.dump(metrics, f, indent=2, ensure_ascii=False)
            else:
                with open(out, "w", encoding="utf-8") as f:
                    f.write(md_report)
            print(f"[Éxito] Reporte guardado en {args.output}")
        else:
            print(md_report)

    elif args.command == "annual-series":
        annual_df = calculate_annual_series(
            df,
            year_from=args.year_from,
            year_to=args.year_to,
            level=args.level,
            min_docs=args.min_docs,
            top_n=args.top,
            cma_window=args.cma_window,
            indicators=ind_list,
        )
        if args.output:
            save_dataframe_output(annual_df, args.output)
            print(f"[Éxito] Serie anual ({len(annual_df)} filas, {len(annual_df.columns)} columnas) guardada en {args.output}")
        else:
            md_table = format_time_series_markdown(annual_df, f"Serie Temporal Anual: {Path(args.corpus).name}", time_col="year")
            print(md_table)

    elif args.command == "period-series":
        periods = build_periods(
            df=df,
            periods_str=args.periods,
            window=args.window,
            step=args.step,
            last_years=args.last_years,
            single_period=args.single_period,
        )
        if not periods:
            sys.stderr.write("[Aviso] No se pudieron determinar periodos temporales en el corpus.\n")
            sys.exit(0)

        print(f"[TlachIA Metrics] Analizando {len(periods)} periodos: {[p[0] for p in periods]}")
        period_df = calculate_period_series(
            df,
            periods=periods,
            level=args.level,
            min_docs=args.min_docs,
            top_n=args.top,
            indicators=ind_list,
        )
        if args.output:
            save_dataframe_output(period_df, args.output)
            print(f"[Éxito] Análisis de periodos guardado ({len(period_df)} filas, {len(period_df.columns)} columnas) en {args.output}")
        else:
            if args.level:
                print(period_df.head(20).to_string(index=False))
            else:
                md_table = format_time_series_markdown(period_df, f"Análisis por Periodos: {Path(args.corpus).name}", time_col="period")
                print(md_table)

    elif args.command in ("aggregate-by", "by-entity"):
        agg_df = aggregate_by_entity(
            df,
            level=args.level,
            min_docs=args.min_docs,
            top_n=args.top,
            indicators=ind_list,
        )
        save_dataframe_output(agg_df, args.output)
        print(f"[Éxito] Matriz a nivel '{args.level}' guardada ({len(agg_df)} entidades x {len(agg_df.columns)} columnas) en {args.output}")

    elif args.command == "gini-diversity":
        col = args.column
        if col not in df.columns:
            sys.stderr.write(f"[Error] La columna '{col}' no existe en el corpus.\n")
            sys.exit(1)

        term_counts: Dict[str, int] = {}
        for val in df[col].dropna():
            for t in _split_semicolon_items(val):
                term_counts[t] = term_counts.get(t, 0) + 1

        if not term_counts:
            print("[Aviso] No se encontraron términos para calcular Gini.")
            sys.exit(0)

        freqs = np.array(list(term_counts.values()))
        gini = compute_gini_coefficient(freqs)
        print(f"Coeficiente de Concentración de Gini ({col}): {gini:.4f}")
        print(f"Número total de términos analizados: {len(freqs)}")
        print(f"Término más frecuente: '{max(term_counts, key=term_counts.get)}' ({max(freqs)} ocurrencias)")


if __name__ == "__main__":
    main()
