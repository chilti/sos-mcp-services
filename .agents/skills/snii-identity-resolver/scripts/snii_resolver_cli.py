#!/usr/bin/env python3
"""
CLI Helper: SNII Identity Resolver
Resolves official researcher identity against the National System of Researchers (SNII 2025 Padrón),
retrieving canonical level, knowledge area, institutional accreditation, ORCID, and OpenAlex ID.
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional

# Add sos-mcp-services to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if SOS_DIR not in sys.path:
    sys.path.insert(0, SOS_DIR)

try:
    from services.sinapsisai.tools.snii_tools import resolve_snii_identity, get_researcher_profile
except ImportError:
    pass


def cmd_resolve(args):
    """Resolves single researcher identity against official SNII registry."""
    res = resolve_snii_identity(
        fullname=args.name,
        institution=args.institution or "UNAM",
        dependency=args.dependency or ""
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    match = res.get("canonical_match", {})
    print(f"Resolved SNII Identity for '{args.name}': Level={match.get('snii_level', 'N/A')}, Confidence={res.get('disambiguation_confidence')}. Output: {args.output}")
    sys.exit(0)


def cmd_profile(args):
    """Retrieves full SNII and bibliometric profile."""
    res = get_researcher_profile(args.name)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print(f"Profile for '{args.name}' retrieved. Saved to {args.output}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="CLI for SNII Identity Resolver")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: resolve
    p_res = subparsers.add_parser("resolve", help="Resolve researcher against official SNII registry")
    p_res.add_argument("--name", required=True, help="Full author name")
    p_res.add_argument("--institution", default="UNAM", help="Institution affiliation")
    p_res.add_argument("--dependency", default="", help="Academic department / faculty")
    p_res.add_argument("--output", required=True, help="Path to output JSON")
    p_res.set_defaults(func=cmd_resolve)

    # Subcommand: profile
    p_pro = subparsers.add_parser("profile", help="Get full researcher SNII profile")
    p_pro.add_argument("--name", required=True, help="Author name fragment")
    p_pro.add_argument("--output", required=True, help="Path to output JSON")
    p_pro.set_defaults(func=cmd_profile)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
