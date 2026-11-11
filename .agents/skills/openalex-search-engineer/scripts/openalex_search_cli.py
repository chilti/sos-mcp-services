#!/usr/bin/env python3
"""
CLI Helper: OpenAlex Search Engineer
Formulates and executes optimized ClickHouse queries and API calls for OpenAlex data:
- Tokenized and diacritic-insensitive author search with Hispanic name permutations
- Publications search on rag.works_flat (global, 464.8M works) or rag.works_academic_all (Mexico, 1.65M works)
- Direct execution of transpiled SQL files (--sql-file clickhouse_query.sql) with ZERO JOINs
- Direct export to .parquet, .csv, or .json in canonical schema for seamless chaining with downstream skills
"""

import sys
import os
import re
import json
import argparse
from typing import Dict, List, Any, Optional

import pandas as pd

# Add sos-mcp-services to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_SOS_DIRS = [
    os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..")),
    "/mnt/expansion/desplegados/sos-mcp-services",
]
for d in CANDIDATE_SOS_DIRS:
    if os.path.isdir(os.path.join(d, "shared")) and d not in sys.path:
        sys.path.insert(0, d)

try:
    import clickhouse_connect
except ImportError:
    clickhouse_connect = None

try:
    from shared.config import settings
    from shared.clickhouse import execute_safe_query
    from services.openalex.tools.search_tools import openalex_search_authors, openalex_search_works
    from services.openalex.tools.entity_tools import openalex_get_entity_by_id, openalex_aggregate_group_by
except ImportError:
    pass


def get_clickhouse_client():
    """Obtiene un cliente ClickHouse conectado al host local/remoto configurado."""
    if clickhouse_connect is None:
        return None
    host = os.getenv("CLICKHOUSE_HOST", os.getenv("CH_HOST", "10.90.0.87"))
    port = int(os.getenv("CLICKHOUSE_PORT", os.getenv("CH_PORT", "8124")))
    user = os.getenv("CLICKHOUSE_USER", os.getenv("CH_USER", "rag_user"))
    pwd_raw = os.getenv("CLICKHOUSE_PASSWORD", os.getenv("CH_PASSWORD", "$B3tt3r-R4g-3veR-d0N3++"))
    password = pwd_raw.replace("$$", "$")
    database = os.getenv("CLICKHOUSE_DATABASE", os.getenv("CH_DATABASE", "rag"))
    try:
        return clickhouse_connect.get_client(
            host=host,
            port=port,
            username=user,
            password=password,
            database=database,
            connect_timeout=5,
            send_receive_timeout=120,
        )
    except Exception as e:
        print(f"Warning: ClickHouse connection failed ({host}:{port}): {e}", file=sys.stderr)
        return None


def sanitize_no_joins(sql: str) -> bool:
    """Verifica que la consulta no contenga sentencias JOIN prohibidas."""
    if re.search(r"\bjoin\b", sql, re.IGNORECASE):
        raise ValueError("Violación de política de datos: Las sentencias JOIN están estrictamente prohibidas en ClickHouse.")
    return True


def generate_hispanic_name_permutations(name: str) -> List[str]:
    """Generates common Hispanic name variations (hyphenation, maternal/paternal order)."""
    clean_name = name.replace(",", "").strip()
    tokens = clean_name.split()
    permutations = [name, clean_name]

    if len(tokens) == 3:
        first, p1, p2 = tokens[0], tokens[1], tokens[2]
        permutations.append(f"{first} {p1}-{p2}")
        permutations.append(f"{p1} {p2}, {first}")
        permutations.append(f"{p1}-{p2}, {first}")
        permutations.append(f"{p1}, {first}")
    elif len(tokens) == 4:
        n1, n2, p1, p2 = tokens[0], tokens[1], tokens[2], tokens[3]
        permutations.append(f"{n1} {n2} {p1}-{p2}")
        permutations.append(f"{p1} {p2}, {n1} {n2}")
        permutations.append(f"{p1}-{p2}, {n1} {n2}")
        permutations.append(f"{p1}, {n1}")

    seen = set()
    unique = []
    for p in permutations:
        low = p.lower()
        if low not in seen:
            seen.add(low)
            unique.append(p)
    return unique


