import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models.document import Document, EmbeddingStatus
from app.db.models.document_chunk import DocumentChunk
from app.services.embeddings import get_embedding_service, BaseEmbeddingService
from app.services.vector_store.base import VectorStore
from app.services.vector_store.chroma_store import ChromaVectorStore

class EmbeddingIndexService:
    """Service for generating vector embeddings and synchronizing chunks with ChromaDB."""

    def __init__(
        self,
        db: Session,
        embedding_service: Optional[BaseEmbeddingService] = None,
        vector_store: Optional[VectorStore] = None
    ):
        self.db = db
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or ChromaVectorStore()

    def index_document(self, document_id: uuid.UUID) -> Document:
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document with ID '{document_id}' not found.")

        chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        if not chunks:
            err_msg = f"Cannot index document '{document_id}': No chunks found in PostgreSQL."
            logger.warning(err_msg)
            doc.embedding_status = EmbeddingStatus.FAILED
            doc.embedding_error = err_msg
            self.db.commit()
            return doc

        logger.info(f"Indexing vector embeddings for document_id={doc.id}, chunk_count={len(chunks)}")
        
        # 1. Update status to indexing
        doc.embedding_status = EmbeddingStatus.INDEXING
        doc.embedding_error = None
        doc.embedding_model = self.embedding_service.model_name
        self.db.commit()

        try:
            # 2. Clear old ChromaDB vectors for re-indexing safety
            self.vector_store.delete_document(str(doc.id))

            # 3. Extract text payloads
            chunk_texts = [c.text for c in chunks]

            # 4. Batch generate dense vector embeddings
            embeddings = self.embedding_service.embed_documents(chunk_texts)

            # 5. Build vectors & metadata arrays
            ids = [str(c.id) for c in chunks]
            metadatas = []

            for c in chunks:
                meta = {
                    "document_id": str(doc.id),
                    "chunk_id": str(c.id),
                    "chunk_index": c.chunk_index,
                    "page_number": c.page_number if c.page_number is not None else "",
                    "section": c.section or "",
                    "document_type": c.document_type,
                    "extraction_method": c.extraction_method,
                    "embedding_model": self.embedding_service.model_name
                }
                metadatas.append(meta)

            # 6. Add points to ChromaDB
            self.vector_store.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=metadatas
            )

            # 7. Update status to indexed
            doc.embedding_status = EmbeddingStatus.INDEXED
            doc.embedding_error = None
            doc.indexed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(doc)

            logger.info(f"Vector indexing completed for document_id={doc.id}. Indexed vectors: {len(ids)}")
            return doc

        except Exception as e:
            self.db.rollback()
            err_msg = f"Embedding indexing failed: {str(e)}"
            logger.error(f"Error indexing document_id={doc.id}: {err_msg}")
            
            doc.embedding_status = EmbeddingStatus.FAILED
            doc.embedding_error = err_msg
            self.db.commit()
            self.db.refresh(doc)
            return doc
