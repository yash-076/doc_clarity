import uuid
from app.services.embeddings import get_embedding_service
from app.services.vector_store.chroma_store import ChromaVectorStore

def test_chroma_vector_store_isolation(tmp_path):
    chroma_dir = tmp_path / "chroma_test_data"
    store = ChromaVectorStore(persist_dir=chroma_dir, collection_name="test_isolation")
    embedder = get_embedding_service()

    doc_a_id = str(uuid.uuid4())
    doc_b_id = str(uuid.uuid4())

    text_a = "Legal contract for non-disclosure agreement."
    text_b = "Medical patient heart surgery records."

    vector_a = embedder.embed_documents([text_a])
    vector_b = embedder.embed_documents([text_b])

    chunk_a_id = str(uuid.uuid4())
    chunk_b_id = str(uuid.uuid4())

    # Add Document A chunk
    store.add(
        ids=[chunk_a_id],
        embeddings=vector_a,
        documents=[text_a],
        metadatas=[{"document_id": doc_a_id, "section": "NDA Clause"}]
    )

    # Add Document B chunk
    store.add(
        ids=[chunk_b_id],
        embeddings=vector_b,
        documents=[text_b],
        metadatas=[{"document_id": doc_b_id, "section": "Surgery Notes"}]
    )

    # Search Document A -> MUST NOT return Document B
    query_vector = embedder.embed_query("non disclosure agreement")
    results_a = store.search(query_vector, document_id=doc_a_id, top_k=5)
    
    assert len(results_a) == 1
    assert results_a[0]["chunk_id"] == chunk_a_id
    assert results_a[0]["document_id"] == doc_a_id

    # Search Document B -> MUST NOT return Document A
    query_vector_b = embedder.embed_query("heart surgery")
    results_b = store.search(query_vector_b, document_id=doc_b_id, top_k=5)
    
    assert len(results_b) == 1
    assert results_b[0]["chunk_id"] == chunk_b_id
    assert results_b[0]["document_id"] == doc_b_id
