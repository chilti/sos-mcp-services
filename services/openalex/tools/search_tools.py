import httpx
from shared.config import settings
from shared.clickhouse import execute_safe_query

def openalex_search_authors(search_query: str = "", orcid: str = None, institution_ror: str = None, limit: int = 10) -> dict:
    """Busca autores en la base local de OpenAlex mediante búsqueda tokenizada e insensible a acentos/diacríticos."""
    # Intento 1: API REST local de OpenAlex
    try:
        params = {"search": search_query, "per-page": limit}
        if orcid:
            params["filter"] = f"orcid:{orcid}"
        if institution_ror:
            params["filter"] = f"last_known_institution.ror:{institution_ror}"
        
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(f"{settings.openalex_api_url}/authors", params=params)
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    # Intento 2: Consulta directa en ClickHouse
    where_clauses = []
    if search_query:
        where_clauses.append(f"positionCaseInsensitiveUTF8(display_name, '{search_query}') > 0")
    if orcid:
        where_clauses.append(f"orcid = '{orcid}'")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    sql = f"SELECT id, display_name, orcid, works_count, cited_by_count FROM openalex.authors WHERE {where_sql} ORDER BY cited_by_count DESC LIMIT {limit}"
    return execute_safe_query(sql)

def openalex_search_works(search_query: str = "", author_id: str = None, institution_ror: str = None, topic_id: str = None, from_publication_date: str = None, to_publication_date: str = None, is_oa: bool = None, limit: int = 20) -> dict:
    """Busca artículos y publicaciones científicas por título, tópico, autor, revista o fechas."""
    try:
        params = {"search": search_query, "per-page": limit}
        filters = []
        if author_id:
            filters.append(f"author.id:{author_id}")
        if institution_ror:
            filters.append(f"institutions.ror:{institution_ror}")
        if topic_id:
            filters.append(f"primary_topic.id:{topic_id}")
        if from_publication_date:
            filters.append(f"from_publication_date:{from_publication_date}")
        if to_publication_date:
            filters.append(f"to_publication_date:{to_publication_date}")
        if is_oa is not None:
            filters.append(f"is_oa:{str(is_oa).lower()}")
        
        if filters:
            params["filter"] = ",".join(filters)

        with httpx.Client(timeout=4.0) as client:
            resp = client.get(f"{settings.openalex_api_url}/works", params=params)
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    # Fallback ClickHouse
    where_clauses = []
    if search_query:
        where_clauses.append(f"positionCaseInsensitiveUTF8(title, '{search_query}') > 0")
    if is_oa is not None:
        where_clauses.append(f"is_oa = {1 if is_oa else 0}")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    sql = f"SELECT id, doi, title, publication_year, cited_by_count, is_oa, oa_status FROM openalex.works WHERE {where_sql} ORDER BY cited_by_count DESC LIMIT {limit}"
    return execute_safe_query(sql)
