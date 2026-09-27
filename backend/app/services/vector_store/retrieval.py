import uuid
from typing import Optional
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
    """Document-isolated vector retrieval service for semantic similarity search."""

    def __init__(
        self,
        db: Optional[Session] = None,
        embedding_service: Optional[BaseEmbeddingService] = None,
        vector_store: Optional[VectorStore] = None
    ):
        self.db = db
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or ChromaVectorStore()

    def search(
        self,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 5
    ) -> list[RetrievalResult]:
        """Performs document-isolated vector search returning list of RetrievalResult."""
        capped_top_k = min(max(1, top_k), settings.MAX_TOP_K)

        logger.info(f"Retrieval query for document_id={document_id}, top_k={capped_top_k}")

        try:
            query_vector = self.embedding_service.embed_query(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query embedding error: {str(e)}"
            )

        raw_results = self.vector_store.search(
            query_embedding=query_vector,
            document_id=str(document_id),
            top_k=capped_top_k
        )

        results: list[RetrievalResult] = []
        for item in raw_results:
            results.append(
                RetrievalResult(
                    chunk_id=uuid.UUID(item["chunk_id"]),
                    document_id=document_id,
                    text=item["text"],
                    score=item["score"],
                    page_number=item["page_number"],
                    section=item["section"],
                    document_type=item["document_type"],
                    extraction_method=item["extraction_method"]
                )
            )

        logger.info(f"Retrieval completed for document_id={document_id}. Matches count={len(results)}")
        return results

    def search_document(
        self,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 5
    ) -> RetrievalResponse:
        # 1. Verify document exists if db session is present
        if self.db:
            doc = self.db.query(Document).filter(Document.id == document_id).first()
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document with ID '{document_id}' not found."
                )

        results = self.search(query=query, document_id=document_id, top_k=top_k)
        return RetrievalResponse(
            query=query,
            document_id=document_id,
            top_k=min(max(1, top_k), settings.MAX_TOP_K),
            results=results
        )
