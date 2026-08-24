from qdrant_client import QdrantClient
from shared.config import settings

def get_qdrant_client():
    """Retorna cliente Qdrant o None si no está disponible."""
    try:
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port, timeout=3)
        client.get_collections()
        return client
    except Exception:
        return None
