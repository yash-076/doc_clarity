import logging
import time
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Document
from app.schemas.retrieval import RetrievalResponse, RetrievalResult
from app.services.retrieval.models import RetrievedCandidate
from app.services.retrieval.hybrid_retriever import HybridRetriever
from app.services.retrieval.vector_retriever import VectorRetriever
from app.services.retrieval.keyword_retriever import KeywordRetriever
from app.services.retrieval.reranker import BaseReranker, get_reranker
from app.services.retrieval.query_expander import QueryExpander
from app.services.retrieval.diversity import (
    apply_section_and_page_boosting,
    apply_diversity_selection,
)

logger = logging.getLogger(__name__)


class AdvancedRetrievalService:
    """Master orchestrator for Advanced Retrieval, Hybrid Search, Reranking & Diversity Selection."""

    def __init__(
        self,
        db: Optional[Session] = None,
        hybrid_retriever: Optional[HybridRetriever] = None,
        reranker: Optional[BaseReranker] = None,
        query_expander: Optional[QueryExpander] = None,
    ):
        self.db = db
        self.hybrid_retriever = hybrid_retriever or HybridRetriever()
        self.reranker = reranker or get_reranker()
        self.query_expander = query_expander or QueryExpander()

    def search_candidates(
        self,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 5,
        mode: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> tuple[List[RetrievedCandidate], dict]:
        """Executes full advanced retrieval pipeline and returns ranked candidates with latency breakdown."""
        start_time = time.perf_counter()
        session = db or self.db
        retrieval_mode = (mode or settings.RETRIEVAL_MODE).lower()
        capped_top_k = min(max(1, top_k), settings.MAX_TOP_K)

        logger.info(
            f"AdvancedRetrievalService: query='{query}', doc_id={document_id}, "
            f"mode={retrieval_mode}, top_k={capped_top_k}"
        )

        # 1. Query Normalization & Optional Expansion
        expanded_queries = self.query_expander.expand(query)
        primary_query = expanded_queries[0]

        # 2. Retrieval Candidates Generation
        retrieval_start = time.perf_counter()
        if retrieval_mode == "vector":
            candidates = self.hybrid_retriever.vector_retriever.search(
                primary_query, document_id, top_k=settings.VECTOR_CANDIDATE_K
            )
            for c in candidates:
                c.hybrid_score = c.norm_vector_score
                c.final_score = c.hybrid_score
        elif retrieval_mode == "keyword" and session:
            candidates = self.hybrid_retriever.keyword_retriever.search(
                session, primary_query, document_id, top_k=settings.KEYWORD_CANDIDATE_K
            )
            for c in candidates:
                c.hybrid_score = c.norm_keyword_score
                c.final_score = c.hybrid_score
        else:
            # Hybrid mode
            candidates = self.hybrid_retriever.search(
                query=primary_query,
                document_id=document_id,
                db=session,
                vector_candidate_k=settings.VECTOR_CANDIDATE_K,
                keyword_candidate_k=settings.KEYWORD_CANDIDATE_K,
            )

            # If query expansion yielded extra queries, collect candidates for them too
            if len(expanded_queries) > 1:
                existing_ids = {c.chunk_id for c in candidates}
                for exp_q in expanded_queries[1:]:
                    exp_candidates = self.hybrid_retriever.search(
                        query=exp_q,
                        document_id=document_id,
                        db=session,
                        vector_candidate_k=5,
                        keyword_candidate_k=5,
                    )
                    for ec in exp_candidates:
                        if ec.chunk_id not in existing_ids:
                            candidates.append(ec)
                            existing_ids.add(ec.chunk_id)

        retrieval_ms = round((time.perf_counter() - retrieval_start) * 1000, 2)

        # 3. Section and Page Boosting
        candidates = apply_section_and_page_boosting(primary_query, candidates)

        # 4. Reranking Stage
        rerank_start = time.perf_counter()
        reranked_candidates = self.reranker.rerank(
            query=primary_query,
            candidates=candidates,
            top_k=settings.RERANKER_CANDIDATE_LIMIT,
        )
        rerank_ms = round((time.perf_counter() - rerank_start) * 1000, 2)

        # 5. Context Diversity Selection
        final_candidates = apply_diversity_selection(
            candidates=reranked_candidates,
            top_k=capped_top_k,
            max_per_section=2,
        )

        total_ms = round((time.perf_counter() - start_time) * 1000, 2)
        latencies = {
            "retrieval_ms": retrieval_ms,
            "rerank_ms": rerank_ms,
            "total_ms": total_ms,
        }

        logger.info(
            f"AdvancedRetrieval completed in {total_ms}ms (retrieval={retrieval_ms}ms, rerank={rerank_ms}ms). "
            f"Returned {len(final_candidates)} candidates."
        )
        return final_candidates, latencies

    def search(
        self,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 5,
        mode: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[RetrievalResult]:
        """Performs document-isolated retrieval returning a list of RetrievalResult objects."""
        candidates, _ = self.search_candidates(
            query=query,
            document_id=document_id,
            top_k=top_k,
            mode=mode,
            db=db,
        )

        results: List[RetrievalResult] = []
        for c in candidates:
            results.append(
                RetrievalResult(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    text=c.text,
                    score=round(float(c.final_score), 4),
                    page_number=c.page_number,
                    section=c.section,
                    document_type=c.document_type,
                    extraction_method=c.extraction_method,
                    vector_score=round(float(c.vector_score), 4) if c.vector_score is not None else None,
                    keyword_score=round(float(c.keyword_score), 4) if c.keyword_score is not None else None,
                    rerank_score=round(float(c.rerank_score), 4) if c.rerank_score is not None else None,
                )
            )
        return results

    def search_document(
        self,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 5,
        mode: Optional[str] = None,
    ) -> RetrievalResponse:
        """API wrapper verifying document existence and returning structured RetrievalResponse."""
        session = self.db
        if session:
            doc = session.query(Document).filter(Document.id == document_id).first()
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document with ID '{document_id}' not found."
                )

        candidates, latencies = self.search_candidates(
            query=query,
            document_id=document_id,
            top_k=top_k,
            mode=mode,
            db=session,
        )

        results: List[RetrievalResult] = []
        for c in candidates:
            results.append(
                RetrievalResult(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    text=c.text,
                    score=round(float(c.final_score), 4),
                    page_number=c.page_number,
                    section=c.section,
                    document_type=c.document_type,
                    extraction_method=c.extraction_method,
                    vector_score=round(float(c.vector_score), 4) if c.vector_score is not None else None,
                    keyword_score=round(float(c.keyword_score), 4) if c.keyword_score is not None else None,
                    rerank_score=round(float(c.rerank_score), 4) if c.rerank_score is not None else None,
                )
            )

        effective_mode = mode or settings.RETRIEVAL_MODE
        return RetrievalResponse(
            query=query,
            document_id=document_id,
            top_k=min(max(1, top_k), settings.MAX_TOP_K),
            results=results,
            retrieval_mode=effective_mode,
            latency_ms=latencies,
        )
