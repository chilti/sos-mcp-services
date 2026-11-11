import httpx
from shared.config import settings
from shared.clickhouse import execute_safe_query

def openalex_get_entity_by_id(entity_type: str, identifier: str) -> dict:
    """Recupera el objeto normalizado completo (Work, Author, Institution, Source, Topic, Funder) por ID."""
    clean_id = identifier.replace("https://openalex.org/", "").strip()
    try:
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(f"{settings.openalex_api_url}/{entity_type}/{clean_id}")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    table_name = f"openalex.{entity_type}"
    sql = f"SELECT * FROM {table_name} WHERE id = '{clean_id}' OR id = 'https://openalex.org/{clean_id}' LIMIT 1"
    ch_res = execute_safe_query(sql)
    if ch_res.get("status") == "success" and ch_res.get("data"):
        return ch_res

    try:
        with httpx.Client(timeout=12.0, headers={"User-Agent": "SoSMCPServices/1.0 (mailto:soporte@knomap.org)"}) as client:
            resp = client.get(f"https://api.openalex.org/{entity_type}/{clean_id}")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return ch_res

def openalex_aggregate_group_by(entity_type: str = "works", filter_param: str = None, group_by_field: str = "publication_year") -> dict:
    """Ejecuta agregaciones y conteos agrupados (por año, país, OA, tópico) a velocidad ClickHouse o API pública."""
    where_sql = "1=1"
    if filter_param:
        where_sql = filter_param
    sql = f"SELECT {group_by_field}, count(*) as total_count, sum(cited_by_count) as total_citations FROM openalex.{entity_type} WHERE {where_sql} GROUP BY {group_by_field} ORDER BY total_count DESC LIMIT 100"
    ch_res = execute_safe_query(sql)
    if ch_res.get("status") == "success" and ch_res.get("data"):
        return ch_res

    try:
        params = {"group_by": group_by_field}
        if filter_param and ":" in filter_param and "=" not in filter_param:
            params["filter"] = filter_param
        with httpx.Client(timeout=12.0, headers={"User-Agent": "SoSMCPServices/1.0 (mailto:soporte@knomap.org)"}) as client:
            resp = client.get(f"https://api.openalex.org/{entity_type}", params=params)
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return ch_res
