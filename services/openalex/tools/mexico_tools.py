import os
import json
import unicodedata
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional
from shared.config import settings
from shared.clickhouse import get_clickhouse_client, sanitize_no_joins, execute_safe_query


def _normalize_entity_key(s: str) -> str:
    """Normaliza cadenas eliminando acentos, puntuación y mayúsculas para deduplicación segura."""
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower().replace("-", " ").replace(",", "").replace(".", "").strip()


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


def prioritize_mexican_institutions(inst_str: str) -> str:
    """Prioriza instituciones mexicanas conocidas al inicio de la lista/cadena de afiliaciones."""
    if not inst_str:
        return ""
    insts = [i.strip() for i in inst_str.split("|") if i.strip()]
    mex_keywords = [
        "méxico", "mexico", "unam", "cinvestav", "ipn", "uam", "autónoma", "autonoma",
        "instituto nacional de", "hospital general", "tecnológico de monterrey", "itesm",
        "el colegio de méxico", "colmex", "universidad de guadalajara", "universidad autónoma",
        "salud pública", "nutrición", "cardiología", "respiratorias"
    ]
    mex_insts = []
    other_insts = []
    seen = set()
    for inst in insts:
        low = inst.lower()
        if low in seen:
            continue
        seen.add(low)
        if any(k in low for k in mex_keywords):
            mex_insts.append(inst)
        else:
            other_insts.append(inst)
    return " | ".join(mex_insts + other_insts)


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
               arrayStringConcat(
                   arrayFilter(x -> length(x) > 0,
                       arrayMap(i -> JSONExtractString(i, 'display_name'),
                           JSONExtractArrayRaw(any(raw_data), 'last_known_institutions')
                       )
                   ),
                   ' | '
               ) as institution,
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
                    inst_formatted = prioritize_mexican_institutions(r[5] or "")
                    authors.append({
                        "id": r[0],
                        "display_name": r[1],
                        "orcid": r[2],
                        "works_count": r[3],
                        "cited_by_count": r[4],
                        "institution": inst_formatted,
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
    author_id: str = "",
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
    Soporta filtro directo por ID canónico OpenAlex de autor (author_id, ej: 'A5060963552')
    o por nombre de autor (author_name, ej: 'Annie Pardo'), resolviendo variantes automáticamente.
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "works": []}

    where_clauses = ["1=1"]

    if query:
        clean_q = query.replace("'", "\\'")
        where_clauses.append(f"positionCaseInsensitiveUTF8(title, '{clean_q}') > 0")
    if author_id:
        clean_aid = author_id.strip()
        if not clean_aid.startswith("http"):
            uri_aid = f"https://openalex.org/{clean_aid}"
        else:
            uri_aid = clean_aid
            clean_aid = clean_aid.replace("https://openalex.org/", "")
        where_clauses.append(f"(has(author_names, '{uri_aid}') OR has(author_names, '{clean_aid}'))")
    elif author_name:
        clean_a = author_name.replace("'", "\\'").strip()
        resolved_ids = []
        try:
            res_ids = client.query(f"SELECT id FROM rag.authors_seed_mexico WHERE positionCaseInsensitiveUTF8(display_name, '{clean_a}') > 0 LIMIT 10")
            for r_id in res_ids.result_rows:
                resolved_ids.append(r_id[0])
        except Exception:
            pass
        sub_conds = []
        for aid in resolved_ids:
            clean_short = aid.replace("https://openalex.org/", "")
            sub_conds.append(f"has(author_names, '{aid}')")
            sub_conds.append(f"has(author_names, '{clean_short}')")
        sub_conds.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_a}') > 0, author_names)")
        where_clauses.append(f"({' OR '.join(sub_conds)})")
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
    author_id: str = "",
    author_name: str = "",
    filter_param: str = "1=1",
    institution_ror: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Calcula métricas agregadas y series temporales sobre rag.works_academic_all:
    distribución anual, 6 vías OA (Diamond, Gold, Hybrid), gasto APC USD, FWCI y % Top 10%.
    Soporta agregaciones específicas por autor (author_id o author_name) e institución (institution_ror).
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

    where_clauses = []
    if author_id:
        clean_aid = author_id.strip()
        if not clean_aid.startswith("http"):
            uri_aid = f"https://openalex.org/{clean_aid}"
        else:
            uri_aid = clean_aid
            clean_aid = clean_aid.replace("https://openalex.org/", "")
        where_clauses.append(f"(has(author_names, '{uri_aid}') OR has(author_names, '{clean_aid}'))")
    elif author_name:
        clean_a = author_name.replace("'", "\\'").strip()
        resolved_ids = []
        try:
            res_ids = client.query(f"SELECT id FROM rag.authors_seed_mexico WHERE positionCaseInsensitiveUTF8(display_name, '{clean_a}') > 0 LIMIT 10")
            for r_id in res_ids.result_rows:
                resolved_ids.append(r_id[0])
        except Exception:
            pass
        sub_conds = []
        for aid in resolved_ids:
            clean_short = aid.replace("https://openalex.org/", "")
            sub_conds.append(f"has(author_names, '{aid}')")
            sub_conds.append(f"has(author_names, '{clean_short}')")
        sub_conds.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_a}') > 0, author_names)")
        where_clauses.append(f"({' OR '.join(sub_conds)})")

    if institution_ror:
        clean_ror = institution_ror.replace("https://ror.org/", "").strip()
        where_clauses.append(f"(has(institution_rors, '{clean_ror}') OR has(institution_rors, 'https://ror.org/{clean_ror}'))")

    if filter_param and filter_param.strip() != "1=1":
        import re
        fp = filter_param.strip()
        if "author_id" in fp and "has(" not in fp:
            m = re.search(r"author_id\s*=\s*'([^']+)'", fp)
            if m:
                aid_val = m.group(1).replace("https://openalex.org/", "")
                fp = fp.replace(m.group(0), f"(has(author_names, 'https://openalex.org/{aid_val}') OR has(author_names, '{aid_val}'))")
        if "author_name" in fp and "arrayExists" not in fp:
            m = re.search(r"author_name\s*=\s*'([^']+)'", fp)
            if m:
                aname_val = m.group(1).replace("'", "\\'")
                fp = fp.replace(m.group(0), f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{aname_val}') > 0, author_names)")
        where_clauses.append(fp)

    if not where_clauses:
        where_clauses = ["1=1"]

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


def _resolve_institutions_metadata(client, inst_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """Resuelve metadatos canónicos (openalex_id y ror) para una lista de nombres de instituciones."""
    inst_meta = {}
    if not inst_names:
        return inst_meta

    escaped_names = [n.replace("'", "\\'") for n in inst_names if n]
    if not escaped_names:
        return inst_meta

    in_clause = ", ".join(f"'{n}'" for n in set(escaped_names))
    sql_inst = f"""
    SELECT display_name, any(id), any(ror)
    FROM rag.institutions_seed_mexico
    WHERE display_name IN ({in_clause})
    GROUP BY display_name
    """
    sanitize_no_joins(sql_inst)
    try:
        res_seed = client.query(sql_inst)
        for sr in res_seed.result_rows:
            ror_val = sr[2] if (sr[2] and str(sr[2]).startswith("http")) else f"https://ror.org/{sr[2]}" if sr[2] else None
            inst_meta[sr[0]] = {
                "openalex_id": sr[1],
                "ror": ror_val
            }
    except Exception:
        pass

    missing = [n for n in inst_names if n and n not in inst_meta]
    for m in missing:
        clean_m = m.replace("'", "\\'")
        try:
            sql_alt = f"""
            SELECT any(id), any(ror)
            FROM rag.institutions_seed_mexico
            WHERE positionCaseInsensitiveUTF8(raw_data, '{clean_m}') > 0
            LIMIT 1
            """
            sanitize_no_joins(sql_alt)
            res_alt = client.query(sql_alt)
            if res_alt.result_rows and res_alt.result_rows[0][0]:
                sr_id, sr_ror = res_alt.result_rows[0]
                ror_val = sr_ror if (sr_ror and str(sr_ror).startswith("http")) else f"https://ror.org/{sr_ror}" if sr_ror else None
                inst_meta[m] = {
                    "openalex_id": sr_id,
                    "ror": ror_val
                }
        except Exception:
            pass

    return inst_meta


def _resolve_authors_metadata(client, author_keys: List[str]) -> Dict[str, Dict[str, Any]]:
    """Resuelve display_name real, openalex_id y últimas 2 instituciones para una lista de autores."""
    author_meta = {}
    if not author_keys:
        return author_meta

    id_keys = []
    name_variants_map = {}

    for key in author_keys:
        if not key:
            continue
        if key.startswith("http"):
            id_keys.append(key)
        else:
            name_variants_map[key] = key
            if "," in key:
                parts = [p.strip() for p in key.split(",") if p.strip()]
                if len(parts) == 2:
                    inverted = f"{parts[1]} {parts[0]}"
                    name_variants_map[inverted] = key

    # 1. Lookup por ID en authors_seed_mexico
    if id_keys:
        esc_ids = [i.replace("'", "\\'") for i in set(id_keys)]
        in_clause = ", ".join(f"'{i}'" for i in esc_ids)
        sql_ids = f"""
        SELECT id, any(display_name),
               arraySlice(
                   arrayFilter(x -> length(x) > 0,
                       arrayMap(i -> JSONExtractString(i, 'display_name'),
                           JSONExtractArrayRaw(any(raw_data), 'last_known_institutions')
                       )
                   ),
                   1, 2
               ) as insts
        FROM rag.authors_seed_mexico
        WHERE id IN ({in_clause})
        GROUP BY id
        """
        sanitize_no_joins(sql_ids)
        try:
            res_id = client.query(sql_ids)
            for sr in res_id.result_rows:
                author_meta[sr[0]] = {
                    "display_name": sr[1] if sr[1] else sr[0],
                    "openalex_id": sr[0],
                    "last_known_institutions": list(sr[2]) if sr[2] else []
                }
        except Exception:
            pass

    # 2. Lookup por Nombre en authors_seed_mexico
    if name_variants_map:
        esc_names = [n.replace("'", "\\'") for n in set(name_variants_map.keys())]
        in_names = ", ".join(f"'{n}'" for n in esc_names)
        sql_names = f"""
        SELECT any(id), display_name,
               arraySlice(
                   arrayFilter(x -> length(x) > 0,
                       arrayMap(i -> JSONExtractString(i, 'display_name'),
                           JSONExtractArrayRaw(any(raw_data), 'last_known_institutions')
                       )
                   ),
                   1, 2
               ) as insts
        FROM rag.authors_seed_mexico
        WHERE display_name IN ({in_names})
        GROUP BY display_name
        """
        sanitize_no_joins(sql_names)
        try:
            res_names = client.query(sql_names)
            for sr in res_names.result_rows:
                raw_key = name_variants_map.get(sr[1])
                if raw_key and raw_key not in author_meta:
                    author_meta[raw_key] = {
                        "display_name": sr[1],
                        "openalex_id": sr[0],
                        "last_known_institutions": list(sr[2]) if sr[2] else []
                    }
        except Exception:
            pass

    # 3. Fallback a academics_all para IDs o nombres no resueltos
    unresolved_ids = [k for k in id_keys if k not in author_meta]
    if unresolved_ids:
        esc_u_ids = [i.replace("'", "\\'") for i in set(unresolved_ids)]
        in_u_ids = ", ".join(f"'{i}'" for i in esc_u_ids)
        sql_acad = f"""
        SELECT id, any(name), any(institution), any(dependency)
        FROM rag.academics_all
        WHERE id IN ({in_u_ids})
        GROUP BY id
        """
        sanitize_no_joins(sql_acad)
        try:
            res_acad = client.query(sql_acad)
            for ar in res_acad.result_rows:
                insts = [i for i in [ar[2], ar[3]] if i][:2]
                author_meta[ar[0]] = {
                    "display_name": ar[1] if ar[1] else ar[0],
                    "openalex_id": ar[0],
                    "last_known_institutions": insts
                }
        except Exception:
            pass

    return author_meta


def openalex_top_entities(
    query: str,
    by: str = "institutions",
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Clasifica las instituciones o autores líderes en un tema o subcampo dentro de México,
    calculando volumen de papers, citas acumuladas, promedio de FWCI, porcentaje en el Top 10% y Top 1%.
    Búsqueda exhaustiva en título, subcampo, tópico y palabras clave (keywords).
    Devuelve para instituciones: openalex_id, ror y métricas (incluyendo pct_top_10 y pct_top_1).
    Devuelve para autores: display_name resuelto, openalex_id, las últimas 2 afiliaciones conocidas y métricas (incluyendo pct_top_10 y pct_top_1).
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "top_entities": []}

    by_clean = by.lower().strip()
    if by_clean not in ("institutions", "authors"):
        return {"status": "error", "message": "Parámetro 'by' debe ser 'institutions' o 'authors'", "top_entities": []}

    clean_q = query.replace("'", "\\'")
    where_clauses = [
        f"(positionCaseInsensitiveUTF8(title, '{clean_q}') > 0 "
        f"OR positionCaseInsensitiveUTF8(subfield, '{clean_q}') > 0 "
        f"OR positionCaseInsensitiveUTF8(topic, '{clean_q}') > 0 "
        f"OR arrayExists(k -> positionCaseInsensitiveUTF8(k, '{clean_q}') > 0, keywords))"
    ]
    if year_min is not None:
        where_clauses.append(f"publication_year >= {int(year_min)}")
    if year_max is not None:
        where_clauses.append(f"publication_year <= {int(year_max)}")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    limit_val = min(max(limit, 1), 50)

    try:
        if by_clean == "institutions":
            sql = f"""
            SELECT
                inst_name AS entity_name,
                count(*) AS total_works,
                sum(cited_by_count) AS total_citations,
                round(avg(fwci), 3) AS avg_fwci,
                round(avg(is_top_10) * 100, 2) AS pct_top_10,
                round(avg(is_top_1) * 100, 2) AS pct_top_1
            FROM rag.works_academic_all
            ARRAY JOIN institution_names AS inst_name
            WHERE {where_sql} AND inst_name != ''
            GROUP BY inst_name
            ORDER BY total_works DESC
            LIMIT {limit_val}
            """
            sanitize_no_joins(sql)
            res = client.query(sql)
            raw_rows = res.result_rows

            inst_meta = _resolve_institutions_metadata(client, [r[0] for r in raw_rows if r[0]])
            seen_ids = set()
            seen_names = set()
            entities = []
            for r in raw_rows:
                name = r[0]
                meta = inst_meta.get(name, {})
                inst_id = meta.get("openalex_id")
                norm_name = _normalize_entity_key(name)
                if inst_id and inst_id in seen_ids:
                    continue
                if norm_name and norm_name in seen_names:
                    continue
                if inst_id:
                    seen_ids.add(inst_id)
                if norm_name:
                    seen_names.add(norm_name)

                entities.append({
                    "rank": len(entities) + 1,
                    "display_name": name,
                    "openalex_id": inst_id,
                    "ror": meta.get("ror"),
                    "total_works": r[1],
                    "total_citations": r[2],
                    "avg_fwci": r[3],
                    "pct_top_10": r[4],
                    "pct_top_1": r[5]
                })
                if len(entities) >= limit_val:
                    break
        else:
            sql = f"""
            SELECT
                auth_name AS entity_name,
                count(*) AS total_works,
                sum(cited_by_count) AS total_citations,
                round(avg(fwci), 3) AS avg_fwci,
                round(avg(is_top_10) * 100, 2) AS pct_top_10,
                round(avg(is_top_1) * 100, 2) AS pct_top_1
            FROM rag.works_academic_all
            ARRAY JOIN author_names AS auth_name
            WHERE {where_sql} AND auth_name != ''
            GROUP BY auth_name
            ORDER BY total_works DESC
            LIMIT {min(limit_val * 2, 100)}
            """
            sanitize_no_joins(sql)
            res = client.query(sql)
            raw_rows = res.result_rows

            author_meta = _resolve_authors_metadata(client, [r[0] for r in raw_rows if r[0]])
            seen_ids = set()
            seen_names = set()
            entities = []
            for r in raw_rows:
                key = r[0]
                meta = author_meta.get(key, {})
                display_name = meta.get("display_name") or key
                openalex_id = meta.get("openalex_id") or (key if key.startswith("http") else None)
                norm_name = _normalize_entity_key(display_name)
                if openalex_id and openalex_id in seen_ids:
                    continue
                if norm_name and norm_name in seen_names:
                    continue
                if openalex_id:
                    seen_ids.add(openalex_id)
                if norm_name:
                    seen_names.add(norm_name)

                last_known_institutions = meta.get("last_known_institutions") or []
                entities.append({
                    "rank": len(entities) + 1,
                    "display_name": display_name,
                    "openalex_id": openalex_id,
                    "last_known_institutions": last_known_institutions,
                    "total_works": r[1],
                    "total_citations": r[2],
                    "avg_fwci": r[3],
                    "pct_top_10": r[4],
                    "pct_top_1": r[5]
                })
                if len(entities) >= limit_val:
                    break

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
    year_max: Optional[int] = None,
    oa_status: Optional[str] = None,
    limit: int = 15
) -> Dict[str, Any]:
    """
    Búsqueda semántica conceptual mediante embeddings locales Nomic (768d) y similitud coseno
    sobre 1.37M publicaciones en rag.works_academic_all en ClickHouse.
    Permite descubrir trabajos, instituciones líderes o autores más activos en un concepto o nicho científico.
    target puede ser 'works', 'institutions' o 'authors'.
    Para instituciones y autores devuelve métricas completas: volumen, citas, fwci, pct_top_10, pct_top_1,
    similitud semántica, openalex_id, ror y últimas afiliaciones conocidas.
    """
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible", "results": [], "top_entities": []}

    target_clean = target.lower().strip()
    if target_clean not in ("works", "institutions", "authors"):
        return {"status": "error", "message": "Parámetro target debe ser 'works', 'institutions' o 'authors'", "results": [], "top_entities": []}

    try:
        query_vec = get_text_embedding(query)
    except Exception as e:
        return {"status": "error", "message": f"Error generando embedding conceptual: {str(e)}", "results": [], "top_entities": []}

    vec_str = str(query_vec)
    limit_val = min(max(limit, 1), 50)

    where_clauses = ["length(embedding_nomic) = 768", "title != ''"]
    if year_min is not None:
        where_clauses.append(f"publication_year >= {int(year_min)}")
    if year_max is not None:
        where_clauses.append(f"publication_year <= {int(year_max)}")
    if oa_status:
        where_clauses.append(f"lower(oa_status) = '{oa_status.lower().strip()}'")
    if institution_name:
        clean_inst = institution_name.replace("'", "\\'")
        where_clauses.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_inst}') > 0, institution_names)")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    try:
        if target_clean == "works":
            sql = f"""
            SELECT
                id,
                title,
                any(publication_year) as year,
                max(cited_by_count) as citations,
                any(oa_status) as oa,
                any(fwci) as fwci_val,
                any(is_top_10) as top10,
                any(is_top_1) as top1,
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
            sanitize_no_joins(sql)
            res = client.query(sql)

            # Resolver nombres legibles de autores para las publicaciones devueltas
            all_author_keys = []
            for r in res.result_rows:
                if r[8]:
                    all_author_keys.extend(r[8])
            auth_meta = _resolve_authors_metadata(client, all_author_keys) if all_author_keys else {}

            results = []
            for r in res.result_rows:
                dist = float(r[11])
                raw_authors = r[8] or []
                resolved_authors = [
                    auth_meta.get(a, {}).get("display_name") or a
                    for a in raw_authors
                ]
                results.append({
                    "id": r[0],
                    "title": r[1],
                    "publication_year": r[2],
                    "cited_by_count": r[3],
                    "oa_status": r[4],
                    "fwci": round(float(r[5]), 3) if r[5] is not None else None,
                    "is_top_10": bool(r[6] == 1),
                    "is_top_1": bool(r[7] == 1),
                    "author_names": resolved_authors,
                    "institution_names": r[9] or [],
                    "subfield": r[10],
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

        elif target_clean == "institutions":
            sql = f"""
            WITH top_works AS (
                SELECT id, cited_by_count, fwci, is_top_10, is_top_1, institution_names, cosineDistance(embedding_nomic, {vec_str}) as dist
                FROM rag.works_academic_all
                WHERE {where_sql}
                ORDER BY dist ASC
                LIMIT 300
            )
            SELECT 
                inst_name AS entity_name,
                count(*) AS total_works,
                sum(cited_by_count) AS total_citations,
                round(avg(fwci), 3) AS avg_fwci,
                round(avg(is_top_10) * 100, 2) AS pct_top_10,
                round(avg(is_top_1) * 100, 2) AS pct_top_1,
                round(avg(dist), 4) AS avg_cosine_dist,
                round(1.0 - avg(dist), 4) AS avg_semantic_similarity
            FROM top_works
            ARRAY JOIN institution_names AS inst_name
            WHERE inst_name != ''
            GROUP BY inst_name
            ORDER BY total_works DESC, avg_semantic_similarity DESC
            LIMIT {min(limit_val * 2, 100)}
            """
            sanitize_no_joins(sql)
            res = client.query(sql)
            raw_rows = res.result_rows

            inst_meta = _resolve_institutions_metadata(client, [r[0] for r in raw_rows if r[0]])
            seen_ids = set()
            seen_names = set()
            entities = []
            for r in raw_rows:
                name = r[0]
                meta = inst_meta.get(name, {})
                inst_id = meta.get("openalex_id")
                norm_name = _normalize_entity_key(name)
                if inst_id and inst_id in seen_ids:
                    continue
                if norm_name and norm_name in seen_names:
                    continue
                if inst_id:
                    seen_ids.add(inst_id)
                if norm_name:
                    seen_names.add(norm_name)

                entities.append({
                    "rank": len(entities) + 1,
                    "display_name": name,
                    "openalex_id": inst_id,
                    "ror": meta.get("ror"),
                    "total_works": r[1],
                    "total_citations": r[2],
                    "avg_fwci": r[3],
                    "pct_top_10": r[4],
                    "pct_top_1": r[5],
                    "avg_cosine_distance": r[6],
                    "avg_semantic_similarity": r[7]
                })
                if len(entities) >= limit_val:
                    break

            return {
                "status": "success",
                "query": query,
                "target": "institutions",
                "embedding_model": settings.embedding_model,
                "total_entities": len(entities),
                "top_entities": entities
            }

        else:  # target_clean == "authors"
            sql = f"""
            WITH top_works AS (
                SELECT id, cited_by_count, fwci, is_top_10, is_top_1, author_names, cosineDistance(embedding_nomic, {vec_str}) as dist
                FROM rag.works_academic_all
                WHERE {where_sql}
                ORDER BY dist ASC
                LIMIT 300
            )
            SELECT 
                auth_name AS entity_name,
                count(*) AS total_works,
                sum(cited_by_count) AS total_citations,
                round(avg(fwci), 3) AS avg_fwci,
                round(avg(is_top_10) * 100, 2) AS pct_top_10,
                round(avg(is_top_1) * 100, 2) AS pct_top_1,
                round(avg(dist), 4) AS avg_cosine_dist,
                round(1.0 - avg(dist), 4) AS avg_semantic_similarity
            FROM top_works
            ARRAY JOIN author_names AS auth_name
            WHERE auth_name != ''
            GROUP BY auth_name
            ORDER BY total_works DESC, avg_semantic_similarity DESC
            LIMIT {min(limit_val * 2, 100)}
            """
            sanitize_no_joins(sql)
            res = client.query(sql)
            raw_rows = res.result_rows

            author_meta = _resolve_authors_metadata(client, [r[0] for r in raw_rows if r[0]])
            seen_ids = set()
            seen_names = set()
            entities = []
            for r in raw_rows:
                key = r[0]
                meta = author_meta.get(key, {})
                display_name = meta.get("display_name") or key
                openalex_id = meta.get("openalex_id") or (key if key.startswith("http") else None)
                norm_name = _normalize_entity_key(display_name)
                if openalex_id and openalex_id in seen_ids:
                    continue
                if norm_name and norm_name in seen_names:
                    continue
                if openalex_id:
                    seen_ids.add(openalex_id)
                if norm_name:
                    seen_names.add(norm_name)

                last_known_institutions = meta.get("last_known_institutions") or []
                entities.append({
                    "rank": len(entities) + 1,
                    "display_name": display_name,
                    "openalex_id": openalex_id,
                    "last_known_institutions": last_known_institutions,
                    "total_works": r[1],
                    "total_citations": r[2],
                    "avg_fwci": r[3],
                    "pct_top_10": r[4],
                    "pct_top_1": r[5],
                    "avg_cosine_distance": r[6],
                    "avg_semantic_similarity": r[7]
                })
                if len(entities) >= limit_val:
                    break

            return {
                "status": "success",
                "query": query,
                "target": "authors",
                "embedding_model": settings.embedding_model,
                "total_entities": len(entities),
                "top_entities": entities
            }

    except Exception as e:
        return {"status": "error", "message": str(e), "results": [], "top_entities": []}


def openalex_run_select_query(query: str, limit: int = 50) -> Dict[str, Any]:
    """
    Ejecuta una consulta SQL SELECT directa sobre la base de datos ClickHouse (rag).
    Aplica verificación estricta de CERO JOINs para garantizar la integridad y rendimiento.
    """
    return execute_safe_query(query=query, limit=limit)
