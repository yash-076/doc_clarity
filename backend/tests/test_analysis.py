import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app
from app.db.models.document import Document, DocumentStatus, EmbeddingStatus
from app.db.models.document_analysis import DocumentAnalysis
from app.schemas.analysis import DocumentAnalysisResponse
from app.services.analysis_service import DocumentAnalysisService
from app.services.vector_store.retrieval import RetrievalResult

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Document Analysis Service Unit Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analysis_document_not_found(db_session):
    analysis_service = DocumentAnalysisService()
    non_existent_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await analysis_service.get_or_create_analysis(
            db=db_session,
            document_id=non_existent_id,
            force_refresh=False,
        )
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_analysis_document_not_ready(db_session):
    doc = Document(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        original_filename="processing.pdf",
        stored_filename="processing_123.pdf",
        file_path="/tmp/processing.pdf",
        file_size=1000,
        mime_type="application/pdf",
        document_type="legal",
        status=DocumentStatus.PROCESSING.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    analysis_service = DocumentAnalysisService()
    with pytest.raises(HTTPException) as exc_info:
        await analysis_service.get_or_create_analysis(
            db=db_session,
            document_id=doc.id,
        )
    assert exc_info.value.status_code == 409
    assert "not complete" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_analysis_generation_and_citation_mapping(db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="contract.pdf",
        stored_filename="contract_456.pdf",
        file_path="/tmp/contract.pdf",
        file_size=3000,
        mime_type="application/pdf",
        document_type="legal",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    chunk_id_1 = uuid.uuid4()
    chunk_1 = RetrievalResult(
        chunk_id=chunk_id_1,
        document_id=doc_id,
        text="The tenant shall pay a monthly rent of $2,500 due on the 1st of each month.",
        score=0.92,
        page_number=2,
        section="Rent & Payment",
        document_type="legal",
        extraction_method="native_pdf",
    )

    mock_retrieval = MagicMock()
    mock_retrieval.search.return_value = [chunk_1]

    mock_llm_output = """{
      "summary": "This lease contract defines rental terms between landlord and tenant with monthly payment requirements.",
      "key_points": [
        {
          "title": "Monthly Rent Obligation",
          "description": "Tenant must pay $2,500 monthly on the 1st day.",
          "citation_ids": ["SOURCE_1"]
        }
      ],
      "important_dates": [
        {
          "description": "Monthly Due Date",
          "date": "1st of each month",
          "citation_ids": ["SOURCE_1"]
        }
      ],
      "financial_terms": [
        {
          "description": "Monthly Rent Amount",
          "amount": "$2,500",
          "citation_ids": ["SOURCE_1"]
        }
      ],
      "obligations": [
        {
          "party": "Tenant",
          "description": "Pay monthly rent on time.",
          "citation_ids": ["SOURCE_1"]
        }
      ],
      "exclusions": [],
      "attention_items": [
        {
          "title": "Strict Payment Deadline",
          "description": "Rent is strictly due on the 1st.",
          "category": "deadline",
          "severity": "high",
          "citation_ids": ["SOURCE_1"]
        }
      ]
    }"""

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = mock_llm_output

    analysis_service = DocumentAnalysisService(
        retrieval_service=mock_retrieval,
        llm_service=mock_llm,
    )

    resp = await analysis_service.get_or_create_analysis(
        db=db_session,
        document_id=doc_id,
        force_refresh=True,
    )

    assert resp.document_id == doc_id
    assert "lease contract" in resp.summary.lower()
    assert len(resp.key_points) == 1
    assert resp.key_points[0].title == "Monthly Rent Obligation"
    assert len(resp.key_points[0].citations) == 1
    assert resp.key_points[0].citations[0].chunk_id == chunk_id_1
    assert resp.key_points[0].citations[0].page_number == 2
    assert resp.key_points[0].citations[0].section == "Rent & Payment"

    assert len(resp.financial_terms) == 1
    assert resp.financial_terms[0].amount == "$2,500"

    assert len(resp.attention_items) == 1
    assert resp.attention_items[0].severity == "high"
    assert resp.attention_items[0].category == "deadline"

    # Verify cached analysis is stored in DB
    stored_db = db_session.query(DocumentAnalysis).filter(DocumentAnalysis.document_id == doc_id).first()
    assert stored_db is not None
    assert stored_db.is_stale is False


@pytest.mark.asyncio
async def test_analysis_caching_behavior(db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="cached.pdf",
        stored_filename="cached_789.pdf",
        file_path="/tmp/cached.pdf",
        file_size=1500,
        mime_type="application/pdf",
        document_type="insurance",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)

    # Insert pre-cached analysis record
    cached_record = DocumentAnalysis(
        id=uuid.uuid4(),
        document_id=doc_id,
        analysis_version=1,
        summary="Cached policy analysis overview.",
        analysis_json={
            "summary": "Cached policy analysis overview.",
            "key_points": [],
            "important_dates": [],
            "financial_terms": [],
            "obligations": [],
            "exclusions": [],
            "attention_items": [],
        },
        embedding_model="BAAI/bge-small-en-v1.5",
        llm_model="gemini-2.5-flash",
        is_stale=False,
    )
    db_session.add(cached_record)
    db_session.commit()

    mock_llm = AsyncMock()  # Should NOT be called due to cache
    analysis_service = DocumentAnalysisService(llm_service=mock_llm)

    # First call with force_refresh=False -> should return cached result without LLM call
    resp = await analysis_service.get_or_create_analysis(
        db=db_session,
        document_id=doc_id,
        force_refresh=False,
    )

    assert resp.summary == "Cached policy analysis overview."
    mock_llm.generate.assert_not_called()


# ---------------------------------------------------------------------------
# 2. API Endpoint Integration Tests
# ---------------------------------------------------------------------------
def test_get_nonexistent_analysis_api(client):
    non_existent_id = uuid.uuid4()
    resp = client.get(f"/api/v1/documents/{non_existent_id}/analysis")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
