import os
import uuid
import pathlib
import io
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.core.logging import logger
from app.db.models.document import Document, DocumentType, DocumentStatus
from app.db.models.document_chunk import DocumentChunk
from app.schemas.retrieval import IndexStatusResponse, RetrievalRequest, RetrievalResponse
from app.services.storage.base import StorageProvider
from app.services.storage.local_storage import LocalFileStorage
from app.services.processing.pipeline import DocumentProcessingPipeline
from app.services.vector_store.chroma_store import ChromaVectorStore
from app.services.vector_store.indexer import EmbeddingIndexService
from app.services.vector_store.retrieval import RetrievalService

class DocumentService:
    """Service layer for document validation, storage, DB management, processing, vector indexing, and retrieval."""

    def __init__(self, db: Session, storage: Optional[StorageProvider] = None):
        self.db = db
        self.storage = storage or LocalFileStorage()
        self.vector_store = ChromaVectorStore()

    def validate_file(self, file: UploadFile, content: bytes) -> tuple[str, str]:
        """Validate extension, MIME type, size, and header magic bytes."""
        file_size = len(content)
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty. Uploaded file must be greater than 0 bytes."
            )

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB} MB."
            )

        original_filename = pathlib.Path(file.filename or "document").name
        ext = pathlib.Path(original_filename).suffix.lower()

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file extension '{ext}'. Allowed types: PDF, DOCX, TXT."
            )

        if ext == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File header validation failed: File content does not match standard PDF magic bytes."
                )
        elif ext == ".docx":
            if not content.startswith(b"PK\x03\x04"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File header validation failed: File content does not match standard DOCX ZIP header."
                )
        elif ext == ".txt":
            try:
                content[:1024].decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File header validation failed: File content is binary or invalid UTF-8 text."
                )

        return original_filename, ext

    async def upload_document(
        self,
        file: UploadFile,
        document_type: str,
        user_id: Optional[str] = None
    ) -> Document:
        content = await file.read()
        original_filename, ext = self.validate_file(file, content)
        
        try:
            doc_type_enum = DocumentType(document_type.lower())
        except ValueError:
            valid_types = [t.value for t in DocumentType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document_type '{document_type}'. Allowed types: {', '.join(valid_types)}"
            )

        target_user_id = uuid.UUID(user_id or settings.MOCK_USER_ID)
        doc_uuid = uuid.uuid4()
        stored_filename = f"{doc_uuid}{ext}"
        
        file_stream = io.BytesIO(content)
        file_path = await self.storage.save(file_stream, stored_filename)

        db_doc = Document(
            id=doc_uuid,
            user_id=target_user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            document_type=doc_type_enum,
            status=DocumentStatus.UPLOADED
        )
        
        self.db.add(db_doc)
        self.db.commit()
        self.db.refresh(db_doc)

        logger.info(f"Document uploaded: ID {db_doc.id}. Triggering automatic processing & indexing pipeline...")
        pipeline = DocumentProcessingPipeline(self.db)
        processed_doc = pipeline.process_document(db_doc.id)
        return processed_doc

    def process_document_manual(self, document_id: uuid.UUID) -> Document:
        doc = self.get_document_by_id(document_id)
        pipeline = DocumentProcessingPipeline(self.db)
        return pipeline.process_document(doc.id)

    def reindex_document(self, document_id: uuid.UUID) -> Document:
        index_service = EmbeddingIndexService(self.db)
        return index_service.index_document(document_id)

    def get_index_status(self, document_id: uuid.UUID) -> IndexStatusResponse:
        doc = self.get_document_by_id(document_id)
        chunks_count = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .count()
        )
        indexed_count = self.vector_store.get_indexed_count(str(document_id))

        emb_status_str = doc.embedding_status.value if hasattr(doc.embedding_status, "value") else str(doc.embedding_status)
        proc_status_str = doc.status.value if hasattr(doc.status, "value") else str(doc.status)

        return IndexStatusResponse(
            document_id=doc.id,
            processing_status=proc_status_str,
            embedding_status=emb_status_str,
            embedding_error=doc.embedding_error,
            chunk_count=chunks_count,
            indexed_count=indexed_count,
            embedding_model=doc.embedding_model or settings.EMBEDDING_MODEL,
            indexed_at=doc.indexed_at
        )

    def search_document(
        self,
        document_id: uuid.UUID,
        req: RetrievalRequest
    ) -> RetrievalResponse:
        retrieval_service = RetrievalService(self.db, vector_store=self.vector_store)
        return retrieval_service.search_document(
            query=req.query,
            document_id=document_id,
            top_k=req.top_k
        )

    def list_documents(self, user_id: Optional[str] = None) -> List[Document]:
        target_user_id = uuid.UUID(user_id or settings.MOCK_USER_ID)
        return (
            self.db.query(Document)
            .filter(Document.user_id == target_user_id)
            .order_by(desc(Document.created_at))
            .all()
        )

    def get_document_by_id(self, document_id: uuid.UUID, user_id: Optional[str] = None) -> Document:
        target_user_id = uuid.UUID(user_id or settings.MOCK_USER_ID)
        doc = (
            self.db.query(Document)
            .filter(Document.id == document_id, Document.user_id == target_user_id)
            .first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found."
            )
        return doc

    def get_document_chunks(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        self.get_document_by_id(document_id)
        return (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

    async def delete_document(self, document_id: uuid.UUID, user_id: Optional[str] = None) -> bool:
        doc = self.get_document_by_id(document_id, user_id=user_id)
        
        # 1. Delete physical storage file
        await self.storage.delete(doc.file_path)
        
        # 2. Delete ChromaDB vector points
        self.vector_store.delete_document(str(doc.id))

        # 3. Delete PostgreSQL document (cascades to document_chunks)
        self.db.delete(doc)
        self.db.commit()

        logger.info(f"Document ID '{document_id}', physical file, PostgreSQL chunks, and Chroma vectors deleted.")
        return True
