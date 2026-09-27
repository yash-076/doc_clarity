import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.core.personas import PersonaType, PERSONA_CONFIG, get_persona_instructions
from app.db.models.document import Document, DocumentStatus, EmbeddingStatus
from app.db.models.persona_response_cache import PersonaResponseCache
from app.services.prompt_builder import RAGPromptBuilder
from app.services.rag_service import RAGService
from app.services.conversation_service import ConversationService
from app.services.vector_store.retrieval import RetrievalResult

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Persona Model & Configuration Tests
# ---------------------------------------------------------------------------
def test_persona_enum_and_config():
    assert PersonaType.CONSUMER == "consumer"
    assert PersonaType.PROFESSIONAL == "professional"
    assert PersonaType.BUSINESS == "business"

    assert "consumer" in PERSONA_CONFIG
    assert "professional" in PERSONA_CONFIG
    assert "business" in PERSONA_CONFIG

    consumer_instructions = get_persona_instructions(PersonaType.CONSUMER)
    assert "simple language" in consumer_instructions.lower()

    prof_instructions = get_persona_instructions(PersonaType.PROFESSIONAL)
    assert "technical" in prof_instructions.lower() or "precise" in prof_instructions.lower()

    biz_instructions = get_persona_instructions(PersonaType.BUSINESS)
    assert "obligations" in biz_instructions.lower() or "business" in biz_instructions.lower()


def test_prompt_builder_persona_instructions():
    builder = RAGPromptBuilder()

    consumer_sys = builder.build_system_instruction(PersonaType.CONSUMER)
    assert "CONSUMER MODE" in consumer_sys
    assert "simple language" in consumer_sys.lower()

    prof_sys = builder.build_system_instruction(PersonaType.PROFESSIONAL)
    assert "PROFESSIONAL MODE" in prof_sys
    assert "precise" in prof_sys.lower() or "technical" in prof_sys.lower()

    chunks = [{"chunk_id": str(uuid.uuid4()), "content": "The deductible is $1,000.", "page_number": 1, "section": "Terms", "score": 0.9}]
    prompt_str, used = builder.build_user_prompt("What is the deductible?", chunks, persona=PersonaType.BUSINESS)
    assert "EXPLANATION PERSONA: BUSINESS" in prompt_str


# ---------------------------------------------------------------------------
# 2. RAG Service Persona & Caching Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rag_service_persona_and_caching(db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="policy.pdf",
        stored_filename="policy_7.pdf",
        file_path="/tmp/policy_7.pdf",
        file_size=2000,
        mime_type="application/pdf",
        document_type="insurance",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    chunk_id = uuid.uuid4()
    mock_chunk = RetrievalResult(
        chunk_id=chunk_id,
        document_id=doc_id,
        text="Section 4.1: Pre-existing conditions are excluded for 48 months from inception.",
        score=0.92,
        page_number=4,
        section="Exclusions",
        document_type="insurance",
        extraction_method="native_pdf",
    )

    mock_retrieval = MagicMock()
    mock_retrieval.search.return_value = [mock_chunk]

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "Consumer Answer: Pre-existing conditions aren't covered for the first 48 months."

    rag_svc = RAGService(retrieval_service=mock_retrieval, llm_service=mock_llm)

    # Consumer query
    resp_consumer = await rag_svc.answer_question(
        db=db_session,
        document_id=doc_id,
        question="Are pre-existing conditions covered?",
        persona=PersonaType.CONSUMER,
    )

    assert resp_consumer.persona == PersonaType.CONSUMER
    assert "first 48 months" in resp_consumer.answer
    assert len(resp_consumer.citations) == 1
    assert resp_consumer.citations[0].chunk_id == chunk_id

    # Verify response is cached in PersonaResponseCache
    cached_db = db_session.query(PersonaResponseCache).filter(
        PersonaResponseCache.document_id == doc_id,
        PersonaResponseCache.persona == PersonaType.CONSUMER.value,
    ).first()
    assert cached_db is not None

    # Repeated query with same persona -> returns cached result without LLM call
    mock_llm.generate.reset_mock()
    resp_cached = await rag_svc.answer_question(
        db=db_session,
        document_id=doc_id,
        question="Are pre-existing conditions covered?",
        persona=PersonaType.CONSUMER,
    )
    assert resp_cached.answer == resp_consumer.answer
    mock_llm.generate.assert_not_called()

    # Query with Professional persona -> generates new professional answer & preserves same citations
    mock_llm.generate.return_value = "Professional Answer: Pursuant to Section 4.1, a 48-month exclusionary period applies to pre-existing conditions."
    resp_prof = await rag_svc.answer_question(
        db=db_session,
        document_id=doc_id,
        question="Are pre-existing conditions covered?",
        persona=PersonaType.PROFESSIONAL,
    )
    assert resp_prof.persona == PersonaType.PROFESSIONAL
    assert "Section 4.1" in resp_prof.answer
    assert len(resp_prof.citations) == 1
    assert resp_prof.citations[0].chunk_id == chunk_id


