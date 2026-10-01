import logging
import re
from typing import List

from app.core.config import settings

logger = logging.getLogger(__name__)


# Deterministic expansion mappings for common complex document questions
EXPANSION_RULES = {
    "stop paying": ["premium payment failure", "late payment", "non-payment consequences", "grace period"],
    "cancel policy": ["policy termination", "cancellation procedure", "notice period", "refund"],
    "pre existing": ["pre-existing condition", "exclusion period", "waiting period"],
    "waiting period": ["exclusion period", "pre-existing conditions", "qualifying period"],
    "deductible": ["out of pocket expense", "co-pay", "claim threshold"],
    "coverage limit": ["maximum benefit", "sum insured", "policy limit"],
}


class QueryExpander:
    """Query normalization and deterministic query expansion service for retrieval enhancement."""

    def normalize(self, query: str) -> str:
        """Normalizes contractions and formatting in search queries."""
        q = query.strip()
        q = re.sub(r"what's", "what is", q, flags=re.IGNORECASE)
        q = re.sub(r"where's", "where is", q, flags=re.IGNORECASE)
        q = re.sub(r"don't", "do not", q, flags=re.IGNORECASE)
        q = re.sub(r"can't", "cannot", q, flags=re.IGNORECASE)
        q = re.sub(r"isn't", "is not", q, flags=re.IGNORECASE)
        return q

    def expand(self, query: str) -> List[str]:
        """Expands query into a list of retrieval queries if QUERY_EXPANSION_ENABLED is set."""
        normalized_q = self.normalize(query)
        queries = [normalized_q]

        if not settings.QUERY_EXPANSION_ENABLED:
            return queries

        q_lower = normalized_q.lower()
        for phrase, expansions in EXPANSION_RULES.items():
            if phrase in q_lower:
                for exp in expansions:
                    if exp not in queries:
                        queries.append(exp)

        logger.info(f"Query expansion produced {len(queries)} search queries for original: '{query}'")
        return queries
