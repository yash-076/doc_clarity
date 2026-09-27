import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentDeleteResponse
)
from app.schemas.processing import ChunkListResponse, ChunkResponse
from app.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    IndexStatusResponse
)
from app.schemas.rag import (
    RAGQuestionRequest,
    RAGAnswerResponse
)
from app.schemas.analysis import (
    AnalysisRequest,
    DocumentAnalysisResponse
)
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService
from app.services.analysis_service import DocumentAnalysisService

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload, extract, chunk, and vector index a document",
    description="Validates file, extracts text/OCR, generates semantic chunks, and indexes embeddings into ChromaDB."
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return await service.upload_document(file=file, document_type=document_type)

@router.get(
    "",
    response_model=List[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List all uploaded documents",
    description="Returns a list of all documents belonging to the user, sorted by created_at DESC."
)
def list_documents(db: Session = Depends(get_db)):
    service = DocumentService(db)
    return service.list_documents()

@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document details",
    description="Returns metadata for a specific document by UUID."
)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    service = DocumentService(db)
    return service.get_document_by_id(document_id)

@router.post(
    "/{document_id}/process",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocess document extraction, chunking, and indexing",
    description="Deletes existing chunks and Chroma vectors, then runs the complete extraction, OCR, chunking, and indexing pipeline."
)
def process_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    service = DocumentService(db)
    return service.process_document_manual(document_id)

@router.post(
    "/{document_id}/index",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-index document vector embeddings",
    description="Generates fresh vector embeddings for document chunks and updates ChromaDB collection."
)
def reindex_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    service = DocumentService(db)
    return service.reindex_document(document_id)

@router.get(
    "/{document_id}/index-status",
    response_model=IndexStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document vector index status",
    description="Returns indexing status, total chunks, indexed vector count, and embedding model information."
)
def get_index_status(document_id: uuid.UUID, db: Session = Depends(get_db)):
    service = DocumentService(db)
    return service.get_index_status(document_id)

@router.post(
    "/{document_id}/search",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform document-isolated semantic similarity search",
    description="Embeds natural language query and retrieves top K relevant chunks strictly filtered to the specified document ID."
)
def search_document(
    document_id: uuid.UUID,
    req: RetrievalRequest,
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return service.search_document(document_id=document_id, req=req)

@router.get(
    "/{document_id}/chunks",
    response_model=ChunkListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chunks generated for a document",
    description="Returns list of chunks created for a document ordered by chunk_index ASC (for developer inspection)."
)
def get_document_chunks(document_id: uuid.UUID, db: Session = Depends(get_db)):
    service = DocumentService(db)
    chunks = service.get_document_chunks(document_id)
    return ChunkListResponse(
        document_id=document_id,
        total_chunks=len(chunks),
        chunks=[ChunkResponse.model_validate(c) for c in chunks]
    )

@router.post(
    "/{document_id}/ask",
    response_model=RAGAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about a specific document (RAG + Gemini)",
    description="Embeds user question, retrieves relevant document chunks, constructs grounded context with prompt injection protection, and generates grounded answer with Gemini LLM."
)
async def ask_document(
    document_id: uuid.UUID,
    req: RAGQuestionRequest,
    db: Session = Depends(get_db)
):
    rag_service = RAGService()
    return await rag_service.answer_question(
        db=db,
        document_id=document_id,
        question=req.question,
        top_k=req.top_k,
    )

@router.post(
    "/{document_id}/analyze",
    response_model=DocumentAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate or return cached automatic document analysis",
    description="Runs multi-query targeted retrieval across document facets, constructs grounded context, generates executive summary, key points, dates, financials, obligations, exclusions, and risk attention items with Gemini LLM."
)
async def analyze_document(
    document_id: uuid.UUID,
    req: Optional[AnalysisRequest] = None,
    db: Session = Depends(get_db)
):
    force_refresh = req.force_refresh if req else False
    analysis_service = DocumentAnalysisService()
    return await analysis_service.get_or_create_analysis(
        db=db,
        document_id=document_id,
        force_refresh=force_refresh
    )

@router.get(
    "/{document_id}/analysis",
    response_model=DocumentAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cached document analysis",
    description="Retrieves existing cached document analysis from PostgreSQL without calling LLM."
)
def get_document_analysis(
    document_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    analysis_service = DocumentAnalysisService()
    return analysis_service.get_existing_analysis(db=db, document_id=document_id)

@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a document",
    description="Deletes physical file from storage, removes associated chunks, removes ChromaDB vectors, and deletes record from PostgreSQL."
)
async def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    service = DocumentService(db)
    await service.delete_document(document_id)
    return DocumentDeleteResponse(
        message="Document, physical file, chunks, and vector embeddings deleted successfully.",
        id=document_id
    )
