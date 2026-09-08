#!/usr/bin/env /home/ambientesPy/revistaslatam/bin/python
"""
TlachIA Metrics Engine CLI
--------------------------
Motor cienciométrico autónomo e independiente para el cálculo de más de 30 indicadores
de volumen, citación, excelencia (FWCI, Top 10%, Top 1%), las 6 vías de Acceso Abierto,
economía de la publicación (APC USD y ahorro Diamante), colaboración internacional,
coeficiente de Gini temático y análisis temporal (anual y longitudinal por periodos).
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
    'MX', 'BR', 'AR', 'CL', 'CO', 'PE', 'UY', 'VE', 'EC', 'BO', 'PY', 'CU', 'DO', 'CR', 'PA', 'GT', 'HN', 'SV', 'NI', 'JM', 'TT',
    # África
    'ZA', 'EG', 'NG', 'KE', 'GH', 'ET', 'TZ', 'UG', 'DZ', 'MA', 'TN', 'SN', 'CM', 'CI', 'ZW',
    # Asia y Medio Oriente
    'IN', 'ID', 'PK', 'BD', 'PH', 'VN', 'TH', 'MY', 'IR', 'IQ', 'JO', 'LB', 'LK', 'NP', 'KZ', 'UZ'
}

def load_canonical_corpus(filepath: str) -> pd.DataFrame:
    """Carga un archivo bibliográfico tabular en DataFrame."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")
    ext = p.suffix.lower()
    if ext == ".parquet":
        df = pd.read_parquet(p)
    elif ext == ".csv":
        df = pd.read_csv(p)
    elif ext == ".json":
        df = pd.read_json(p)
    else:
        try:
            df = pd.read_parquet(p)
        except Exception:
            df = pd.read_csv(p)
    return df

def calculate_h_index(citations_series: pd.Series) -> int:
    """Calcula el índice H a partir de un arreglo de citas."""
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

