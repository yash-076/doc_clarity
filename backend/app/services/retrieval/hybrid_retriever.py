import logging
import uuid
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.retrieval.models import RetrievedCandidate
from app.services.retrieval.vector_retriever import VectorRetriever
from app.services.retrieval.keyword_retriever import KeywordRetriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combines vector similarity search and keyword search candidates into a unified hybrid ranking."""

    def __init__(
        self,
        vector_retriever: Optional[VectorRetriever] = None,
        keyword_retriever: Optional[KeywordRetriever] = None,
    ):
        self.vector_retriever = vector_retriever or VectorRetriever()
        self.keyword_retriever = keyword_retriever or KeywordRetriever()

    def search(
        self,
        query: str,
        document_id: uuid.UUID,
        db: Optional[Session] = None,
        vector_candidate_k: Optional[int] = None,
        keyword_candidate_k: Optional[int] = None,
        vector_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
        fusion_method: Optional[str] = None,
    ) -> List[RetrievedCandidate]:
        """Executes vector and keyword search, deduplicates by chunk_id, and computes hybrid scores."""
        v_k = vector_candidate_k or settings.VECTOR_CANDIDATE_K
        k_k = keyword_candidate_k or settings.KEYWORD_CANDIDATE_K
        w_vec = vector_weight if vector_weight is not None else settings.VECTOR_SEARCH_WEIGHT
        w_key = keyword_weight if keyword_weight is not None else settings.KEYWORD_SEARCH_WEIGHT
        f_method = fusion_method or settings.HYBRID_FUSION_METHOD

        logger.info(f"HybridRetriever search: doc_id={document_id}, mode={f_method}, v_k={v_k}, k_k={k_k}")

        # 1. Retrieve Vector Candidates
        try:
            vector_candidates = self.vector_retriever.search(query, document_id, top_k=v_k)
        except Exception as e:
            logger.error(f"Vector retrieval failed during hybrid search: {str(e)}")
            vector_candidates = []

        # 2. Retrieve Keyword Candidates (if DB session is provided)
        keyword_candidates: List[RetrievedCandidate] = []
        if db:
            try:
                keyword_candidates = self.keyword_retriever.search(db, query, document_id, top_k=k_k)
            except Exception as e:
                logger.error(f"Keyword retrieval failed during hybrid search: {str(e)}")
                keyword_candidates = []

        # 3. Build candidate map indexed by chunk_id
        candidate_map: Dict[uuid.UUID, RetrievedCandidate] = {}
        vector_ranks: Dict[uuid.UUID, int] = {}
        keyword_ranks: Dict[uuid.UUID, int] = {}

        for rank, c in enumerate(vector_candidates, start=1):
            candidate_map[c.chunk_id] = c
            vector_ranks[c.chunk_id] = rank

        for rank, c in enumerate(keyword_candidates, start=1):
            keyword_ranks[c.chunk_id] = rank
            if c.chunk_id in candidate_map:
                existing = candidate_map[c.chunk_id]
                existing.keyword_score = c.keyword_score
                existing.norm_keyword_score = c.norm_keyword_score
            else:
                candidate_map[c.chunk_id] = c

        # 4. Compute Hybrid Scores (Weighted or RRF)
        rrf_k = settings.RRF_K
        fused_candidates: List[RetrievedCandidate] = []

        for chunk_id, c in candidate_map.items():
            if f_method == "rrf":
                score_vec = (1.0 / (rrf_k + vector_ranks[chunk_id])) if chunk_id in vector_ranks else 0.0
                score_key = (1.0 / (rrf_k + keyword_ranks[chunk_id])) if chunk_id in keyword_ranks else 0.0
                c.hybrid_score = score_vec + score_key
            else:
                # Weighted combination
                c.hybrid_score = (w_vec * c.norm_vector_score) + (w_key * c.norm_keyword_score)
            
            c.final_score = c.hybrid_score
            fused_candidates.append(c)

        # 5. Sort candidates descending by hybrid_score
        fused_candidates.sort(key=lambda x: x.hybrid_score, reverse=True)
        logger.info(f"Hybrid search produced {len(fused_candidates)} deduplicated candidates.")
        return fused_candidates
