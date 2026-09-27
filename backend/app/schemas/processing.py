from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ExtractedContent(BaseModel):
    page_number: Optional[int] = None
    text: str
    section: Optional[str] = None
    content_type: str = "paragraph"
    extraction_method: str = "text"

class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    document_type: str
    extraction_method: str
    metadata_payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChunkListResponse(BaseModel):
    document_id: UUID
    total_chunks: int
    chunks: List[ChunkResponse]
