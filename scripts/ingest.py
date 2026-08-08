#!/usr/bin/env python3
import os
import glob
import sys
from backend.services.rag import RAGService

def main():
    textos_dir = os.path.join(os.getcwd(), "textos")
    if not os.path.exists(textos_dir):
        os.makedirs(textos_dir, exist_ok=True)
        print(f"Created directory '{textos_dir}'. Place clinical PDF protocols here.")
    
    pdf_pattern = os.path.join(textos_dir, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    rag = RAGService()
    
    if not pdf_files:
        print(f"No PDF files found in {textos_dir}.")
        # Create a sample text file or handle graceful zero PDFs if running in setup
        print(f"ChromaDB collection '{rag.collection_name}' ready. Current chunk count: {rag.collection.count()}")
        return

    print(f"Found {len(pdf_files)} PDF(s) in {textos_dir}. Ingesting...")
    
    total_chunks = 0
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        doc_id = os.path.splitext(filename)[0]
        title = doc_id.replace("_", " ").title()
        
        print(f"Processing '{filename}' (doc_id: {doc_id})...")
        content = rag.extract_pdf_text(pdf_path)
        chunks_count = rag.ingest_document(doc_id=doc_id, title=title, content=content)
        total_chunks += chunks_count
        print(f"  -> Ingested {chunks_count} chunks.")

    print(f"\nIngestion complete! Total chunks in collection: {rag.collection.count()}")

if __name__ == "__main__":
    main()
