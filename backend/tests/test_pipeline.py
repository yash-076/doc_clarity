import io
import pymupdf as fitz

def test_pipeline_processing_and_chunks(client):
    # Create valid native PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "ARTICLE 1: DEFINITIONS\n\nEligible expense means any necessary hospital service.")
    pdf_bytes = doc.tobytes()
    doc.close()

    # 1. Upload document (triggers automatic processing)
    res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("definitions.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"document_type": "legal"}
    )
    assert res.status_code == 201
    doc_data = res.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == "ready"

    # 2. Get chunks API
    chunks_res = client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert chunks_res.status_code == 200
    chunks_data = chunks_res.json()
    assert chunks_data["total_chunks"] >= 1
    assert chunks_data["chunks"][0]["chunk_index"] == 0
    assert chunks_data["chunks"][0]["extraction_method"] == "text"

    # 3. Manual reprocess API
    reprocess_res = client.post(f"/api/v1/documents/{doc_id}/process")
    assert reprocess_res.status_code == 200
    assert reprocess_res.json()["status"] == "ready"
