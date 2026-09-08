#!/usr/bin/env python3
"""
CLI Helper: Open Access Monitor
Monitors the 6 Open Access pathways (Diamond, Gold APC, Hybrid, Bronze, Green, Closed),
quantifies transitional dynamics, and calculates estimated commercial APC expenditure in USD.
"""

import sys
import os
import json
import csv
import argparse
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional

DEFAULT_GOLD_APC_USD = 2200.0
DEFAULT_HYBRID_APC_USD = 3200.0


def load_corpus(filepath: str) -> List[Dict[str, Any]]:
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


def classify_oa_pathway(oa_raw: str, journal: str = "") -> str:
    """Classifies an article into one of the 6 canonical OA pathways."""
    raw = str(oa_raw).strip().lower()
    if not raw or raw in ["closed", "no", "false", "paywall"]:
        return "closed"
    if "diamond" in raw or "diamante" in raw:
        return "diamond"
    if "gold" in raw or "dorada" in raw or "oro" in raw:
        return "gold_apc"
    if "hybrid" in raw or "híbrida" in raw or "hibrida" in raw:
        return "hybrid"
    if "green" in raw or "verde" in raw or "repository" in raw:
        return "green"
    if "bronze" in raw or "bronce" in raw:
        return "bronze"
    if raw in ["true", "open", "oa", "yes"]:
        return "diamond" if any(k in journal.lower() for k in ["scielo", "redalyc", "unam"]) else "gold_apc"
    return "closed"


