# Apply Progress: Units 1 & 2 / Phases 1 & 2

- **Status**: Unit 2 Completed (RAG Hot-Swap Service)
- **Completed Tasks**: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4
- **Files Created / Modified**:
  - `requirements.txt` (pinned dependencies)
  - `.env.example`, `.gitignore`
  - `backend/main.py`, `backend/services/rag.py`
  - `scripts/setup.sh`, `scripts/ingest.py`
  - `tests/test_main.py`, `tests/test_rag.py`
  - `README.md`
- **Verification**:
  - `pytest` executed successfully (`5 passed` across `test_main.py` and `test_rag.py`).
  - RAG hot-swap ingestion, zero contamination, chunking boundaries, and deletion verified via automated tests.
- **Rollback Boundary**: Revert PR 2 files (`backend/services/rag.py`, `scripts/ingest.py`, `tests/test_rag.py`) for Unit 2 rollback.
