from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Top K relevant chunks to retrieve")

class RetrievalResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    text: str
    score: float
    page_number: Optional[int] = None
    section: Optional[str] = None
    document_type: str
    extraction_method: str
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    rerank_score: Optional[float] = None

class RetrievalResponse(BaseModel):
    query: str
    document_id: UUID
    top_k: int
    results: List[RetrievalResult]
    retrieval_mode: Optional[str] = "hybrid"
    latency_ms: Optional[dict] = None


class IndexStatusResponse(BaseModel):
    document_id: UUID
    processing_status: str
    embedding_status: str
    embedding_error: Optional[str] = None
    chunk_count: int
    indexed_count: int
    embedding_model: str
    indexed_at: Optional[datetime] = None
