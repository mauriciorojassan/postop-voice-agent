import os
import hashlib
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "postop_knowledge", client: Optional[Any] = None):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client (persistent or provided in-memory client for testing)
        if client is not None:
            self.client = client
        else:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Initialize BGE-M3 embedding function via sentence-transformers
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="BAAI/bge-m3"
        )
        
        # Get or create collection with BGE-M3 embedding function
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )

    def chunk_text(self, text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> List[str]:
        """
        Splits text into chunks of specified word/token size with overlap.
        Preserves the knob for chunk_size and chunk_overlap.
        """
        if not text:
            return []
        
        words = text.split()
        if not words:
            return []
            
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            if end >= len(words):
                break
            start += (chunk_size - chunk_overlap)
            
        return chunks

    def compute_version_hash(self, content: str) -> str:
        """Computes SHA-256 version hash for document content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def ingest_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        version_hash: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 64
    ) -> int:
        """
        Hot-swap ingestion:
        1. Purges existing chunks matching doc_id to guarantee zero cross-version contamination.
        2. Chunks document content.
        3. Adds new chunks with metadata (doc_id, title, chunk_idx, version_hash).
        """
        if not version_hash:
            version_hash = self.compute_version_hash(content)
            
        # Zero-contamination purge: remove all existing chunks for this doc_id
        self.delete_document(doc_id)
        
        chunks = self.chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            return 0
            
        ids = [f"{doc_id}_c{idx}_{version_hash}" for idx in range(len(chunks))]
        documents = chunks
        metadatas = [
            {
                "doc_id": doc_id,
                "title": title,
                "chunk_idx": idx,
                "version_hash": version_hash
            }
            for idx in range(len(chunks))
        ]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Ingested document '{doc_id}' ({title}) with {len(chunks)} chunks [version: {version_hash}]")
        return len(chunks)

    def delete_document(self, doc_id: str) -> None:
        """Purges all vector chunks associated with doc_id."""
        try:
            # Query existing IDs or use where filter
            existing = self.collection.get(where={"doc_id": doc_id})
            if existing and existing["ids"]:
                self.collection.delete(ids=existing["ids"])
                logger.info(f"Purged {len(existing['ids'])} chunks for doc_id '{doc_id}'")
        except Exception as e:
            logger.error(f"Error purging doc_id '{doc_id}': {e}")

    def query(self, query_text: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Queries ChromaDB collection and returns matching documents and structured source citations.
        """
        if self.collection.count() == 0:
            return {"documents": [], "metadatas": [], "distances": [], "source_citations": []}
            
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count())
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        source_citations = []
        for meta in metadatas:
            source_citations.append({
                "doc_id": meta.get("doc_id"),
                "title": meta.get("title"),
                "chunk_idx": meta.get("chunk_idx"),
                "version_hash": meta.get("version_hash")
            })
            
        return {
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances,
            "source_citations": source_citations
        }

    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extracts text from PDF file using pypdf.
        Handles scanned-PDF-no-text-layer case gracefully with a warning/fallback message.
        """
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            full_text = []
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text.append(text)
            
            combined = "\n".join(full_text).strip()
            if not combined:
                logger.warning(f"PDF '{pdf_path}' yielded no text layer (scanned PDF or image-only).")
                return f"[Documento escaneado sin capa de texto: {os.path.basename(pdf_path)}]"
            return combined
        except Exception as e:
            logger.error(f"Failed to extract text from PDF '{pdf_path}': {e}")
            return f"[Error al extraer texto del PDF {os.path.basename(pdf_path)}: {str(e)}]"
