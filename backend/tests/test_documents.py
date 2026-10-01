import io
import uuid
import pytest
import pymupdf as fitz
from app.core.config import settings

def create_dummy_pdf():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a valid test PDF contract document for Doc Clarity test suite.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def create_dummy_docx():
    # ZIP header signature + dummy padding
    return b"PK\x03\x04\x14\x00\x08\x00\x08\x00" + (b"0" * 100)

def create_dummy_txt():
    return b"This is a sample plain text legal contract agreement."

def test_upload_valid_pdf(client):
    pdf_data = create_dummy_pdf()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("contract.pdf", io.BytesIO(pdf_data), "application/pdf")},
        data={"document_type": "legal"}
    )
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["original_filename"] == "contract.pdf"
    assert json_data["document_type"] == "legal"
    assert json_data["status"] == "ready"
    assert json_data["file_size"] == len(pdf_data)
    assert "id" in json_data

def test_upload_valid_docx(client):
    docx_data = create_dummy_docx()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("policy.docx", io.BytesIO(docx_data), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"document_type": "insurance"}
    )
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["original_filename"] == "policy.docx"
    assert json_data["document_type"] == "insurance"

def test_upload_valid_txt(client):
    txt_data = create_dummy_txt()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", io.BytesIO(txt_data), "text/plain")},
        data={"document_type": "medical"}
    )
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["original_filename"] == "notes.txt"
    assert json_data["document_type"] == "medical"
    assert json_data["status"] == "ready"

def test_upload_unsupported_extension(client):
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("script.exe", io.BytesIO(b"executable data"), "application/octet-stream")},
        data={"document_type": "other"}
    )
    assert response.status_code == 415
    assert "Unsupported file extension" in response.json()["detail"]

def test_upload_invalid_mime_magic_bytes(client):
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("fake.pdf", io.BytesIO(b"INVALID PDF HEADER DATA"), "application/pdf")},
        data={"document_type": "legal"}
    )
    assert response.status_code == 400
    assert "magic bytes" in response.json()["detail"]

def test_upload_empty_file(client):
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        data={"document_type": "legal"}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_upload_oversized_file(client):
    large_data = b"0" * (20 * 1024 * 1024 + 10)
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large.txt", io.BytesIO(large_data), "text/plain")},
        data={"document_type": "other"}
    )
    assert response.status_code == 413
    assert "exceeds maximum" in response.json()["detail"]

def test_upload_invalid_document_type(client):
    txt_data = create_dummy_txt()
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc.txt", io.BytesIO(txt_data), "text/plain")},
        data={"document_type": "finance_invalid"}
    )
    assert response.status_code == 400
    assert "Invalid document_type" in response.json()["detail"]

def test_list_documents(client):
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc1.pdf", io.BytesIO(create_dummy_pdf()), "application/pdf")},
        data={"document_type": "legal"}
    )
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc2.txt", io.BytesIO(create_dummy_txt()), "text/plain")},
        data={"document_type": "medical"}
    )

    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["original_filename"] == "doc2.txt"
    assert data[1]["original_filename"] == "doc1.pdf"

def test_get_existing_document(client):
    upload_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("policy.pdf", io.BytesIO(create_dummy_pdf()), "application/pdf")},
        data={"document_type": "insurance"}
    ).json()
    doc_id = upload_res["id"]

    response = client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["original_filename"] == "policy.pdf"
    assert "stored_filename" in data
    assert "file_path" in data

def test_get_nonexistent_document(client):
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/documents/{random_uuid}")
    assert response.status_code == 404

def test_delete_existing_document(client):
    upload_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("delete_me.pdf", io.BytesIO(create_dummy_pdf()), "application/pdf")},
        data={"document_type": "other"}
    ).json()
    doc_id = upload_res["id"]

    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == doc_id

    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 404

def test_delete_nonexistent_document(client):
    random_uuid = str(uuid.uuid4())
    del_res = client.delete(f"/api/v1/documents/{random_uuid}")
    assert del_res.status_code == 404