def _normalize_work_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Asegura que un registro de obra (de ClickHouse o de la API pública de OpenAlex) tenga todas las columnas canónicas."""
    rec = dict(raw)
    if not rec.get("title") and rec.get("display_name"):
        rec["title"] = rec["display_name"]

    year_val = rec.get("year") if rec.get("year") is not None else rec.get("publication_year")
    rec["year"] = int(year_val) if year_val is not None else None
    rec["publication_year"] = rec["year"]

    cites_val = rec.get("citations") if rec.get("citations") is not None else rec.get("cited_by_count", 0)
    rec["citations"] = int(cites_val or 0)
    rec["cited_by_count"] = rec["citations"]

    doc_type = rec.get("doc_type") or rec.get("type") or "article"
    rec["doc_type"] = str(doc_type)
    rec["type"] = str(doc_type)

    # Extraer authorships si viene de la API pública de OpenAlex
    authorships = rec.get("authorships")
    if isinstance(authorships, list) and authorships and not rec.get("author_names"):
        a_names, i_names, i_rors, c_codes = [], [], [], []
        for auth in authorships:
            if not isinstance(auth, dict):
                continue
            aname = (auth.get("author") or {}).get("display_name") or auth.get("raw_author_name")
            if aname:
                a_names.append(str(aname))
            for c in auth.get("countries") or []:
                if c and c not in c_codes:
                    c_codes.append(str(c))
            for inst in auth.get("institutions") or []:
                if not isinstance(inst, dict):
                    continue
                iname = inst.get("display_name")
                iror = inst.get("ror")
                icc = inst.get("country_code")
                if iname and iname not in i_names:
                    i_names.append(str(iname))
                if iror and iror not in i_rors:
                    i_rors.append(str(iror))
                if icc and icc not in c_codes:
                    c_codes.append(str(icc))
        rec["author_names"] = a_names
        rec["institution_names"] = i_names
        rec["institution_rors"] = i_rors
        rec["all_country_codes"] = c_codes

    # Extraer open_access si viene anidado de la API pública
    oa_obj = rec.get("open_access")
    if isinstance(oa_obj, dict):
        if "is_oa" not in rec or rec["is_oa"] is None:
            rec["is_oa"] = oa_obj.get("is_oa", False)
        if not rec.get("oa_status"):
            rec["oa_status"] = oa_obj.get("oa_status", "closed")

    # Extraer primary_topic si viene anidado
    pt_obj = rec.get("primary_topic")
    if isinstance(pt_obj, dict):
        rec.setdefault("topic", pt_obj.get("display_name", ""))
        rec.setdefault("subfield", (pt_obj.get("subfield") or {}).get("display_name", ""))
        rec.setdefault("field", (pt_obj.get("field") or {}).get("display_name", ""))
        rec.setdefault("domain", (pt_obj.get("domain") or {}).get("display_name", ""))

    # Extraer APCs y SDGs si vienen anidados
    if isinstance(rec.get("apc_paid"), dict) and not rec.get("apc_paid_usd"):
        rec["apc_paid_usd"] = rec["apc_paid"].get("value_usd") or 0.0
    if isinstance(rec.get("apc_list"), dict) and not rec.get("apc_list_usd"):
        rec["apc_list_usd"] = rec["apc_list"].get("value_usd") or 0.0
    if isinstance(rec.get("sustainable_development_goals"), list) and not rec.get("sdgs"):
        rec["sdgs"] = [s.get("display_name") or s.get("id") for s in rec["sustainable_development_goals"] if isinstance(s, dict)]
    if isinstance(rec.get("keywords"), list) and rec["keywords"] and isinstance(rec["keywords"][0], dict):
        rec["keywords"] = [k.get("display_name", "") for k in rec["keywords"] if isinstance(k, dict) and k.get("display_name")]

    author_names = rec.get("author_names") or rec.get("raw_author_names") or []
    if isinstance(author_names, str):
        author_names = [a.strip() for a in author_names.split(";") if a.strip()]
    rec["author_names"] = list(author_names)
    if not rec.get("authors"):
        rec["authors"] = "; ".join(str(a) for a in author_names if a)

    inst_names = rec.get("institution_names") or []
    if isinstance(inst_names, str):
        inst_names = [i.strip() for i in inst_names.split(";") if i.strip()]
    rec["institution_names"] = list(inst_names)
    if not rec.get("affiliations"):
        rec["affiliations"] = "; ".join(str(i) for i in inst_names if i)

    all_cc = rec.get("all_country_codes") or []
    if isinstance(all_cc, str):
        all_cc = [c.strip() for c in all_cc.split(";") if c.strip()]
    if not all_cc and rec.get("country_codes"):
        if isinstance(rec["country_codes"], list):
            all_cc = rec["country_codes"]
        elif isinstance(rec["country_codes"], str):
            all_cc = [c.strip() for c in rec["country_codes"].split(";") if c.strip()]
    if not all_cc and rec.get("country_code"):
        all_cc = [str(rec["country_code"])]
    rec["all_country_codes"] = list(all_cc)
    rec["country_codes"] = "; ".join(str(c) for c in all_cc if c)

    kws = rec.get("keywords") or []
    if isinstance(kws, str):
        kws = [k.strip() for k in kws.split(";") if k.strip()]
    rec["keywords"] = list(kws)
    if not rec.get("keywords_author"):
        rec["keywords_author"] = "; ".join(str(k) for k in kws if k)
    if "keywords_plus" not in rec:
        rec["keywords_plus"] = rec.get("topic") or ""

    if not rec.get("source_title"):
        rec["source_title"] = str(rec.get("source_id") or "")

    refs = rec.get("referenced_works")
    if refs is None:
        refs = []
    elif isinstance(refs, str):
        refs = [r.strip() for r in refs.replace("|", ";").split(";") if r.strip()]
    rec["referenced_works"] = list(refs)

    rec["is_oa"] = bool(rec.get("is_oa") in (1, "1", True, "true", "True"))
    rec["is_top_10"] = bool(rec.get("is_top_10") in (1, "1", True, "true", "True"))
    rec["is_top_1"] = bool(rec.get("is_top_1") in (1, "1", True, "true", "True"))
    rec["apc_paid_usd"] = float(rec.get("apc_paid_usd") or 0.0)
    rec["apc_list_usd"] = float(rec.get("apc_list_usd") or 0.0)
    rec["source_db"] = rec.get("source_db") or "OpenAlex-ClickHouse"
    return rec


def _save_works_output(records: List[Dict[str, Any]], output_path: str, meta: Dict[str, Any]) -> None:
    """Guarda registros de obras en .parquet, .csv o .json de forma compatible con todo el ecosistema."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    ext = os.path.splitext(output_path)[1].lower()
    if ext == ".parquet":
        df = pd.DataFrame(records)
        df.to_parquet(output_path, index=False)
    elif ext == ".csv":
        df = pd.DataFrame(records)
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, list)).any():
                df[col] = df[col].apply(lambda x: "; ".join(map(str, x)) if isinstance(x, list) else x)
        df.to_csv(output_path, index=False)
    else:
        payload = dict(meta)
        payload["total_returned"] = len(records)
        payload["works"] = records
        payload["records"] = records
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)


