import pytest
from app.services.embeddings import get_embedding_service, LocalEmbeddingService

def test_embedding_service_initialization():
    service = get_embedding_service()
    assert isinstance(service, LocalEmbeddingService)
    assert service.dimension == 384
    assert service.model_name == "BAAI/bge-small-en-v1.5"

def test_embed_documents():
    service = get_embedding_service()
    texts = [
        "The insurance policy covers emergency hospital visits.",
        "Excluded conditions include pre-existing illnesses."
    ]
    vectors = service.embed_documents(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384

def test_embed_query():
    service = get_embedding_service()
    query_vector = service.embed_query("What conditions are excluded?")
    assert len(query_vector) == 384
