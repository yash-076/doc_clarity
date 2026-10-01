import uuid
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class RetrievedCandidate:
    """Represents a chunk candidate retrieved during vector, keyword, or hybrid retrieval."""
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    text: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    document_type: str = "general"
    extraction_method: str = "text"
    
    # Raw scores
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    rerank_score: Optional[float] = None
    
    # Normalized scores
    norm_vector_score: float = 0.0
    norm_keyword_score: float = 0.0
    
    # Fused & final scores
    hybrid_score: float = 0.0
    final_score: float = 0.0


def normalize_scores(scores: List[float]) -> List[float]:
    """Min-max normalizes a list of numerical scores into [0.0, 1.0]."""
    if not scores:
        return []
    min_val = min(scores)
    max_val = max(scores)
    if max_val == min_val:
        return [1.0 if max_val > 0 else 0.0 for _ in scores]
    return [(s - min_val) / (max_val - min_val) for s in scores]
