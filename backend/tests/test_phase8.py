import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.personas import PersonaType
from app.db.models.document import Document, DocumentStatus, EmbeddingStatus
from app.db.models.document_chunk import DocumentChunk
from app.schemas.retrieval import RetrievalResponse, RetrievalResult
from app.services.retrieval.models import RetrievedCandidate, normalize_scores
from app.services.retrieval.vector_retriever import VectorRetriever
from app.services.retrieval.keyword_retriever import KeywordRetriever
from app.services.retrieval.hybrid_retriever import HybridRetriever
from app.services.retrieval.reranker import PassThroughReranker, SentenceTransformerReranker
from app.services.retrieval.query_expander import QueryExpander
from app.services.retrieval.diversity import (
    apply_section_and_page_boosting,
    apply_diversity_selection,
)
from app.services.retrieval.advanced_service import AdvancedRetrievalService
from app.services.rag_service import RAGService


@pytest.fixture
def mock_db(db_session):
    return db_session


def test_score_normalization():
    raw_scores = [10.0, 20.0, 30.0]
    norm = normalize_scores(raw_scores)
    assert norm == [0.0, 0.5, 1.0]

    single = normalize_scores([5.0])
    assert single == [1.0]

    empty = normalize_scores([])
    assert empty == []


def test_vector_retriever(mock_db):
    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = [
        {
            "chunk_id": str(uuid.uuid4()),
            "text": "The policy waiting period is 48 months for pre-existing diseases.",
            "score": 0.85,
            "page_number": 5,
            "section": "Section 8",
            "document_type": "insurance",
            "extraction_method": "text",
        }
    ]

    mock_embedding_service = MagicMock()
    mock_embedding_service.embed_query.return_value = [0.1] * 384

    doc_id = uuid.uuid4()
    retriever = VectorRetriever(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
    )
    candidates = retriever.search(query="waiting period", document_id=doc_id, top_k=5)

    assert len(candidates) == 1
    assert candidates[0].document_id == doc_id
    assert candidates[0].section == "Section 8"
    assert candidates[0].vector_score == 0.85
    assert candidates[0].norm_vector_score == 1.0


def test_keyword_retriever(mock_db):
    doc_id = uuid.uuid4()
    chunk1 = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=0,
        text="Section 8 establishes a 48-month waiting period for pre-existing conditions.",
        page_number=8,
        section="Section 8.2",
        document_type="policy",
        extraction_method="text",
    )
    chunk2 = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=1,
        text="Premium payments must be remitted within 30 days of notice.",
        page_number=12,
        section="Payment Terms",
        document_type="policy",
        extraction_method="text",
    )
    mock_db.add_all([chunk1, chunk2])
    mock_db.commit()

    retriever = KeywordRetriever()
    candidates = retriever.search(db=mock_db, query="waiting period Section 8", document_id=doc_id, top_k=5)

    assert len(candidates) >= 1
    assert candidates[0].chunk_id == chunk1.id
    assert candidates[0].keyword_score > 0
    assert candidates[0].norm_keyword_score == 1.0


def test_hybrid_retriever_fusion():
    doc_id = uuid.uuid4()
    chunk_id1 = uuid.uuid4()
    chunk_id2 = uuid.uuid4()

    mock_vector_retriever = MagicMock()
    mock_vector_retriever.search.return_value = [
        RetrievedCandidate(
            chunk_id=chunk_id1,
            document_id=doc_id,
            text="Vector match chunk 1",
            vector_score=0.9,
            norm_vector_score=1.0,
        )
    ]

    mock_keyword_retriever = MagicMock()
    mock_keyword_retriever.search.return_value = [
        RetrievedCandidate(
            chunk_id=chunk_id2,
            document_id=doc_id,
            text="Keyword match chunk 2",
            keyword_score=5.0,
            norm_keyword_score=1.0,
        )
    ]

    hybrid = HybridRetriever(
        vector_retriever=mock_vector_retriever,
        keyword_retriever=mock_keyword_retriever,
    )

    # Weighted scoring test
    weighted_candidates = hybrid.search(
        query="test query",
        document_id=doc_id,
        db=MagicMock(),
        vector_weight=0.7,
        keyword_weight=0.3,
        fusion_method="weighted",
    )
    assert len(weighted_candidates) == 2
    c1 = next(c for c in weighted_candidates if c.chunk_id == chunk_id1)
    c2 = next(c for c in weighted_candidates if c.chunk_id == chunk_id2)
    assert pytest.approx(c1.hybrid_score, 0.01) == 0.7
    assert pytest.approx(c2.hybrid_score, 0.01) == 0.3

    # RRF fusion test
    rrf_candidates = hybrid.search(
        query="test query",
        document_id=doc_id,
        db=MagicMock(),
        fusion_method="rrf",
    )
    assert len(rrf_candidates) == 2
    assert rrf_candidates[0].hybrid_score > 0


