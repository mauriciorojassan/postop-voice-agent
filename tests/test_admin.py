import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_admin_path_traversal_rejected():
    # Attempt path traversal via filename
    response = client.post(
        "/api/documents",
        files={"file": ("../../etc/passwd.pdf", b"fake pdf content", "application/pdf")}
    )
    assert response.status_code in [400, 422]

def test_admin_wrong_mime_or_extension_rejected():
    # Attempt uploading non-PDF extension
    response = client.post(
        "/api/documents",
        files={"file": ("malicious.txt", b"some text content", "text/plain")}
    )
    assert response.status_code == 400

def test_admin_upload_list_delete_workflow():
    # Create a dummy PDF bytes (pypdf or simple header)
    # Even if pypdf extracts empty or error, RAGService handles it or we provide minimal valid PDF content
    pdf_content = b"%PDF-1.4 1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n172\n%%EOF"
    
    # 1. Upload
    response = client.post(
        "/api/documents",
        files={"file": ("Guia_Test_2026.pdf", pdf_content, "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Processed and Available"
    assert "Guia_Test_2026.pdf" in data["doc_id"]

    # 2. List documents
    list_response = client.get("/api/documents")
    assert list_response.status_code == 200
    docs = list_response.json()
    assert isinstance(docs, list)
    found = any(d["doc_id"] == "Guia_Test_2026.pdf" and d["status"] == "Processed and Available" for d in docs)
    assert found

    # 3. Delete document
    del_response = client.delete("/api/documents/Guia_Test_2026.pdf")
    assert del_response.status_code == 200

    # 4. Verify deleted
    list_response_after = client.get("/api/documents")
    docs_after = list_response_after.json()
    found_after = any(d["doc_id"] == "Guia_Test_2026.pdf" for d in docs_after)
    assert not found_after
