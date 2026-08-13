# Post-Operative Voice Follow-Up Agent (Colombian Spanish)

An enterprise-grade, real-time bidirectional voice assistant for post-operative patient follow-up in Colombian Spanish. Features low-latency speech-to-text (STT), hot-swappable RAG with metadata hashing, a deterministic clinical safety floor coupled with Llama 3 reasoning, local text-to-speech (TTS), and a comprehensive evaluation harness.

---

## Linux Demo: Real Microphone Voice Loop

The supported route is Linux with Python 3.12 and `STT_PROVIDER=local`: real browser microphone audio (`audio.webm`) goes through the WebSocket to Faster-Whisper, then the response is spoken by the browser. This is not real telephony; it is a web call using a microphone and WebSocket with manual turn submission.

### 1. Clone & Virtual Environment
```bash
git clone <repo-url> postop-voice-agent
cd postop-voice-agent
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
cp .env.example .env
# Local STT is the default. Groq is optional.
```

### 4. Initial Model Download
`faster-whisper` runs locally on CPU with int8. The model downloads on first local transcription, so the first turn needs network access and disk space; this is not included in a 15-minute setup promise. Set `LOCAL_WHISPER_MODEL=tiny` for a faster demo. Tests do not download models.

### 5. Run Application
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000/call` in Chrome/Chromium and allow microphone permission. Browser Speech Synthesis is the base audible response path; WAV audio from the backend remains supported when available. Groq can be selected with `STT_PROVIDER=groq` and a real `GROQ_API_KEY`.

### 6. Verify Operational State
- Health check: `curl -s http://localhost:8000/health`
- Admin Console: Access static dashboard at `http://localhost:8000/admin`
- Interactive API Docs: `http://localhost:8000/docs`

---

## Models Used & Rationale (G3 Declaration)

| Component | Model / Technology | Rationale |
|---|---|---|
| **Speech-to-Text (STT)** | Faster-Whisper local CPU/int8 by default; Groq optional | Real Spanish transcription from `audio.webm`; no fake transcript fallback. |
| **Reasoning & Triage** | Llama 3 via Groq API | High-speed inference adhering strictly to the allowed model family with zero cold-start overhead. |
| **Embeddings** | BGE-M3 (`BAAI/bge-m3`) | State-of-the-art multi-lingual embedding model optimized for Spanish clinical text retrieval. |
| **Vector Store** | ChromaDB (Local Persistent) | Zero external server dependency, fast metadata filtering, and metadata-hashed version purging. |
| **Text-to-Speech (TTS)** | Kokoro-82M ONNX / Piper | Natural-sounding local synthesis with automatic fallback if load exceeds 5s. |

---

## Evaluation Harness & Run Command

Run the evaluation suite against the dataset (via local path):
```bash
.venv/bin/python eval/run_eval.py --dataset /path/to/dataset_final.xlsx --offline
```
- Measures triage accuracy, latency (P50 < 600ms, P95 < 950ms), and confusion matrix.
- Enforces eliminatory safety gate: **zero missed `rojo` red flags**.
- The repository suite currently verifies **57 tests**.

## Deliverables

- [Final Technical Report](FINAL_REPORT.md)
- [Architecture Diagram](ARCHITECTURE_DIAGRAM.md)
- [Local Video Demo](demo/postop-voice-agent-demo.mp4)
- [Video Demo](https://youtu.be/RGncO51IokA) — YouTube unlisted and published

The video demo is published on YouTube as **unlisted** and is accessible through the direct link above.

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
