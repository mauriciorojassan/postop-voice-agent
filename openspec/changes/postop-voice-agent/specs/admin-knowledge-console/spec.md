# Specification: Admin Knowledge Console

## Purpose

Defines the web dashboard interface for clinical document management, enabling upload, listing, status inspection, and deletion of clinical source PDFs with visible "processed and available" status indicators.

## Requirements

### Requirement: PDF Document Upload and Ingestion Endpoint

The system MUST provide an HTTP POST endpoint and console UI for uploading clinical PDF documents and triggering background chunking and embedding.

#### Scenario: Uploading a PDF via admin console

- GIVEN an admin user accesses the admin console web interface
- WHEN the user uploads a valid PDF file (`Guia_PostOp_2026.pdf`) via the upload form
- THEN the backend receives the file, stores it in `textos/`, triggers BGE-M3 embedding and ChromaDB indexing, and returns a success status

### Requirement: Knowledge Document Listing and Status Inspection

The system MUST display a list of all ingested clinical documents in the admin console with visible status badges (`Processing`, `Processed and Available`, `Error`).

#### Scenario: Viewing document statuses in the console

- GIVEN documents have been uploaded to the system
- WHEN the admin user opens the console dashboard
- THEN a table displays each document filename, upload timestamp, chunk count, and a clear "Processed and Available" status badge

### Requirement: Document Deletion and Instant Index Purging

The system MUST provide a deletion action in the admin console that removes the source PDF file and purges all corresponding vector chunks from ChromaDB.

#### Scenario: Deleting a document from the console

- GIVEN an active document listed in the admin console
- WHEN the admin user clicks the delete button for that document
- THEN the source file is removed and ChromaDB vector chunks are purged instantly, updating the UI list immediately
