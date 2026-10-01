import logging
import re
import uuid
from typing import List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document_chunk import DocumentChunk
from app.services.retrieval.models import RetrievedCandidate, normalize_scores

logger = logging.getLogger(__name__)


class KeywordRetriever:
    """Document-isolated keyword search retriever using PostgreSQL Full-Text Search (FTS) with fallback."""

    def search(
        self,
        db: Session,
        query: str,
        document_id: uuid.UUID,
        top_k: int = 15,
    ) -> List[RetrievedCandidate]:
        """Performs keyword search against PostgreSQL FTS or fallback term matching."""
        capped_top_k = min(max(1, top_k), settings.MAX_TOP_K)
        logger.info(f"Keyword search for document_id={document_id}, top_k={capped_top_k}")

        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        bind = db.get_bind()
        dialect_name = bind.dialect.name if bind else "postgresql"

        candidates: List[RetrievedCandidate] = []
        raw_scores: List[float] = []

        if dialect_name == "postgresql":
            try:
                # PostgreSQL Full-Text Search using tsvector and plainto_tsquery
                ts_vector = func.to_tsvector(
                    'english',
                    func.coalesce(DocumentChunk.text, '') + ' ' + func.coalesce(DocumentChunk.section, '')
                )
                ts_query = func.plainto_tsquery('english', cleaned_query)
                rank_col = func.ts_rank_cd(ts_vector, ts_query).label('rank')

                results = (
                    db.query(DocumentChunk, rank_col)
                    .filter(DocumentChunk.document_id == document_id)
                    .filter(ts_vector.op('@@')(ts_query))
                    .order_by(rank_col.desc())
                    .limit(capped_top_k)
                    .all()
                )

                for chunk, rank in results:
                    score = float(rank)
                    raw_scores.append(score)
                    candidates.append(
                        RetrievedCandidate(
                            chunk_id=chunk.id,
                            document_id=chunk.document_id,
                            text=chunk.text,
                            page_number=chunk.page_number,
                            section=chunk.section,
                            document_type=chunk.document_type,
                            extraction_method=chunk.extraction_method,
                            keyword_score=score,
                        )
                    )
            except Exception as e:
                logger.warning(f"PostgreSQL FTS query failed, using term-matching fallback: {str(e)}")
                candidates = []
                raw_scores = []

        # If dialect is not postgresql or FTS yielded 0 candidates, use term-matching fallback
        if not candidates:
            candidates, raw_scores = self._fallback_term_search(
                db=db,
                query=cleaned_query,
                document_id=document_id,
                top_k=capped_top_k
            )

        norm_scores = normalize_scores(raw_scores)
        for idx, norm_score in enumerate(norm_scores):
            candidates[idx].norm_keyword_score = norm_score

        return candidates

    def _fallback_term_search(
        self,
        db: Session,
        query: str,
        document_id: uuid.UUID,
        top_k: int
    ) -> tuple[List[RetrievedCandidate], List[float]]:
        """Fallback term matching for non-PostgreSQL DBs or fallback queries."""
        keywords = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
        if not keywords:
            keywords = [w.lower() for w in re.findall(r'\w+', query)]

        all_chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .all()
        )

        scored_chunks = []
        for chunk in all_chunks:
            chunk_text_lower = (chunk.text or "").lower()
            section_lower = (chunk.section or "").lower()
            combined_text = f"{chunk_text_lower} {section_lower}"

            score = 0.0
            # Exact phrase match bonus
            if query.lower() in combined_text:
                score += 5.0

            for kw in keywords:
                # Section match bonus
                if kw in section_lower:
                    score += 2.0
                # Text occurrence count
                count = combined_text.count(kw)
                score += count * 1.0

            if score > 0:
                scored_chunks.append((chunk, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = scored_chunks[:top_k]

        candidates = []
        raw_scores = []
        for chunk, score in top_chunks:
            raw_scores.append(score)
            candidates.append(
                RetrievedCandidate(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    document_type=chunk.document_type,
                    extraction_method=chunk.extraction_method,
                    keyword_score=score,
                )
            )

        return candidates, raw_scores
