"""
Universal Scientometrics DuckDB Analytics Engine
------------------------------------------------
Motor analítico local y embebido basado en DuckDB para la ejecución de consultas
cienciométricas ultra rápidas sobre archivos de corpus (Parquet, Arrow, CSV)
sin necesidad de servidores externos ni dependencias de red.
Compatible con el motor de visualización (openalex_visualizer_cli.py / sos_visualizer).
"""

import os
import re
from typing import Dict, Any, List, Optional
import duckdb
import pandas as pd


def get_duckdb_connection(parquet_path: Optional[str] = None) -> duckdb.DuckDBPyConnection:
    """
    Crea una conexión DuckDB en memoria y, si se proporciona la ruta a un corpus,
    lo registra bajo las vistas canónicas 'works' y 'rag.works_academic_all'.
    """
    con = duckdb.connect(database=":memory:")
    
    if parquet_path and os.path.exists(parquet_path):
        normalized_path = parquet_path.replace("\\", "/")
        con.execute("CREATE SCHEMA IF NOT EXISTS rag;")
        con.execute(f"CREATE OR REPLACE VIEW works AS SELECT * FROM read_parquet('{normalized_path}');")
        con.execute(f"CREATE OR REPLACE VIEW rag.works_academic_all AS SELECT * FROM read_parquet('{normalized_path}');")
        
    return con


def execute_corpus_query(
    query: str,
    parquet_path: str,
    params: Optional[List[Any]] = None,
    as_dict: bool = True
) -> Dict[str, Any]:
    """
    Ejecuta una consulta SQL analítica sobre el archivo Parquet especificado.
    Soporta funciones modernas de arrays de DuckDB (unnest, list_contains, list_transform).
    """
    if not os.path.exists(parquet_path):
        return {
            "status": "error",
            "message": f"Archivo de corpus no encontrado: {parquet_path}",
            "data": []
        }

    try:
        con = get_duckdb_connection(parquet_path)
        
        adapted_query = query
        adapted_query = re.sub(r"\bpositionCaseInsensitive\s*\(", "contains(lower(", adapted_query, flags=re.IGNORECASE)
        adapted_query = re.sub(r"\bcountIf\s*\((.*?)\)", r"count(*) FILTER (WHERE \1)", adapted_query, flags=re.IGNORECASE)

        rel = con.execute(adapted_query, params or [])
        cols = [desc[0] for desc in rel.description]
        rows = rel.fetchall()

        if as_dict:
            dict_rows = [dict(zip(cols, row)) for row in rows]
            return {
                "status": "success",
                "columns": cols,
                "data": dict_rows,
                "row_count": len(dict_rows)
            }
        else:
            return {
                "status": "success",
                "columns": cols,
                "data": rows,
                "row_count": len(rows)
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error ejecutando consulta en DuckDB: {str(e)}",
            "data": []
        }


# ==============================================================================
# MÓDULOS DE ANÁLISIS CIENCIOMÉTRICO COMPATIBLES CON EL VISUALIZADOR
# ==============================================================================

def aggregate_corpus_by_year(parquet_path: str) -> Dict[str, Any]:
    """Calcula series temporales anuales estructuradas para el visualizador."""
    sql = """
    SELECT 
        publication_year as year,
        count(*) as total_works,
        sum(cited_by_count) as total_citations,
        round(avg(COALESCE(fwci, 1.0)), 2) as avg_fwci,
        count(*) FILTER (WHERE is_top_10 = 1) as top10_count,
        count(*) FILTER (WHERE oa_status = 'diamond') as diamond_count,
        count(*) FILTER (WHERE oa_status = 'gold') as gold_count,
        count(*) FILTER (WHERE oa_status = 'hybrid') as hybrid_count,
        count(*) FILTER (WHERE oa_status = 'green') as green_count,
        count(*) FILTER (WHERE oa_status = 'bronze') as bronze_count,
        count(*) FILTER (WHERE oa_status = 'closed') as closed_count,
        round(sum(COALESCE(apc_paid_usd, 0.0)), 2) as total_apc_paid_usd
    FROM works
    WHERE publication_year IS NOT NULL
    GROUP BY publication_year
    ORDER BY publication_year ASC;
    """
    res = execute_corpus_query(sql, parquet_path)
    if res.get("status") == "success":
        return {
            "status": "success",
            "grouped_by": "publication_year",
            "total_groups": res.get("row_count", 0),
            "results": res.get("data", [])
        }
    return res


def aggregate_corpus_oa_distribution(parquet_path: str) -> Dict[str, Any]:
    """Calcula la distribución de Acceso Abierto estructurada para la dona OA."""
    sql = """
    SELECT 
        oa_status,
        count(*) as total_works,
        round(count(*) * 100.0 / sum(count(*)) OVER (), 2) as percentage,
        sum(cited_by_count) as total_citations,
        round(sum(COALESCE(apc_paid_usd, 0.0)), 2) as total_apc_usd
    FROM works
    GROUP BY oa_status
    ORDER BY total_works DESC;
    """
    res = execute_corpus_query(sql, parquet_path)
    if res.get("status") == "success":
        rows = res.get("data", [])
        total_works = sum(r["total_works"] for r in rows)
        diamond_works = sum(r["total_works"] for r in rows if r["oa_status"] == "diamond")
        gold_works = sum(r["total_works"] for r in rows if r["oa_status"] == "gold")
        apc_usd = sum(r["total_apc_usd"] for r in rows)
        
        return {
            "status": "success",
            "grouped_by": "oa_status",
            "results": rows,
            "summary_kpis": {
                "total_works": total_works,
                "diamond_works": diamond_works,
                "diamond_percentage": round(diamond_works * 100.0 / total_works, 2) if total_works else 0.0,
                "gold_apc_works": gold_works,
                "total_apc_paid_usd": apc_usd
            }
        }
    return res


