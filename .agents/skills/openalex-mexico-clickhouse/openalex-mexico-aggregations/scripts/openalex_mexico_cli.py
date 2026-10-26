#!/usr/bin/env python3
"""
CLI Helper: OpenAlex México ClickHouse Engine
Motor analítico para la consulta y extracción de la producción científica mexicana en ClickHouse.
Tablas materializadas consultadas:
- rag.works_academic_all (~1.65M publicaciones de México con FWCI, APC, OA, ODS y embeddings nomic de 768d)
- rag.authors_seed_mexico (2.57M autores vinculados a México con métricas e instituciones)
- rag.academics_all (431K investigadoras/es con padrón y dependencias)
- rag.institutions_seed_mexico (456K instituciones con ROR y acrónimos)

Regla de oro: PROHIBICIÓN ESTRICTA DE JOINs EN CLICKHOUSE.
Requisitos: Python >= 3.10, clickhouse-connect
"""

import sys
import os
import json
import argparse
import re
import unicodedata
from typing import Dict, List, Any, Optional

try:
    import clickhouse_connect
except ImportError:
    print("Error: clickhouse-connect no instalado en el entorno. Instálelo con: pip install clickhouse-connect", file=sys.stderr)
    sys.exit(1)


def get_clickhouse_client():
    """Obtiene un cliente ClickHouse conectado al host local/remoto configurado."""
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
            connect_timeout=4,
            send_receive_timeout=30
        )
    except Exception as e:
        print(f"Error al conectar con ClickHouse ({host}:{port}): {e}", file=sys.stderr)
        return None


def sanitize_no_joins(sql: str) -> bool:
    """Verifica que la consulta no contenga sentencias JOIN prohibidas."""
    if re.search(r"\bjoin\b", sql, re.IGNORECASE):
        raise ValueError(
            "Violación de política de datos: Las sentencias JOIN están estrictamente prohibidas en ClickHouse. "
            "Utilice las tablas materializadas precalculadas (rag.works_academic_all, rag.authors_seed_mexico) "
            "o filtros directos por arrays."
        )
    return True


def _normalize_entity_key(s: str) -> str:
    """Normaliza cadenas eliminando acentos, puntuación y mayúsculas para deduplicación segura."""
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower().replace("-", " ").replace(",", "").replace(".", "").strip()


def _resolve_institutions_metadata(client, inst_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """Resuelve metadatos canónicos (openalex_id y ror) para una lista de nombres de instituciones."""
    inst_meta = {}
    if not inst_names:
        return inst_meta

    escaped_names = [n.replace("'", "\'") for n in inst_names if n]
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
        clean_m = m.replace("'", "\'")
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
        esc_ids = [i.replace("'", "\'") for i in set(id_keys)]
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
        esc_names = [n.replace("'", "\'") for n in set(name_variants_map.keys())]
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
        esc_u_ids = [i.replace("'", "\'") for i in set(unresolved_ids)]
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
    import urllib.request
    import urllib.error

    clean_text = text.strip()
    if not clean_text:
        raise ValueError("El texto para generar embeddings no puede estar vacío.")

    candidate_urls = []
    env_url = os.getenv("LM_STUDIO_URL", os.getenv("EMBEDDING_API_BASE"))
    if env_url:
        candidate_urls.append(env_url)
    candidate_urls.extend([
        "http://127.0.0.1:1234/v1/embeddings",
        "http://172.17.0.1:1234/v1/embeddings"
    ])

    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-nomic-ai-nomic-embed-text-v2-moe")
    api_key = os.getenv("LM_STUDIO_API_KEY", "sk-lm-911DBjzu:mnU3kI7Zj5dGgX8mzxyj")
    payload = json.dumps({"model": model_name, "input": clean_text}).encode("utf-8")

    last_err = None
    for url in candidate_urls:
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["data"][0]["embedding"]
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"No fue posible conectar con el servidor de embeddings local en LM Studio: {last_err}")


