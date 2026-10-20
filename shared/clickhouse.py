import re
import clickhouse_connect
from typing import Optional, Dict, Any, List
from shared.config import settings


def sanitize_no_joins(sql: str) -> bool:
    """
    Verifica y bloquea de manera estricta cualquier intento de usar JOIN relacional en ClickHouse.
    Permite ARRAY JOIN nativo para desanidar columnas de arrays en la misma fila.
    """
    # Excluir 'ARRAY JOIN' antes de verificar palabras reservadas 'JOIN'
    sql_without_array_join = re.sub(r"\barray\s+join\b", "", sql, flags=re.IGNORECASE)
    if re.search(r"\bjoin\b", sql_without_array_join, re.IGNORECASE):
        raise ValueError(
            "Violación de política cienciométrica de datos UNAM: Las sentencias JOIN están estrictamente prohibidas en ClickHouse. "
            "Utilice las tablas materializadas precalculadas (rag.works_academic_all, rag.authors_seed_mexico, rag.institutions_seed_mexico) "
            "o filtros directos por funciones de arrays (has, arrayExists)."
        )
    return True


def get_clickhouse_client(database: Optional[str] = None):
    """Retorna un cliente ClickHouse conectado al host remoto configurado o None si falla."""
    db_name = database or settings.clickhouse_database
    try:
        return clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_clean_password,
            database=db_name,
            connect_timeout=4,
            send_receive_timeout=30
        )
    except Exception as e:
        return None


def execute_safe_query(
    query: str,
    params: Optional[dict] = None,
    database: Optional[str] = None,
    as_dict: bool = True,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ejecuta una consulta SELECT / SHOW / DESCRIBE en ClickHouse de forma segura.
    Valida la regla estricta de CERO JOINs y retorna resultados estructurados.
    """
    clean_query = query.strip().rstrip(";")

    # 1. Validar solo lectura
    upper_query = clean_query.upper()
    if not (upper_query.startswith("SELECT") or upper_query.startswith("SHOW") or upper_query.startswith("DESCRIBE") or upper_query.startswith("WITH")):
        return {
            "status": "error",
            "message": "Operación denegada: Solo se permiten consultas de solo lectura (SELECT, SHOW, DESCRIBE, WITH).",
            "data": []
        }

    # 2. Validar estricto CERO JOINs
    try:
        sanitize_no_joins(clean_query)
    except ValueError as ve:
        return {
            "status": "error",
            "message": str(ve),
            "data": []
        }

    # 3. Aplicar límite de seguridad si no existe LIMIT explícito y se especifica limit
    if limit and not re.search(r"\blimit\s+\d+", upper_query):
        clean_query = f"{clean_query} LIMIT {limit}"

    client = get_clickhouse_client(database=database)
    if client is None:
        return {
            "status": "offline",
            "message": f"ClickHouse no disponible en {settings.clickhouse_host}:{settings.clickhouse_port}",
            "data": []
        }

    try:
        res = client.query(clean_query, parameters=params)
        cols = res.column_names

        if as_dict:
            dict_rows = [dict(zip(cols, row)) for row in res.result_rows]
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
                "data": res.result_rows,
                "row_count": len(res.result_rows)
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al ejecutar consulta ClickHouse: {str(e)}",
            "data": []
        }

