#!/usr/bin/env python3
"""
CLI Helper: Info TlachIA Scholar Intelligence
Fast read-only analytical queries on DuckDB (analytics_cache.duckdb, 14 tables)
for Researcher, Entity, Institution, and National levels. Supports JSON and Markdown output.
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any, Optional

import duckdb

DEFAULT_DUCKDB_PATH = os.environ.get("DUCKDB_ANALYTICS_PATH", "/home/sinapsisai/data/analytics_cache.duckdb")


def get_duckdb_conn(db_path: str = DEFAULT_DUCKDB_PATH) -> duckdb.DuckDBPyConnection:
    """Connects to DuckDB strictly in read_only mode for safe multi-agent concurrency."""
    if not os.path.exists(db_path):
        sys.stderr.write(f"Error: DuckDB file does not exist: {db_path}\n")
        sys.exit(1)
    return duckdb.connect(db_path, read_only=True)


def format_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Formats a list of rows into GitHub Flavored Markdown table."""
    if not headers or not rows:
        return "*Sin resultados.*"
    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for r in rows:
        row_str = [str(x) if x is not None else "" for x in r]
        md += "| " + " | ".join(row_str) + " |\n"
    return md


def save_output(data: Any, md_str: str, output_path: Optional[str], fmt: str):
    """Outputs either JSON or Markdown to file or stdout."""
    content = md_str if fmt == "markdown" else json.dumps(data, indent=2, ensure_ascii=False)
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Output saved in {fmt.upper()} format to {output_path}")
    else:
        print(content)


def cmd_researcher(args):
    """Queries researcher profile in DuckDB."""
    con = get_duckdb_conn(args.db_path)
    name = args.name.strip()
    query = """
        SELECT academic_name, is_snii, institutions, entities, num_documents, citations,
               fwci_avg, pct_top_10, h_index, pct_open_access, apc_paid_usd,
               pct_international, gini_topics, top_topic, orcid
        FROM investigador_total
        WHERE academic_name ILIKE ? OR db_academic_name ILIKE ?
        ORDER BY num_documents DESC LIMIT ?
    """
    param = f"%{name}%"
    df = con.execute(query, [param, param, args.limit or 10]).fetchdf()
    con.close()

    records = df.to_dict(orient="records")
    headers = ["Investigador", "SNII", "Institución", "Docs", "Citas", "FWCI", "% Top 10%", "H-Index", "Gasto APC ($)", "Tópico Principal"]
    rows = []
    for r in records:
        rows.append([
            r.get("academic_name"),
            "Sí" if r.get("is_snii") else "No",
            (r.get("institutions") or "")[:35],
            r.get("num_documents"),
            r.get("citations"),
            round(r.get("fwci_avg", 0.0), 2) if r.get("fwci_avg") is not None else "N/A",
            f"{round(r.get('pct_top_10', 0.0) * 100, 1)}%" if r.get("pct_top_10") is not None else "N/A",
            r.get("h_index"),
            f"${r.get('apc_paid_usd', 0):,.0f}" if r.get("apc_paid_usd") is not None else "$0",
            (r.get("top_topic") or "")[:30]
        ])

    md = f"### Perfil de Investigador: {name}\n\n" + format_markdown_table(headers, rows)
    save_output({"query": name, "total_found": len(records), "results": records}, md, args.output, args.format)
    sys.exit(0)


