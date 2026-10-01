import logging
import uuid
from typing import Optional, List
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.embeddings import BaseEmbeddingService, get_embedding_service
from app.services.vector_store.base import VectorStore
from app.services.vector_store.chroma_store import ChromaVectorStore
from app.services.retrieval.models import RetrievedCandidate, normalize_scores

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Document-isolated vector similarity retriever using BGE embeddings and ChromaDB."""

    def __init__(
        self,
        embedding_service: Optional[BaseEmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or ChromaVectorStore()

    def search(
        self,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 15,
    ) -> List[RetrievedCandidate]:
        """Performs document-isolated vector search and returns a list of RetrievedCandidate."""
        capped_top_k = min(max(1, top_k), settings.MAX_TOP_K)
        logger.info(f"Vector search for document_id={document_id}, top_k={capped_top_k}")

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

        candidates: List[RetrievedCandidate] = []
        raw_scores = []
        for item in raw_results:
            raw_score = float(item["score"])
            raw_scores.append(raw_score)
            c = RetrievedCandidate(
                chunk_id=uuid.UUID(item["chunk_id"]),
                document_id=document_id,
                text=item["text"],
                page_number=item.get("page_number"),
                section=item.get("section"),
                document_type=item.get("document_type", "general"),
                extraction_method=item.get("extraction_method", "text"),
                vector_score=raw_score,
            )
            candidates.append(c)

        # Normalize vector scores
        norm_scores = normalize_scores(raw_scores)
        for idx, norm_score in enumerate(norm_scores):
            candidates[idx].norm_vector_score = norm_score

        return candidates
