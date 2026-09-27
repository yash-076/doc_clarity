import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app
from app.db.models.document import Document, DocumentStatus, EmbeddingStatus
from app.db.models.document_analysis import DocumentAnalysis
from app.db.models.document_question import DocumentQuestion
from app.db.models.conversation import Conversation, ConversationMessage
from app.services.guided_question_service import GuidedQuestionService
from app.services.conversation_service import ConversationService
from app.services.vector_store.retrieval import RetrievalResult
from app.schemas.analysis import DocumentAnalysisResponse, KeyPoint

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Guided Question Service Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_questions_document_not_found(db_session):
    service = GuidedQuestionService()
    non_existent_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await service.get_or_generate_questions(
            db=db_session,
            document_id=non_existent_id,
        )
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_questions_document_not_ready(db_session):
    doc = Document(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        original_filename="processing.pdf",
        stored_filename="proc_1.pdf",
        file_path="/tmp/proc.pdf",
        file_size=1000,
        mime_type="application/pdf",
        document_type="legal",
        status=DocumentStatus.PROCESSING.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    service = GuidedQuestionService()
    with pytest.raises(HTTPException) as exc_info:
        await service.get_or_generate_questions(
            db=db_session,
            document_id=doc.id,
        )
    assert exc_info.value.status_code == 409
    assert "not complete" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_question_generation_and_caching(db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="policy.pdf",
        stored_filename="policy_1.pdf",
        file_path="/tmp/policy.pdf",
        file_size=2000,
        mime_type="application/pdf",
        document_type="insurance",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    # Mock Analysis Service
    mock_analysis_resp = DocumentAnalysisResponse(
        id=uuid.uuid4(),
        document_id=doc_id,
        document_type="insurance",
        analysis_version=1,
        summary="This policy covers property damage up to $100,000 with a $1,000 deductible.",
        key_points=[KeyPoint(title="Property Coverage", description="Up to $100,000 limit.", citations=[])],
        important_dates=[],
        financial_terms=[],
        obligations=[],
        exclusions=[],
        attention_items=[],
        embedding_model="BAAI/bge-small-en-v1.5",
        llm_model="gemini-2.5-flash",
    )

    mock_analysis_svc = AsyncMock()
    mock_analysis_svc.get_or_create_analysis.return_value = mock_analysis_resp

    mock_llm_output = """{
      "questions": [
        {"id": "q1", "question": "What is the maximum coverage limit for property damage?", "category": "coverage"},
        {"id": "q2", "question": "What deductible applies to claims?", "category": "financial"},
        {"id": "q3", "question": "What exclusions apply to flood damage?", "category": "exclusions"}
      ]
    }"""
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = mock_llm_output

    guided_svc = GuidedQuestionService(
        analysis_service=mock_analysis_svc,
        llm_service=mock_llm,
    )

    resp = await guided_svc.get_or_generate_questions(
        db=db_session,
        document_id=doc_id,
        force_refresh=True,
    )

    assert resp.document_id == doc_id
    assert resp.analysis_version == 1
    assert len(resp.questions) == 3
    assert resp.questions[0].category == "coverage"
    assert "maximum coverage limit" in resp.questions[0].question.lower()

    # Verify questions are stored in DB
    cached = db_session.query(DocumentQuestion).filter(DocumentQuestion.document_id == doc_id).all()
    assert len(cached) == 3

    # Subsequent call with force_refresh=False should return cached result without calling LLM
    mock_llm.generate.reset_mock()
    resp_cached = await guided_svc.get_or_generate_questions(
        db=db_session,
        document_id=doc_id,
        force_refresh=False,
    )
    assert len(resp_cached.questions) == 3
    mock_llm.generate.assert_not_called()


# ---------------------------------------------------------------------------
# 2. Conversation Service Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_and_get_conversation(db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="contract.pdf",
        stored_filename="contract_1.pdf",
        file_path="/tmp/contract.pdf",
        file_size=2500,
        mime_type="application/pdf",
        document_type="legal",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    conv_svc = ConversationService()
    conv = conv_svc.create_conversation(db=db_session, document_id=doc_id, title="Lease Agreement Q&A")

    assert conv.document_id == doc_id
    assert conv.title == "Lease Agreement Q&A"
    assert len(conv.messages) == 0

    fetched = conv_svc.get_conversation(db=db_session, conversation_id=conv.id)
    assert fetched.id == conv.id
    assert fetched.document_id == doc_id


@pytest.mark.asyncio
async def test_send_message_and_query_rewrite(db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="lease.pdf",
        stored_filename="lease_1.pdf",
        file_path="/tmp/lease.pdf",
        file_size=3000,
        mime_type="application/pdf",
        document_type="legal",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    conv_svc = ConversationService()
    conv = conv_svc.create_conversation(db=db_session, document_id=doc_id)

    chunk_id = uuid.uuid4()
    mock_chunk = RetrievalResult(
        chunk_id=chunk_id,
        document_id=doc_id,
        text="The security deposit is $2,000 and is fully refundable upon move-out inspection.",
        score=0.88,
        page_number=3,
        section="Deposit Terms",
        document_type="legal",
        extraction_method="native_pdf",
    )

    mock_retrieval = MagicMock()
    mock_retrieval.search.return_value = [mock_chunk]

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "The security deposit is $2,000 and refundable after inspection."

    conv_svc.retrieval_service = mock_retrieval
    conv_svc.llm_service = mock_llm

    # Message 1
    msg1 = await conv_svc.send_message(
        db=db_session,
        conversation_id=conv.id,
        content="How much is the security deposit?",
    )
    assert msg1.role == "assistant"
    assert "security deposit" in msg1.content.lower()
    assert len(msg1.citations) == 1
    assert msg1.citations[0].chunk_id == chunk_id
    assert msg1.confidence in ["high", "medium"]

    # Message 2 (Follow-up requiring query rewrite)
    mock_llm.generate.side_effect = [
        "What are the conditions for refunding the security deposit?",  # Query rewrite response
        "The security deposit is fully refundable upon move-out inspection.",  # RAG Answer response
    ]

    msg2 = await conv_svc.send_message(
        db=db_session,
        conversation_id=conv.id,
        content="Is it refundable?",
    )
    assert msg2.role == "assistant"
    assert "refundable" in msg2.content.lower()


# ---------------------------------------------------------------------------
# 3. API Integration Tests
# ---------------------------------------------------------------------------
def test_suggested_questions_api_not_found(client):
    non_existent_id = uuid.uuid4()
    resp = client.get(f"/api/v1/documents/{non_existent_id}/suggested-questions")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_conversation_api_not_found(client):
    non_existent_id = uuid.uuid4()
    resp = client.get(f"/api/v1/conversations/{non_existent_id}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
