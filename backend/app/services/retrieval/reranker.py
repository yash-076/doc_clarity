import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.config import settings
from app.services.retrieval.models import RetrievedCandidate

logger = logging.getLogger(__name__)


class BaseReranker(ABC):
    """Abstract Base Class for candidate rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[RetrievedCandidate],
        top_k: int = 5,
    ) -> List[RetrievedCandidate]:
        """Reranks candidate chunks for a given query."""
        pass


class PassThroughReranker(BaseReranker):
    """Pass-through reranker when reranking is disabled or unavailable."""

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedCandidate],
        top_k: int = 5,
    ) -> List[RetrievedCandidate]:
        logger.info(f"PassThroughReranker: Returning top {top_k} candidates based on hybrid score.")
        for c in candidates:
            c.rerank_score = c.hybrid_score
            c.final_score = c.hybrid_score
        return candidates[:top_k]


class SentenceTransformerReranker(BaseReranker):
    """Local CrossEncoder reranker using sentence-transformers CrossEncoder."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.RERANKER_MODEL
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading local Reranker model: '{self.model_name}'...")
            self.model = CrossEncoder(self.model_name)
            logger.info(f"Local Reranker model '{self.model_name}' loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Failed to load CrossEncoder model '{self.model_name}': {str(e)}. "
                "Reranker will fallback to score pass-through."
            )
            self.model = None

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedCandidate],
        top_k: int = 5,
    ) -> List[RetrievedCandidate]:
        if not candidates:
            return []

        if not settings.RERANKER_ENABLED or self.model is None:
            return PassThroughReranker().rerank(query, candidates, top_k)

        limit = min(len(candidates), settings.RERANKER_CANDIDATE_LIMIT)
        bounded_candidates = candidates[:limit]

        try:
            # Build (query, text) pairs
            pairs = [(query, c.text) for c in bounded_candidates]
            scores = self.model.predict(pairs)

            for idx, score in enumerate(scores):
                bounded_candidates[idx].rerank_score = float(score)
                bounded_candidates[idx].final_score = float(score)

            bounded_candidates.sort(key=lambda x: x.final_score, reverse=True)
            return bounded_candidates[:top_k]
        except Exception as e:
            logger.error(f"Error during reranking evaluation: {str(e)}. Falling back to pass-through.")
            return PassThroughReranker().rerank(query, candidates, top_k)


# Global singleton instance
_reranker_instance: Optional[BaseReranker] = None


def get_reranker() -> BaseReranker:
    """Returns initialized singleton Reranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        if settings.RERANKER_ENABLED:
            _reranker_instance = SentenceTransformerReranker()
        else:
            _reranker_instance = PassThroughReranker()
    return _reranker_instance