def cmd_breakdown(args):
    """Calculates distribution of production across the 6 OA pathways."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus(input_path)
    counts = Counter()
    total = len(records)

    for r in records:
        oa_val = r.get("oa_status") or r.get("Open Access") or r.get("OA") or ""
        src = r.get("source_title") or r.get("Source title") or ""
        pathway = classify_oa_pathway(oa_val, src)
        counts[pathway] += 1

    open_total = sum(counts[p] for p in ["diamond", "gold_apc", "hybrid", "green", "bronze"])
    oa_percentage = (open_total / total * 100.0) if total > 0 else 0.0

    breakdown_pct = {}
    for p in ["diamond", "gold_apc", "hybrid", "green", "bronze", "closed"]:
        breakdown_pct[p] = {
            "count": counts[p],
            "percentage": round((counts[p] / total * 100.0) if total > 0 else 0.0, 2)
        }

    result = {
        "total_documents_analyzed": total,
        "total_open_access_documents": open_total,
        "overall_open_access_rate_pct": round(oa_percentage, 2),
        "pathways_breakdown": breakdown_pct,
        "sovereignty_verdict": "Alta Soberanía Científica (Preponderancia Diamante)" if counts["diamond"] > counts["gold_apc"] else "Dependencia de Mercado Comercial (Preponderancia APC)"
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"OA Breakdown: {oa_percentage:.1f}% Open Access (Diamond: {counts['diamond']}, Gold: {counts['gold_apc']}). Saved to {args.output}")
    sys.exit(0)


def cmd_apc(args):
    """Calculates estimated APC spending in USD for commercial open access."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus(input_path)
    gold_cost = args.gold_apc_usd or DEFAULT_GOLD_APC_USD
    hybrid_cost = args.hybrid_apc_usd or DEFAULT_HYBRID_APC_USD

    gold_docs = 0
    hybrid_docs = 0

    for r in records:
        oa_val = r.get("oa_status") or r.get("Open Access") or ""
        src = r.get("source_title") or r.get("Source title") or ""
        pathway = classify_oa_pathway(oa_val, src)
        if pathway == "gold_apc":
            gold_docs += 1
        elif pathway == "hybrid":
            hybrid_docs += 1

    gold_total_usd = gold_docs * gold_cost
    hybrid_total_usd = hybrid_docs * hybrid_cost
    grand_total_usd = gold_total_usd + hybrid_total_usd

    result = {
        "total_commercial_apc_articles": gold_docs + hybrid_docs,
        "gold_oa_articles": gold_docs,
        "hybrid_oa_articles": hybrid_docs,
        "benchmark_apc_unit_costs_usd": {"gold_apc": gold_cost, "hybrid_apc": hybrid_cost},
        "estimated_gold_apc_total_usd": round(gold_total_usd, 2),
        "estimated_hybrid_apc_total_usd": round(hybrid_total_usd, 2),
        "estimated_total_apc_expenditure_usd": round(grand_total_usd, 2)
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Estimated APC Expenditure: ${grand_total_usd:,.2f} USD ({gold_docs + hybrid_docs} papers). Saved to {args.output}")
    sys.exit(0)


def cmd_trend(args):
    """Calculates annual open access transition series."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus(input_path)
    annual_totals = defaultdict(int)
    annual_oa = defaultdict(lambda: defaultdict(int))

    for r in records:
        yr_raw = r.get("year") or r.get("Year") or r.get("PY") or ""
        try:
            yr = int(str(yr_raw)[:4])
            if yr < 1990 or yr > 2030:
                continue
        except (ValueError, TypeError):
            continue

        oa_val = r.get("oa_status") or r.get("Open Access") or ""
        src = r.get("source_title") or r.get("Source title") or ""
        pathway = classify_oa_pathway(oa_val, src)

        annual_totals[yr] += 1
        annual_oa[yr][pathway] += 1

    years_sorted = sorted(list(annual_totals.keys()))
    trend = []

    for y in years_sorted:
        tot = annual_totals[y]
        p_map = annual_oa[y]
        op = sum(p_map[k] for k in ["diamond", "gold_apc", "hybrid", "green", "bronze"])
        trend.append({
            "year": y,
            "total_documents": tot,
            "open_access_documents": op,
            "open_access_percentage": round((op / tot * 100.0) if tot > 0 else 0.0, 2),
            "diamond_percentage": round((p_map["diamond"] / tot * 100.0) if tot > 0 else 0.0, 2),
            "gold_apc_percentage": round((p_map["gold_apc"] / tot * 100.0) if tot > 0 else 0.0, 2),
            "closed_percentage": round((p_map["closed"] / tot * 100.0) if tot > 0 else 0.0, 2)
        })

    result = {
        "transition_period": [years_sorted[0], years_sorted[-1]] if years_sorted else [],
        "annual_trend": trend
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"OA Transition Trend calculated across {len(years_sorted)} years. Output: {args.output}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="CLI for Open Access Monitor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: breakdown
    p_brk = subparsers.add_parser("breakdown", help="Calculate distribution across 6 OA pathways")
    p_brk.add_argument("--input", required=True, help="Path to corpus file")
    p_brk.add_argument("--output", required=True, help="Path to output JSON")
    p_brk.set_defaults(func=cmd_breakdown)

    # Subcommand: apc-spending
    p_apc = subparsers.add_parser("apc-spending", help="Calculate estimated commercial APC expenditure")
    p_apc.add_argument("--input", required=True, help="Path to corpus file")
    p_apc.add_argument("--gold-apc-usd", type=float, default=DEFAULT_GOLD_APC_USD, help="Unit cost Gold APC (USD)")
    p_apc.add_argument("--hybrid-apc-usd", type=float, default=DEFAULT_HYBRID_APC_USD, help="Unit cost Hybrid APC (USD)")
    p_apc.add_argument("--output", required=True, help="Path to output JSON")
    p_apc.set_defaults(func=cmd_apc)

    # Subcommand: transition-trend
    p_tre = subparsers.add_parser("transition-trend", help="Analyze annual open access transition series")
    p_tre.add_argument("--input", required=True, help="Path to corpus file")
    p_tre.add_argument("--output", required=True, help="Path to output JSON")
    p_tre.set_defaults(func=cmd_trend)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
