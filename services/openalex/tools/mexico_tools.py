import os
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional
from shared.config import settings
from shared.clickhouse import get_clickhouse_client, sanitize_no_joins, execute_safe_query


def generate_hispanic_name_permutations(name: str) -> List[str]:
    """Genera variantes y permutaciones comunes de nombres y apellidos hispanos."""
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


def get_text_embedding(text: str) -> List[float]:
    """Genera vector de 768 dimensiones usando el servidor local de embeddings (LM Studio)."""
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("El texto para generar embeddings no puede estar vacío.")

    candidate_urls = []
    if settings.lm_studio_url:
        base = settings.lm_studio_url.rstrip("/")
        if not base.endswith("/embeddings"):
            candidate_urls.append(f"{base}/embeddings")
        else:
            candidate_urls.append(base)
    candidate_urls.extend([
        "http://127.0.0.1:1234/v1/embeddings",
        "http://172.17.0.1:1234/v1/embeddings",
        "http://host.docker.internal:1234/v1/embeddings"
    ])

    model_name = settings.embedding_model
    api_key = settings.llm_api_key or os.getenv("LM_STUDIO_API_KEY", "")
    payload = json.dumps({"model": model_name, "input": clean_text}).encode("utf-8")

    last_err = None
    for url in candidate_urls:
        try:
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["data"][0]["embedding"]
        except Exception as e:
            last_err = e

    raise RuntimeError(f"No fue posible conectar con el servicio local de embeddings (768d): {last_err}")


