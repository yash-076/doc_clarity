from app.services.embeddings.base import BaseEmbeddingService
from app.services.embeddings.local_embedding import LocalEmbeddingService

_default_embedding_service: BaseEmbeddingService | None = None

def get_embedding_service() -> BaseEmbeddingService:
    global _default_embedding_service
    if _default_embedding_service is None:
        _default_embedding_service = LocalEmbeddingService()
    return _default_embedding_service

__all__ = [
    "BaseEmbeddingService",
    "LocalEmbeddingService",
    "get_embedding_service"
]
