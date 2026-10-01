import uuid
from typing import Optional, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models.document import Document
from app.schemas.retrieval import RetrievalResponse, RetrievalResult
from app.services.embeddings import get_embedding_service, BaseEmbeddingService
from app.services.vector_store.base import VectorStore
from app.services.vector_store.chroma_store import ChromaVectorStore


class RetrievalService:
    """Document-isolated retrieval service delegating to AdvancedRetrievalService (Hybrid + Reranking)."""

    def __init__(
        self,
        db: Optional[Session] = None,
        embedding_service: Optional[BaseEmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
        advanced_service: Optional[Any] = None,
    ):
        from app.services.retrieval.advanced_service import AdvancedRetrievalService

        self.db = db
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or ChromaVectorStore()
        self.advanced_service = advanced_service or AdvancedRetrievalService(db=db)

    def search(
        self,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 5,
        mode: Optional[str] = None,
    ) -> list[RetrievalResult]:
        """Performs advanced document-isolated retrieval."""
        return self.advanced_service.search(
            query=query,
            document_id=document_id,
            top_k=top_k,
            mode=mode,
            db=self.db,
        )

    def search_document(
        self,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 5,
        mode: Optional[str] = None,
    ) -> RetrievalResponse:
        """API wrapper for search delegating to AdvancedRetrievalService."""
        return self.advanced_service.search_document(
            query=query,
            document_id=document_id,
            top_k=top_k,
            mode=mode,
        )