def openalex_get_institution(
    query: str = "",
    acronym: str = "",
    state: str = "",
    ror: str = "",
    limit: int = 15
) -> Dict[str, Any]:
    """
    Consulta y mapea instituciones, universidades y centros de investigación de México
    en rag.institutions_seed_mexico. Resuelve códigos canónicos ROR, sedes y dependencias matriz.
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "institutions": []}

    where_clauses = ["(country_code = 'MX' OR country_code = '')"]

    if query:
        clean_q = query.replace("'", "\\'")
        where_clauses.append(f"positionCaseInsensitiveUTF8(display_name, '{clean_q}') > 0")
    if acronym:
        clean_acr = acronym.strip().upper()
        where_clauses.append(f"has(acronyms, '{clean_acr}')")
    if state:
        clean_st = state.replace("'", "\\'")
        where_clauses.append(f"positionCaseInsensitiveUTF8(state, '{clean_st}') > 0")
    if ror:
        clean_ror = ror.replace("https://ror.org/", "").strip()
        where_clauses.append(f"(ror = '{clean_ror}' OR ror = 'https://ror.org/{clean_ror}')")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    limit_val = min(max(limit, 1), 100)
    sql = f"""
    SELECT
        id,
        display_name,
        ror,
        type,
        city,
        state,
        acronyms,
        parent_id,
        parent_name
    FROM rag.institutions_seed_mexico
    WHERE {where_sql}
    ORDER BY display_name ASC
    LIMIT {limit_val}
    """

    try:
        res = client.query(sql)
        institutions = []
        for r in res.result_rows:
            ror_canonical = r[2] if str(r[2]).startswith("http") else f"https://ror.org/{r[2]}" if r[2] else None
            institutions.append({
                "openalex_id": r[0],
                "display_name": r[1],
                "ror": ror_canonical,
                "type": r[3],
                "city": r[4],
                "state": r[5],
                "acronyms": r[6] or [],
                "parent_id": r[7],
                "parent_name": r[8]
            })

        return {
            "status": "success",
            "total_found": len(institutions),
            "institutions": institutions
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "institutions": []}


def openalex_search_authors(
    name: str = "",
    institution: str = "",
    dependency: str = "",
    snii_level: str = "",
    orcid: str = "",
    limit: int = 20
) -> Dict[str, Any]:
    """
    Busca y desambigua investigadoras e investigadores de México en rag.authors_seed_mexico
    y rag.academics_all, considerando variantes de nombres hispanos, SNII, adscripción y ORCID.
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "authors": []}

    limit_val = min(max(limit, 1), 200)
    name_str = name.strip()
    permutations = generate_hispanic_name_permutations(name_str) if name_str else []

    authors = []
    seen_ids = set()

    # Si se pide nivel SNII explícito o dependencia, priorizar academics_all
    if snii_level or dependency:
        where_clauses = ["1=1"]
        if name_str:
            sub_conds = [f"positionCaseInsensitiveUTF8(name, '{p}') > 0" for p in permutations[:4]]
            where_clauses.append(f"({' OR '.join(sub_conds)})")
        if snii_level:
            clean_snii = snii_level.strip().replace("'", "\\'")
            where_clauses.append(f"positionCaseInsensitiveUTF8(snii_level, '{clean_snii}') > 0")
        if dependency:
            clean_dep = dependency.strip().replace("'", "\\'")
            where_clauses.append(f"positionCaseInsensitiveUTF8(dependency, '{clean_dep}') > 0")

        where_sql = " AND ".join(where_clauses)
        sanitize_no_joins(where_sql)

        sql_acad = f"""
        SELECT id, name, institution, dependency, subdependency, snii_level, orcid, paper_count, citation_count
        FROM rag.academics_all
        WHERE {where_sql}
        ORDER BY citation_count DESC
        LIMIT {limit_val}
        """
        try:
            res_acad = client.query(sql_acad)
            for row in res_acad.result_rows:
                seen_ids.add(row[0])
                authors.append({
                    "id": row[0],
                    "display_name": row[1],
                    "institution": row[2],
                    "dependency": row[3],
                    "subdependency": row[4],
                    "snii_level": row[5],
                    "orcid": row[6],
                    "works_count": row[7],
                    "cited_by_count": row[8],
                    "source_table": "academics_all"
                })
        except Exception:
            pass

    # Consulta principal sobre authors_seed_mexico
    if len(authors) < limit_val:
        where_seed = ["1=1"]
        if name_str:
            sub_conds = [f"positionCaseInsensitiveUTF8(display_name, '{p}') > 0" for p in permutations[:4]]
            where_seed.append(f"({' OR '.join(sub_conds)})")
        if institution:
            clean_inst = institution.replace("'", "\\'")
            where_seed.append(f"positionCaseInsensitiveUTF8(raw_data, '{clean_inst}') > 0")
        if orcid:
            clean_orcid = orcid.replace("https://orcid.org/", "").strip()
            where_seed.append(f"position(orcid, '{clean_orcid}') > 0")

        where_sql_seed = " AND ".join(where_seed)
        sanitize_no_joins(where_sql_seed)

        needed = limit_val - len(authors)
        sql_seed = f"""
        SELECT id, any(display_name), any(orcid),
               any(JSONExtractInt(raw_data, 'works_count')) as works_count,
               any(JSONExtractInt(raw_data, 'cited_by_count')) as cited_by_count,
               any(JSONExtractString(raw_data, 'last_known_institutions', 1, 'display_name')) as institution,
               any(JSONExtractInt(raw_data, 'summary_stats', 'h_index')) as h_index
        FROM rag.authors_seed_mexico
        WHERE {where_sql_seed}
        GROUP BY id
        ORDER BY cited_by_count DESC
        LIMIT {needed}
        """
        try:
            res_seed = client.query(sql_seed)
            for r in res_seed.result_rows:
                if r[0] not in seen_ids:
                    seen_ids.add(r[0])
                    authors.append({
                        "id": r[0],
                        "display_name": r[1],
                        "orcid": r[2],
                        "works_count": r[3],
                        "cited_by_count": r[4],
                        "institution": r[5],
                        "h_index": r[6],
                        "source_table": "authors_seed_mexico"
                    })
        except Exception as e:
            if not authors:
                return {"status": "error", "message": str(e), "authors": []}

    return {
        "status": "success",
        "total_found": len(authors),
        "authors": authors
    }


