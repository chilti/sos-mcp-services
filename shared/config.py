import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class DatabaseSettings(BaseModel):
    # ClickHouse Remote (RAG / OpenAlex)
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", os.getenv("CH_HOST", "10.90.0.87"))
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", os.getenv("CH_PORT", 8124)))
    clickhouse_user: str = os.getenv("CLICKHOUSE_USER", os.getenv("CH_USER", "rag_user"))
    clickhouse_password: str = os.getenv("CLICKHOUSE_PASSWORD", os.getenv("CH_PASSWORD", "$$B3tt3r-R4g-3veR-d0N3++"))
    clickhouse_database: str = os.getenv("CLICKHOUSE_DATABASE", os.getenv("CH_DATABASE", "rag"))
    openalex_api_url: str = os.getenv("OPENALEX_API_URL", "http://localhost:5012")

    # ClickHouse Local (ORCID)
    ch_orcid_host: str = os.getenv("CH_ORCID_HOST", "127.0.0.1")
    ch_orcid_port: int = int(os.getenv("CH_ORCID_PORT", 8123))
    ch_orcid_user: str = os.getenv("CH_ORCID_USER", "admin")
    ch_orcid_password: str = os.getenv("CH_ORCID_PASSWORD", "admin")
    ch_orcid_database: str = os.getenv("CH_ORCID_DATABASE", "orcid")

    # Neo4j
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password123")

    # Qdrant
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", 6333))

    # LLM / Embeddings
    lm_studio_url: str = os.getenv("LM_STUDIO_URL", os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"))
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-nomic-ai-nomic-embed-text-v2-moe")

    @property
    def clickhouse_clean_password(self) -> str:
        """Retorna la contraseña de ClickHouse con escapes de signos de dólar resueltos."""
        return self.clickhouse_password.replace("$$", "$")

settings = DatabaseSettings()
