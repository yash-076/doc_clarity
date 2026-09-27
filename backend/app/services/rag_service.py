import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Document, DocumentStatus, EmbeddingStatus
from app.schemas.rag import RAGAnswerResponse, CitationItem
from app.services.vector_store.retrieval import RetrievalService
from app.services.llm import LLMService, get_llm_service
from app.services.prompt_builder import RAGPromptBuilder, SYSTEM_GROUNDING_INSTRUCTIONS

logger = logging.getLogger(__name__)


class RAGService:
    """End-to-end RAG Service orchestrating document validation, retrieval, prompt construction, and LLM answer generation."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[LLMService] = None,
        prompt_builder: Optional[RAGPromptBuilder] = None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm_service = llm_service or get_llm_service()
        self.prompt_builder = prompt_builder or RAGPromptBuilder()

    async def answer_question(
        self,
        db: Session,
        document_id: uuid.UUID,
        question: str,
        top_k: Optional[int] = None,
    ) -> RAGAnswerResponse:
        """Processes a document-grounded Q&A query.
        
        Args:
            db: Database session.
            document_id: UUID of the target document.
            question: Cleaned user question string.
            top_k: Optional top-k chunks parameter.

        Returns:
            RAGAnswerResponse containing grounded answer, citations, confidence, and disclaimers.
        """
        # 1. Validate Document Existence and Status
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.warning(f"RAG requested for non-existent document_id={document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found."
            )

        if document.status != DocumentStatus.READY.value and document.status != DocumentStatus.READY:
            logger.warning(f"RAG requested for incomplete document_id={document_id}, status={document.status}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document processing is not complete yet (current status: '{document.status}')."
            )

        if document.embedding_status != EmbeddingStatus.INDEXED.value and document.embedding_status != EmbeddingStatus.INDEXED:
            logger.warning(f"RAG requested for unindexed document_id={document_id}, embedding_status={document.embedding_status}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document vector indexing is not complete yet (status: '{document.embedding_status}')."
            )

        # 2. Determine effective top_k
        requested_top_k = top_k or settings.DEFAULT_RAG_TOP_K
        effective_top_k = min(max(1, requested_top_k), settings.MAX_RAG_TOP_K)

        logger.info(f"Executing RAG Q&A for doc_id={document_id}, question='{question[:50]}...', top_k={effective_top_k}")

        # 3. Retrieve relevant chunks from ChromaDB via RetrievalService
        retrieved_results = self.retrieval_service.search(
            query=question,
            document_id=document_id,
            top_k=effective_top_k,
        )

        # 4. Handle Zero-Result Retrieval
        if not retrieved_results:
            logger.info(f"Zero chunks retrieved for document_id={document_id}. Returning default no-evidence response.")
            return RAGAnswerResponse(
                document_id=document_id,
                question=question,
                answer="I couldn't find relevant information about this question in the uploaded document.",
                citations=[],
                confidence="low",
            )

        # Convert RetrievalResult items to dict for prompt builder
        chunks_data = [
            {
                "chunk_id": str(res.chunk_id),
                "content": res.text,
                "page_number": res.page_number,
                "section": res.section,
                "score": res.score,
            }
            for res in retrieved_results
        ]

        # 5. Build context & user prompt using RAGPromptBuilder
        user_prompt, used_chunks = self.prompt_builder.build_user_prompt(
            question=question,
            retrieved_chunks=chunks_data,
        )

        # 6. Generate answer via LLM Provider
        answer_text = await self.llm_service.generate(
            system_prompt=SYSTEM_GROUNDING_INSTRUCTIONS,
            user_prompt=user_prompt,
        )

        # 7. Construct Citations
        citations: list[CitationItem] = []
        for chk in used_chunks:
            citations.append(
                CitationItem(
                    chunk_id=uuid.UUID(chk["chunk_id"]),
                    page_number=chk["page_number"],
                    section=chk["section"],
                    relevance_score=chk["score"],
                )
            )

        # 8. Calculate Basic Confidence Heuristic
        confidence = self._calculate_confidence(
            answer_text=answer_text,
            used_chunks=used_chunks,
        )

        return RAGAnswerResponse(
            document_id=document_id,
            question=question,
            answer=answer_text,
            citations=citations,
            confidence=confidence,
        )

    def _calculate_confidence(
        self,
        answer_text: str,
        used_chunks: list[dict],
    ) -> str:
        """Calculates basic confidence heuristic ("high", "medium", "low")."""
        low_confidence_triggers = [
            "couldn't find",
            "could not find",
            "does not contain",
            "not mentioned",
            "insufficient information",
            "no information",
        ]
        lower_ans = answer_text.lower()
        if any(trigger in lower_ans for trigger in low_confidence_triggers):
            return "low"

        if not used_chunks:
            return "low"

        scores = [chk["score"] for chk in used_chunks]
        max_score = max(scores)

        if max_score >= 0.70 and len(used_chunks) >= 1:
            return "high"
        elif max_score >= 0.45:
            return "medium"
        else:
            return "low"
