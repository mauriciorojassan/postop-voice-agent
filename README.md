# Post-Operative Voice Follow-Up Agent (Colombian Spanish)

An enterprise-grade, real-time bidirectional voice assistant for post-operative patient follow-up in Colombian Spanish. Features low-latency speech-to-text (STT), hot-swappable RAG with metadata hashing, a deterministic clinical safety floor coupled with Llama 3 reasoning, local text-to-speech (TTS), and a comprehensive evaluation harness.

---

## 15-Minute Reproducible Setup

### 1. Clone & Virtual Environment
```bash
git clone <repo-url> postop-voice-agent
cd postop-voice-agent
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
cp .env.example .env
# Populate GROQ_API_KEY=gsk_... in .env
```

### 4. Model & Vector Store Initialization
Embeddings (BGE-M3) and TTS weights (Kokoro-82M / Piper) auto-download upon first initialization.

### 5. Run Application
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Verify Operational State
- Health check: `curl -s http://localhost:8000/health`
- Admin Console: Access static dashboard at `http://localhost:8000/admin`
- Interactive API Docs: `http://localhost:8000/docs`

---

## Models Used & Rationale (G3 Declaration)

| Component | Model / Technology | Rationale |
|---|---|---|
| **Speech-to-Text (STT)** | Groq Whisper Large V3 | Ultra-low latency (<150ms transcription) with regional Colombian Spanish vocabulary prompting (`capa2_ruidosa`). |
| **Reasoning & Triage** | Llama 3 via Groq API | High-speed inference adhering strictly to the allowed model family with zero cold-start overhead. |
| **Embeddings** | BGE-M3 (`BAAI/bge-m3`) | State-of-the-art multi-lingual embedding model optimized for Spanish clinical text retrieval. |
| **Vector Store** | ChromaDB (Local Persistent) | Zero external server dependency, fast metadata filtering, and metadata-hashed version purging. |
| **Text-to-Speech (TTS)** | Kokoro-82M ONNX / Piper | Natural-sounding local synthesis with automatic fallback if load exceeds 5s. |

---

## Evaluation Harness & Run Command

Run the evaluation suite against the dataset (via local path):
```bash
python eval/run_eval.py --dataset /path/to/dataset_final.xlsx --offline
```
- Measures triage accuracy, latency (P50 < 600ms, P95 < 950ms), and confusion matrix.
- Enforces eliminatory safety gate: **zero missed `rojo` red flags**.

## Deliverables

- [Final Technical Report](FINAL_REPORT.md)
- [Architecture Diagram](ARCHITECTURE_DIAGRAM.md)
- Video Demo: **[Video Demo link pending upload]**

Before final submission, upload the video demo to YouTube as **unlisted**, then replace the placeholder above with the resulting direct link. Do not invent or publish a URL before the upload exists.

The repository includes the [MIT License](LICENSE). Use [.env.example](.env.example) as the safe starting point for local configuration; keep secrets in `.env` and out of version control.

---

## Rubric Map & Deliverables

- **Phase 1 (Scaffold & Setup)**: Pinned requirements, setup automation, FastAPI app & health endpoint.
- **Phase 2 (Hot-Swap RAG)**: ChromaDB integration, BGE-M3 embeddings, 512/64 chunking, version-hash purging.
- **Phase 3 (Escalation Engine)**: Deterministic red-flag safety floor (Colombian Spanish regex rules), Llama 3 reasoning, and Pydantic decision schema.
- **Phase 4 (Admin Console)**: Secure REST endpoints for PDF upload/management, path-traversal prevention, and static dashboard.
- **Phase 5 (Conversation Manager)**: Adaptive multi-domain state machine, clarification loops for ambiguous inputs (`capa2`), and escalation handoffs.
- **Phase 6 (Voice Loop)**: WebSocket audio streaming (`/ws/voice`), STT/TTS integration, rate limiting, and session summary records.
- **Phase 7 (Evaluation & Docs)**: Comprehensive evaluation runner, latency budgets, confusion matrix, and reproducible setup guide.