def cmd_search_authors(args):
    """Searches authors using permutations and ClickHouse tokenization."""
    name = args.name
    limit = min(args.limit or 50, 1000)
    permutations = generate_hispanic_name_permutations(name) if name else []

    results = []
    seen_ids = set()

    client = get_clickhouse_client()
    if client is not None:
        for perm in permutations[:3]:
            clean_p = perm.replace("'", "\\'")
            sql = f"""
            SELECT id, display_name, orcid, works_count, cited_by_count, h_index, last_known_institution_name, last_known_institution_ror
            FROM rag.authors_seed_mexico
            WHERE positionCaseInsensitiveUTF8(display_name, '{clean_p}') > 0
            ORDER BY cited_by_count DESC
            LIMIT {limit}
            """
            try:
                res = client.query(sql)
                for r in res.result_rows:
                    if r[0] not in seen_ids:
                        seen_ids.add(r[0])
                        results.append({
                            "id": r[0],
                            "display_name": r[1],
                            "orcid": r[2],
                            "works_count": r[3],
                            "cited_by_count": r[4],
                            "h_index": r[5],
                            "last_known_institution": r[6],
                            "ror": r[7],
                        })
            except Exception:
                pass

    if not results and "openalex_search_authors" in globals():
        res = openalex_search_authors(
            search_query=name,
            orcid=args.orcid,
            institution_ror=args.institution_ror,
            limit=limit,
        )
        items = res.get("data", res.get("results", []))
        for it in items:
            it_id = it.get("id")
            if it_id and it_id not in seen_ids:
                seen_ids.add(it_id)
                h_idx = it.get("h_index")
                if h_idx is None and isinstance(it.get("summary_stats"), dict):
                    h_idx = it["summary_stats"].get("h_index")
                inst_name = it.get("last_known_institution")
                ror_id = it.get("ror")
                if not inst_name and it.get("last_known_institutions"):
                    inst_first = it["last_known_institutions"][0]
                    inst_name = inst_first.get("display_name")
                    ror_id = inst_first.get("ror")
                results.append({
                    "id": it_id,
                    "display_name": it.get("display_name"),
                    "orcid": it.get("orcid"),
                    "works_count": it.get("works_count"),
                    "cited_by_count": it.get("cited_by_count"),
                    "h_index": h_idx,
                    "last_known_institution": inst_name,
                    "ror": ror_id,
                })

    output_data = {
        "query": name,
        "permutations_tested": permutations,
        "total_results": len(results),
        "authors": results[:limit],
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Author search completed for '{name}': {len(results)} found. Output: {args.output}")
    sys.exit(0)


def cmd_search_works(args):
    """Searches works in ClickHouse (rag.works_flat or rag.works_academic_all) or via --sql-file with NO JOINs."""
    limit = min(args.limit or 500, 50000)
    client = get_clickhouse_client()
    records: List[Dict[str, Any]] = []

    if args.sql_file:
        if not os.path.exists(args.sql_file):
            print(f"Error: SQL file not found: {args.sql_file}", file=sys.stderr)
            sys.exit(1)
        with open(args.sql_file, "r", encoding="utf-8") as f:
            sql = f.read().strip().rstrip(";")
        sanitize_no_joins(sql)
        if args.limit and "LIMIT" in sql.upper():
            sql = re.sub(r"LIMIT\s+\d+", f"LIMIT {limit}", sql, flags=re.IGNORECASE)
        if client is None:
            print("Error: ClickHouse client unavailable to execute --sql-file.", file=sys.stderr)
            sys.exit(1)
        res = client.query(sql)
        col_names = list(res.column_names)
        for row in res.result_rows:
            row_dict = dict(zip(col_names, row))
            records.append(_normalize_work_record(row_dict))
    elif client is not None:
        table = args.table or "rag.works_flat"
        where_clauses = ["1=1"]
        if args.query:
            clean_q = args.query.replace("'", "\\'")
            where_clauses.append(
                f"(positionCaseInsensitiveUTF8(title, '{clean_q}') > 0 "
                f"OR positionCaseInsensitiveUTF8(topic, '{clean_q}') > 0 "
                f"OR arrayExists(k -> positionCaseInsensitiveUTF8(k, '{clean_q}') > 0, keywords))"
            )
        if args.author_id:
            clean_aid = args.author_id.replace("'", "\\'")
            if "works_flat" in table:
                where_clauses.append(f"has(author_ids, '{clean_aid}')")
        if args.institution_ror:
            clean_ror = args.institution_ror.replace("https://ror.org/", "").strip()
            where_clauses.append(f"(has(institution_rors, '{clean_ror}') OR has(institution_rors, 'https://ror.org/{clean_ror}'))")
        if args.topic_id:
            clean_tid = args.topic_id.replace("'", "\\'")
            where_clauses.append(f"(primary_topic_id = '{clean_tid}' OR positionCaseInsensitiveUTF8(topic, '{clean_tid}') > 0)")
        if args.country:
            clean_cc = args.country.upper().strip()
            where_clauses.append(f"(country_code = '{clean_cc}' OR has(all_country_codes, '{clean_cc}'))")
        if args.year_min:
            where_clauses.append(f"publication_year >= {int(args.year_min)}")
        if args.year_max:
            where_clauses.append(f"publication_year <= {int(args.year_max)}")
        if args.is_oa is not None:
            val = 1 if args.is_oa else 0
            where_clauses.append(f"toUInt8OrZero(toString(is_oa)) = {val}")

        where_sql = " AND ".join(where_clauses)
        sanitize_no_joins(where_sql)
        ref_expr = "referenced_works" if "works_flat" in table else "JSONExtract(raw_data, 'referenced_works', 'Array(String)') AS referenced_works"

        sql = f"""
        SELECT
            id, doi, title, publication_year, type, language, oa_status, is_oa,
            cited_by_count, fwci, percentile, is_top_10, is_top_1,
            apc_paid_usd, apc_list_usd, is_doaj_indexed, has_repository_fulltext,
            source_id, source_type, author_names, institution_names, institution_rors,
            all_country_codes, country_code, topic, subfield, field, domain,
            keywords, sdgs, {ref_expr}
        FROM {table}
        WHERE {where_sql}
        ORDER BY cited_by_count DESC
        LIMIT {limit}
        """
        try:
            res = client.query(sql)
            col_names = list(res.column_names)
            for row in res.result_rows:
                row_dict = dict(zip(col_names, row))
                records.append(_normalize_work_record(row_dict))
        except Exception as e:
            print(f"Warning: ClickHouse query failed ({e}). Falling back to OpenAlex API.", file=sys.stderr)
            records = []

    if not records and not args.sql_file:
        res = openalex_search_works(
            search_query=args.query or "",
            author_id=args.author_id,
            institution_ror=args.institution_ror,
            topic_id=args.topic_id,
            from_publication_date=f"{args.year_min}-01-01" if args.year_min else None,
            to_publication_date=f"{args.year_max}-12-31" if args.year_max else None,
            is_oa=args.is_oa,
            limit=limit,
        )
        items = res.get("data") or res.get("results") or []
        records = [_normalize_work_record(it) for it in items]

    _save_works_output(
        records,
        args.output,
        meta={"query": args.query, "sql_file": args.sql_file, "table": args.table, "limit": limit},
    )
    print(f"Works search completed: {len(records)} works retrieved. Saved to {args.output}")
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
        group_by_field=args.group_by,
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
    p_wrk = subparsers.add_parser("search-works", help="Search works in ClickHouse (NO JOINs safe)")
    p_wrk.add_argument("--query", default="", help="Text search query")
    p_wrk.add_argument("--sql-file", help="Optional path to transpiled ClickHouse SQL file (e.g., clickhouse_query.sql)")
    p_wrk.add_argument("--table", default="rag.works_flat", help="ClickHouse table: rag.works_flat (global) or rag.works_academic_all (Mexico)")
    p_wrk.add_argument("--author-id", help="OpenAlex Author ID")
    p_wrk.add_argument("--institution-ror", help="Institution ROR ID")
    p_wrk.add_argument("--topic-id", help="Primary Topic ID or name")
    p_wrk.add_argument("--country", help="ISO-2 country code filter (e.g., MX, US, BR)")
    p_wrk.add_argument("--year-min", type=int, help="Start year")
    p_wrk.add_argument("--year-max", type=int, help="End year")
    p_wrk.add_argument("--is-oa", type=bool, default=None, help="Open Access flag")
    p_wrk.add_argument("--limit", type=int, default=500, help="Max works (default: 500, max: 50000)")
    p_wrk.add_argument("--output", required=True, help="Path to output (.parquet, .csv, or .json)")
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
