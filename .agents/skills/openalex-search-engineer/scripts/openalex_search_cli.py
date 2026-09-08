#!/usr/bin/env python3
"""
CLI Helper: OpenAlex Search Engineer
Formulates and executes optimized ClickHouse queries and API calls for OpenAlex data:
- Tokenized and diacritic-insensitive author search with Hispanic name permutations
- Publications search with safe filters (NO JOINs)
- Entity retrieval and aggregation group-by
- File-based JSON output redirection to avoid LLM context window bloat
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
    from shared.config import settings
    from shared.clickhouse import execute_safe_query
    from services.openalex.tools.search_tools import openalex_search_authors, openalex_search_works
    from services.openalex.tools.entity_tools import openalex_get_entity_by_id, openalex_aggregate_group_by
except ImportError:
    pass


def generate_hispanic_name_permutations(name: str) -> List[str]:
    """Generates common Hispanic name variations (hyphenation, maternal/paternal order)."""
    clean_name = name.replace(",", "").strip()
    tokens = clean_name.split()
    permutations = [name, clean_name]

    if len(tokens) == 3:
        # e.g. "Rafael Torres Córdoba" -> "Rafael Torres-Córdoba", "Torres Córdoba, Rafael", "Torres, Rafael"
        first, p1, p2 = tokens[0], tokens[1], tokens[2]
        permutations.append(f"{first} {p1}-{p2}")
        permutations.append(f"{p1} {p2}, {first}")
        permutations.append(f"{p1}-{p2}, {first}")
        permutations.append(f"{p1}, {first}")
    elif len(tokens) == 4:
        # e.g. "José Luis Jiménez Andrade" -> "José Luis Jiménez-Andrade", "Jiménez Andrade, José Luis"
        n1, n2, p1, p2 = tokens[0], tokens[1], tokens[2], tokens[3]
        permutations.append(f"{n1} {n2} {p1}-{p2}")
        permutations.append(f"{p1} {p2}, {n1} {n2}")
        permutations.append(f"{p1}-{p2}, {n1} {n2}")
        permutations.append(f"{p1}, {n1}")

    # Remove duplicates preserving order
    seen = set()
    unique = []
    for p in permutations:
        low = p.lower()
        if low not in seen:
            seen.add(low)
            unique.append(p)
    return unique


def cmd_search_authors(args):
    """Searches authors using permutations and ClickHouse tokenization."""
    name = args.name
    limit = min(args.limit or 50, 1000)
    permutations = generate_hispanic_name_permutations(name) if name else []

    results = []
    seen_ids = set()

    # Search with primary query first
    res = openalex_search_authors(
        search_query=name,
        orcid=args.orcid,
        institution_ror=args.institution_ror,
        limit=limit
    )
    items = res.get("data", res.get("results", []))
    for it in items:
        it_id = it.get("id")
        if it_id and it_id not in seen_ids:
            seen_ids.add(it_id)
            results.append(it)

    # If few results and name has permutations, query variants
    if len(results) < 5 and len(permutations) > 1:
        for perm in permutations[1:3]:
            sub_res = openalex_search_authors(
                search_query=perm,
                orcid=args.orcid,
                institution_ror=args.institution_ror,
                limit=limit
            )
            sub_items = sub_res.get("data", sub_res.get("results", []))
            for it in sub_items:
                it_id = it.get("id")
                if it_id and it_id not in seen_ids:
                    seen_ids.add(it_id)
                    results.append(it)

    output_data = {
        "query": name,
        "permutations_tested": permutations,
        "total_results": len(results),
        "authors": results[:limit]
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Author search completed for '{name}': {len(results)} found. Output: {args.output}")
    sys.exit(0)


def cmd_search_works(args):
    """Searches works with filters respecting NO-JOIN ClickHouse rule."""
    limit = min(args.limit or 100, 50000)
    res = openalex_search_works(
        search_query=args.query or "",
        author_id=args.author_id,
        institution_ror=args.institution_ror,
        topic_id=args.topic_id,
        from_publication_date=f"{args.year_min}-01-01" if args.year_min else None,
        to_publication_date=f"{args.year_max}-12-31" if args.year_max else None,
        is_oa=args.is_oa,
        limit=limit
    )

    items = res.get("data", res.get("results", []))
    output_data = {
        "query": args.query,
        "limit": limit,
        "total_returned": len(items),
        "works": items
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Works search completed: {len(items)} works retrieved. Saved to {args.output}")
    sys.exit(0)


def cmd_get_entity(args):
    """Retrieves full normalized object by ID."""
    res = openalex_get_entity_by_id(args.entity_type, args.id)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print(f"Entity {args.entity_type}/{args.id} retrieved. Output: {args.output}")
    sys.exit(0)


def cmd_aggregate(args):
    """Runs aggregate group-by query in ClickHouse."""
    res = openalex_aggregate_group_by(
        entity_type=args.entity_type,
        filter_param=args.filter,
        group_by_field=args.group_by
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print(f"Aggregation by {args.group_by} on {args.entity_type} saved to {args.output}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="CLI for OpenAlex Search Engineer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: search-authors
    p_auth = subparsers.add_parser("search-authors", help="Search authors with Hispanic name permutations")
    p_auth.add_argument("--name", required=True, help="Author name to search")
    p_auth.add_argument("--orcid", help="Optional ORCID filter")
    p_auth.add_argument("--institution-ror", help="Optional ROR filter")
    p_auth.add_argument("--limit", type=int, default=50, help="Max results (default: 50, max: 1000)")
    p_auth.add_argument("--output", required=True, help="Path to output JSON")
    p_auth.set_defaults(func=cmd_search_authors)

    # Subcommand: search-works
    p_wrk = subparsers.add_parser("search-works", help="Search works (NO JOINs safe)")
    p_wrk.add_argument("--query", default="", help="Text search query")
    p_wrk.add_argument("--author-id", help="OpenAlex Author ID")
    p_wrk.add_argument("--institution-ror", help="Institution ROR ID")
    p_wrk.add_argument("--topic-id", help="Primary Topic ID")
    p_wrk.add_argument("--year-min", type=int, help="Start year")
    p_wrk.add_argument("--year-max", type=int, help="End year")
    p_wrk.add_argument("--is-oa", type=bool, default=None, help="Open Access flag")
    p_wrk.add_argument("--limit", type=int, default=100, help="Max works (default: 100, max: 50000)")
    p_wrk.add_argument("--output", required=True, help="Path to output JSON")
    p_wrk.set_defaults(func=cmd_search_works)

    # Subcommand: get-entity
    p_ent = subparsers.add_parser("get-entity", help="Get entity by ID")
    p_ent.add_argument("--entity-type", choices=["works", "authors", "institutions", "sources", "topics", "funders"], required=True)
    p_ent.add_argument("--id", required=True, help="OpenAlex ID, ROR, or ORCID")
    p_ent.add_argument("--output", required=True, help="Path to output JSON")
    p_ent.set_defaults(func=cmd_get_entity)

    # Subcommand: aggregate
    p_agg = subparsers.add_parser("aggregate", help="Aggregate count and citations group-by")
    p_agg.add_argument("--entity-type", choices=["works", "authors"], default="works")
    p_agg.add_argument("--group-by", choices=["publication_year", "oa_status", "type", "primary_topic_id", "country_code"], default="publication_year")
    p_agg.add_argument("--filter", help="SQL WHERE clause filter")
    p_agg.add_argument("--output", required=True, help="Path to output JSON")
    p_agg.set_defaults(func=cmd_aggregate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
