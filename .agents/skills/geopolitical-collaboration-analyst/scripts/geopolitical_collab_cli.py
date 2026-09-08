#!/usr/bin/env python3
"""
CLI Helper: Geopolitical Collaboration Analyst
Analyzes international co-authorship networks, bilateral Salton similarity,
regional analytical groupings (Iberoamerica, GlobalSouth, OECD, BRICS) in ISO-3166 alpha-3,
and scientific leadership (corresponding/first author ratios).
"""

import sys
import os
import json
import csv
import math
import argparse
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Set

# Country mapping dictionary to ISO-3166-1 alpha-3
COUNTRY_TO_ISO3 = {
    "mexico": "MEX", "méxico": "MEX", "mex": "MEX",
    "united states": "USA", "usa": "USA", "united states of america": "USA",
    "spain": "ESP", "españa": "ESP", "esp": "ESP",
    "france": "FRA", "francia": "FRA", "fra": "FRA",
    "brazil": "BRA", "brasil": "BRA", "bra": "BRA",
    "united kingdom": "GBR", "uk": "GBR", "gbr": "GBR", "england": "GBR",
    "germany": "DEU", "alemania": "DEU", "deu": "DEU",
    "canada": "CAN", "canadá": "CAN", "can": "CAN",
    "chile": "CHL", "chl": "CHL",
    "colombia": "COL", "col": "COL",
    "argentina": "ARG", "arg": "ARG",
    "china": "CHN", "chn": "CHN",
    "japan": "JPN", "japón": "JPN", "jpn": "JPN",
    "italy": "ITA", "italia": "ITA", "ita": "ITA",
    "portugal": "PRT", "prt": "PRT",
    "india": "IND", "ind": "IND",
    "south africa": "ZAF", "zaf": "ZAF"
}

REGIONAL_GROUPINGS = {
    "iberoamerica": {"MEX", "ESP", "BRA", "ARG", "CHL", "COL", "PRT", "PER", "URY", "CUB", "CRI", "PAN"},
    "globalsouth": {"MEX", "BRA", "ARG", "CHL", "COL", "IND", "ZAF", "EGY", "NGA", "IDN", "VNM"},
    "oecd": {"USA", "CAN", "GBR", "FRA", "DEU", "JPN", "ITA", "ESP", "MEX", "CHL", "KOR", "AUS"},
    "brics": {"BRA", "RUS", "IND", "CHN", "ZAF", "EGY", "ETH", "IRN", "ARE"}
}


def normalize_country(raw_text: str) -> Optional[str]:
    """Normalizes country name string to ISO-3166-1 alpha-3."""
    clean = raw_text.strip().lower().replace(".", "").replace(",", "")
    if clean in COUNTRY_TO_ISO3:
        return COUNTRY_TO_ISO3[clean]
    for key, code in COUNTRY_TO_ISO3.items():
        if key in clean:
            return code
    return clean[:3].upper() if len(clean) >= 3 else None


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


