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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

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

    # Estimación de APC para anotación visual
    gold_cost = getattr(args, "gold_apc_usd", DEFAULT_GOLD_APC_USD) or DEFAULT_GOLD_APC_USD
    hybrid_cost = getattr(args, "hybrid_apc_usd", DEFAULT_HYBRID_APC_USD) or DEFAULT_HYBRID_APC_USD
    est_apc_usd = counts["gold_apc"] * gold_cost + counts["hybrid"] * hybrid_cost

    result = {
        "total_documents_analyzed": total,
        "total_open_access_documents": open_total,
        "overall_open_access_rate_pct": round(oa_percentage, 2),
        "pathways_breakdown": breakdown_pct,
        "estimated_commercial_apc_usd": round(est_apc_usd, 2),
        "sovereignty_verdict": "Alta Soberanía Científica (Preponderancia Diamante)" if counts["diamond"] > counts["gold_apc"] else "Dependencia de Mercado Comercial (Preponderancia APC)"
    }

    # Renderizado de Figuras Estáticas (300 DPI) para Publicación Científica (ES y EN)
    dpi = getattr(args, "dpi", 300) or 300
    plot_paths = {}
    if getattr(args, "plot_es", None):
        plot_paths["es"] = args.plot_es
    if getattr(args, "plot_en", None):
        plot_paths["en"] = args.plot_en

    pathway_order = ["diamond", "green", "gold_apc", "hybrid", "bronze", "closed"]
    oa_colors = {
        "diamond": "#10b981",
        "green": "#06b6d4",
        "gold_apc": "#f59e0b",
        "hybrid": "#8b5cf6",
        "bronze": "#b45309",
        "closed": "#64748b"
    }
    labels_es = {
        "diamond": "Diamante (Sin APC)",
        "green": "Verde (Repositorio)",
        "gold_apc": "Dorada APC (Comercial)",
        "hybrid": "Híbrida (Comercial)",
        "bronze": "Bronce (Sin licencia)",
        "closed": "Cerrada (Acceso Restringido)"
    }
    labels_en = {
        "diamond": "Diamond (No APC)",
        "green": "Green (Repository)",
        "gold_apc": "Gold APC (Commercial)",
        "hybrid": "Hybrid (Commercial)",
        "bronze": "Bronze (No license)",
        "closed": "Closed (Paywall)"
    }

    ordered_counts = [counts[p] for p in pathway_order]
    ordered_colors = [oa_colors[p] for p in pathway_order]

    for lang, p_out in plot_paths.items():
        os.makedirs(os.path.dirname(os.path.abspath(p_out)), exist_ok=True)
        fig = plt.figure(figsize=(10.5, 5.5), dpi=dpi)
        gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 1.4], wspace=0.1)
        ax_pie = fig.add_subplot(gs[0, 0])
        ax_legend = fig.add_subplot(gs[0, 1])
        ax_legend.set_xlim(0, 1)
        ax_legend.set_ylim(0, 1)
        ax_legend.axis("off")

        # Gráfica de Donas
        wedges, _ = ax_pie.pie(
            ordered_counts,
            colors=ordered_colors,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2.0)
        )
        ax_pie.text(0, 0.08, f"{oa_percentage:.1f}%", ha="center", va="center", fontsize=22, fontweight="black", color="#0f172a")
        sub_center = f"Acceso Abierto\nTotal: {total:,} docs" if lang == "es" else f"Open Access\nTotal: {total:,} docs"
        ax_pie.text(0, -0.12, sub_center, ha="center", va="center", fontsize=9, color="#64748b", fontweight="bold")

        # Panel de leyenda lateral
        panel_title = "DISTRIBUCIÓN DE LAS 6 VÍAS DE ACCESO ABIERTO" if lang == "es" else "DISTRIBUTION OF THE 6 OPEN ACCESS PATHWAYS"
        ax_legend.text(0.05, 0.98, panel_title, fontsize=10.5, fontweight="black", color="#0f172a", va="top")

        y_pos = 0.86
        for p in pathway_order:
            c = counts[p]
            pct = (c / total * 100.0) if total > 0 else 0.0
            col = oa_colors[p]
            name = labels_es[p] if lang == "es" else labels_en[p]
            ax_legend.plot(0.05, y_pos, marker="s", color=col, markersize=10, markeredgecolor="white")
            ax_legend.text(0.12, y_pos, name, fontsize=9.0, fontweight="bold", color="#1e293b", va="center")
            ax_legend.text(0.88, y_pos, f"{c:,} ({pct:.1f}%)", fontsize=9.0, fontweight="bold", color="#334155", va="center", ha="right")
            y_pos -= 0.12

        apc_box_title = (
            f"Gasto Comercial Estimado en APC: ${est_apc_usd:,.0f} USD"
            if lang == "es"
            else f"Estimated Commercial APC Spending: ${est_apc_usd:,.0f} USD"
        )
        ax_legend.text(
            0.05, 0.14, apc_box_title,
            fontsize=9.2, fontweight="bold", color="#b45309",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#fffbeb", edgecolor="#fde68a")
        )

        plt.savefig(p_out, dpi=dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    # Gráfica interactiva Plotly si se especifica
    plotly_html = getattr(args, "plotly_html", None)
    if plotly_html and HAS_PLOTLY:
        os.makedirs(os.path.dirname(os.path.abspath(plotly_html)), exist_ok=True)
        fig_oa = go.Figure(data=[go.Pie(
            labels=[labels_es[p] for p in pathway_order],
            values=ordered_counts,
            hole=0.45,
            marker=dict(colors=ordered_colors, line=dict(color="#ffffff", width=2)),
            textinfo="percent+label",
            hoverinfo="label+value+percent"
        )])
        fig_oa.update_layout(
            title=f"Distribución de Vías de Acceso Abierto ({oa_percentage:.1f}% OA)",
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        fig_oa.write_html(plotly_html, include_plotlyjs="cdn")
        result["plotly_html"] = plotly_html

    if plot_paths:
        result["plot_paths"] = plot_paths

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"OA Breakdown: {oa_percentage:.1f}% Open Access (Diamond: {counts['diamond']}, Gold: {counts['gold_apc']}). Saved to {args.output}")
    if plot_paths:
        for k, p in plot_paths.items():
            print(f"  - PNG {k.upper()} (300 DPI): {p}")
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
    observed_paid_usd = 0.0
    observed_list_usd = 0.0
    observed_paid_count = 0

    for r in records:
        oa_val = r.get("oa_status") or r.get("Open Access") or ""
        src = r.get("source_title") or r.get("Source title") or ""
        pathway = classify_oa_pathway(oa_val, src)
        if pathway == "gold_apc":
            gold_docs += 1
        elif pathway == "hybrid":
            hybrid_docs += 1
        try:
            paid = float(r.get("apc_paid_usd") or 0.0)
            if paid > 0:
                observed_paid_usd += paid
                observed_paid_count += 1
        except (ValueError, TypeError):
            pass
        try:
            lst = float(r.get("apc_list_usd") or 0.0)
            if lst > 0:
                observed_list_usd += lst
        except (ValueError, TypeError):
            pass

    gold_total_usd = gold_docs * gold_cost
    hybrid_total_usd = hybrid_docs * hybrid_cost
    grand_total_usd = gold_total_usd + hybrid_total_usd

    result = {
        "total_commercial_apc_articles": gold_docs + hybrid_docs,
        "gold_oa_articles": gold_docs,
        "hybrid_oa_articles": hybrid_docs,
        "observed_apc_paid_articles": observed_paid_count,
        "observed_apc_paid_total_usd": round(observed_paid_usd, 2),
        "observed_apc_list_total_usd": round(observed_list_usd, 2),
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
    p_brk.add_argument("--plot-es", help="Optional path to Spanish publication PNG plot (300 DPI)")
    p_brk.add_argument("--plot-en", help="Optional path to English publication PNG plot (300 DPI)")
    p_brk.add_argument("--plotly-html", help="Optional path to interactive Plotly HTML")
    p_brk.add_argument("--dpi", type=int, default=300, help="DPI for publication plots (default: 300)")
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
