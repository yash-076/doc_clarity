import io
import fitz

def test_full_indexing_and_search_api(client):
    # 1. Create a PDF document
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "INSURANCE POLICY EXCLUSIONS\n\nSection 1: Pre-existing heart conditions are strictly excluded from coverage."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload document (triggers extraction, chunking, and automatic vector indexing)
    res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("policy_exclusions.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "insurance"}
    )
    assert res.status_code == 201
    doc_data = res.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == "ready"
    assert doc_data["embedding_status"] == "indexed"

    # 3. Check /index-status API
    status_res = client.get(f"/api/v1/documents/{doc_id}/index-status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["embedding_status"] == "indexed"
    assert status_data["indexed_count"] >= 1

    # 4. Perform document-isolated semantic search API
    search_res = client.post(
        f"/api/v1/documents/{doc_id}/search",
        json={"query": "What conditions are excluded?", "top_k": 3}
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["top_k"] == 3
    assert len(search_data["results"]) >= 1
    
    top_result = search_data["results"][0]
    assert "pre-existing" in top_result["text"].lower()
    assert top_result["score"] > 0.0
    assert top_result["document_id"] == doc_id
