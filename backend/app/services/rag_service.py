import hashlib
import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.personas import PersonaType, ensure_persona
from app.db.models.document import Document, DocumentStatus, EmbeddingStatus
from app.db.models.persona_response_cache import PersonaResponseCache
from app.db.models.document_chunk import DocumentChunk
from app.schemas.rag import RAGAnswerResponse, CitationItem
from app.services.vector_store.retrieval import RetrievalService
from app.services.llm import LLMService, get_llm_service
from app.services.prompt_builder import RAGPromptBuilder

logger = logging.getLogger(__name__)


class RAGService:
    """End-to-end RAG Service orchestrating document validation, retrieval, persona prompt construction, response caching, and LLM answer generation."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_service: Optional[LLMService] = None,
        prompt_builder: Optional[RAGPromptBuilder] = None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm_service = llm_service or get_llm_service()
        self.prompt_builder = prompt_builder or RAGPromptBuilder()

    def _hash_question(self, question: str) -> str:
        """Generates SHA-256 hash string for a normalized question string."""
        return hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()

    async def answer_question(
        self,
        db: Session,
        document_id: uuid.UUID,
        question: str,
        persona: Optional[str | PersonaType] = PersonaType.CONSUMER,
        top_k: Optional[int] = None,
        force_refresh: bool = False,
    ) -> RAGAnswerResponse:
        """Processes a document-grounded Q&A query with persona explanation style and caching.
        
        Args:
            db: Database session.
            document_id: UUID of the target document.
            question: Cleaned user question string.
            persona: Selected explanation persona (consumer, professional, business).
            top_k: Optional top-k chunks parameter.
            force_refresh: Optional flag to bypass cache and regenerate answer.

        Returns:
            RAGAnswerResponse containing grounded answer, persona style, citations, and confidence.
        """
        persona_enum = ensure_persona(persona)

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

        q_hash = self._hash_question(question)

        # 2. Check Response Cache for identical (document_id, q_hash, persona)
        if not force_refresh:
            cached_resp = (
                db.query(PersonaResponseCache)
                .filter(
                    PersonaResponseCache.document_id == document_id,
                    PersonaResponseCache.question_hash == q_hash,
                    PersonaResponseCache.persona == persona_enum.value,
                )
                .order_by(PersonaResponseCache.created_at.desc())
                .first()
            )
            if cached_resp:
                logger.info(f"Returning cached persona answer for doc_id={document_id}, persona={persona_enum.value}")
                citations = []
                if cached_resp.citations_json:
                    for item in cached_resp.citations_json:
                        if isinstance(item, dict) and "chunk_id" in item:
                            try:
                                citations.append(
                                    CitationItem(
                                        chunk_id=uuid.UUID(str(item["chunk_id"])),
                                        page_number=item.get("page_number"),
                                        section=item.get("section"),
                                        relevance_score=float(item.get("relevance_score", 0.0)),
                                    )
                                )
                            except Exception:
                                pass
                return RAGAnswerResponse(
                    document_id=document_id,
                    question=question,
                    persona=persona_enum,
                    answer=cached_resp.answer,
                    citations=citations,
                    confidence=cached_resp.confidence or "high",
                )

        # 3. Determine effective top_k
        requested_top_k = top_k or settings.DEFAULT_RAG_TOP_K
        effective_top_k = min(max(1, requested_top_k), settings.MAX_RAG_TOP_K)

        logger.info(f"Executing RAG Q&A for doc_id={document_id}, persona={persona_enum.value}, question='{question[:40]}...'")

        # 4. Retrieve relevant chunks from ChromaDB via RetrievalService
        retrieved_results = self.retrieval_service.search(
            query=question,
            document_id=document_id,
            top_k=effective_top_k,
        )

        # 5. Handle Zero-Result Retrieval
        if not retrieved_results:
            logger.info(f"Zero chunks retrieved for document_id={document_id}. Returning default no-evidence response.")
            return RAGAnswerResponse(
                document_id=document_id,
                question=question,
                persona=persona_enum,
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

        # 6. Build context & user prompt using RAGPromptBuilder with persona
        user_prompt, used_chunks = self.prompt_builder.build_user_prompt(
            question=question,
            retrieved_chunks=chunks_data,
            persona=persona_enum,
        )
        system_prompt = self.prompt_builder.build_system_instruction(persona=persona_enum)

        # 7. Generate answer via LLM Provider
        answer_text = await self.llm_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # 8. Construct Citations
        citations: list[CitationItem] = []
        citations_json = []
        for chk in used_chunks:
            cid = uuid.UUID(chk["chunk_id"])
            citations.append(
                CitationItem(
                    chunk_id=cid,
                    page_number=chk["page_number"],
                    section=chk["section"],
                    relevance_score=chk["score"],
                )
            )
            citations_json.append({
                "chunk_id": str(cid),
                "page_number": chk["page_number"],
                "section": chk["section"],
                "relevance_score": chk["score"],
            })

        # 9. Calculate Confidence
        confidence = self._calculate_confidence(
            answer_text=answer_text,
            used_chunks=used_chunks,
        )

        # 10. Cache in PostgreSQL
        cache_entry = PersonaResponseCache(
            id=uuid.uuid4(),
            document_id=document_id,
            question_hash=q_hash,
            persona=persona_enum.value,
            answer=answer_text,
            citations_json=citations_json,
            confidence=confidence,
        )
        db.add(cache_entry)
        db.commit()

        return RAGAnswerResponse(
            document_id=document_id,
            question=question,
            persona=persona_enum,
            answer=answer_text,
            citations=citations,
            confidence=confidence,
        )

    async def reexplain_question(
        self,
        db: Session,
        document_id: uuid.UUID,
        question: str,
        persona: PersonaType,
        source_chunk_ids: Optional[list[uuid.UUID]] = None,
    ) -> RAGAnswerResponse:
        """Re-explains existing document evidence using a different target persona WITHOUT re-running vector retrieval when possible."""
        persona_enum = ensure_persona(persona)

        # Check cache first
        q_hash = self._hash_question(question)
        cached_resp = (
            db.query(PersonaResponseCache)
            .filter(
                PersonaResponseCache.document_id == document_id,
                PersonaResponseCache.question_hash == q_hash,
                PersonaResponseCache.persona == persona_enum.value,
            )
            .order_by(PersonaResponseCache.created_at.desc())
            .first()
        )
        if cached_resp:
            citations = []
            if cached_resp.citations_json:
                for item in cached_resp.citations_json:
                    if isinstance(item, dict) and "chunk_id" in item:
                        try:
                            citations.append(
                                CitationItem(
                                    chunk_id=uuid.UUID(str(item["chunk_id"])),
                                    page_number=item.get("page_number"),
                                    section=item.get("section"),
                                    relevance_score=float(item.get("relevance_score", 0.0)),
                                )
                            )
                        except Exception:
                            pass
            return RAGAnswerResponse(
                document_id=document_id,
                question=question,
                persona=persona_enum,
                answer=cached_resp.answer,
                citations=citations,
                confidence=cached_resp.confidence or "high",
            )

        # If source_chunk_ids supplied, fetch chunks directly from DB
        chunks_data = []
        if source_chunk_ids:
            db_chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.id.in_(source_chunk_ids))
                .all()
            )
            for chk in db_chunks:
                chunks_data.append({
                    "chunk_id": str(chk.id),
                    "content": chk.content,
                    "page_number": chk.page_number,
                    "section": chk.detected_section,
                    "score": 0.90,
                })

        # Fallback to search if no explicit source_chunk_ids
        if not chunks_data:
            return await self.answer_question(
                db=db,
                document_id=document_id,
                question=question,
                persona=persona_enum,
                force_refresh=True,
            )

        # Build prompt & generate with new persona
        user_prompt, used_chunks = self.prompt_builder.build_user_prompt(
            question=question,
            retrieved_chunks=chunks_data,
            persona=persona_enum,
        )
        system_prompt = self.prompt_builder.build_system_instruction(persona=persona_enum)

        answer_text = await self.llm_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        citations = []
        citations_json = []
        for chk in used_chunks:
            cid = uuid.UUID(chk["chunk_id"])
            citations.append(
                CitationItem(
                    chunk_id=cid,
                    page_number=chk["page_number"],
                    section=chk["section"],
                    relevance_score=chk["score"],
                )
            )
            citations_json.append({
                "chunk_id": str(cid),
                "page_number": chk["page_number"],
                "section": chk["section"],
                "relevance_score": chk["score"],
            })

        confidence = self._calculate_confidence(answer_text=answer_text, used_chunks=used_chunks)

        # Store in cache
        cache_entry = PersonaResponseCache(
            id=uuid.uuid4(),
            document_id=document_id,
            question_hash=q_hash,
            persona=persona_enum.value,
            answer=answer_text,
            citations_json=citations_json,
            confidence=confidence,
        )
        db.add(cache_entry)
        db.commit()

        return RAGAnswerResponse(
            document_id=document_id,
            question=question,
            persona=persona_enum,
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
