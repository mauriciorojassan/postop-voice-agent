# Specification: Hot-Swap RAG & Source Traceability

## Purpose

Defines ChromaDB vector storage with BGE-M3 embeddings, instant chunk-level document ingestion, zero cross-version contamination via metadata hashing (`doc_id` & `version_hash`), and per-answer source citation mapping.

## Requirements

### Requirement: BGE-M3 Embeddings and ChromaDB Storage

The system MUST embed clinical PDF documents using BGE-M3 embeddings and persist vector chunks in a local ChromaDB collection.

#### Scenario: Indexing a clinical protocol PDF

- GIVEN a clinical recovery protocol PDF in `textos/`
- WHEN processed by the ingestion service using BGE-M3
- THEN chunks are generated with vector embeddings and stored in ChromaDB with metadata (`doc_id`, `chunk_idx`, `title`, `version_hash`)

### Requirement: Instant Hot-Swap Upload and Ingestion

The system MUST ingest newly uploaded clinical documents into ChromaDB instantly without requiring server restart or interrupting active sessions.

#### Scenario: Uploading a new clinical document at runtime

- GIVEN the backend and voice agent are actively running
- WHEN a new clinical PDF is uploaded via the admin console
- THEN the document is parsed, embedded, and added to the active ChromaDB collection within 3 seconds

### Requirement: Zero-Stale-Version Deletion Hooks

The system MUST purge existing vector chunks matching a document ID prior to re-ingestion or deletion to guarantee zero cross-version contamination.

#### Scenario: Deleting or updating an existing document

- GIVEN an existing clinical document `doc_id: proto_lap_v1` exists in ChromaDB
- WHEN a deletion request or updated version upload is triggered for `proto_lap_v1`
- THEN all vector chunks associated with `proto_lap_v1` are deleted prior to inserting new chunks, ensuring no stale retrieval matches occur

### Requirement: Per-Answer Source Citation and Traceability

The system MUST include precise source citations (`[Doc: title, Chunk ID]`) in every agent response derived from RAG retrieval.

#### Scenario: Generating a traceable clinical answer

- GIVEN a patient query about post-op diet restrictions answered using retrieved chunks from `Protocolo_Laparoscopia.pdf`
- WHEN the Llama reasoning model generates the response
- THEN the response payload includes structured source citations referencing the exact document title and chunk ID used
