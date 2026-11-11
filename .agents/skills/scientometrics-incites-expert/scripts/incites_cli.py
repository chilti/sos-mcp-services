#!/usr/bin/env python3
"""
Standalone CLI for scientometrics-incites-expert
Wraps services/knomap/tools/incites_tools.py for autonomous execution without MCP server.
Subcommands:
  - inspect       : Inspect InCites package (.zip, directory, or CSV)
  - unit-matrix   : Extract clean [N x D] matrix for SOM / longitudinal analysis
  - trend         : Extract annual Trend series with ECMA smoothing for PathSOM
  - growth-matrix : Compute Strategic Growth Matrix (CAGR % vs Volume) + 300 DPI bilingual plots
"""

import os
import sys
import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.knomap.tools.incites_tools import (
    inspect_incites_package,
    get_incites_unit_matrix,
    get_incites_temporal_evolution,
    compute_strategic_growth_matrix,
)


def render_growth_matrix_figures(res: dict, plot_dir: str, dpi: int = 300):
    """Renders 300 DPI bilingual PNGs for Strategic Growth Matrix (CAGR % vs Volume)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(plot_dir, exist_ok=True)
    quads = res.get("quadrant_classification", {})
    if not quads:
        return

    thresholds = res.get("thresholds", {})
    med_vol = float(thresholds.get("volume_median", 0.0))
    med_cagr = float(thresholds.get("cagr_pct_median", 0.0))
    ind_name = res.get("indicator", "Documents")

    quad_styles = [
        ("Star Leaders (High Volume, High CAGR)", "Líderes Estrella", "#10b981"),
        ("Emerging Stars (Moderate Volume, High CAGR)", "Estrellas Emergentes", "#3b82f6"),
        ("Established Giants (High Volume, Low CAGR)", "Gigantes Consolidados", "#f59e0b"),
        ("Low Priority (Low Volume, Low CAGR)", "Baja Prioridad", "#94a3b8"),
    ]

    for lang in ["es", "en"]:
        fig, ax = plt.subplots(figsize=(10, 7), dpi=dpi, facecolor="white")
        ax.set_facecolor("white")

        for key_en, label_es, color in quad_styles:
            pts = quads.get(key_en, [])
            if not pts:
                continue
            xs = [float(e.get("current_volume", 0)) for e in pts]
            ys = [float(e.get("cagr_pct", 0)) for e in pts]
            lbl = label_es if lang == "es" else key_en
            ax.scatter(xs, ys, c=color, s=75, alpha=0.85, edgecolors="#1e293b", linewidths=0.7, label=lbl, zorder=4)
            for e in pts[:12]:
                ax.annotate(
                    str(e.get("entity", ""))[:22],
                    (float(e.get("current_volume", 0)), float(e.get("cagr_pct", 0))),
                    xytext=(4, 4), textcoords="offset points", fontsize=7.5, fontweight="bold", color="#1e293b"
                )

        ax.axvline(med_vol, color="#64748b", linestyle="--", linewidth=1.1, zorder=2)
        ax.axhline(med_cagr, color="#64748b", linestyle="--", linewidth=1.1, zorder=2)
        ax.grid(True, linestyle=":", alpha=0.45, color="#cbd5e1")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        if lang == "es":
            ax.set_xlabel(f"Volumen Actual ({ind_name})", fontsize=11, fontweight="bold", color="#0f172a")
            ax.set_ylabel("Tasa de Crecimiento Anual Compuesto - CAGR (%)", fontsize=11, fontweight="bold", color="#0f172a")
        else:
            ax.set_xlabel(f"Current Volume ({ind_name})", fontsize=11, fontweight="bold", color="#0f172a")
            ax.set_ylabel("Compound Annual Growth Rate - CAGR (%)", fontsize=11, fontweight="bold", color="#0f172a")

        ax.legend(frameon=True, facecolor="white", edgecolor="#e2e8f0", fontsize=9, loc="best")
        out_path = os.path.join(plot_dir, f"incites_growth_matrix_{lang}.png")
        fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Standalone CLI for Clarivate InCites Benchmarking & Analytics")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_ins = subparsers.add_parser("inspect", help="Inspect InCites package or CSV")
    p_ins.add_argument("--input", required=True, help="Path to InCites .zip, directory, or .csv")
    p_ins.add_argument("--output", default=None, help="Optional JSON output file")

    p_mat = subparsers.add_parser("unit-matrix", help="Extract multidimensional matrix for SOM")
    p_mat.add_argument("--session-dir", required=True, help="Session dir or package path")
    p_mat.add_argument("--unit", default="Organizations", help="Unit name (Organizations, Locations, etc.)")
    p_mat.add_argument("--recent-5years", action="store_true", help="Use recent 5-year window instead of Whole")
    p_mat.add_argument("--indicators", default=None, help="Comma-separated list of indicators")
    p_mat.add_argument("--min-threshold", type=float, default=0.0, help="Minimum document threshold")
    p_mat.add_argument("--top-n", type=int, default=100, help="Top N entities")
    p_mat.add_argument("--output", required=True, help="Output file (.json or .parquet)")

    p_tr = subparsers.add_parser("trend", help="Extract annual Trend series with ECMA smoothing")
    p_tr.add_argument("--session-dir", required=True, help="Session dir or package path")
    p_tr.add_argument("--unit", default="Organizations", help="Unit name")
    p_tr.add_argument("--entities", required=True, help="Comma-separated entity names")
    p_tr.add_argument("--indicators", default=None, help="Comma-separated indicators")
    p_tr.add_argument("--smoothing", choices=["ecma3", "ecma5", "raw"], default="ecma3")
    p_tr.add_argument("--output", required=True, help="Output JSON file")

    p_gr = subparsers.add_parser("growth-matrix", help="Compute Strategic Growth Matrix (CAGR %% vs Volume)")
    p_gr.add_argument("--session-dir", required=True, help="Session dir or package path")
    p_gr.add_argument("--unit", default="Organizations", help="Unit name")
    p_gr.add_argument("--indicator", default="Web of Science Documents", help="Target indicator for CAGR")
    p_gr.add_argument("--top-n", type=int, default=50, help="Top N entities")
    p_gr.add_argument("--output", required=True, help="Output JSON file")
    p_gr.add_argument("--plot-dir", default=None, help="Directory to export 300 DPI bilingual figures")
    p_gr.add_argument("--dpi", type=int, default=300)

    args = parser.parse_args()

    if args.subcommand == "inspect":
        res = inspect_incites_package(args.input)
        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif args.subcommand == "unit-matrix":
        inds = [x.strip() for x in args.indicators.split(",") if x.strip()] if args.indicators else None
        res = get_incites_unit_matrix(
            session_dir_or_zip=args.session_dir,
            unit_name=args.unit,
            period_mode="5Years" if args.recent_5years else "Whole",
            selected_indicators=inds,
            filter_min_threshold=args.min_threshold,
            limit_top_n=args.top_n,
        )
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        if args.output.endswith(".parquet") and res.get("status") == "success":
            import pandas as pd
            df = pd.DataFrame(res["data"], columns=res["indicators"])
            df.insert(0, "entity", res["labels"])
            df.to_parquet(args.output, index=False)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
        print(json.dumps({"status": res.get("status"), "rows": len(res.get("labels", [])), "output": args.output}, indent=2))

    elif args.subcommand == "trend":
        ents = [x.strip() for x in args.entities.split(",") if x.strip()]
        inds = [x.strip() for x in args.indicators.split(",") if x.strip()] if args.indicators else None
        res = get_incites_temporal_evolution(
            session_dir_or_zip=args.session_dir,
            unit_name=args.unit,
            entities=ents,
            indicators=inds,
            smoothing=args.smoothing,
        )
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(json.dumps({"status": res.get("status"), "output": args.output}, indent=2))

    elif args.subcommand == "growth-matrix":
        res = compute_strategic_growth_matrix(
            session_dir_or_zip=args.session_dir,
            unit_name=args.unit,
            indicator=args.indicator,
        )
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        if args.plot_dir:
            render_growth_matrix_figures(res, args.plot_dir, dpi=args.dpi)
        print(json.dumps({"status": res.get("status"), "output": args.output}, indent=2))


if __name__ == "__main__":
    main()