def cmd_entity(args):
    """Queries subdependence / faculty metrics."""
    con = get_duckdb_conn(args.db_path)
    entity = args.entity.strip()
    query = """
        SELECT db_institution_name, db_entity_name, num_documents, citations,
               fwci_avg, pct_top_10, pct_open_access, apc_paid_usd, pct_international
        FROM institucion_total
        WHERE db_entity_name ILIKE ?
        ORDER BY num_documents DESC LIMIT ?
    """
    param = f"%{entity}%"
    df = con.execute(query, [param, args.limit or 10]).fetchdf()
    con.close()

    records = df.to_dict(orient="records")
    headers = ["Institución", "Dependencia / Facultad", "Docs", "Citas", "FWCI", "% Top 10%", "% OA", "Gasto APC ($)"]
    rows = []
    for r in records:
        rows.append([
            (r.get("db_institution_name") or "")[:30],
            r.get("db_entity_name"),
            r.get("num_documents"),
            r.get("citations"),
            round(r.get("fwci_avg", 0.0), 2) if r.get("fwci_avg") is not None else "N/A",
            f"{round(r.get('pct_top_10', 0.0) * 100, 1)}%" if r.get("pct_top_10") is not None else "N/A",
            f"{round(r.get('pct_open_access', 0.0) * 100, 1)}%" if r.get("pct_open_access") is not None else "N/A",
            f"${r.get('apc_paid_usd', 0):,.0f}" if r.get("apc_paid_usd") is not None else "$0"
        ])

    md = f"### Métricas de Dependencia: {entity}\n\n" + format_markdown_table(headers, rows)
    save_output({"query": entity, "total_found": len(records), "results": records}, md, args.output, args.format)
    sys.exit(0)


def cmd_institution(args):
    """Queries university / research center metrics."""
    con = get_duckdb_conn(args.db_path)
    inst = args.institution.strip()
    query = """
        SELECT db_institution_name, num_documents, citations, fwci_avg, pct_top_10,
               pct_open_access, pct_oa_gold, pct_oa_hybrid, apc_paid_usd, pct_international,
               top_topic, top_domain
        FROM institucion_total
        WHERE db_institution_name ILIKE ? AND (db_entity_name IS NULL OR db_entity_name = '' OR db_entity_name = db_institution_name)
        ORDER BY num_documents DESC LIMIT ?
    """
    param = f"%{inst}%"
    df = con.execute(query, [param, args.limit or 5]).fetchdf()
    con.close()

    records = df.to_dict(orient="records")
    headers = ["Institución", "Docs", "Citas", "FWCI", "% Top 10%", "% OA", "Gasto APC ($)", "Colaboración Int.", "Top Dominio"]
    rows = []
    for r in records:
        rows.append([
            r.get("db_institution_name"),
            r.get("num_documents"),
            r.get("citations"),
            round(r.get("fwci_avg", 0.0), 2) if r.get("fwci_avg") is not None else "N/A",
            f"{round(r.get('pct_top_10', 0.0) * 100, 1)}%" if r.get("pct_top_10") is not None else "N/A",
            f"{round(r.get('pct_open_access', 0.0) * 100, 1)}%" if r.get("pct_open_access") is not None else "N/A",
            f"${r.get('apc_paid_usd', 0):,.0f}" if r.get("apc_paid_usd") is not None else "$0",
            f"{round(r.get('pct_international', 0.0) * 100, 1)}%" if r.get("pct_international") is not None else "N/A",
            r.get("top_domain")
        ])

    md = f"### Perfil Institucional: {inst}\n\n" + format_markdown_table(headers, rows)
    save_output({"query": inst, "total_found": len(records), "results": records}, md, args.output, args.format)
    sys.exit(0)


def cmd_national(args):
    """Generates national overview and summary statistics."""
    con = get_duckdb_conn(args.db_path)
    res = con.execute("""
        SELECT count(*) as total_investigadores,
               sum(CASE WHEN is_snii = 1 THEN 1 ELSE 0 END) as snii_miembros,
               sum(num_documents) as total_docs_investigadores,
               sum(citations) as total_citas,
               avg(fwci_avg) as promedio_fwci,
               sum(apc_paid_usd) as gasto_total_apc_usd
        FROM investigador_total
    """).fetchone()

    inst_res = con.execute("""
        SELECT count(DISTINCT db_institution_name) as total_instituciones
        FROM institucion_total
    """).fetchone()
    con.close()

    summary = {
        "total_investigadores_registrados": res[0],
        "miembros_padron_snii": res[1],
        "total_instituciones_mapeadas": inst_res[0],
        "produccion_total_articulos": res[2],
        "citas_acumuladas": res[3],
        "fwci_promedio_nacional": round(res[4], 2) if res[4] else 1.0,
        "gasto_estimado_total_apc_usd": round(res[5], 2) if res[5] else 0.0
    }

    md = "### Panorama Nacional de Ciencia en México (Padrón SNII & OpenAlex)\n\n"
    md += f"- **Investigadores Registrados:** {summary['total_investigadores_registrados']:,}\n"
    md += f"- **Miembros Acreditados SNII:** {summary['miembros_padron_snii']:,}\n"
    md += f"- **Instituciones Mapeadas:** {summary['total_instituciones_mapeadas']:,}\n"
    md += f"- **Artículos Analizados:** {summary['produccion_total_articulos']:,}\n"
    md += f"- **Citas Totales:** {summary['citas_acumuladas']:,}\n"
    md += f"- **FWCI Promedio Nacional:** {summary['fwci_promedio_nacional']}\n"
    md += f"- **Gasto Estimado en APC (USD):** ${summary['gasto_estimado_total_apc_usd']:,.2f}\n"

    save_output(summary, md, args.output, args.format)
    sys.exit(0)


