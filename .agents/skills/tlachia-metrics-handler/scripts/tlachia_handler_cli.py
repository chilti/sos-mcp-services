#!/usr/bin/env python3
"""
Standalone CLI for tlachia-metrics-handler
Wraps services/knomap/tools/tlachia_tools.py for autonomous execution without MCP server.
Subcommands:
  - inspect     : Inspect TlachIA Metrics .zip or directory package
  - unit-matrix : Extract clean [N x D] matrix for SOM / longitudinal analysis
  - trend       : Extract annual Trend series with ECMA smoothing for PathSOM
  - works-meta  : Locate and validate canonical works metadata file for bibliometric networks
"""

import os
import sys
import json
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.knomap.tools.tlachia_tools import (
    inspect_tlachia_package,
    get_tlachia_unit_matrix,
    get_tlachia_temporal_evolution,
    get_tlachia_works_metadata,
)


def _add_lang_arg(p: argparse.ArgumentParser, is_root: bool = False) -> None:
    p.add_argument(
        "--lang",
        choices=["en", "es"],
        default="en" if is_root else argparse.SUPPRESS,
        help="Language for output labels and summaries (default: en)",
    )


def main():
    parser = argparse.ArgumentParser(description="Standalone CLI for TlachIA Metrics Package Handler")
    _add_lang_arg(parser, is_root=True)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_ins = subparsers.add_parser("inspect", help="Inspect TlachIA Metrics package (.zip or directory)")
    _add_lang_arg(p_ins)
    p_ins.add_argument("--input", required=True, help="Path to TlachIA Metrics .zip or directory")
    p_ins.add_argument("--output", default=None, help="Optional JSON output file")

    p_mat = subparsers.add_parser("unit-matrix", help="Extract multidimensional matrix for SOM")
    _add_lang_arg(p_mat)
    p_mat.add_argument("--session-dir", required=True, help="Session dir or .zip path")
    p_mat.add_argument("--unit", default="Locations", help="Unit name (Locations, Organizations, etc.)")
    p_mat.add_argument("--period-mode", default="Whole", choices=["Whole", "5Years"], help="Whole or 5Years")
    p_mat.add_argument("--indicators", default=None, help="Comma-separated list of indicators")
    p_mat.add_argument("--min-docs", type=float, default=0.0, help="Minimum document threshold")
    p_mat.add_argument("--top-n", type=int, default=100, help="Top N entities")
    p_mat.add_argument("--output", required=True, help="Output file (.json or .parquet)")

    p_tr = subparsers.add_parser("trend", help="Extract annual Trend series with ECMA smoothing")
    _add_lang_arg(p_tr)
    p_tr.add_argument("--session-dir", required=True, help="Session dir or .zip path")
    p_tr.add_argument("--unit", default="Locations", help="Unit name")
    p_tr.add_argument("--entities", default=None, help="Comma-separated entity codes/names")
    p_tr.add_argument("--indicators", default=None, help="Comma-separated indicators")
    p_tr.add_argument("--smoothing", choices=["ecma3", "ecma5", "raw"], default="ecma3")
    p_tr.add_argument("--output", required=True, help="Output JSON file")

    p_wk = subparsers.add_parser("works-meta", help="Locate and validate canonical works metadata file")
    _add_lang_arg(p_wk)
    p_wk.add_argument("--session-dir", required=True, help="Session dir or .zip path")
    p_wk.add_argument("--output", default=None, help="Optional JSON output file")

    args = parser.parse_args()
    lang = getattr(args, "lang", "en") or "en"

    if args.subcommand == "inspect":
        res = inspect_tlachia_package(args.input)
        res["lang"] = lang
        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif args.subcommand == "unit-matrix":
        inds = [x.strip() for x in args.indicators.split(",") if x.strip()] if args.indicators else None
        res = get_tlachia_unit_matrix(
            session_dir_or_zip=args.session_dir,
            unit_name=args.unit,
            period_mode=args.period_mode,
            selected_indicators=inds,
            limit_top_n=args.top_n,
            min_documents=args.min_docs,
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
        print(json.dumps({"status": res.get("status"), "rows": len(res.get("labels", [])), "lang": lang, "output": args.output}, indent=2))

    elif args.subcommand == "trend":
        ents = [x.strip() for x in args.entities.split(",") if x.strip()] if args.entities else None
        inds = [x.strip() for x in args.indicators.split(",") if x.strip()] if args.indicators else None
        res = get_tlachia_temporal_evolution(
            session_dir_or_zip=args.session_dir,
            unit_name=args.unit,
            entities=ents,
            indicators=inds,
            smoothing=args.smoothing,
        )
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(json.dumps({"status": res.get("status"), "lang": lang, "output": args.output}, indent=2))

    elif args.subcommand == "works-meta":
        res = get_tlachia_works_metadata(args.session_dir)
        res["lang"] = lang
        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=2, ensure_ascii=False)
        print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
