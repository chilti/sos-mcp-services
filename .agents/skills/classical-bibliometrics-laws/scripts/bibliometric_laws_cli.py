#!/usr/bin/env python3
"""
CLI Helper: Classical Bibliometrics Laws
Validates and fits classical informetric distributions:
- Lotka's Law of scientific productivity (full/fractional counting, KS test, PNG plot)
- Bradford's Law of literature dispersion (Egghe's continuous formulation, Core identification)
- Price's Index of literature obsolescence and citing half-life
- Scientific growth phases (Exponential vs Logistic curve fitting, doubling time, saturation K)
"""

import sys
import os
import json
import csv
import math
import argparse
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_corpus_data(filepath: str) -> List[Dict[str, Any]]:
    """Loads records from Parquet, CSV, or JSON."""
    lower = filepath.lower()
    if lower.endswith(".parquet"):
        import pandas as pd
        df = pd.read_parquet(filepath)
        return df.to_dict(orient="records")
    if lower.endswith(".csv"):
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
            return list(csv.DictReader(f))
    if lower.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("records", data) if isinstance(data, dict) else data
    return []


def cmd_lotka(args):
    """Fits Lotka's law of author productivity and evaluates goodness of fit."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus_data(input_path)
    counting = args.counting or "full"

    author_papers = defaultdict(float)
    for r in records:
        raw_auth = r.get("authors") or r.get("Authors") or r.get("AU") or ""
        authors = [a.strip() for a in str(raw_auth).split(";") if a.strip()]
        k = len(authors)
        if k == 0:
            continue
        credit = 1.0 if counting == "full" else (1.0 / k)
        for a in authors:
            author_papers[a] += credit

    # Round integer bins for productivity
    prod_counts = defaultdict(int)
    for a, p in author_papers.items():
        bin_p = max(1, int(round(p)))
        prod_counts[bin_p] += 1

    x_vals = np.array(sorted(prod_counts.keys()))
    y_vals = np.array([prod_counts[x] for x in x_vals])
    total_authors = float(sum(y_vals))

    if len(x_vals) < 3:
        sys.stderr.write("Error: Insufficient author productivity variation to fit Lotka's law.\n")
        sys.exit(1)

    # Fit ln(y) = ln(C) - c * ln(x)
    log_x = np.log(x_vals)
    log_y = np.log(y_vals)
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)
    c_exponent = -slope
    c_constant = np.exp(intercept)

    # Theoretical distribution: P(x) = (1 / x^c) / sum(1 / i^c)
    max_x = int(x_vals[-1])
    zeta_approx = sum(1.0 / (i ** c_exponent) for i in range(1, max_x + 1))
    p_theoretical = np.array([(1.0 / (x ** c_exponent)) / zeta_approx for x in x_vals])
    p_empirical = y_vals / total_authors

    # Kolmogorov-Smirnov test statistic D_max
    cum_empirical = np.cumsum(p_empirical)
    cum_theoretical = np.cumsum(p_theoretical)
    d_max = float(np.max(np.abs(cum_empirical - cum_theoretical)))
    # Critical value at alpha = 0.01: 1.63 / sqrt(N)
    d_critical_01 = 1.63 / math.sqrt(total_authors)
    d_critical_05 = 1.36 / math.sqrt(total_authors)
    passes_lotka = d_max <= d_critical_05

    result = {
        "law": "Lotka's Law",
        "counting_mode": counting,
        "total_authors": int(total_authors),
        "fitted_exponent_c": round(float(c_exponent), 4),
        "fitted_constant_C": round(float(c_constant), 2),
        "r_squared": round(float(r_value ** 2), 4),
        "ks_statistic_d_max": round(d_max, 4),
        "ks_critical_value_05": round(d_critical_05, 4),
        "goodness_of_fit_accepted": passes_lotka,
        "empirical_distribution": [{"papers": int(x), "authors": int(y)} for x, y in zip(x_vals[:20], y_vals[:20])]
    }

    # Plot if requested
    if args.plot_output:
        os.makedirs(os.path.dirname(os.path.abspath(args.plot_output)), exist_ok=True)
        plt.figure(figsize=(7, 5))
        plt.scatter(log_x, log_y, color="#2563eb", label="Empirical Data", zorder=3)
        plt.plot(log_x, intercept + slope * log_x, color="#dc2626", linestyle="--",
                 label=f"Lotka Fit: c={c_exponent:.2f} (R²={r_value**2:.2f})")
        plt.xlabel("ln(Papers per Author)")
        plt.ylabel("ln(Number of Authors)")
        plt.title(f"Lotka's Law Distribution ({counting.capitalize()} Counting)")
        plt.legend()
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.tight_layout()
        plt.savefig(args.plot_output, dpi=200)
        plt.close()
        result["plot_path"] = args.plot_output

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Lotka fit completed: c={c_exponent:.3f}, R²={r_value**2:.3f}, Fit={'Accepted' if passes_lotka else 'Rejected'}. Output: {args.output}")
    sys.exit(0)


def cmd_bradford(args):
    """Computes Egghe's continuous formulation of Bradford's Law."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus_data(input_path)
    source_counts = Counter()

    for r in records:
        src = (r.get("source_title") or r.get("Source title") or r.get("SO") or "").strip()
        if src:
            source_counts[src] += 1

    if not source_counts:
        sys.stderr.write("Error: No source titles found in corpus.\n")
        sys.exit(1)

    ranked_sources = source_counts.most_common()
    T = float(len(ranked_sources))  # Total journals
    A = float(sum(source_counts.values()))  # Total articles
    y0 = float(ranked_sources[0][1])  # Articles in top journal
    p = 3  # 3 Bradford zones

    # Egghe formulation: k = (e^Euler * y0)^(1/p) ...
    # Practical numerical demarcation into 3 zones of equal production (A / 3)
    target_zone_articles = A / 3.0

    zones = {1: [], 2: [], 3: []}
    zone_articles = {1: 0, 2: 0, 3: 0}
    current_zone = 1

    for src, count in ranked_sources:
        if current_zone < 3 and (zone_articles[current_zone] + count > target_zone_articles and len(zones[current_zone]) > 0):
            current_zone += 1
        zones[current_zone].append({"source": src, "articles": count})
        zone_articles[current_zone] += count

    n1 = len(zones[1])
    n2 = len(zones[2])
    n3 = len(zones[3])

    # Bradford multiplier k
    k1 = n2 / n1 if n1 > 0 else 1.0
    k2 = n3 / n2 if n2 > 0 else 1.0
    avg_k = round((k1 + k2) / 2.0, 2)

    result = {
        "law": "Bradford's Law (Egghe Demarcation)",
        "total_sources": int(T),
        "total_articles": int(A),
        "zones": {
            "zone_1_core": {
                "description": "Núcleo de Revistas (Core)",
                "sources_count": n1,
                "articles_count": zone_articles[1],
                "top_sources": [s["source"] for s in zones[1][:10]]
            },
            "zone_2_moderate": {
                "description": "Zona de Concentración Moderada",
                "sources_count": n2,
                "articles_count": zone_articles[2]
            },
            "zone_3_peripheral": {
                "description": "Zona Periférica / Alta Dispersión",
                "sources_count": n3,
                "articles_count": zone_articles[3]
            }
        },
        "bradford_multiplier_k": avg_k,
        "theoretical_proportion": f"1 : {avg_k:.1f} : {avg_k**2:.1f}"
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Bradford analysis: Core has {n1} journals ({zone_articles[1]} papers), Multiplier k={avg_k}. Saved to {args.output}")
    sys.exit(0)


def cmd_price_index(args):
    """Calculates Price's obsolescence index and citing half-life."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus_data(input_path)
    import re

    ref_ages = []
    recent_refs = 0
    total_refs = 0

    for r in records:
        doc_yr_raw = r.get("year") or r.get("Year") or r.get("PY") or ""
        try:
            doc_yr = int(str(doc_yr_raw)[:4])
        except (ValueError, TypeError):
            continue

        raw_refs = r.get("references") or r.get("References") or r.get("CR") or ""
        # Match 4-digit years in references string
        found_years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", str(raw_refs))]
        for ref_yr in found_years:
            if ref_yr <= doc_yr:
                age = doc_yr - ref_yr
                ref_ages.append(age)
                total_refs += 1
                if age <= 5:
                    recent_refs += 1

    price_idx = (recent_refs / total_refs * 100.0) if total_refs > 0 else 0.0
    half_life = float(np.median(ref_ages)) if ref_ages else 0.0

    result = {
        "law": "Price's Index of Obsolescence",
        "total_analyzed_references": total_refs,
        "references_le_5_years": recent_refs,
        "price_index_percentage": round(price_idx, 2),
        "citing_half_life_years": round(half_life, 1),
        "interpretation": "Hard Science (Rápida obsolescencia)" if price_idx >= 50 else ("Soft Science / Humanidades (Larga vida citacional)" if price_idx <= 30 else "Transicional")
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Price Index: {price_idx:.1f}%, Citing Half-life: {half_life:.1f} years. Output: {args.output}")
    sys.exit(0)


def cmd_growth(args):
    """Fits Exponential vs Logistic models to determine discipline growth phase."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus_data(input_path)
    annual_counts = Counter()

    for r in records:
        yr_raw = r.get("year") or r.get("Year") or r.get("PY") or ""
        try:
            yr = int(str(yr_raw)[:4])
            if 1900 <= yr <= 2030:
                annual_counts[yr] += 1
        except (ValueError, TypeError):
            continue

    if len(annual_counts) < 4:
        sys.stderr.write("Error: At least 4 distinct years required for growth curve fitting.\n")
        sys.exit(1)

    years = np.array(sorted(annual_counts.keys()))
    docs = np.array([annual_counts[y] for y in years])
    t_norm = years - years[0]

    # Model 1: Exponential N(t) = a * exp(b * t)
    def exp_func(t, a, b):
        return a * np.exp(b * t)

    # Model 2: Logistic N(t) = K / (1 + exp(-r * (t - t0)))
    def logistic_func(t, K, r, t0):
        return K / (1.0 + np.exp(-r * (t - t0)))

    # Fit Exponential
    popt_exp, _ = curve_fit(exp_func, t_norm, docs, p0=[docs[0], 0.05], maxfev=10000)
    docs_pred_exp = exp_func(t_norm, *popt_exp)
    ss_res_exp = np.sum((docs - docs_pred_exp) ** 2)
    ss_tot = np.sum((docs - np.mean(docs)) ** 2)
    r2_exp = max(0.0, 1.0 - (ss_res_exp / ss_tot)) if ss_tot > 0 else 0.0
    doubling_time = math.log(2) / popt_exp[1] if popt_exp[1] > 0 else float("inf")

    # Fit Logistic
    try:
        popt_log, _ = curve_fit(logistic_func, t_norm, docs, p0=[max(docs) * 2, 0.1, len(t_norm) / 2], maxfev=10000)
        docs_pred_log = logistic_func(t_norm, *popt_log)
        ss_res_log = np.sum((docs - docs_pred_log) ** 2)
        r2_log = max(0.0, 1.0 - (ss_res_log / ss_tot)) if ss_tot > 0 else 0.0
        saturation_K = float(popt_log[0])
    except Exception:
        r2_log = 0.0
        saturation_K = None
        docs_pred_log = None

    if r2_exp > r2_log:
        growth_phase = "Fase II: Crecimiento Exponencial (Expansión Activa)"
    elif r2_log > 0.7:
        growth_phase = "Fase III: Madurez / Saturación Logística"
    else:
        growth_phase = "Fase I: Emergencia / Fluctuación Inicial"

    result = {
        "law": "Scientific Growth Phases",
        "years_range": [int(years[0]), int(years[-1])],
        "exponential_fit": {
            "r_squared": round(float(r2_exp), 4),
            "doubling_time_years": round(doubling_time, 2) if doubling_time != float("inf") else None
        },
        "logistic_fit": {
            "r_squared": round(float(r2_log), 4),
            "estimated_saturation_carrying_capacity_K": round(saturation_K, 1) if saturation_K else None
        },
        "diagnosed_phase": growth_phase
    }

    if args.plot_output:
        os.makedirs(os.path.dirname(os.path.abspath(args.plot_output)), exist_ok=True)
        plt.figure(figsize=(8, 5))
        plt.scatter(years, docs, color="#1e293b", label="Empirical Output", zorder=3)
        plt.plot(years, docs_pred_exp, color="#2563eb", linestyle="--", label=f"Exponential (R²={r2_exp:.2f})")
        if docs_pred_log is not None:
            plt.plot(years, docs_pred_log, color="#16a34a", linestyle="-", label=f"Logistic (R²={r2_log:.2f})")
        plt.xlabel("Year")
        plt.ylabel("Publications Count")
        plt.title(f"Scientific Growth Curve ({growth_phase})")
        plt.legend()
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.tight_layout()
        plt.savefig(args.plot_output, dpi=200)
        plt.close()
        result["plot_path"] = args.plot_output

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Growth Phase: {growth_phase} (Exp R²={r2_exp:.2f}, Log R²={r2_log:.2f}). Output: {args.output}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="CLI for Classical Bibliometrics Laws")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: lotka
    p_lot = subparsers.add_parser("lotka", help="Fit Lotka's Law of author productivity")
    p_lot.add_argument("--input", required=True, help="Path to corpus file")
    p_lot.add_argument("--output", required=True, help="Path to output JSON")
    p_lot.add_argument("--counting", choices=["full", "fractional"], default="full")
    p_lot.add_argument("--plot-output", help="Optional path to output PNG plot")
    p_lot.set_defaults(func=cmd_lotka)

    # Subcommand: bradford
    p_bra = subparsers.add_parser("bradford", help="Compute Bradford's Law continuous zones")
    p_bra.add_argument("--input", required=True, help="Path to corpus file")
    p_bra.add_argument("--output", required=True, help="Path to output JSON")
    p_bra.set_defaults(func=cmd_bradford)

    # Subcommand: price-index
    p_pri = subparsers.add_parser("price-index", help="Calculate Price's obsolescence index")
    p_pri.add_argument("--input", required=True, help="Path to corpus file")
    p_pri.add_argument("--output", required=True, help="Path to output JSON")
    p_pri.set_defaults(func=cmd_price_index)

    # Subcommand: growth-phase
    p_gro = subparsers.add_parser("growth-phase", help="Fit Exponential vs Logistic growth models")
    p_gro.add_argument("--input", required=True, help="Path to corpus file")
    p_gro.add_argument("--output", required=True, help="Path to output JSON")
    p_gro.add_argument("--plot-output", help="Optional path to output PNG plot")
    p_gro.set_defaults(func=cmd_growth)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
