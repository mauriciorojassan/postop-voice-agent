# Apply Progress: Post-Operative Voice Follow-Up Agent

## Unit 1 / Phase 1 (Scaffold & Reproducible Bootstrap)
- **Status**: Completed
- **Completed Tasks**: 1.1, 1.2, 1.3, 1.4, 1.5
- **Files Created**:
  - `requirements.txt` (pinned dependencies with Python 3.12 compatibility)
  - `.env.example` (GROQ_API_KEY template)
  - `.gitignore` (venv, .env, .pdf, chroma_db/, test_chroma/)
  - `backend/__init__.py`
  - `backend/main.py` (FastAPI app, CORS, `/health`, `/admin` static mount)
  - `tests/__init__.py`
  - `tests/test_main.py` (Unit test for `/health` and security check that API key is not hardcoded)
  - `scripts/setup.sh` (12-min reproducible bootstrap script)
  - `README.md` (Setup instructions and verification steps)
- **Verification**:
  - `pytest` executed successfully (`2 passed`).
  - `/health` endpoint verified.
- **Rollback Boundary**: Revert PR 1 files; nothing else has landed.

## Unit 2 / Phase 2 (RAG Hot-Swap Service)
- **Status**: Completed
- **Completed Tasks**: 2.1, 2.2, 2.3, 2.4
- **Files Created / Modified**:
  - `backend/services/rag.py` (ChromaDB + BGE-M3, chunking 512/64, metadata-hashed versioning, zero-contamination upsert-purge, retrieval with source citations, scanned-PDF handling)
  - `scripts/ingest.py` (CLI ingest of clinical PDFs with stats)
  - `tests/test_rag.py` (chunk overlap boundaries, v1→v2 zero contamination, deletion forgets)
- **Verification**:
  - `pytest tests/test_rag.py` executed successfully (`5 passed`).
  - RAG hot-swap ingestion, zero contamination, chunking boundaries, and deletion verified via automated tests.
- **Rollback Boundary**: Revert `backend/services/rag.py`, `scripts/ingest.py`, `tests/test_rag.py`.

## Unit 3 / Phase 3 (Escalation Engine + Summary shape)
- **Status**: Completed
- **Completed Tasks**: 3.1, 3.2, 3.3, 3.4
- **Files Created / Modified**:
  - `backend/services/escalation.py` (Deterministic red-flag floor with 8-category Colombian Spanish regex matrix, Llama via Groq contextual reasoning, composition rule preventing floor de-escalation of LLM rojo, Pydantic triage decision payload schema, call summary shape generator)
  - `tests/test_escalation.py` (Parametrized unit tests covering all 8 red-flag categories, trajectory snapshot binding, floor & LLM composition rules, Groq unavailability safe fallback, and call summary validation)
- **Verification**:
  - `pytest tests/test_escalation.py` executed successfully (`32 passed`).
- **Rollback Boundary**: Revert `backend/services/escalation.py` and `tests/test_escalation.py` only.

## Unit 4 / Phase 4 (Admin Knowledge Console)
- **Status**: Completed
- **Completed Tasks**: 4.1, 4.2, 4.3
- **Files Created / Modified**:
  - `backend/routers/admin.py` (REST endpoints POST/GET/DELETE `/api/documents`, filename sanitization via `os.path.basename`, path traversal prevention, PDF extension validation, document registry tracking status: Processing / Processed and Available / Error, purging Chroma chunks and source PDF on delete)
  - `backend/main.py` (Registered admin router under `/api`)
  - `console/index.html` (Minimal admin dashboard HTML with Tailwind styling, upload form, and indexed documents table)
  - `console/admin.js` (Frontend logic for uploading documents, rendering status badges, and deleting documents)
  - `tests/test_admin.py` (Unit and integration tests verifying path traversal rejection, non-PDF rejection, upload -> status becomes Processed and Available, list documents, and delete -> Chroma purge)
- **Verification**:
  - `pytest tests/test_admin.py` and full `pytest` suite executed successfully (`40 passed`).
- **Rollback Boundary**: Revert `backend/routers/admin.py`, `tests/test_admin.py`, `console/`, and router registration in `backend/main.py`.
