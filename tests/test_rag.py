import pytest
import chromadb
from backend.services.rag import RAGService

@pytest.fixture
def temp_rag():
    in_memory_client = chromadb.Client()
    service = RAGService(collection_name="test_postop_rag", client=in_memory_client)
    yield service

def test_chunking_boundaries_and_overlap(temp_rag):
    # Test chunking with 512 size / 64 overlap (using words for token/word approximation)
    words = [f"word{i}" for i in range(1200)]
    text = " ".join(words)
    
    chunks = temp_rag.chunk_text(text, chunk_size=500, chunk_overlap=50)
    assert len(chunks) > 1
    
    # Verify overlap: chunk 1 end should overlap with chunk 2 start
    words_chunk_0 = chunks[0].split()
    words_chunk_1 = chunks[1].split()
    
    overlap_words = words_chunk_0[-50:]
    start_words = words_chunk_1[:50]
    assert overlap_words == start_words

def test_rag_hotswap_and_zero_contamination(temp_rag):
    doc_id = "proto_lap"
    
    # Ingest v1
    content_v1 = "El paciente debe consumir dieta blanda el primer día postoperatorio. No levantar objetos pesados."
    temp_rag.ingest_document(doc_id=doc_id, title="Protocolo Laparoscopia", content=content_v1, version_hash="v1")
    
    # Verify v1 is retrievable
    res_v1 = temp_rag.query("dieta blanda", n_results=1)
    assert len(res_v1["documents"]) > 0
    assert "dieta blanda" in res_v1["documents"][0]
    assert res_v1["source_citations"][0]["version_hash"] == "v1"
    
    # Ingest v2 (replace same doc_id)
    content_v2 = "El paciente debe consumir dieta líquida estricta las primeras 48 horas. Cero sólidos."
    temp_rag.ingest_document(doc_id=doc_id, title="Protocolo Laparoscopia V2", content=content_v2, version_hash="v2")
    
    # Query v2 terms
    res_v2 = temp_rag.query("dieta líquida", n_results=5)
    assert len(res_v2["documents"]) > 0
    assert "dieta líquida" in res_v2["documents"][0]
    
    # Assert zero old version_hash chunks retrievable (no contamination)
    all_chunks = temp_rag.collection.get()
    version_hashes = [meta.get("version_hash") for meta in all_chunks["metadatas"]]
    assert "v1" not in version_hashes
    assert "v2" in version_hashes

def test_rag_deletion(temp_rag):
    doc_id = "proto_temp"
    temp_rag.ingest_document(doc_id=doc_id, title="Temporary Protocol", content="Some test content about pain management.", version_hash="v1")
    
    assert temp_rag.collection.count() > 0
    
    temp_rag.delete_document(doc_id)
    
    all_chunks = temp_rag.collection.get()
    doc_ids = [meta.get("doc_id") for meta in all_chunks["metadatas"]]
    assert doc_id not in doc_ids
