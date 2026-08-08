import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from backend.services.rag import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])

TEXTOS_DIR = "textos"
DOCS_JSON = os.path.join(TEXTOS_DIR, "documents.json")

os.makedirs(TEXTOS_DIR, exist_ok=True)

def load_docs_registry() -> List[Dict[str, Any]]:
    if not os.path.exists(DOCS_JSON):
        return []
    try:
        with open(DOCS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading docs registry: {e}")
        return []

def save_docs_registry(docs: List[Dict[str, Any]]) -> None:
    with open(DOCS_JSON, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

@router.get("/documents")
async def list_documents():
    return load_docs_registry()

@router.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "unknown.pdf"
    
    # Security: Path traversal checks
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename or path traversal detected")
    
    safe_filename = os.path.basename(filename)
    if not safe_filename or not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_path = os.path.join(TEXTOS_DIR, safe_filename)
    
    # Save uploaded file
    try:
        content_bytes = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    doc_id = safe_filename
    registry = load_docs_registry()
    
    # Update or add to registry with "Processing" status
    doc_entry = {
        "doc_id": doc_id,
        "title": safe_filename,
        "filename": safe_filename,
        "status": "Processing",
        "chunks": 0,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Remove existing if re-uploading (hot-swap)
    registry = [d for d in registry if d["doc_id"] != doc_id]
    registry.append(doc_entry)
    save_docs_registry(registry)
    
    try:
        rag = RAGService()
        extracted_text = rag.extract_pdf_text(file_path)
        chunk_count = rag.ingest_document(doc_id=doc_id, title=safe_filename, content=extracted_text)
        
        # Update status to "Processed and Available"
        for d in registry:
            if d["doc_id"] == doc_id:
                d["status"] = "Processed and Available"
                d["chunks"] = chunk_count
        save_docs_registry(registry)
        
        return {
            "doc_id": doc_id,
            "title": safe_filename,
            "status": "Processed and Available",
            "chunks": chunk_count
        }
    except Exception as e:
        logger.error(f"Error ingesting document {doc_id}: {e}")
        for d in registry:
            if d["doc_id"] == doc_id:
                d["status"] = "Error"
        save_docs_registry(registry)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    # Sanitize doc_id
    safe_doc_id = os.path.basename(doc_id)
    if not safe_doc_id:
        raise HTTPException(status_code=400, detail="Invalid document ID")
        
    registry = load_docs_registry()
    
    # Delete from ChromaDB
    try:
        rag = RAGService()
        rag.delete_document(safe_doc_id)
    except Exception as e:
        logger.error(f"Error deleting chunks for {safe_doc_id}: {e}")
        
    # Delete file from textos/
    file_path = os.path.join(TEXTOS_DIR, safe_doc_id)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            
    # Update registry
    registry = [d for d in registry if d["doc_id"] != safe_doc_id]
    save_docs_registry(registry)
    
    return {"status": "success", "deleted": safe_doc_id}