def resolve_authors_for_works(works_list: List[Dict[str, Any]], client) -> None:
    """
    Resuelve los IDs de OpenAlex a nombres legibles y desambigua
    entre investigadoras/es con filiación en México y colaboradores internacionales.
    Cumple estrictamente con la regla de CERO JOINs usando un batch SELECT ... IN (...).
    """
    all_author_ids = set()
    for w in works_list:
        for a in w.get("raw_author_names", []):
            if isinstance(a, str) and a.startswith("https://openalex.org/A"):
                all_author_ids.add(a)

    resolved_info = {}
    if all_author_ids:
        id_list = list(all_author_ids)
        batch_size = 500
        for i in range(0, len(id_list), batch_size):
            chunk = id_list[i:i+batch_size]
            ids_sql = ",".join([f"'{aid}'" for aid in chunk])
            sql = f"""
            SELECT id, any(display_name), any(orcid),
                   any(JSONExtractString(raw_data, 'last_known_institutions', 1, 'display_name')) as inst,
                   any(JSONExtractString(raw_data, 'last_known_institutions', 1, 'country_code')) as country
            FROM rag.authors_seed_mexico
            WHERE id IN ({ids_sql})
            GROUP BY id
            """
            res = client.query(sql)
            for r in res.result_rows:
                resolved_info[r[0]] = {
                    "name": r[1],
                    "orcid": r[2],
                    "institution": r[3],
                    "country": r[4] or "MX"
                }

    for w in works_list:
        raw_authors = w.get("raw_author_names", [])
        mexican_authors = []
        international_authors = []
        all_display = []

        for a in raw_authors:
            if isinstance(a, str) and a.startswith("https://openalex.org/A"):
                if a in resolved_info:
                    info = resolved_info[a]
                    author_obj = {
                        "name": info["name"],
                        "orcid": info["orcid"],
                        "institution": info["institution"],
                        "country": info["country"]
                    }
                    all_display.append(info["name"])
                    if (info.get("country") or "").upper() == "MX":
                        mexican_authors.append(author_obj)
                    else:
                        international_authors.append(author_obj)
                else:
                    all_display.append(a)
            else:
                all_display.append(a)
                mexican_authors.append({"name": a, "affiliation_type": "listed_author"})

        w["author_names"] = all_display
        w["authors_disambiguated"] = {
            "mexican_affiliated_authors": mexican_authors,
            "international_collaborators": international_authors
        }
        w.pop("raw_author_names", None)


def cmd_search_authors(args):
    """Busca autores e investigadores de México en rag.authors_seed_mexico y rag.academics_all."""
    client = get_clickhouse_client()
    if client is None:
        sys.exit(1)

    limit = min(args.limit or 50, 1000)
    name_str = args.name.strip() if args.name else ""
    permutations = generate_hispanic_name_permutations(name_str) if name_str else []

    authors = []
    seen_ids = set()

    # Si se pide nivel SNII explícito, buscar en academics_all
    if args.snii_level or args.dependency:
        where_clauses = ["1=1"]
        if name_str:
            sub_conds = [f"positionCaseInsensitiveUTF8(name, '{p}') > 0" for p in permutations[:4]]
            where_clauses.append(f"({' OR '.join(sub_conds)})")
        if args.snii_level:
            where_clauses.append(f"positionCaseInsensitiveUTF8(snii_level, '{args.snii_level.strip()}') > 0")
        if args.dependency:
            where_clauses.append(f"positionCaseInsensitiveUTF8(dependency, '{args.dependency.strip()}') > 0")
        where_sql = " AND ".join(where_clauses)
        sanitize_no_joins(where_sql)

        sql_acad = f"""
        SELECT id, name, institution, dependency, subdependency, snii_level, orcid, paper_count, citation_count
        FROM rag.academics_all
        WHERE {where_sql}
        ORDER BY citation_count DESC
        LIMIT {limit}
        """
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

    # Consulta principal sobre la semilla masiva de México (authors_seed_mexico)
    if len(authors) < limit:
        where_seed = ["1=1"]
        if name_str:
            sub_conds = [f"positionCaseInsensitiveUTF8(display_name, '{p}') > 0" for p in permutations[:4]]
            where_seed.append(f"({' OR '.join(sub_conds)})")
        if args.institution:
            clean_inst = args.institution.replace("'", "\\'")
            where_seed.append(f"positionCaseInsensitiveUTF8(raw_data, '{clean_inst}') > 0")
        if args.orcid:
            clean_orcid = args.orcid.replace("https://orcid.org/", "").strip()
            where_seed.append(f"position(orcid, '{clean_orcid}') > 0")

        where_sql_seed = " AND ".join(where_seed)
        sanitize_no_joins(where_sql_seed)

        needed = limit - len(authors)
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

    distinct_ids = set(a.get("id") for a in authors if a.get("id"))
    distinct_names = set(_normalize_entity_key(a.get("display_name", "")) for a in authors if a.get("display_name"))
    distinct_count = max(len(distinct_ids), len(distinct_names)) if authors else 0
    disambiguation_required = distinct_count > 1

    output_data = {
        "status": "success",
        "query_name": name_str,
        "filters": {
            "institution": args.institution,
            "dependency": args.dependency,
            "snii_level": args.snii_level,
            "orcid": args.orcid
        },
        "total_returned": len(authors),
        "distinct_count": distinct_count,
        "disambiguation_required": disambiguation_required,
        "authors": authors
    }
    if disambiguation_required:
        output_data["instruction_for_agent"] = (
            f"Se encontraron {distinct_count} autores coincidentes u homónimos. "
            "EVALUACIÓN: Si la consulta del usuario coincide inequívocamente con uno de ellos (o si el usuario ya especificó institución, área temática u ORCID), "
            "puedes decidir proceder directamente con el análisis de ese autor sin frenar. "
            "Solo si existen múltiples candidatos verdaderamente distintos (homónimos en diferentes disciplinas o instituciones) "
            "y no es claro a cuál se refiere el usuario, presenta la lista numerada y solicita confirmación antes de buscar sus obras."
        )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Búsqueda de autores en México completada: {len(authors)} registros guardados en {args.output}")
    sys.exit(0)