def cmd_sql_safe(args):
    """Executes safe, read-only SQL queries on DuckDB."""
    sql = args.query.strip()
    forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "CREATE", "REPLACE"]
    first_word = sql.split()[0].upper()
    if first_word in forbidden or any(f" {f} " in f" {sql.upper()} " for f in forbidden):
        sys.stderr.write(f"Error: Forbidden mutating SQL clause in read-only query.\n")
        sys.exit(1)

    con = get_duckdb_conn(args.db_path)
    df = con.execute(sql).fetchdf()
    con.close()

    records = df.to_dict(orient="records")
    headers = list(df.columns)
    rows = df.values.tolist()
    md = format_markdown_table(headers, rows[:50])

    save_output({"query": sql, "rows_count": len(records), "data": records}, md, args.output, args.format)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="CLI for Info TlachIA Scholar Intelligence")
    parser.add_argument("--db-path", default=DEFAULT_DUCKDB_PATH, help="Path to analytics_cache.duckdb")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: query-researcher
    p_res = subparsers.add_parser("query-researcher", help="Query researcher profile")
    p_res.add_argument("--name", required=True, help="Researcher name (e.g. 'Torres, Rafael')")
    p_res.add_argument("--limit", type=int, default=10, help="Max rows")
    p_res.add_argument("--format", choices=["json", "markdown"], default="json")
    p_res.add_argument("--output", help="Output file path")
    p_res.set_defaults(func=cmd_researcher)

    # Subcommand: query-entity
    p_ent = subparsers.add_parser("query-entity", help="Query faculty / department metrics")
    p_ent.add_argument("--entity", required=True, help="Entity/Faculty name")
    p_ent.add_argument("--limit", type=int, default=10, help="Max rows")
    p_ent.add_argument("--format", choices=["json", "markdown"], default="json")
    p_ent.add_argument("--output", help="Output file path")
    p_ent.set_defaults(func=cmd_entity)

    # Subcommand: query-institution
    p_ins = subparsers.add_parser("query-institution", help="Query institution profile")
    p_ins.add_argument("--institution", required=True, help="Institution name (e.g. 'UNAM')")
    p_ins.add_argument("--limit", type=int, default=5, help="Max rows")
    p_ins.add_argument("--format", choices=["json", "markdown"], default="json")
    p_ins.add_argument("--output", help="Output file path")
    p_ins.set_defaults(func=cmd_institution)

    # Subcommand: national-overview
    p_nat = subparsers.add_parser("national-overview", help="National aggregate statistics")
    p_nat.add_argument("--format", choices=["json", "markdown"], default="json")
    p_nat.add_argument("--output", help="Output file path")
    p_nat.set_defaults(func=cmd_national)

    # Subcommand: sql-safe
    p_sql = subparsers.add_parser("sql-safe", help="Execute read-only SQL query")
    p_sql.add_argument("--query", required=True, help="SQL SELECT query")
    p_sql.add_argument("--format", choices=["json", "markdown"], default="json")
    p_sql.add_argument("--output", help="Output file path")
    p_sql.set_defaults(func=cmd_sql_safe)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