def test_query_expander():
    expander = QueryExpander()
    normalized = expander.normalize("What's the policy rules if I don't pay?")
    assert normalized.lower() == "what is the policy rules if i do not pay?"

    with patch.object(settings, "QUERY_EXPANSION_ENABLED", True):
        expansions = expander.expand("What happens if I stop paying?")
        assert len(expansions) > 1
        assert "premium payment failure" in expansions


def test_section_and_page_boosting():
    doc_id = uuid.uuid4()
    c1 = RetrievedCandidate(
        chunk_id=uuid.uuid4(),
        document_id=doc_id,
        text="Text on page 12",
        page_number=12,
        section="Claims",
        final_score=1.0,
    )
    c2 = RetrievedCandidate(
        chunk_id=uuid.uuid4(),
        document_id=doc_id,
        text="Text in Section 8",
        page_number=5,
        section="Section 8.2",
        final_score=1.0,
    )

    candidates = apply_section_and_page_boosting("What is in Section 8 on page 12?", [c1, c2])
    assert c1.final_score == 1.5  # page boost
    assert c2.final_score == 1.5  # section boost


def test_context_diversity():
    doc_id = uuid.uuid4()
    candidates = [
        RetrievedCandidate(chunk_id=uuid.uuid4(), document_id=doc_id, text="C1", section="SecA", page_number=1, final_score=0.9),
        RetrievedCandidate(chunk_id=uuid.uuid4(), document_id=doc_id, text="C2", section="SecA", page_number=1, final_score=0.8),
        RetrievedCandidate(chunk_id=uuid.uuid4(), document_id=doc_id, text="C3", section="SecA", page_number=1, final_score=0.7),
        RetrievedCandidate(chunk_id=uuid.uuid4(), document_id=doc_id, text="C4", section="SecB", page_number=2, final_score=0.6),
    ]

    selected = apply_diversity_selection(candidates, top_k=3, max_per_section=2)
    assert len(selected) == 3
    sec_a_count = sum(1 for c in selected if c.section == "SecA")
    sec_b_count = sum(1 for c in selected if c.section == "SecB")
    assert sec_a_count == 2
    assert sec_b_count == 1


def test_advanced_retrieval_service(mock_db):
    doc_id = uuid.uuid4()
    mock_hybrid = MagicMock()
    mock_hybrid.search.return_value = [
        RetrievedCandidate(
            chunk_id=uuid.uuid4(),
            document_id=doc_id,
            text="Advanced retrieval candidate text",
            vector_score=0.9,
            keyword_score=4.0,
            hybrid_score=0.85,
            final_score=0.85,
            page_number=3,
            section="Overview",
        )
    ]

    service = AdvancedRetrievalService(db=mock_db, hybrid_retriever=mock_hybrid, reranker=PassThroughReranker())
    results = service.search(query="overview", document_id=doc_id, top_k=5)

    assert len(results) == 1
    assert results[0].text == "Advanced retrieval candidate text"
    assert results[0].score == 0.85
    assert results[0].vector_score == 0.9
    assert results[0].keyword_score == 4.0


@pytest.mark.asyncio
async def test_rag_service_with_advanced_retrieval_and_persona(mock_db):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=uuid.UUID(settings.MOCK_USER_ID),
        original_filename="policy.pdf",
        stored_filename="policy_123.pdf",
        file_path="/tmp/policy.pdf",
        file_size=1024,
        mime_type="application/pdf",
        document_type="insurance",
        status=DocumentStatus.READY,
        embedding_status=EmbeddingStatus.INDEXED,
    )
    mock_db.add(doc)
    mock_db.commit()

    mock_retrieval = MagicMock()
    mock_retrieval.search.return_value = [
        RetrievalResult(
            chunk_id=uuid.uuid4(),
            document_id=doc_id,
            text="The policy excludes pre-existing conditions during the first 48 months.",
            score=0.92,
            page_number=4,
            section="Exclusions",
            document_type="insurance",
            extraction_method="text",
            vector_score=0.95,
            keyword_score=0.8,
            rerank_score=0.92,
        )
    ]

    mock_llm = MagicMock()
    from unittest.mock import AsyncMock
    mock_llm.generate = AsyncMock(return_value="The policy does not cover pre-existing conditions for 48 months. [SOURCE_1]")


    rag_service = RAGService(retrieval_service=mock_retrieval, llm_service=mock_llm)
    response = await rag_service.answer_question(
        db=mock_db,
        document_id=doc_id,
        question="What are the exclusions?",
        persona=PersonaType.CONSUMER,
    )

    assert response.document_id == doc_id
    assert response.persona == PersonaType.CONSUMER
    assert "48 months" in response.answer
    assert len(response.citations) == 1
    assert response.citations[0].section == "Exclusions"