def openalex_search_works(
    query: str = "",
    author_name: str = "",
    institution_name: str = "",
    institution_ror: str = "",
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    oa_status: Optional[str] = None,
    is_top_10: Optional[bool] = None,
    topic: Optional[str] = None,
    limit: int = 25
) -> Dict[str, Any]:
    """
    Busca publicaciones en rag.works_academic_all (1.65M de trabajos con autoría mexicana),
    con metadatos de impacto (FWCI, percentil, Top 10%), vías OA y gasto comercial APC (USD).
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "works": []}

    where_clauses = ["1=1"]

    if query:
        clean_q = query.replace("'", "\\'")
        where_clauses.append(f"positionCaseInsensitiveUTF8(title, '{clean_q}') > 0")
    if author_name:
        clean_a = author_name.replace("'", "\\'")
        where_clauses.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_a}') > 0, author_names)")
    if institution_name:
        clean_inst = institution_name.replace("'", "\\'")
        where_clauses.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_inst}') > 0, institution_names)")
    if institution_ror:
        clean_ror = institution_ror.replace("https://ror.org/", "").strip()
        where_clauses.append(f"(has(institution_rors, '{clean_ror}') OR has(institution_rors, 'https://ror.org/{clean_ror}'))")
    if year_min is not None:
        where_clauses.append(f"publication_year >= {int(year_min)}")
    if year_max is not None:
        where_clauses.append(f"publication_year <= {int(year_max)}")
    if oa_status:
        where_clauses.append(f"lower(oa_status) = '{oa_status.lower().strip()}'")
    if is_top_10 is not None:
        val = 1 if is_top_10 else 0
        where_clauses.append(f"is_top_10 = {val}")
    if topic:
        clean_top = topic.replace("'", "\\'")
        where_clauses.append(f"positionCaseInsensitiveUTF8(topic, '{clean_top}') > 0")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    limit_val = min(max(limit, 1), 200)
    sql = f"""
    SELECT
        id,
        title,
        doi,
        any(publication_year) as year,
        max(cited_by_count) as citations,
        any(oa_status) as oa,
        any(is_oa) as is_open_access,
        any(fwci) as fwci_val,
        any(percentile) as pct,
        any(is_top_10) as top10,
        any(is_top_1) as top1,
        any(apc_paid_usd) as apc,
        any(author_names) as authors,
        any(institution_names) as inst_names,
        any(institution_rors) as inst_rors,
        any(topic) as topic_name,
        any(subfield) as subfield_name
    FROM rag.works_academic_all
    WHERE {where_sql}
    GROUP BY id, title, doi
    ORDER BY citations DESC
    LIMIT {limit_val}
    """

    try:
        res = client.query(sql)
        works = []
        for r in res.result_rows:
            doi_canonical = f"https://doi.org/{r[2]}" if r[2] and not str(r[2]).startswith("http") else r[2]
            works.append({
                "id": r[0],
                "title": r[1],
                "doi": doi_canonical,
                "publication_year": r[3],
                "cited_by_count": r[4],
                "oa_status": r[5],
                "is_oa": bool(r[6] == "1" or r[6] == 1 or str(r[6]).lower() == "true"),
                "fwci": round(float(r[7]), 3) if r[7] is not None else None,
                "percentile": round(float(r[8]), 2) if r[8] is not None else None,
                "is_top_10": bool(r[9] == 1),
                "is_top_1": bool(r[10] == 1),
                "apc_paid_usd": round(float(r[11]), 2) if r[11] is not None else 0.0,
                "author_names": r[12] or [],
                "institution_names": r[13] or [],
                "institution_rors": r[14] or [],
                "topic": r[15],
                "subfield": r[16]
            })

        return {
            "status": "success",
            "total_found": len(works),
            "works": works
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "works": []}


def openalex_aggregate_mexico(
    group_by: str = "publication_year",
    filter_param: str = "1=1",
    institution_ror: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Calcula métricas agregadas y series temporales sobre rag.works_academic_all:
    distribución anual, 6 vías OA (Diamond, Gold, Hybrid), gasto APC USD, FWCI y % Top 10%.
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "results": []}

    allowed_groups = [
        "publication_year", "oa_status", "type", "subfield", "field",
        "domain", "is_top_10", "is_top_1", "country_code", "language", "sdgs"
    ]
    if group_by not in allowed_groups:
        return {
            "status": "error",
            "message": f"group_by debe ser uno de: {', '.join(allowed_groups)}",
            "results": []
        }

    where_clauses = [filter_param if filter_param else "1=1"]
    if institution_ror:
        clean_ror = institution_ror.replace("https://ror.org/", "").strip()
        where_clauses.append(f"(has(institution_rors, '{clean_ror}') OR has(institution_rors, 'https://ror.org/{clean_ror}'))")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    limit_val = min(max(limit, 1), 200)

    if group_by == "publication_year":
        sql = f"""
        SELECT
            publication_year AS year,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 3) AS avg_fwci,
            sum(is_top_10) AS top10_count,
            sum(is_top_1) AS top1_count,
            sum(oa_status = 'diamond') AS diamond_count,
            sum(oa_status = 'gold') AS gold_count,
            sum(oa_status = 'hybrid') AS hybrid_count,
            round(sum(apc_paid_usd), 2) AS total_apc_paid_usd
        FROM rag.works_academic_all
        WHERE {where_sql} AND publication_year > 1960
        GROUP BY publication_year
        ORDER BY publication_year ASC
        LIMIT {limit_val}
        """
    else:
        sql = f"""
        SELECT
            {group_by} AS dimension,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 3) AS avg_fwci,
            round(avg(is_top_10) * 100, 2) AS pct_top_10,
            round(sum(apc_paid_usd), 2) AS total_apc_paid_usd
        FROM rag.works_academic_all
        WHERE {where_sql}
        GROUP BY {group_by}
        ORDER BY total_works DESC
        LIMIT {limit_val}
        """

    try:
        res = client.query(sql)
        cols = res.column_names
        results = [dict(zip(cols, row)) for row in res.result_rows]

        return {
            "status": "success",
            "grouped_by": group_by,
            "total_groups": len(results),
            "results": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "results": []}


def openalex_top_entities(
    query: str,
    by: str = "institutions",
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Clasifica las instituciones o autores líderes en un tema o subcampo dentro de México,
    calculando volumen de papers, citas acumuladas, promedio de FWCI y porcentaje en el Top 10%.
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "top_entities": []}

    by_clean = by.lower().strip()
    if by_clean not in ("institutions", "authors"):
        return {"status": "error", "message": "Parámetro 'by' debe ser 'institutions' o 'authors'", "top_entities": []}

    clean_q = query.replace("'", "\\'")
    where_clauses = [
        f"(positionCaseInsensitiveUTF8(title, '{clean_q}') > 0 OR positionCaseInsensitiveUTF8(subfield, '{clean_q}') > 0 OR positionCaseInsensitiveUTF8(topic, '{clean_q}') > 0)"
    ]
    if year_min is not None:
        where_clauses.append(f"publication_year >= {int(year_min)}")
    if year_max is not None:
        where_clauses.append(f"publication_year <= {int(year_max)}")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    limit_val = min(max(limit, 1), 50)

    if by_clean == "institutions":
        sql = f"""
        SELECT
            inst_name AS entity_name,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 3) AS avg_fwci,
            round(avg(is_top_10) * 100, 2) AS pct_top_10
        FROM rag.works_academic_all
        ARRAY JOIN institution_names AS inst_name
        WHERE {where_sql} AND inst_name != ''
        GROUP BY inst_name
        ORDER BY total_works DESC
        LIMIT {limit_val}
        """
    else:
        sql = f"""
        SELECT
            auth_name AS entity_name,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 3) AS avg_fwci,
            round(avg(is_top_10) * 100, 2) AS pct_top_10
        FROM rag.works_academic_all
        ARRAY JOIN author_names AS auth_name
        WHERE {where_sql} AND auth_name != ''
        GROUP BY auth_name
        ORDER BY total_works DESC
        LIMIT {limit_val}
        """

    try:
        res = client.query(sql)
        entities = []
        for rank, r in enumerate(res.result_rows, 1):
            entities.append({
                "rank": rank,
                "display_name": r[0],
                "total_works": r[1],
                "total_citations": r[2],
                "avg_fwci": r[3],
                "pct_top_10": r[4]
            })

        return {
            "status": "success",
            "query": query,
            "by": by_clean,
            "total_entities": len(entities),
            "top_entities": entities
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "top_entities": []}


def openalex_semantic_search(
    query: str,
    target: str = "works",
    institution_name: Optional[str] = None,
    year_min: Optional[int] = None,
    oa_status: Optional[str] = None,
    limit: int = 15
) -> Dict[str, Any]:
    """
    Búsqueda semántica conceptual mediante embeddings locales Nomic (768d) y similitud coseno
    en rag.works_academic_all o rag.academics_all en ClickHouse.
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "results": []}

    target_clean = target.lower().strip()
    if target_clean not in ("works", "authors"):
        return {"status": "error", "message": "target debe ser 'works' o 'authors'", "results": []}

    try:
        query_vec = get_text_embedding(query)
    except Exception as e:
        return {"status": "error", "message": f"Error generando embedding conceptual: {str(e)}", "results": []}

    vec_str = str(query_vec)
    limit_val = min(max(limit, 1), 50)

    if target_clean == "works":
        where_clauses = ["length(embedding_nomic) = 768", "title != ''"]
        if year_min is not None:
            where_clauses.append(f"publication_year >= {int(year_min)}")
        if oa_status:
            where_clauses.append(f"lower(oa_status) = '{oa_status.lower().strip()}'")
        if institution_name:
            clean_inst = institution_name.replace("'", "\\'")
            where_clauses.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_inst}') > 0, institution_names)")

        where_sql = " AND ".join(where_clauses)
        sanitize_no_joins(where_sql)

        sql = f"""
        SELECT
            id,
            title,
            any(publication_year) as year,
            max(cited_by_count) as citations,
            any(oa_status) as oa,
            any(fwci) as fwci_val,
            any(is_top_10) as top10,
            any(author_names) as authors,
            any(institution_names) as inst_names,
            any(subfield) as subfield_name,
            min(cosineDistance(embedding_nomic, {vec_str})) as cosine_dist
        FROM rag.works_academic_all
        WHERE {where_sql}
        GROUP BY id, title
        ORDER BY cosine_dist ASC
        LIMIT {limit_val}
        """

        try:
            res = client.query(sql)
            results = []
            for r in res.result_rows:
                dist = float(r[10])
                results.append({
                    "id": r[0],
                    "title": r[1],
                    "publication_year": r[2],
                    "cited_by_count": r[3],
                    "oa_status": r[4],
                    "fwci": round(float(r[5]), 3) if r[5] is not None else None,
                    "is_top_10": bool(r[6] == 1),
                    "author_names": r[7] or [],
                    "institution_names": r[8] or [],
                    "subfield": r[9],
                    "cosine_distance": round(dist, 4),
                    "semantic_similarity": round(1.0 - dist, 4)
                })

            return {
                "status": "success",
                "query": query,
                "target": "works",
                "embedding_model": settings.embedding_model,
                "total_returned": len(results),
                "results": results
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "results": []}

    else:
        where_clauses = ["length(embedding_nomic) = 768", "name != ''"]
        if institution_name:
            clean_inst = institution_name.replace("'", "\\'")
            where_clauses.append(f"positionCaseInsensitiveUTF8(institution, '{clean_inst}') > 0")

        where_sql = " AND ".join(where_clauses)
        sanitize_no_joins(where_sql)

        sql = f"""
        SELECT
            id,
            name,
            institution,
            dependency,
            snii_level,
            orcid,
            paper_count,
            citation_count,
            cosineDistance(embedding_nomic, {vec_str}) as cosine_dist
        FROM rag.academics_all
        WHERE {where_sql}
        ORDER BY cosine_dist ASC
        LIMIT {limit_val}
        """

        try:
            res = client.query(sql)
            results = []
            for r in res.result_rows:
                dist = float(r[8])
                results.append({
                    "id": r[0],
                    "name": r[1],
                    "institution": r[2],
                    "dependency": r[3],
                    "snii_level": r[4],
                    "orcid": r[5],
                    "paper_count": r[6],
                    "citation_count": r[7],
                    "cosine_distance": round(dist, 4),
                    "semantic_similarity": round(1.0 - dist, 4)
                })

            return {
                "status": "success",
                "query": query,
                "target": "authors",
                "embedding_model": settings.embedding_model,
                "total_returned": len(results),
                "results": results
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "results": []}


def openalex_run_select_query(query: str, limit: int = 50) -> Dict[str, Any]:
    """
    Ejecuta una consulta SQL SELECT directa sobre la base de datos ClickHouse (rag).
    Aplica verificación estricta de CERO JOINs para garantizar la integridad y rendimiento.
    """
    return execute_safe_query(query=query, limit=limit)