def compute_summary_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcula la suite completa de más de 30 indicadores cienciométricos de TlachIA."""
    n_docs = len(df)
    if n_docs == 0:
        return {
            "num_documents": 0, "times_cited": 0, "cites_per_doc": 0.0, "pct_docs_cited": 0.0,
            "h_index": 0, "i10_index": 0, "fwci_avg": None, "avg_percentile": None,
            "pct_top_10": None, "pct_top_1": None, "pct_oa_total": 0.0, "pct_oa_gold": 0.0,
            "pct_oa_hybrid": 0.0, "pct_oa_diamond": 0.0, "pct_oa_green": 0.0, "pct_oa_closed": 0.0,
            "estimated_apc_paid_usd": 0.0, "avg_apc_per_doc_usd": 0.0, "estimated_diamond_savings_usd": 0.0,
            "pct_international": 0.0, "pct_domestic": 0.0, "pct_global_south": 0.0
        }

    # 1. Volumen y Citas
    cits_col = "citations" if "citations" in df.columns else ("cited_by_count" if "cited_by_count" in df.columns else None)
    if cits_col:
        cits = pd.to_numeric(df[cits_col], errors="coerce").fillna(0)
    else:
        cits = pd.Series([0] * n_docs)

    times_cited = int(cits.sum())
    cites_per_doc = float(times_cited / n_docs)
    pct_docs_cited = float(((cits > 0).sum() / n_docs) * 100.0)
    h_idx = calculate_h_index(cits)
    i10_idx = calculate_i10_index(cits)

    # 2. Impacto Normalizado (FWCI) y Percentiles
    has_fwci = "fwci" in df.columns and df["fwci"].notna().any()
    if has_fwci:
        fwci_s = pd.to_numeric(df["fwci"], errors="coerce").dropna()
        fwci_avg = float(fwci_s.mean()) if len(fwci_s) > 0 else None
    else:
        fwci_avg = None

    has_percentile = "percentile" in df.columns and df["percentile"].notna().any()
    if has_percentile:
        perc_s = pd.to_numeric(df["percentile"], errors="coerce").dropna()
        if len(perc_s) > 0:
            if perc_s.max() <= 1.0 and perc_s.max() > 0:
                perc_s = perc_s * 100.0
            avg_percentile = float(perc_s.mean())
            pct_top_10 = float(((perc_s >= 90.0).sum() / n_docs) * 100.0)
            pct_top_1 = float(((perc_s >= 99.0).sum() / n_docs) * 100.0)
        else:
            avg_percentile, pct_top_10, pct_top_1 = None, None, None
    else:
        avg_percentile, pct_top_10, pct_top_1 = None, None, None

    # 3. Acceso Abierto y Ciencia Abierta (6 Vías)
    oa_status_s = df["oa_status"].fillna("closed").astype(str).str.lower() if "oa_status" in df.columns else pd.Series(["closed"] * n_docs)
    is_oa_s = (df["is_oa"].fillna(0).astype(int) == 1) | (oa_status_s.isin(["gold", "diamond", "green", "hybrid", "bronze"])) if "is_oa" in df.columns else (oa_status_s != "closed")
    
    pct_oa_total = float((is_oa_s.sum() / n_docs) * 100.0)
    pct_oa_gold = float(((oa_status_s == "gold").sum() / n_docs) * 100.0)
    pct_oa_hybrid = float(((oa_status_s == "hybrid").sum() / n_docs) * 100.0)
    pct_oa_diamond = float(((oa_status_s == "diamond").sum() / n_docs) * 100.0)
    pct_oa_green = float(((oa_status_s == "green").sum() / n_docs) * 100.0)
    pct_oa_closed = float(((oa_status_s == "closed").sum() / n_docs) * 100.0)

    # 4. Economía de la Publicación (APC USD y Ahorro Diamante)
    if "apc_paid_usd" in df.columns:
        apc_s = pd.to_numeric(df["apc_paid_usd"], errors="coerce").fillna(0)
        est_apc_paid_usd = float(apc_s.sum())
        avg_apc_per_doc_usd = float(est_apc_paid_usd / n_docs)
    else:
        est_apc_paid_usd = 0.0
        avg_apc_per_doc_usd = 0.0

    diamond_count = int((oa_status_s == "diamond").sum())
    est_diamond_savings_usd = float(diamond_count * 1800.0)

    # 5. Colaboración Internacional y Sur Global
    n_intl = 0
    n_domestic = 0
    n_global_south = 0

    if "country_codes" in df.columns:
        for val in df["country_codes"].dropna():
            codes = [c.strip().upper() for c in str(val).split(";") if c.strip()]
            if len(set(codes)) > 1:
                n_intl += 1
            elif len(set(codes)) == 1:
                n_domestic += 1
            if any(c in GLOBAL_SOUTH_COUNTRIES for c in codes):
                n_global_south += 1

    pct_intl = float((n_intl / n_docs) * 100.0) if n_docs > 0 else 0.0
    pct_dom = float((n_domestic / n_docs) * 100.0) if n_docs > 0 else 0.0
    pct_south = float((n_global_south / n_docs) * 100.0) if n_docs > 0 else 0.0

    return {
        "num_documents": n_docs,
        "times_cited": times_cited,
        "cites_per_doc": round(cites_per_doc, 2),
        "pct_docs_cited": round(pct_docs_cited, 2),
        "h_index": h_idx,
        "i10_index": i10_idx,
        "fwci_avg": round(fwci_avg, 3) if fwci_avg is not None else None,
        "avg_percentile": round(avg_percentile, 2) if avg_percentile is not None else None,
        "pct_top_10": round(pct_top_10, 2) if pct_top_10 is not None else None,
        "pct_top_1": round(pct_top_1, 2) if pct_top_1 is not None else None,
        "pct_oa_total": round(pct_oa_total, 2),
        "pct_oa_gold": round(pct_oa_gold, 2),
        "pct_oa_hybrid": round(pct_oa_hybrid, 2),
        "pct_oa_diamond": round(pct_oa_diamond, 2),
        "pct_oa_green": round(pct_oa_green, 2),
        "pct_oa_closed": round(pct_oa_closed, 2),
        "estimated_apc_paid_usd": round(est_apc_paid_usd, 2),
        "avg_apc_per_doc_usd": round(avg_apc_per_doc_usd, 2),
        "estimated_diamond_savings_usd": round(est_diamond_savings_usd, 2),
        "pct_international": round(pct_intl, 2),
        "pct_domestic": round(pct_dom, 2),
        "pct_global_south": round(pct_south, 2)
    }

def build_periods(df: pd.DataFrame, periods_str: Optional[str] = None,
                  window: Optional[int] = None, step: Optional[int] = None,
                  last_years: Optional[int] = None, single_period: Optional[str] = None) -> List[Tuple[str, int, int]]:
    """
    Construye la lista de periodos (etiqueta, año_inicio, año_fin).
    """
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

    # Por defecto, si no se especifica partición, genera bloques de 5 años
    curr = min_year
    while curr <= max_year:
        end = min(curr + 4, max_year)
        label = f"{curr}-{end}" if curr != end else str(curr)
        periods.append((label, curr, end))
        curr += 5
    return periods

def calculate_annual_series(df: pd.DataFrame, year_from: Optional[int] = None,
                            year_to: Optional[int] = None) -> pd.DataFrame:
    """Calcula la serie temporal año por año con los más de 30 indicadores TlachIA."""
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
    rows = []
    prev_docs = None
    prev_cites = None
    
    for yr in years:
        sub_df = df_clean[df_clean["year"] == yr]
        metrics = compute_summary_indicators(sub_df)
        curr_docs = metrics.get("num_documents", 0)
        curr_cites = metrics.get("times_cited", 0)
        
        doc_growth = None
        cite_growth = None
        if prev_docs is not None and prev_docs > 0:
            doc_growth = round(((curr_docs - prev_docs) / prev_docs) * 100.0, 2)
        if prev_cites is not None and prev_cites > 0:
            cite_growth = round(((curr_cites - prev_cites) / prev_cites) * 100.0, 2)
            
        row = {
            "year": int(yr),
            **metrics,
            "doc_growth_pct": doc_growth,
            "cite_growth_pct": cite_growth
        }
        rows.append(row)
        prev_docs = curr_docs
        prev_cites = curr_cites
        
    return pd.DataFrame(rows)

def calculate_period_series(df: pd.DataFrame, periods: List[Tuple[str, int, int]],
                            level: Optional[str] = None) -> pd.DataFrame:
    """
    Calcula indicadores cienciométricos para una secuencia de periodos.
    Si level es None: serie temporal agregada a nivel de corpus con tasas de crecimiento.
    Si level es 'researcher', 'institution' o 'country': matriz longitudinal de entidades.
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
            metrics = compute_summary_indicators(sub_df)
            curr_docs = metrics.get("num_documents", 0)
            curr_cites = metrics.get("times_cited", 0)
            
            doc_growth = None
            cite_growth = None
            if prev_docs is not None and prev_docs > 0:
                doc_growth = round(((curr_docs - prev_docs) / prev_docs) * 100.0, 2)
            if prev_cites is not None and prev_cites > 0:
                cite_growth = round(((curr_cites - prev_cites) / prev_cites) * 100.0, 2)
                
            row = {
                "period": label,
                "start_year": s_yr,
                "end_year": e_yr,
                **metrics,
                "doc_growth_pct": doc_growth,
                "cite_growth_pct": cite_growth
            }
            rows.append(row)
            prev_docs = curr_docs
            prev_cites = curr_cites
            
        return pd.DataFrame(rows)
    else:
        entity_rows = []
        for label, s_yr, e_yr in periods:
            sub_df = df_clean[(df_clean["year"] >= s_yr) & (df_clean["year"] <= e_yr)]
            if len(sub_df) == 0:
                continue
            agg_df = aggregate_by_entity(sub_df, level)
            if not agg_df.empty:
                agg_df["period"] = label
                agg_df["start_year"] = s_yr
                agg_df["end_year"] = e_yr
                entity_rows.append(agg_df)
            
        if entity_rows:
            res = pd.concat(entity_rows, ignore_index=True)
            cols = ["period", "start_year", "end_year", "entity", "level", "num_documents", "times_cited", "cites_per_doc", "h_index"]
            remaining = [c for c in res.columns if c not in cols]
            return res[[c for c in cols if c in res.columns] + remaining]
        return pd.DataFrame()

