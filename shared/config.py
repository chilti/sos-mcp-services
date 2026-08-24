import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class DatabaseSettings(BaseModel):
    # ClickHouse
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", 9000))
    clickhouse_user: str = os.getenv("CLICKHOUSE_USER", "default")
    clickhouse_password: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    clickhouse_database: str = os.getenv("CLICKHOUSE_DATABASE", "openalex")
    openalex_api_url: str = os.getenv("OPENALEX_API_URL", "http://localhost:5012")

    # Neo4j
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")

    # Qdrant
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", 6333))

    # LLM
    lm_studio_url: str = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")

settings = DatabaseSettings()