def cmd_search_works(args):
    """Busca publicaciones en rag.works_academic_all (1.65M de trabajos con México)."""
    client = get_clickhouse_client()
    if client is None:
        sys.exit(1)

    where_clauses = ["1=1"]

    if args.query:
        clean_q = args.query.replace("'", "\\'")
        where_clauses.append(f"positionCaseInsensitiveUTF8(title, '{clean_q}') > 0")
    if args.author_name:
        clean_a = args.author_name.replace("'", "\\'")
        where_clauses.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_a}') > 0, author_names)")
    if args.institution_name:
        clean_inst = args.institution_name.replace("'", "\\'")
        where_clauses.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_inst}') > 0, institution_names)")
    if args.institution_ror:
        clean_ror = args.institution_ror.replace("https://ror.org/", "").strip()
        where_clauses.append(f"(has(institution_rors, '{clean_ror}') OR has(institution_rors, 'https://ror.org/{clean_ror}'))")
    if args.year_min:
        where_clauses.append(f"publication_year >= {int(args.year_min)}")
    if args.year_max:
        where_clauses.append(f"publication_year <= {int(args.year_max)}")
    if args.oa_status:
        where_clauses.append(f"lower(oa_status) = '{args.oa_status.lower()}'")
    if args.is_top_10 is not None:
        val = 1 if str(args.is_top_10).lower() in ("true", "1") else 0
        where_clauses.append(f"is_top_10 = {val}")
    if args.topic:
        clean_top = args.topic.replace("'", "\\'")
        where_clauses.append(f"positionCaseInsensitiveUTF8(topic, '{clean_top}') > 0")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    limit = min(args.limit or 100, 50000)
    sql = f"""
    SELECT id, title, doi, any(publication_year), max(cited_by_count), any(oa_status), any(is_oa),
           any(fwci), any(percentile), any(is_top_10), any(is_top_1), any(apc_paid_usd),
           any(author_names), any(institution_names), any(institution_rors), any(topic), any(subfield)
    FROM rag.works_academic_all
    WHERE {where_sql}
    GROUP BY id, title, doi
    ORDER BY max(cited_by_count) DESC, any(publication_year) DESC
    LIMIT {limit}
    """

    res = client.query(sql)
    works = []
    for row in res.result_rows:
        works.append({
            "id": row[0],
            "title": row[1],
            "doi": row[2],
            "publication_year": row[3],
            "cited_by_count": row[4],
            "oa_status": row[5],
            "is_oa": bool(row[6] == "1" or row[6] == 1 or str(row[6]).lower() == "true"),
            "fwci": round(row[7], 3) if row[7] is not None else None,
            "percentile": round(row[8], 2) if row[8] is not None else None,
            "is_top_10": bool(row[9] == 1),
            "is_top_1": bool(row[10] == 1),
            "apc_paid_usd": round(row[11], 2) if row[11] is not None else 0.0,
            "raw_author_names": row[12],
            "institution_names": row[13],
            "institution_rors": row[14],
            "topic": row[15],
            "subfield": row[16]
        })

    # Desambiguar y resolver autores de México vs internacionales
    resolve_authors_for_works(works, client)

    output_data = {
        "filters": {
            "query": args.query,
            "author_name": args.author_name,
            "institution_name": args.institution_name,
            "institution_ror": args.institution_ror,
            "year_range": f"{args.year_min}-{args.year_max}",
            "oa_status": args.oa_status,
            "is_top_10": args.is_top_10,
            "topic": args.topic
        },
        "limit": limit,
        "total_returned": len(works),
        "works": works
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Búsqueda de publicaciones en México completada: {len(works)} trabajos guardados en {args.output}")
    sys.exit(0)


def cmd_top_entities(args):
    """Identifica las entidades (autores o instituciones) con mayor capacidad en un tema o disciplina."""
    client = get_clickhouse_client()
    if client is None:
        sys.exit(1)

    query_str = args.query.replace("'", "\'").strip()
    limit = min(args.limit or 20, 200)

    where_clauses = ["1=1"]
    if query_str:
        where_clauses.append(
            f"(positionCaseInsensitiveUTF8(title, '{query_str}') > 0 "
            f"OR positionCaseInsensitiveUTF8(topic, '{query_str}') > 0 "
            f"OR positionCaseInsensitiveUTF8(subfield, '{query_str}') > 0 "
            f""
            f"OR arrayExists(k -> positionCaseInsensitiveUTF8(k, '{query_str}') > 0, keywords))"
        )
    if args.year_min:
        where_clauses.append(f"publication_year >= {int(args.year_min)}")
    if args.year_max:
        where_clauses.append(f"publication_year <= {int(args.year_max)}")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    entities = []

    if args.by == "institutions":
        sql = f"""
        SELECT
            inst,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 2) AS avg_fwci,
            round(avg(is_top_10) * 100, 2) AS pct_top_10,
            round(avg(is_top_1) * 100, 2) AS pct_top_1,
            round(sum(apc_paid_usd), 2) AS total_apc_paid_usd
        FROM rag.works_academic_all
        ARRAY JOIN institution_names AS inst
        WHERE {where_sql}
          AND inst != ''
        GROUP BY inst
        ORDER BY total_works DESC
        LIMIT {limit * 2}
        """
        res = client.query(sql)
        raw_rows = res.result_rows
        inst_meta = _resolve_institutions_metadata(client, [r[0] for r in raw_rows])

        for rank, r in enumerate(raw_rows, 1):
            meta = inst_meta.get(r[0], {})
            entities.append({
                "rank": len(entities) + 1,
                "institution": r[0],
                "openalex_id": meta.get("openalex_id"),
                "ror": meta.get("ror"),
                "total_works": r[1],
                "total_citations": r[2],
                "avg_fwci": r[3],
                "pct_top_10": r[4],
                "pct_top_1": r[5],
                "total_apc_paid_usd": r[6]
            })
            if len(entities) >= limit:
                break

    elif args.by == "authors":
        sql = f"""
        SELECT
            author,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 2) AS avg_fwci,
            round(avg(is_top_10) * 100, 2) AS pct_top_10,
            round(avg(is_top_1) * 100, 2) AS pct_top_1
        FROM rag.works_academic_all
        ARRAY JOIN author_names AS author
        WHERE {where_sql}
          AND author != ''
        GROUP BY author
        ORDER BY total_works DESC
        LIMIT {limit * 3}
        """
        res = client.query(sql)
        raw_rows = res.result_rows

        author_meta = _resolve_authors_metadata(client, [r[0] for r in raw_rows if r[0]])
        seen_ids = set()
        seen_names = set()
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

            entities.append({
                "rank": len(entities) + 1,
                "display_name": display_name,
                "openalex_id": openalex_id,
                "last_known_institutions": meta.get("last_known_institutions") or [],
                "total_works": r[1],
                "total_citations": r[2],
                "avg_fwci": r[3],
                "pct_top_10": r[4],
                "pct_top_1": r[5]
            })
            if len(entities) >= limit:
                break

    output_data = {
        "status": "success",
        "query": args.query,
        "by": args.by,
        "year_range": f"{args.year_min or 'all'}-{args.year_max or 'all'}",
        "total_entities": len(entities),
        "top_entities": entities
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Top {len(entities)} {args.by} en '{args.query}' guardado exitosamente en {args.output}")
    sys.exit(0)

def cmd_semantic_search(args):
    """Búsqueda semántica usando embeddings locales nomic (768d) y similitud coseno en ClickHouse."""
    client = get_clickhouse_client()
    if client is None:
        sys.exit(1)

    query_str = args.query.strip()
    if not query_str:
        print("Error: Se requiere --query para la búsqueda semántica.", file=sys.stderr)
        sys.exit(1)

    print(f"Generando vector de embedding para '{query_str}'...", file=sys.stderr)
    try:
        query_vec = get_text_embedding(query_str)
    except Exception as e:
        print(f"Error generando embedding: {e}", file=sys.stderr)
        sys.exit(1)

    vec_str = str(query_vec)
    limit = min(args.limit or 20, 500)
    target = (args.target or "works").lower().strip()

    where_clauses = ["length(embedding_nomic) = 768", "title != ''"]
    if args.year_min:
        where_clauses.append(f"publication_year >= {int(args.year_min)}")
    if args.year_max:
        where_clauses.append(f"publication_year <= {int(args.year_max)}")
    if args.oa_status:
        where_clauses.append(f"lower(oa_status) = '{args.oa_status.lower()}'")
    if getattr(args, "is_top_10", None) is not None:
        val = 1 if str(args.is_top_10).lower() in ("true", "1") else 0
        where_clauses.append(f"is_top_10 = {val}")
    if getattr(args, "institution_name", None):
        clean_inst = args.institution_name.replace("'", "\'")
        where_clauses.append(f"arrayExists(x -> positionCaseInsensitiveUTF8(x, '{clean_inst}') > 0, institution_names)")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    if target == "works":
        sql = f"""
        SELECT id, title, any(publication_year), max(cited_by_count), any(oa_status), any(is_oa),
               any(fwci), any(percentile), any(is_top_10), any(is_top_1), any(apc_paid_usd),
               any(author_names), any(institution_names), any(institution_rors), any(topic), any(subfield),
               min(cosineDistance(embedding_nomic, {vec_str})) as cosine_dist
        FROM rag.works_academic_all
        WHERE {where_sql}
        GROUP BY id, title
        ORDER BY cosine_dist ASC
        LIMIT {limit}
        """
        res = client.query(sql)
        works = []
        for row in res.result_rows:
            dist = float(row[16])
            similarity = round(1.0 - dist, 4)
            works.append({
                "id": row[0],
                "title": row[1],
                "publication_year": row[2],
                "cited_by_count": row[3],
                "oa_status": row[4],
                "is_oa": bool(row[5] == "1" or row[5] == 1 or str(row[5]).lower() == "true"),
                "fwci": round(row[6], 3) if row[6] is not None else None,
                "percentile": round(row[7], 2) if row[7] is not None else None,
                "is_top_10": bool(row[8] == 1),
                "is_top_1": bool(row[9] == 1),
                "apc_paid_usd": round(row[10], 2) if row[10] is not None else 0.0,
                "raw_author_names": row[11],
                "institution_names": row[12],
                "institution_rors": row[13],
                "topic": row[14],
                "subfield": row[15],
                "cosine_distance": round(dist, 4),
                "semantic_similarity": similarity
            })

        resolve_authors_for_works(works, client)

        output_data = {
            "status": "success",
            "query": query_str,
            "target": "works",
            "model": "text-embedding-nomic-ai-nomic-embed-text-v2-moe (768d)",
            "limit": limit,
            "total_returned": len(works),
            "results": works
        }

    elif target == "institutions":
        sql = f"""
        SELECT
            inst,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 2) AS avg_fwci,
            round(avg(is_top_10) * 100, 2) AS pct_top_10,
            round(avg(is_top_1) * 100, 2) AS pct_top_1,
            round(avg(cosine_dist), 4) AS avg_cosine_dist
        FROM (
            SELECT
                institution_names,
                cited_by_count,
                fwci,
                is_top_10,
                is_top_1,
                cosineDistance(embedding_nomic, {vec_str}) AS cosine_dist
            FROM rag.works_academic_all
            WHERE {where_sql}
            ORDER BY cosine_dist ASC
            LIMIT 500
        )
        ARRAY JOIN institution_names AS inst
        WHERE inst != ''
        GROUP BY inst
        ORDER BY total_works DESC, avg_cosine_dist ASC
        LIMIT {limit * 2}
        """
        res = client.query(sql)
        raw_rows = res.result_rows
        inst_meta = _resolve_institutions_metadata(client, [r[0] for r in raw_rows])

        institutions = []
        for r in raw_rows:
            meta = inst_meta.get(r[0], {})
            sim = round(1.0 - float(r[6]), 4)
            institutions.append({
                "rank": len(institutions) + 1,
                "institution": r[0],
                "openalex_id": meta.get("openalex_id"),
                "ror": meta.get("ror"),
                "total_works": r[1],
                "total_citations": r[2],
                "avg_fwci": r[3],
                "pct_top_10": r[4],
                "pct_top_1": r[5],
                "semantic_similarity": sim
            })
            if len(institutions) >= limit:
                break

        output_data = {
            "status": "success",
            "query": query_str,
            "target": "institutions",
            "model": "text-embedding-nomic-ai-nomic-embed-text-v2-moe (768d)",
            "limit": limit,
            "total_returned": len(institutions),
            "results": institutions,
            "top_entities": institutions
        }

    elif target == "authors":
        sql = f"""
        SELECT
            auth,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 2) AS avg_fwci,
            round(avg(is_top_10) * 100, 2) AS pct_top_10,
            round(avg(is_top_1) * 100, 2) AS pct_top_1,
            round(avg(cosine_dist), 4) AS avg_cosine_dist
        FROM (
            SELECT
                author_names,
                cited_by_count,
                fwci,
                is_top_10,
                is_top_1,
                cosineDistance(embedding_nomic, {vec_str}) AS cosine_dist
            FROM rag.works_academic_all
            WHERE {where_sql}
            ORDER BY cosine_dist ASC
            LIMIT 500
        )
        ARRAY JOIN author_names AS auth
        WHERE auth != ''
        GROUP BY auth
        ORDER BY total_works DESC, avg_cosine_dist ASC
        LIMIT {limit * 3}
        """
        res = client.query(sql)
        raw_rows = res.result_rows

        author_meta = _resolve_authors_metadata(client, [r[0] for r in raw_rows if r[0]])
        seen_ids = set()
        seen_names = set()
        authors = []

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

            sim = round(1.0 - float(r[6]), 4)
            authors.append({
                "rank": len(authors) + 1,
                "display_name": display_name,
                "openalex_id": openalex_id,
                "last_known_institutions": meta.get("last_known_institutions") or [],
                "total_works": r[1],
                "total_citations": r[2],
                "avg_fwci": r[3],
                "pct_top_10": r[4],
                "pct_top_1": r[5],
                "semantic_similarity": sim
            })
            if len(authors) >= limit:
                break

        output_data = {
            "status": "success",
            "query": query_str,
            "target": "authors",
            "model": "text-embedding-nomic-ai-nomic-embed-text-v2-moe (768d)",
            "limit": limit,
            "total_returned": len(authors),
            "results": authors,
            "top_entities": authors
        }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Búsqueda semántica ({target}) completada: {len(output_data['results'])} resultados guardados en {args.output}")
    sys.exit(0)

def cmd_aggregate(args):
    """Ejecuta agregaciones cienciométricas sobre rag.works_academic_all."""
    client = get_clickhouse_client()
    if client is None:
        sys.exit(1)

    group_field = args.group_by
    allowed_groups = [
        "publication_year", "oa_status", "type", "subfield", "field",
        "domain", "is_top_10", "is_top_1", "country_code", "language",
        "topics_hierarchy", "sdg", "sdgs"
    ]
    if group_field not in allowed_groups:
        print(f"Error: group-by debe ser uno de: {', '.join(allowed_groups)}", file=sys.stderr)
        sys.exit(1)

    where_sql = args.filter if args.filter else "1=1"
    sanitize_no_joins(where_sql)

    rows = []
    if group_field in ("topics_hierarchy", "taxonomy"):
        sql = f"""
        SELECT
            domain,
            field,
            subfield,
            topic,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 3) AS avg_fwci
        FROM rag.works_academic_all
        WHERE {where_sql}
          AND domain != '' AND field != '' AND subfield != '' AND topic != ''
        GROUP BY domain, field, subfield, topic
        ORDER BY total_works DESC
        LIMIT 150
        """
        res = client.query(sql)
        for r in res.result_rows:
            rows.append({
                "domain": r[0],
                "field": r[1],
                "subfield": r[2],
                "topic": r[3],
                "total_works": r[4],
                "total_citations": r[5],
                "avg_fwci": r[6]
            })

    elif group_field in ("sdg", "sdgs"):
        sql = f"""
        SELECT
            splitByChar('/', sdg_id)[-1] as sdg_num,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 3) AS avg_fwci
        FROM rag.works_academic_all
        ARRAY JOIN arrayDistinct(arrayConcat(sdgs, sdg_ids)) AS sdg_id
        WHERE {where_sql}
          AND sdg_id != ''
        GROUP BY sdg_num
        ORDER BY toInt32OrZero(sdg_num) ASC
        """
        res = client.query(sql)
        for r in res.result_rows:
            rows.append({
                "dimension": str(r[0]),
                "sdg_num": int(r[0]) if str(r[0]).isdigit() else 0,
                "total_works": r[1],
                "total_citations": r[2],
                "avg_fwci": r[3]
            })

    else:
        sql = f"""
        SELECT
            {group_field} AS dimension,
            count(*) AS total_works,
            sum(cited_by_count) AS total_citations,
            round(avg(fwci), 3) AS avg_fwci,
            round(avg(is_top_10) * 100, 2) AS pct_top_10,
            round(sum(apc_paid_usd), 2) AS total_apc_paid_usd
        FROM rag.works_academic_all
        WHERE {where_sql}
        GROUP BY {group_field}
        ORDER BY total_works DESC
        LIMIT 100
        """
        res = client.query(sql)
        for r in res.result_rows:
            rows.append({
                "dimension": r[0],
                "total_works": r[1],
                "total_citations": r[2],
                "avg_fwci": r[3],
                "pct_top_10": r[4],
                "total_apc_paid_usd": r[5]
            })

    output_data = {
        "grouped_by": group_field,
        "filter": args.filter,
        "total_groups": len(rows),
        "results": rows
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Agregación por '{group_field}' en producción mexicana guardada en {args.output}")
    sys.exit(0)


def cmd_get_institution(args):
    """Consulta el catálogo nacional de instituciones en rag.institutions_seed_mexico."""
    client = get_clickhouse_client()
    if client is None:
        sys.exit(1)

    where_clauses = ["1=1"]

    if args.query:
        clean_q = args.query.replace("'", "\'").strip()
        where_clauses.append(f"positionCaseInsensitiveUTF8(display_name, '{clean_q}') > 0")
    if args.acronym:
        clean_acr = args.acronym.strip().upper()
        where_clauses.append(f"has(acronyms, '{clean_acr}')")
    if args.state:
        clean_st = args.state.replace("'", "\'").strip()
        where_clauses.append(f"positionCaseInsensitiveUTF8(state, '{clean_st}') > 0")
    if args.ror:
        clean_ror = args.ror.replace("https://ror.org/", "").strip()
        where_clauses.append(f"(ror = '{clean_ror}' OR ror = 'https://ror.org/{clean_ror}')")

    where_clauses.append("(country_code = 'MX' OR country_code = '')")

    where_sql = " AND ".join(where_clauses)
    sanitize_no_joins(where_sql)

    limit = min(args.limit or 25, 500)
    sql = f"""
    SELECT id, display_name, ror, type, city, state, acronyms, parent_id, parent_name
    FROM rag.institutions_seed_mexico
    WHERE {where_sql}
    ORDER BY display_name ASC
    LIMIT {limit * 2}
    """

    res = client.query(sql)
    seen_keys = set()
    institutions = []
    for r in res.result_rows:
        inst_id = r[0]
        ror_canonical = r[2] if str(r[2]).startswith("http") else f"https://ror.org/{r[2]}" if r[2] else None
        dedup_key = (inst_id, ror_canonical, _normalize_entity_key(r[1]))
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)
        institutions.append({
            "openalex_id": inst_id,
            "display_name": r[1],
            "ror": ror_canonical,
            "type": r[3],
            "city": r[4],
            "state": r[5],
            "acronyms": r[6] or [],
            "parent_id": r[7],
            "parent_name": r[8]
        })
        if len(institutions) >= limit:
            break

    distinct_rors = set(i["ror"] for i in institutions if i["ror"])
    distinct_names = set(_normalize_entity_key(i["display_name"]) for i in institutions if i.get("display_name"))
    distinct_entities = max(len(distinct_rors), len(distinct_names), len(institutions)) if institutions else 0
    disambiguation_required = distinct_entities > 1

    output_data = {
        "status": "success",
        "filters": {
            "query": args.query,
            "acronym": args.acronym,
            "state": args.state,
            "ror": args.ror
        },
        "total_returned": len(institutions),
        "distinct_entities": distinct_entities,
        "disambiguation_required": disambiguation_required,
        "institutions": institutions
    }
    if disambiguation_required:
        output_data["instruction_for_agent"] = (
            f"Se encontraron {distinct_entities} instituciones o sedes coincidentes. "
            "EVALUACIÓN: Si la consulta del usuario identifica con claridad a una de ellas (o si una es la institución matriz evidente y las demás son sedes o duplicados), "
            "puedes decidir proceder directamente con el análisis usando su ROR u OpenAlex ID sin detenerte. "
            "Solo si existe una ambigüedad genuina sobre cuál institución o sede desea analizar el usuario, "
            "presenta la lista de opciones y pregúntale a cuál se refiere antes de continuar."
        )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Catálogo de instituciones en México: {len(institutions)} registros guardados en {args.output}")
    sys.exit(0)

def cmd_validate_query(args):
    """Valida la sintaxis defensiva de una consulta ClickHouse contra la regla de CERO JOINs."""
    query = args.query.strip()
    is_safe = True
    reason = "Consulta aprobada: cumple con la política de CERO JOINs."

    try:
        sanitize_no_joins(query)
    except ValueError as ve:
        is_safe = False
        reason = str(ve)

    result = {
        "is_safe": is_safe,
        "query": query,
        "reason": reason
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    status_str = "VÁLIDA (Segura)" if is_safe else "RECHAZADA (Infracción de JOIN)"
    print(f"Validación de consulta: {status_str}. Reporte en {args.output}")
    if not is_safe:
        sys.exit(1)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="CLI para OpenAlex México ClickHouse Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando: search-authors
    p_auth = subparsers.add_parser("search-authors", help="Busca investigadoras/es de México en authors_seed_mexico y academics_all")
    p_auth.add_argument("--name", default="", help="Nombre o apellido del autor")
    p_auth.add_argument("--institution", help="Nombre o acrónimo de la institución (ej. UNAM, CINVESTAV)")
    p_auth.add_argument("--dependency", help="Dependencia académica (ej. Facultad de Ciencias)")
    p_auth.add_argument("--snii-level", help="Nivel SNII (Candidato, I, II, III, Emérito)")
    p_auth.add_argument("--orcid", help="ORCID canónico")
    p_auth.add_argument("--limit", type=int, default=50, help="Límite de registros (default: 50, max: 1000)")
    p_auth.add_argument("--output", required=True, help="Ruta de guardado para el archivo JSON")
    p_auth.set_defaults(func=cmd_search_authors)

    # Subcomando: search-works
    p_wrk = subparsers.add_parser("search-works", help="Recupera publicaciones en rag.works_academic_all")
    p_wrk.add_argument("--query", default="", help="Término a buscar en el título")
    p_wrk.add_argument("--author-name", help="Nombre del autor en el array de autores")
    p_wrk.add_argument("--institution-name", help="Nombre de la institución en el array")
    p_wrk.add_argument("--institution-ror", help="Identificador ROR (ej. 01tmp8f25 para UNAM)")
    p_wrk.add_argument("--topic", help="Tópico o tema")
    p_wrk.add_argument("--year-min", type=int, help="Año mínimo de publicación")
    p_wrk.add_argument("--year-max", type=int, help="Año máximo de publicación")
    p_wrk.add_argument("--oa-status", choices=["diamond", "gold", "hybrid", "bronze", "green", "closed"], help="Vía de Acceso Abierto")
    p_wrk.add_argument("--is-top-10", help="Filtrar por publicaciones Top 10%% (true/false)")
    p_wrk.add_argument("--limit", type=int, default=100, help="Límite de publicaciones (default: 100, max: 50000)")
    p_wrk.add_argument("--output", required=True, help="Ruta de guardado para el archivo JSON")
    p_wrk.set_defaults(func=cmd_search_works)

    # Subcomando: semantic-search
    p_sem = subparsers.add_parser("semantic-search", help="Búsqueda semántica usando embeddings nomic locales (768d)")
    p_sem.add_argument("--query", required=True, help="Texto o pregunta en lenguaje natural")
    p_sem.add_argument("--target", choices=["works", "institutions", "authors"], default="works", help="Objetivo de búsqueda: works, institutions o authors")
    p_sem.add_argument("--institution-name", help="Filtrar por institución")
    p_sem.add_argument("--year-min", type=int, help="Año mínimo")
    p_sem.add_argument("--year-max", type=int, help="Año máximo")
    p_sem.add_argument("--oa-status", choices=["diamond", "gold", "hybrid", "bronze", "green", "closed"], help="Vía de Acceso Abierto")
    p_sem.add_argument("--is-top-10", help="Filtrar por publicaciones Top 10%% (true/false)")
    p_sem.add_argument("--limit", type=int, default=20, help="Límite de resultados")
    p_sem.add_argument("--output", required=True, help="Ruta de guardado para el archivo JSON")
    p_sem.set_defaults(func=cmd_semantic_search)

    # Subcomando: top-entities
    p_top = subparsers.add_parser("top-entities", help="Identifica autores o instituciones con mayor capacidad en un tema")
    p_top.add_argument("--query", required=True, help="Tema o disciplina a evaluar (ej. 'lithium', 'baterias de litio')")
    p_top.add_argument("--by", choices=["authors", "institutions"], required=True, help="Entidad a rankear (authors o institutions)")
    p_top.add_argument("--year-min", type=int, help="Año mínimo")
    p_top.add_argument("--year-max", type=int, help="Año máximo")
    p_top.add_argument("--limit", type=int, default=15, help="Número de entidades en el ranking (default: 15, max: 200)")
    p_top.add_argument("--output", required=True, help="Ruta de guardado para el archivo JSON")
    p_top.set_defaults(func=cmd_top_entities)

    # Subcomando: aggregate
    p_agg = subparsers.add_parser("aggregate", help="Agregaciones cuantitativas en rag.works_academic_all")
    p_agg.add_argument("--group-by", default="oa_status", help="Campo de agrupación (oa_status, publication_year, subfield, etc.)")
    p_agg.add_argument("--filter", help="Cláusula WHERE para filtrar la agregación")
    p_agg.add_argument("--output", required=True, help="Ruta de guardado para el archivo JSON")
    p_agg.set_defaults(func=cmd_aggregate)

    # Subcomando: get-institution
    p_inst = subparsers.add_parser("get-institution", help="Consulta catálogo nacional en rag.institutions_seed_mexico")
    p_inst.add_argument("--query", default="", help="Nombre de la institución")
    p_inst.add_argument("--acronym", help="Acrónimo institucional (ej. UNAM, IPN, UAM, CINVESTAV)")
    p_inst.add_argument("--state", help="Estado / Entidad federativa de México")
    p_inst.add_argument("--ror", help="Código ROR")
    p_inst.add_argument("--limit", type=int, default=25, help="Límite de resultados")
    p_inst.add_argument("--output", required=True, help="Ruta de guardado para el archivo JSON")
    p_inst.set_defaults(func=cmd_get_institution)

    # Subcomando: validate-query
    p_val = subparsers.add_parser("validate-query", help="Valida sintaxis y bloquea consultas con JOIN")
    p_val.add_argument("--query", required=True, help="Sentencia SQL a validar")
    p_val.add_argument("--output", required=True, help="Ruta de guardado para el reporte")
    p_val.set_defaults(func=cmd_validate_query)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
