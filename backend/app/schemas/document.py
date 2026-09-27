from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.db.models.document import DocumentType, DocumentStatus, EmbeddingStatus

class DocumentBase(BaseModel):
    original_filename: str
    document_type: DocumentType
    file_size: int

class DocumentCreate(DocumentBase):
    user_id: UUID
    stored_filename: str
    file_path: str
    mime_type: str

class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    document_type: DocumentType
    status: DocumentStatus
    file_size: int
    processing_error: Optional[str] = None
    embedding_status: Optional[EmbeddingStatus] = EmbeddingStatus.PENDING
    embedding_error: Optional[str] = None
    embedding_model: Optional[str] = None
    indexed_at: Optional[datetime] = None
    has_ocr: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentDetailResponse(DocumentResponse):
    user_id: UUID
    stored_filename: str
    file_path: str
    mime_type: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentDeleteResponse(BaseModel):
    message: str
    id: UUID