def cmd_country_matrix(args):
    """Calculates country co-authorship matrix and Salton cosine index."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus(input_path)
    anchor = (args.anchor_country or "MEX").upper()

    country_counts = Counter()
    collab_pairs = Counter()

    for r in records:
        affils = r.get("affiliations") or r.get("Affiliations") or r.get("C1") or ""
        doc_countries = set()
        for aff in str(affils).split(";"):
            parts = aff.split(",")
            if parts:
                c_code = normalize_country(parts[-1])
                if c_code:
                    doc_countries.add(c_code)

        for c in doc_countries:
            country_counts[c] += 1

        c_list = sorted(list(doc_countries))
        for i in range(len(c_list)):
            for j in range(i + 1, len(c_list)):
                collab_pairs[(c_list[i], c_list[j])] += 1

    anchor_total = country_counts.get(anchor, 1)
    anchor_collabs = []

    for (c1, c2), count in collab_pairs.items():
        partner = None
        if c1 == anchor:
            partner = c2
        elif c2 == anchor:
            partner = c1

        if partner:
            partner_total = country_counts.get(partner, 1)
            salton = count / math.sqrt(anchor_total * partner_total) if (anchor_total * partner_total) > 0 else 0.0
            anchor_collabs.append({
                "partner_country": partner,
                "coauthored_papers": count,
                "partner_total_papers": partner_total,
                "salton_cosine_similarity": round(salton, 4)
            })

    anchor_collabs.sort(key=lambda x: x["coauthored_papers"], reverse=True)

    result = {
        "anchor_country_iso3": anchor,
        "anchor_total_papers": anchor_total,
        "total_partner_countries": len(anchor_collabs),
        "total_collaborations": sum(x["coauthored_papers"] for x in anchor_collabs),
        "top_partners": anchor_collabs[:args.top_n or 25]
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Country matrix generated for {anchor}: {len(anchor_collabs)} partners mapped. Saved to {args.output}")
    sys.exit(0)


def cmd_regional(args):
    """Benchmarks collaboration share across geopolitical regions."""
    region_key = args.region.lower()
    if region_key not in REGIONAL_GROUPINGS:
        sys.stderr.write(f"Error: Unknown region '{args.region}'. Choose from: {list(REGIONAL_GROUPINGS.keys())}\n")
        sys.exit(1)

    region_countries = REGIONAL_GROUPINGS[region_key]
    anchor = (args.anchor_country or "MEX").upper()
    matrix_file = args.matrix_file

    if not os.path.exists(matrix_file):
        sys.stderr.write(f"Error: Matrix file does not exist: {matrix_file}\n")
        sys.exit(1)

    with open(matrix_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    partners = data.get("top_partners", [])
    regional_partners = [p for p in partners if p["partner_country"] in region_countries and p["partner_country"] != anchor]

    total_regional_collabs = sum(p["coauthored_papers"] for p in regional_partners)
    all_collabs = data.get("total_collaborations", 1)
    share_pct = (total_regional_collabs / all_collabs * 100.0) if all_collabs > 0 else 0.0

    result = {
        "anchor_country": anchor,
        "region_name": args.region,
        "region_member_countries_iso3": sorted(list(region_countries)),
        "regional_collaborations_count": total_regional_collabs,
        "percentage_of_total_collaborations": round(share_pct, 2),
        "regional_partners_breakdown": regional_partners
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Regional benchmark ({args.region}): {total_regional_collabs} collabs ({share_pct:.1f}% share). Saved to {args.output}")
    sys.exit(0)


def cmd_leadership(args):
    """Evaluates scientific leadership by first author and corresponding author status."""
    input_path = args.input
    if not os.path.exists(input_path):
        sys.stderr.write(f"Error: Input file does not exist: {input_path}\n")
        sys.exit(1)

    records = load_corpus(input_path)
    target_country = (args.country or "MEX").upper()

    total_intl_papers = 0
    first_author_count = 0

    for r in records:
        affils = r.get("affiliations") or r.get("Affiliations") or r.get("C1") or ""
        aff_list = [a.strip() for a in str(affils).split(";") if a.strip()]
        if not aff_list:
            continue

        doc_countries = set()
        for aff in aff_list:
            parts = aff.split(",")
            if parts:
                c = normalize_country(parts[-1])
                if c:
                    doc_countries.add(c)

        # Is international paper?
        if len(doc_countries) > 1 and target_country in doc_countries:
            total_intl_papers += 1
            # Check first affiliation
            first_aff = aff_list[0].split(",")
            if first_aff:
                first_c = normalize_country(first_aff[-1])
                if first_c == target_country:
                    first_author_count += 1

    leadership_rate = (first_author_count / total_intl_papers * 100.0) if total_intl_papers > 0 else 0.0

    result = {
        "country_iso3": target_country,
        "total_international_collaborations": total_intl_papers,
        "first_author_led_papers": first_author_count,
        "scientific_leadership_rate_pct": round(leadership_rate, 2),
        "asymmetry_status": "Liderazgo Preponderante (Soberanía Científica)" if leadership_rate >= 50 else "Colaboración Participativa (Asimetría Norte-Sur)"
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Leadership for {target_country}: {leadership_rate:.1f}% ({result['asymmetry_status']}). Output: {args.output}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="CLI for Geopolitical Collaboration Analyst")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: country-matrix
    p_mat = subparsers.add_parser("country-matrix", help="Generate country co-authorship matrix (ISO-3)")
    p_mat.add_argument("--input", required=True, help="Path to corpus file")
    p_mat.add_argument("--anchor-country", default="MEX", help="Anchor country ISO-3 (default: MEX)")
    p_mat.add_argument("--top-n", type=int, default=25, help="Number of top partners to output")
    p_mat.add_argument("--output", required=True, help="Path to output JSON")
    p_mat.set_defaults(func=cmd_country_matrix)

    # Subcommand: regional-benchmark
    p_reg = subparsers.add_parser("regional-benchmark", help="Benchmark across geopolitical regions")
    p_reg.add_argument("--matrix-file", required=True, help="Path to country matrix JSON from country-matrix")
    p_reg.add_argument("--region", choices=["Iberoamerica", "GlobalSouth", "OECD", "BRICS"], required=True)
    p_reg.add_argument("--anchor-country", default="MEX", help="Anchor country ISO-3")
    p_reg.add_argument("--output", required=True, help="Path to output JSON")
    p_reg.set_defaults(func=cmd_regional)

    # Subcommand: scientific-leadership
    p_lea = subparsers.add_parser("scientific-leadership", help="Calculate first author leadership in international papers")
    p_lea.add_argument("--input", required=True, help="Path to corpus file")
    p_lea.add_argument("--country", default="MEX", help="Target country ISO-3 (default: MEX)")
    p_lea.add_argument("--output", required=True, help="Path to output JSON")
    p_lea.set_defaults(func=cmd_leadership)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
