from neo4j import GraphDatabase
from shared.config import settings

def get_neo4j_driver():
    """Retorna driver Neo4j o None si no hay conectividad."""
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=3
        )
        driver.verify_connectivity()
        return driver
    except Exception:
        return None

def execute_cypher_query(query: str, parameters: dict = None):
    """Ejecuta consulta Cypher en Neo4j de forma segura."""
    driver = get_neo4j_driver()
    if driver is None:
        return {"status": "offline", "message": "Neo4j no disponible (verificar host)", "records": []}
    
    try:
        with driver.session() as session:
            result = session.run(query, parameters or {})
            records = [record.data() for record in result]
            return {"status": "success", "records": records, "count": len(records)}
    except Exception as e:
        return {"status": "error", "message": str(e), "records": []}
    finally:
        driver.close()