def get_corpus_top_authors(parquet_path: str, limit: int = 25) -> Dict[str, Any]:
    """Extrae autores destacados estructurados para el ranking de barras horizontales."""
    sql = f"""
    WITH author_flattened AS (
        SELECT 
            unnest(author_names) as entity_name,
            cited_by_count,
            COALESCE(fwci, 1.0) as fwci,
            is_top_10,
            oa_status
        FROM works
        WHERE author_names IS NOT NULL
    )
    SELECT 
        entity_name,
        count(*) as total_works,
        sum(cited_by_count) as total_citations,
        round(avg(fwci), 2) as avg_fwci,
        count(*) FILTER (WHERE is_top_10 = 1) as top10_works,
        count(*) FILTER (WHERE oa_status = 'diamond') as diamond_works
    FROM author_flattened
    WHERE length(trim(entity_name)) > 2
    GROUP BY entity_name
    ORDER BY total_works DESC, total_citations DESC
    LIMIT {limit};
    """
    res = execute_corpus_query(sql, parquet_path)
    if res.get("status") == "success":
        return {
            "status": "success",
            "top_entities": res.get("data", []),
            "target": "authors",
            "total_found": res.get("row_count", 0)
        }
    return res


def extract_coauthorship_graph(parquet_path: str, min_collaborations: int = 1, max_nodes: int = 60) -> Dict[str, Any]:
    """
    Construye la matriz de adyacencia de coautorías (nodos y aristas con peso)
    estructurada para el visualizador interactivo de grafos.
    """
    con = get_duckdb_connection(parquet_path)
    try:
        nodes_df = con.execute(f"""
            WITH flat AS (
                SELECT unnest(author_names) as name, cited_by_count
                FROM works
                WHERE author_names IS NOT NULL
            )
            SELECT name, count(*) as works_count, sum(cited_by_count) as citations
            FROM flat
            WHERE length(trim(name)) > 2
            GROUP BY name
            ORDER BY works_count DESC
            LIMIT {max_nodes};
        """).fetchdf()

        top_author_set = set(nodes_df["name"].tolist())

        works_authors = con.execute("""
            SELECT id, author_names 
            FROM works 
            WHERE author_names IS NOT NULL AND len(author_names) > 1;
        """).fetchall()

        collab_counts = {}
        for _, authors in works_authors:
            valid_authors = [a for a in authors if a in top_author_set]
            n = len(valid_authors)
            for i in range(n):
                for j in range(i + 1, n):
                    u, v = sorted([valid_authors[i], valid_authors[j]])
                    collab_counts[(u, v)] = collab_counts.get((u, v), 0) + 1

        edges = [
            {"source": u, "target": v, "weight": w}
            for (u, v), w in collab_counts.items()
            if w >= min_collaborations
        ]

        nodes = [
            {"id": row["name"], "label": row["name"], "works_count": int(row["works_count"]), "citations": int(row["citations"])}
            for _, row in nodes_df.iterrows()
        ]

        return {
            "status": "success",
            "chart_type": "network",
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "nodes": nodes,
            "edges": edges
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "nodes": [], "edges": []}


def calculate_lotka_law_fit(parquet_path: str) -> Dict[str, Any]:
    """
    Ajusta la Ley Clásica de Lotka (x^n * y = C) sobre la distribución de productividad
    de autores en el corpus.
    """
    import numpy as np
    
    con = get_duckdb_connection(parquet_path)
    try:
        dist_df = con.execute("""
            WITH author_counts AS (
                SELECT unnest(author_names) as name, count(*) as p
                FROM works
                WHERE author_names IS NOT NULL
                GROUP BY name
            )
            SELECT p as papers, count(*) as authors_count
            FROM author_counts
            WHERE length(trim(name)) > 2
            GROUP BY p
            ORDER BY papers ASC;
        """).fetchdf()

        if len(dist_df) < 3:
            return {"status": "insufficient_data", "message": "Corpus con muy pocos autores para ajustar Lotka."}

        x = np.log(dist_df["papers"].values)
        y = np.log(dist_df["authors_count"].values)
        
        poly = np.polyfit(x, y, 1)
        n_exponent = -float(poly[0])
        c_constant = float(np.exp(poly[1]))

        return {
            "status": "success",
            "lotka_exponent_n": round(n_exponent, 3),
            "lotka_constant_c": round(c_constant, 2),
            "theoretical_exponent_benchmark": 2.0,
            "interpretation": (
                f"El exponente de productividad es n={round(n_exponent, 2)} "
                f"(valor teórico canónico: ~2.00). "
                f"{'Presenta mayor concentración en pocos autores de élite.' if n_exponent > 2.0 else 'Presenta mayor dispersión de autorías ocasionales.'}"
            ),
            "distribution_sample": dist_df.head(10).to_dict(orient="records")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