def aggregate_by_entity(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """Agrega indicadores cienciométricos a nivel de investigador, institución o país."""
    records = []
    
    if level == "researcher":
        author_map = {}
        for _, row in df.iterrows():
            cits = row.get("citations", 0) or 0
            is_oa = row.get("is_oa", 0) or 0
            fwci = row.get("fwci")
            authors = [a.strip() for a in str(row.get("authors", "")).split(";") if a.strip()]
            for auth in authors:
                if auth not in author_map:
                    author_map[auth] = {"cits": [], "docs": 0, "oa_count": 0, "fwci_vals": []}
                author_map[auth]["docs"] += 1
                author_map[auth]["cits"].append(cits)
                author_map[auth]["oa_count"] += 1 if is_oa else 0
                if fwci is not None and not np.isnan(fwci):
                    author_map[auth]["fwci_vals"].append(float(fwci))
                    
        for auth, data in author_map.items():
            c_arr = pd.Series(data["cits"])
            fw_mean = float(np.mean(data["fwci_vals"])) if data["fwci_vals"] else None
            records.append({
                "entity": auth,
                "level": "researcher",
                "num_documents": data["docs"],
                "times_cited": int(c_arr.sum()),
                "cites_per_doc": round(float(c_arr.mean()), 2),
                "h_index": calculate_h_index(c_arr),
                "i10_index": calculate_i10_index(c_arr),
                "pct_oa": round((data["oa_count"] / data["docs"]) * 100.0, 2),
                "fwci_avg": round(fw_mean, 3) if fw_mean is not None else None
            })
            
    elif level == "institution":
        inst_map = {}
        for _, row in df.iterrows():
            cits = row.get("citations", 0) or 0
            is_oa = row.get("is_oa", 0) or 0
            affils = [af.strip() for af in str(row.get("affiliations", "")).split(";") if af.strip()]
            for aff in affils:
                if aff not in inst_map:
                    inst_map[aff] = {"cits": [], "docs": 0, "oa_count": 0}
                inst_map[aff]["docs"] += 1
                inst_map[aff]["cits"].append(cits)
                inst_map[aff]["oa_count"] += 1 if is_oa else 0
                
        for aff, data in inst_map.items():
            c_arr = pd.Series(data["cits"])
            records.append({
                "entity": aff,
                "level": "institution",
                "num_documents": data["docs"],
                "times_cited": int(c_arr.sum()),
                "cites_per_doc": round(float(c_arr.mean()), 2),
                "h_index": calculate_h_index(c_arr),
                "pct_oa": round((data["oa_count"] / data["docs"]) * 100.0, 2)
            })
            
    elif level == "country":
        country_map = {}
        for _, row in df.iterrows():
            cits = row.get("citations", 0) or 0
            codes = [c.strip().upper() for c in str(row.get("country_codes", "")).split(";") if c.strip()]
            for cc in codes:
                if cc not in country_map:
                    country_map[cc] = {"cits": [], "docs": 0}
                country_map[cc]["docs"] += 1
                country_map[cc]["cits"].append(cits)
                
        for cc, data in country_map.items():
            c_arr = pd.Series(data["cits"])
            records.append({
                "entity": cc,
                "level": "country",
                "num_documents": data["docs"],
                "times_cited": int(c_arr.sum()),
                "cites_per_doc": round(float(c_arr.mean()), 2),
                "h_index": calculate_h_index(c_arr),
                "is_global_south": 1 if cc in GLOBAL_SOUTH_COUNTRIES else 0
            })
            
    res_df = pd.DataFrame(records)
    if not res_df.empty:
        res_df = res_df.sort_values(by="num_documents", ascending=False)
    return res_df

def format_summary_markdown(metrics: Dict[str, Any], corpus_path: str, subtitle: str = "") -> str:
    """Genera un reporte legible en Markdown de los indicadores."""
    lines = [
        f"# Reporte Cienciométrico TlachIA: {Path(corpus_path).name}",
        f"*{subtitle}*" if subtitle else "",
        "",
        "## 1. Volumen y Citación",
        f"- **Documentos Totales:** {metrics.get('num_documents', 0):,}",
        f"- **Citas Recibidas:** {metrics.get('times_cited', 0):,}",
        f"- **Citas Promedio por Documento:** {metrics.get('cites_per_doc', 0.0)}",
        f"- **Porcentaje de Documentos Citados:** {metrics.get('pct_docs_cited', 0.0)}%",
        f"- **Índice H del Corpus:** {metrics.get('h_index', 0)}",
        f"- **Índice i10:** {metrics.get('i10_index', 0)}",
        "",
        "## 2. Impacto Normalizado y Excelencia",
        f"- **FWCI Promedio:** {metrics.get('fwci_avg') if metrics.get('fwci_avg') is not None else 'N/D (Sólo citas brutas)'}",
        f"- **Percentil Promedio:** {metrics.get('avg_percentile') if metrics.get('avg_percentile') is not None else 'N/D'}",
        f"- **Porcentaje en Top 10% Más Citado:** {metrics.get('pct_top_10') if metrics.get('pct_top_10') is not None else 'N/D'}%",
        f"- **Porcentaje en Top 1% Élite:** {metrics.get('pct_top_1') if metrics.get('pct_top_1') is not None else 'N/D'}%",
        "",
        "## 3. Ciencia Abierta y Acceso (6 Vías)",
        f"- **Acceso Abierto Total:** {metrics.get('pct_oa_total', 0.0)}%",
        f"  - Gold Comercial: {metrics.get('pct_oa_gold', 0.0)}%",
        f"  - Diamond (Sin APC institucional): {metrics.get('pct_oa_diamond', 0.0)}%",
        f"  - Hybrid: {metrics.get('pct_oa_hybrid', 0.0)}%",
        f"  - Green (Auto-archivo / Repositorios): {metrics.get('pct_oa_green', 0.0)}%",
        f"  - Closed (Suscripción): {metrics.get('pct_oa_closed', 0.0)}%",
        "",
        "## 4. Economía de la Publicación",
        f"- **Gasto Estimado en APC:** ${metrics.get('estimated_apc_paid_usd', 0.0):,.2f} USD",
        f"- **Gasto Medio en APC por Documento:** ${metrics.get('avg_apc_per_doc_usd', 0.0):,.2f} USD",
        f"- **Ahorro Estimado por Publicación Diamante:** ${metrics.get('estimated_diamond_savings_usd', 0.0):,.2f} USD",
        "",
        "## 5. Colaboración e Internacionalización",
        f"- **Colaboración Internacional:** {metrics.get('pct_international', 0.0)}%",
        f"- **Colaboración Doméstica:** {metrics.get('pct_domestic', 0.0)}%",
        f"- **Participación del Sur Global:** {metrics.get('pct_global_south', 0.0)}%"
    ]
    return "\n".join([l for l in lines if l is not None])

def format_time_series_markdown(df_ts: pd.DataFrame, title: str, time_col: str = "period") -> str:
    """Genera una tabla comparativa Markdown limpia para series anuales o de periodos."""
    lines = [f"# {title}", ""]
    cols_to_show = [time_col, "num_documents", "times_cited", "cites_per_doc", "h_index", "fwci_avg", "pct_oa_total", "estimated_apc_paid_usd", "doc_growth_pct"]
    avail_cols = [c for c in cols_to_show if c in df_ts.columns]
    
    headers = {
        time_col: "Periodo" if time_col == "period" else "Año",
        "num_documents": "Docs",
        "times_cited": "Citas",
        "cites_per_doc": "Citas/Doc",
        "h_index": "H-Index",
        "fwci_avg": "FWCI",
        "pct_oa_total": "% OA",
        "estimated_apc_paid_usd": "APC (USD)",
        "doc_growth_pct": "Δ Docs (%)"
    }
    
    header_row = "| " + " | ".join([headers.get(c, c) for c in avail_cols]) + " |"
    separator_row = "| " + " | ".join(["---"] * len(avail_cols)) + " |"
    lines.append(header_row)
    lines.append(separator_row)
    
    for _, row in df_ts.iterrows():
        vals = []
        for c in avail_cols:
            v = row.get(c)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                vals.append("-")
            elif c == "estimated_apc_paid_usd":
                vals.append(f"${v:,.0f}")
            elif c in ["doc_growth_pct", "pct_oa_total"]:
                vals.append(f"{v:+.1f}%" if c == "doc_growth_pct" else f"{v:.1f}%")
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
        md_text = format_time_series_markdown(df, "Serie Temporal Cienciométrica", time_col=time_col)
        with open(out, "w", encoding="utf-8") as f:
            f.write(md_text)
    else:
        df.to_parquet(out.with_suffix(".parquet"), index=False, engine="pyarrow")

def main():
    parser = argparse.ArgumentParser(
        description="TlachIA Metrics Engine CLI: Cálculo de indicadores cienciométricos, económicos y de ciencia abierta."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. calculate-summary
    p_sum = subparsers.add_parser("calculate-summary", help="Calcula los más de 30 indicadores globales del corpus.")
    p_sum.add_argument("--corpus", type=str, required=True, help="Ruta al archivo tabular (.parquet, .json, .csv)")
    p_sum.add_argument("--year", type=int, help="Filtrar por un año exacto")
    p_sum.add_argument("--year-from", type=int, help="Año de inicio")
    p_sum.add_argument("--year-to", type=int, help="Año de fin")
    p_sum.add_argument("--period", type=str, help="Filtrar por periodo (ej. '2019-2024')")
    p_sum.add_argument("--last-years", type=int, help="Filtrar por los últimos N años del corpus (ej. 5 para el último lustro)")
    p_sum.add_argument("--output", type=str, help="Ruta para guardar el reporte (.json o .md)")
    
    # 2. annual-series
    p_ann = subparsers.add_parser("annual-series", help="Genera la serie temporal de indicadores año por año.")
    p_ann.add_argument("--corpus", type=str, required=True, help="Ruta al archivo tabular")
    p_ann.add_argument("--year-from", type=int, help="Año inicial opcional")
    p_ann.add_argument("--year-to", type=int, help="Año final opcional")
    p_ann.add_argument("--output", type=str, help="Ruta de guardado (.parquet, .csv, .json, .md)")
    
    # 3. period-series
    p_per = subparsers.add_parser("period-series", help="Calcula indicadores por periodos consecutivos o ventanas deslizantes.")
    p_per.add_argument("--corpus", type=str, required=True, help="Ruta al archivo tabular")
    p_per.add_argument("--window", type=int, help="Tamaño de ventana en años (ej. 5 o 10)")
    p_per.add_argument("--step", type=int, help="Paso de desplazamiento en años (default: igual a --window)")
    p_per.add_argument("--periods", type=str, help="Lista explícita de periodos separados por coma (ej. '2000-2009,2010-2019,2020-2024')")
    p_per.add_argument("--single-period", type=str, help="Un solo periodo específico (ej. '2020-2024')")
    p_per.add_argument("--last-years", type=int, help="Evaluar únicamente el último bloque de N años")
    p_per.add_argument("--level", type=str, choices=["researcher", "institution", "country"],
                       help="Generar matriz longitudinal por entidad a través de periodos (para SOM)")
    p_per.add_argument("--output", type=str, help="Ruta de guardado (.parquet, .csv, .json, .md)")
    
    # 4. aggregate-by
    p_agg = subparsers.add_parser("aggregate-by", help="Agrega indicadores por investigador, institución o país.")
    p_agg.add_argument("--corpus", type=str, required=True, help="Ruta al archivo tabular")
    p_agg.add_argument("--level", type=str, choices=["researcher", "institution", "country"], required=True,
                       help="Nivel de agregación")
    p_agg.add_argument("--output", type=str, required=True, help="Ruta del archivo de salida (.parquet, .csv, .json)")
    
    # 5. gini-diversity
    p_gini = subparsers.add_parser("gini-diversity", help="Calcula el coeficiente de concentración de Gini temático.")
    p_gini.add_argument("--corpus", type=str, required=True, help="Ruta al archivo tabular")
    p_gini.add_argument("--column", type=str, default="keywords_plus", help="Columna para analizar frecuencias (default: keywords_plus)")

    args = parser.parse_args()
    df = load_canonical_corpus(args.corpus)
    
    if args.command == "calculate-summary":
        subtitle_parts = []
        filtered_df = df.copy()
        
        # Filtrado temporal si se especificó
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
        annual_df = calculate_annual_series(df, year_from=args.year_from, year_to=args.year_to)
        
        if args.output:
            save_dataframe_output(annual_df, args.output)
            print(f"[Éxito] Serie anual ({len(annual_df)} años) guardada en {args.output}")
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
            single_period=args.single_period
        )
        if not periods:
            sys.stderr.write("[Aviso] No se pudieron determinar periodos temporales en el corpus.\n")
            sys.exit(0)
            
        print(f"[TlachIA Metrics] Analizando {len(periods)} periodos: {[p[0] for p in periods]}")
        period_df = calculate_period_series(df, periods=periods, level=args.level)
        
        if args.output:
            save_dataframe_output(period_df, args.output)
            print(f"[Éxito] Análisis de periodos guardado ({len(period_df)} filas) en {args.output}")
        else:
            if args.level:
                print(period_df.head(20).to_string(index=False))
            else:
                md_table = format_time_series_markdown(period_df, f"Análisis por Periodos: {Path(args.corpus).name}", time_col="period")
                print(md_table)

    elif args.command == "aggregate-by":
        agg_df = aggregate_by_entity(df, args.level)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        ext = out.suffix.lower()
        if ext == ".parquet":
            agg_df.to_parquet(out, index=False, engine="pyarrow")
        elif ext == ".csv":
            agg_df.to_csv(out, index=False, encoding="utf-8")
        elif ext == ".json":
            agg_df.to_json(out, orient="records", force_ascii=False, indent=2)
        else:
            agg_df.to_parquet(out.with_suffix(".parquet"), index=False, engine="pyarrow")
        print(f"[Éxito] Agregación a nivel '{args.level}' guardada ({len(agg_df)} entidades) en {args.output}")
        
    elif args.command == "gini-diversity":
        col = args.column
        if col not in df.columns:
            sys.stderr.write(f"[Error] La columna '{col}' no existe en el corpus.\n")
            sys.exit(1)
            
        term_counts = {}
        for val in df[col].dropna():
            for t in str(val).split(";"):
                clean_t = t.strip()
                if clean_t:
                    term_counts[clean_t] = term_counts.get(clean_t, 0) + 1
                    
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
