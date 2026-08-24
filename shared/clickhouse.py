import clickhouse_connect
from shared.config import settings

def get_clickhouse_client():
    """Retorna un cliente ClickHouse o None si no hay conectividad."""
    try:
        return clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_database,
            connect_timeout=3,
            send_receive_timeout=15
        )
    except Exception as e:
        return None

def execute_safe_query(query: str, params: dict = None):
    """Ejecuta una consulta SELECT sobre ClickHouse con manejo defensivo."""
    client = get_clickhouse_client()
    if client is None:
        return {"status": "offline", "message": "ClickHouse no disponible (verificar VPN/host)", "data": []}
    
    clean_query = query.strip()
    if not clean_query.upper().startswith("SELECT") and not clean_query.upper().startswith("SHOW") and not clean_query.upper().startswith("DESCRIBE"):
        return {"status": "error", "message": "Solo se permiten consultas de solo lectura (SELECT)", "data": []}
    
    try:
        res = client.query(clean_query, parameters=params)
        return {
            "status": "success",
            "columns": res.column_names,
            "data": res.result_rows,
            "row_count": len(res.result_rows)
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "data": []}
