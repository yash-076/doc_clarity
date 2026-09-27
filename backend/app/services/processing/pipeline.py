import uuid
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.db.models.document import Document, DocumentStatus
from app.db.models.document_chunk import DocumentChunk
from app.services.extraction import get_extractor_for_file
from app.services.processing.cleaner import TextCleaner
from app.services.processing.structure import StructureDetector
from app.services.processing.chunker import DocumentChunker
from app.services.vector_store.indexer import EmbeddingIndexService
from app.services.analysis_service import DocumentAnalysisService

class DocumentProcessingPipeline:
    """Orchestrates document loading, extraction, OCR, cleaning, structure detection, chunking, and vector indexing."""

    def __init__(self, db: Session):
        self.db = db
        self.cleaner = TextCleaner()
        self.structure_detector = StructureDetector()
        self.chunker = DocumentChunker()

    def process_document(self, document_id: uuid.UUID) -> Document:
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document with ID '{document_id}' not found.")

        logger.info(f"Processing started for document_id={doc.id}, file={doc.original_filename}")
        
        # 1. Update status to processing
        doc.status = DocumentStatus.PROCESSING
        doc.processing_error = None
        self.db.commit()

        try:
            # 2. Get extractor
            extractor = get_extractor_for_file(doc.file_path)
            
            # 3. Extract content (with automatic OCR fallback on scanned pages)
            raw_elements = extractor.extract(doc.file_path)
            if not raw_elements:
                raise ValueError("No text or content could be extracted from document.")

            # 4. Clean extracted text
            cleaned_elements = self.cleaner.clean_elements(raw_elements)

            # 5. Detect structure (sections, headings)
            structured_elements = self.structure_detector.detect_structure(cleaned_elements)

            # 6. Generate semantic chunks
            chunk_data_list = self.chunker.create_chunks(
                elements=structured_elements,
                document_id=str(doc.id),
                document_type=doc.document_type.value if hasattr(doc.document_type, "value") else str(doc.document_type)
            )

            # 7. Delete existing chunks for this document (reprocessing safety)
            self.db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            
            # Mark existing analysis as stale
            try:
                analysis_service = DocumentAnalysisService()
                analysis_service.mark_stale(self.db, doc.id)
            except Exception:
                pass
            self.db.commit()

            # 8. Persist new chunks to PostgreSQL
            new_chunks = []
            for item in chunk_data_list:
                chunk_obj = DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    chunk_index=item["chunk_index"],
                    text=item["text"],
                    page_number=item["page_number"],
                    section=item["section"],
                    document_type=item["document_type"],
                    extraction_method=item["extraction_method"],
                    metadata_payload=item["metadata_payload"]
                )
                new_chunks.append(chunk_obj)

            self.db.add_all(new_chunks)

            # 9. Update document status to ready
            doc.status = DocumentStatus.READY
            doc.processing_error = None
            self.db.commit()
            self.db.refresh(doc)

            logger.info(f"Processing completed for document_id={doc.id}. Total chunks generated={len(new_chunks)}")

            # 10. Automatically trigger Phase 3 Vector Indexing
            index_service = EmbeddingIndexService(self.db)
            indexed_doc = index_service.index_document(doc.id)
            return indexed_doc

        except Exception as e:
            self.db.rollback()
            err_detail = str(e)
            logger.error(f"Processing failed for document_id={doc.id}: {err_detail}")
            
            doc.status = DocumentStatus.FAILED
            doc.processing_error = err_detail
            self.db.commit()
            self.db.refresh(doc)
            return doc