@pytest.mark.asyncio
async def test_reexplain_question_reuses_evidence(db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="contract.pdf",
        stored_filename="contract_7.pdf",
        file_path="/tmp/contract_7.pdf",
        file_size=3000,
        mime_type="application/pdf",
        document_type="legal",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    chunk_id = uuid.uuid4()
    mock_chunk = RetrievalResult(
        chunk_id=chunk_id,
        document_id=doc_id,
        text="The tenant shall give 30 days written notice prior to termination.",
        score=0.85,
        page_number=2,
        section="Notice",
        document_type="legal",
        extraction_method="native_pdf",
    )

    mock_retrieval = MagicMock()
    mock_retrieval.search.return_value = [mock_chunk]

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "Business Answer: Operational risk: 30-day notice requirement must be tracked before contract termination."

    rag_svc = RAGService(retrieval_service=mock_retrieval, llm_service=mock_llm)

    resp_reexplain = await rag_svc.reexplain_question(
        db=db_session,
        document_id=doc_id,
        question="What are the notice requirements?",
        persona=PersonaType.BUSINESS,
    )

    assert resp_reexplain.persona == PersonaType.BUSINESS
    assert "Operational risk" in resp_reexplain.answer


# ---------------------------------------------------------------------------
# 3. Conversation Persona Switching Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_conversation_persona_switching(db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="policy.pdf",
        stored_filename="policy_8.pdf",
        file_path="/tmp/policy_8.pdf",
        file_size=2000,
        mime_type="application/pdf",
        document_type="insurance",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    conv_svc = ConversationService()
    conv = conv_svc.create_conversation(db=db_session, document_id=doc_id, persona=PersonaType.CONSUMER)
    assert conv.persona == PersonaType.CONSUMER

    chunk_id = uuid.uuid4()
    mock_chunk = RetrievalResult(
        chunk_id=chunk_id,
        document_id=doc_id,
        text="The annual deductible is $500 per covered individual.",
        score=0.90,
        page_number=1,
        section="Deductibles",
        document_type="insurance",
        extraction_method="native_pdf",
    )

    mock_retrieval = MagicMock()
    mock_retrieval.search.return_value = [mock_chunk]

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "You pay the first $500 of medical expenses each year."

    conv_svc.retrieval_service = mock_retrieval
    conv_svc.llm_service = mock_llm

    # Message 1 (Consumer)
    msg1 = await conv_svc.send_message(
        db=db_session,
        conversation_id=conv.id,
        content="What is the deductible?",
        persona=PersonaType.CONSUMER,
    )
    assert msg1.persona == PersonaType.CONSUMER

    # Message 2 (Switch to Professional)
    mock_llm.generate.return_value = "Pursuant to Section 1, an annual individual deductible of $500 applies."
    msg2 = await conv_svc.send_message(
        db=db_session,
        conversation_id=conv.id,
        content="Explain that technically.",
        persona=PersonaType.PROFESSIONAL,
    )
    assert msg2.persona == PersonaType.PROFESSIONAL

    # Check updated conversation persona state
    updated_conv = conv_svc.get_conversation(db=db_session, conversation_id=conv.id)
    assert updated_conv.persona == PersonaType.PROFESSIONAL


# ---------------------------------------------------------------------------
# 4. API Endpoints Persona Integration Tests
# ---------------------------------------------------------------------------
def test_ask_document_api_with_persona(client, db_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.uuid4(),
        original_filename="lease.pdf",
        stored_filename="lease_9.pdf",
        file_path="/tmp/lease_9.pdf",
        file_size=2000,
        mime_type="application/pdf",
        document_type="legal",
        status=DocumentStatus.READY.value,
        embedding_status=EmbeddingStatus.INDEXED.value,
    )
    db_session.add(doc)
    db_session.commit()

    resp = client.post(
        f"/api/v1/documents/{doc_id}/ask",
        json={"question": "What is the rent?", "persona": "business"}
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["persona"] == "business"


def test_invalid_persona_validation_error(client):
    doc_id = uuid.uuid4()
    resp = client.post(
        f"/api/v1/documents/{doc_id}/ask",
        json={"question": "What is the rent?", "persona": "doctor"}
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
